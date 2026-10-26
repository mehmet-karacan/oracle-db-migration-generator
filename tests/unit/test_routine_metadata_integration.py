"""A normal Oracle capture must persist its bounded read-only compiler evidence."""
from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from oracle_db_migration_generator.oracle.collector import TargetObservation
from oracle_db_migration_generator.runtime.worker import save_observation
from oracle_db_migration_generator.source.oracle_reader import save_source
from oracle_db_migration_generator.source.oracle_reader import from_observation
from oracle_db_migration_generator.source.models import SourceArtifact
from tests.factories import actual


class Cursor:
    def __init__(self):
        self.sql=[];self.rows=[]

    def execute(self,sql,binds=None):
        self.sql.append(sql)
        normalized=' '.join(sql.upper().split());binds=binds or {}
        assert normalized.startswith('SELECT ') or normalized=='SET TRANSACTION READ ONLY'
        name=binds.get('name')
        if 'SESSION_USER' in normalized and 'FROM DUAL' in normalized:self.rows=[('APP',)]
        elif 'FROM ALL_OBJECTS' in normalized:self.rows=[('PROCEDURE','VALID','2026-10-26T10:00:00',None)] if name=='P' else [('TABLE','VALID','2026-10-26T10:00:00',None)]
        elif 'FROM ALL_DEPENDENCIES' in normalized:self.rows=[('P','PROCEDURE','APP','T','TABLE',None,'HARD')] if name=='P' else []
        elif 'FROM ALL_PLSQL_OBJECT_SETTINGS' in normalized:self.rows=[('PROCEDURE',2,'INTERPRETED','FALSE','DISABLE:ALL','BYTE',None,'IDENTIFIERS:NONE')]
        elif 'FROM ALL_PROCEDURES' in normalized:self.rows=[(None,1,None,'PROCEDURE','DEFINER','NO','NO','NO','NO','NO','NO')] if name=='P' else []
        elif 'FROM ALL_TAB_COLS' in normalized:self.rows=[('ID','NUMBER',None,22,None,None,0,None,'Y',1,'NO','NO','NO','NO',None)] if name=='T' else []
        elif 'GET_DDL' in normalized:self.rows=[('CREATE PROCEDURE APP.P IS BEGIN SELECT 1 INTO N FROM APP.T; END;' if name=='P' else 'CREATE TABLE APP.T (ID NUMBER)',)]
        else:self.rows=[]

    def fetchall(self):return self.rows
    def close(self):pass


class CloseFailureCursor(Cursor):
    def close(self):raise RuntimeError('cursor close failed')


class Connection:
    version='19.0.0.0.0'
    def __init__(self):self.read=Cursor();self.rolled_back=False;self.closed=False
    def cursor(self):return self.read
    def rollback(self):self.rolled_back=True
    def close(self):self.closed=True


def test_metadata_cleanup_error_preserves_main_capture_and_closes_connection():
    from oracle_db_migration_generator.oracle.routine_metadata import complete_routine_observation
    connection=Connection();connection.read=CloseFailureCursor()
    result=complete_routine_observation(source_observation(),config(),
        lambda _key:SimpleNamespace(username='APP',password='secret'),
        connect=lambda _config,_credential:connection)
    assert result.snapshot.capabilities.get('routine_metadata') is None
    assert result.receipt['routine_metadata']['status']=='UNAVAILABLE'
    assert connection.rolled_back and connection.closed


def source_observation():
    sql='CREATE TABLE APP.T(ID NUMBER); CREATE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT ID INTO N FROM APP.T; END;'
    raw=sql.encode();artifact=SourceArtifact('app/fixture.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    observation=from_observation(TargetObservation(actual(sql),{'status':'CAPTURED'},(artifact,)),
                                 connection_id='source-c')
    snapshot=observation.snapshot
    snapshot=replace(snapshot,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)}) if obj.identity.object_type=='PROCEDURE'
        else obj for obj in snapshot.objects))
    return replace(observation,snapshot=snapshot)


def config():
    return SimpleNamespace(schema_mappings=(SimpleNamespace(target_schema='APP',credential_id='c',metadata_reader=None),),
                           capture_timeout_seconds=120)


def test_normal_source_and_target_capture_attach_and_archive_read_only_metadata(tmp_path):
    from oracle_db_migration_generator.oracle.routine_metadata import complete_routine_observation
    connections=[]
    def connect(_config,_credential):
        conn=Connection();connections.append(conn);return conn
    credentials=lambda _key:SimpleNamespace(username='APP',password='secret')
    captured_source=complete_routine_observation(source_observation(),config(),credentials,connect=connect)
    assert captured_source.receipt['routine_metadata']['status']=='CAPTURED'
    assert captured_source.snapshot.capabilities['routine_metadata'].state=='KNOWN'
    source_path=tmp_path/'source';save_source(captured_source,source_path)
    restored_source=load_snapshot(source_path/'source-snapshot.json',require_ddl=True)
    assert restored_source.capabilities['routine_metadata'].state=='KNOWN'
    assert all(query.upper().startswith('SELECT') or query=='SET TRANSACTION READ ONLY'
               for query in connections[0].read.sql)
    target=TargetObservation(actual('CREATE TABLE APP.T(ID NUMBER);'),{'status':'CAPTURED'},())
    captured_target=complete_routine_observation(target,config(),credentials,source=restored_source,connect=connect)
    assert captured_target.receipt['routine_metadata']['status']=='CAPTURED'
    target_path=tmp_path/'target';save_observation(captured_target,target_path)
    evidence=next(ev for ev in captured_target.snapshot.evidence if ev.query_id=='oracle.compiled-static/v1')
    assert (target_path/evidence.path).is_file()
    assert all(conn.rolled_back and conn.closed for conn in connections)
