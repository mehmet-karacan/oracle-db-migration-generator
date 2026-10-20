import json
from pathlib import Path

from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.config.loader import load_source_profile, load_targets
from oracle_db_migration_generator.oracle.collector import collect_target, get_dependent_ddl

ROOT = Path(__file__).resolve().parents[2]


class FakeCursor:
    def __init__(self, inventory=None, denied=None, changing=False):
        self.inventory = inventory or []
        self.denied = denied
        self.changing = changing
        self.inventory_reads = 0
        self.calls = []
        self.current = ''
        self.description = None

    def execute(self, query, binds=None):
        self.calls.append((query, binds))
        self.current = query
        if self.denied and self.denied in query.upper():
            raise RuntimeError('ORA-01031: synthetic-password')

    def fetchone(self):
        upper = self.current.upper()
        if 'SYS_CONTEXT' in upper:
            return ('APP',)
        if 'GET_DDL' in upper:
            return ('CREATE TABLE APP.DEMO (ID NUMBER);',)
        return None

    def fetchall(self):
        upper = self.current.upper()
        if 'ALL_OBJECTS' in upper and 'LAST_DDL_TIME' in upper:
            self.inventory_reads += 1
            if self.changing:
                return [('TABLE','DEMO','VALID',str(self.inventory_reads))]
            return self.inventory
        return []

    def close(self):
        pass


class FakeConnection:
    version = '19.0.0.0.0'

    def __init__(self, **kwargs):
        self.reader = FakeCursor(**kwargs)
        self.closed = False
        self.rollbacks = 0

    def cursor(self):
        return self.reader

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def inputs():
    return (load_targets(ROOT / 'examples/targets.example.json', ('DEMO-TEST',))[0],
            load_source_profile(ROOT / 'examples/source-profile.example.json'))


def test_ora01031_is_not_absence():
    target, profile = inputs()
    connection = FakeConnection(denied='ALL_OBJECTS')
    result = collect_target(target, lambda _: Credentials('APP','synthetic-password'), profile,
                            connect=lambda *_: connection)
    assert result.snapshot is None
    assert result.receipt['status'] == 'ERROR'
    assert result.receipt['difference_count'] is None
    assert 'synthetic-password' not in json.dumps(result.receipt)
    assert connection.closed


def test_dependent_ddl_unexpected_error_propagates():
    import pytest
    class Cursor:
        def execute(self, *_):
            raise RuntimeError('ORA-01031: synthetic-password')
    with pytest.raises(RuntimeError):
        get_dependent_ddl(Cursor(),'COMMENT','DEMO','APP', inventory_complete=True)


def test_empty_visible_schema_requires_complete_inventory():
    target, profile = inputs()
    good = collect_target(target, lambda _: Credentials('APP','secret'), profile,
                          connect=lambda *_: FakeConnection())
    assert good.snapshot is not None
    assert good.snapshot.completeness.inventory == 'COMPLETE'
    assert len(good.snapshot.objects) == 0
    assert any(ev.kind == 'ABSENCE_SCOPE' for ev in good.snapshot.evidence)
    denied = collect_target(target, lambda _: Credentials('APP','secret'), profile,
                            connect=lambda *_: FakeConnection(denied='ALL_TAB_COLS'))
    assert denied.snapshot.completeness.dictionary != 'COMPLETE'


def test_snapshot_changes_during_capture():
    target, profile = inputs()
    connections = []
    def connect(*_):
        c = FakeConnection(changing=True)
        connections.append(c)
        return c
    observation = collect_target(target, lambda _: Credentials('APP','secret'), profile,connect=connect)
    assert observation.receipt['status'] == 'INCONSISTENT'
    assert observation.snapshot is None
    assert len(connections) == 2 and all(c.closed for c in connections)


def test_collector_uses_no_business_data_or_nextval():
    target, profile = inputs()
    connection = FakeConnection()
    observation = collect_target(target, lambda _: Credentials('APP','secret'), profile, connect=lambda *_: connection)
    assert observation.snapshot is not None
    queries = [sql.strip().upper() for sql,_ in connection.reader.calls]
    assert all(sql == 'SET TRANSACTION READ ONLY' or sql.split()[0]=='SELECT' for sql in queries)
    assert not any(word in sql for sql in queries for word in ('NEXTVAL','DBMS_SQL','INSERT INTO','CREATE TABLE','FROM APP.'))
    assert connection.closed


def test_each_schema_uses_its_own_credential_and_connection():
    from dataclasses import replace
    from oracle_db_migration_generator.config.models import SchemaMapping
    target,profile=inputs()
    target=replace(target,schema_mappings=(SchemaMapping('APP','APP','C1'),SchemaMapping('OTHER','OTHER','C2')))
    connected=[]
    class OwnCursor(FakeCursor):
        def fetchone(self):
            return (self.owner,) if 'SYS_CONTEXT' in self.current.upper() else super().fetchone()
    def connect(config,credential):
        connection=FakeConnection();connection.reader=OwnCursor();connection.reader.owner=credential.username
        connected.append((credential.username,connection));return connection
    result=collect_target(target,lambda key:Credentials('APP' if key=='C1' else 'OTHER','synthetic'),profile,connect=connect)
    assert result.snapshot.schemas==('APP','OTHER')
    assert [owner for owner,_ in connected]==['APP','OTHER']
    assert all(connection.closed for _,connection in connected)
    assert all(binds['owner']==owner for owner,connection in connected for _,binds in connection.reader.calls if binds and 'owner' in binds)


def test_cleanup_failure_is_an_error_receipt():
    target,profile=inputs();connection=FakeConnection()
    def close(): raise RuntimeError('synthetic-secret')
    connection.reader.close=close
    result=collect_target(target,lambda _:Credentials('APP','synthetic-secret'),profile,connect=lambda *_:connection)
    assert result.snapshot is None and result.receipt['status']=='ERROR'
    assert result.receipt['schemas'][0]['error_code']=='TARGET_CAPTURE_CLEANUP_FAILED'
    assert connection.closed and 'synthetic-secret' not in json.dumps(result.receipt)


def test_recyclebin_and_user_security_grants_are_explicitly_outside_object_scope():
    from oracle_db_migration_generator.oracle.collector import _sidecar_artifacts
    groups={'grants':[
        {'table_name':'T','grantee':'READER','privilege':'SELECT','grantable':'NO','object_type':'TABLE'},
        {'table_name':'BIN$synthetic$0','grantee':'READER','privilege':'SELECT','grantable':'NO','object_type':'TABLE'},
        {'table_name':'APP','grantee':'PUBLIC','privilege':'INHERIT PRIVILEGES','grantable':'NO','object_type':'USER'},
    ]}
    excluded=[]
    artifacts=_sidecar_artifacts(groups,'APP',excluded=excluded)
    raw=b'\n'.join(item.raw for item in artifacts)
    assert b'"APP"."T"' in raw and b'BIN$' not in raw and b'INHERIT PRIVILEGES' not in raw
    assert {item['reason_code'] for item in excluded}=={'INTERNAL_RECYCLEBIN_OBJECT','USER_SECURITY_GRANT_OUT_OF_SCOPE'}


def test_live_collector_compares_trigger_definition_separately_from_export_context():
    from tests.factories import source
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    target,profile=inputs()
    ddl='CREATE EDITIONABLE TRIGGER APP.TR BEFORE INSERT ON APP.T BEGIN NULL; END;\n/\nALTER TRIGGER APP.TR DISABLE;'
    connection=FakeConnection(inventory=[('TRIGGER','TR','VALID','synthetic')])
    class TriggerCursor(FakeCursor):
        def fetchone(self):
            return (ddl,) if 'GET_DDL' in self.current.upper() else super().fetchone()
    connection.reader=TriggerCursor(inventory=[('TRIGGER','TR','VALID','synthetic')])
    result=collect_target(target,lambda _:Credentials('APP','synthetic'),profile,connect=lambda *_:connection)
    desired=source(ddl,profile)
    differences=compare_snapshots(desired,result.snapshot,profile.policy)
    assert not differences.differences
    assert result.snapshot.objects[0].projection.properties['enabled_state']=='DISABLE'
