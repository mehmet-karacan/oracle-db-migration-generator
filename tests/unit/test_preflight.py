import json
from pathlib import Path

import pytest

from oracle_db_migration_generator.oracle.preflight import probe_target
from oracle_db_migration_generator.config.loader import load_targets
from oracle_db_migration_generator.config.credentials import Credentials, EnvCredentialResolver

ROOT = Path(__file__).resolve().parents[2]


class Cursor:
    def __init__(self, denied=False):
        self.calls = []
        self.current = ''
        self.denied = denied

    def execute(self, statement, binds=None):
        self.current = statement
        self.calls.append((statement, binds))
        if self.denied and 'USER_OBJECTS' in statement.upper():
            raise RuntimeError('ORA-01031: synthetic-password must not leak')

    def fetchone(self):
        if 'SYS_CONTEXT' in self.current:
            return ('APP',)
        if 'GET_DDL' in self.current:
            return ('CREATE TABLE APP.DEMO (ID NUMBER)',)
        if 'ROWNUM' in self.current:
            return None
        raise AssertionError(self.current)

    def fetchall(self):
        return [('TABLE', 'DEMO', 'VALID', '2026-01-01T00:00:00')]

    def close(self):
        pass


class Connection:
    version = '19.0.0.0.0'

    def __init__(self, denied=False):
        self.reader = Cursor(denied)
        self.closed = False
        self.rolled_back = False

    def cursor(self):
        return self.reader

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def config():
    return load_targets(ROOT / 'examples/targets.example.json', ('DEMO-TEST',))[0]


def test_collector_uses_no_business_data_or_nextval():
    connection = Connection()
    result = probe_target(config(), lambda _: Credentials('APP', 'synthetic-password'), connect=lambda *_: connection)
    assert result['status'] == 'PASSED'
    assert result['comparison_status'] == 'NOT_RUN'
    assert result['difference_count'] is None
    statements = [sql.strip().upper() for sql, _ in connection.reader.calls]
    assert statements[0] == 'SET TRANSACTION READ ONLY'
    assert all(sql.startswith('SELECT ') for sql in statements[1:])
    assert not any(word in sql for sql in statements for word in ['NEXTVAL', 'DBMS_SQL', 'CREATE TABLE', 'INSERT INTO'])
    assert connection.closed and connection.rolled_back
    assert 'synthetic-password' not in json.dumps(result)


def test_metadata_failure_is_not_empty_or_success():
    connection = Connection(denied=True)
    result = probe_target(config(), lambda _: Credentials('APP', 'synthetic-password'), connect=lambda *_: connection)
    assert result['status'] == 'FAILED'
    assert result['difference_count'] is None
    assert result['schemas'][0]['error_code'] == 'ORA-01031'
    assert 'synthetic-password' not in json.dumps(result)
    assert connection.closed


def test_multi_schema_target_uses_isolated_credentials(tmp_path):
    data = json.loads((ROOT / 'examples/targets.example.json').read_text(encoding='utf-8'))
    data['targets'][0]['schema_mappings'].append({'source_schema':'OTHER', 'target_schema':'OTHER', 'credential_id':'other'})
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    target = load_targets(path, ('DEMO-TEST',))[0]
    resolved = []
    connections = []
    def resolve(key):
        resolved.append(key)
        return Credentials('APP' if key != 'other' else 'OTHER', 'synthetic-password')
    def connect(_target, credential):
        connection = Connection()
        if credential.username == 'OTHER':
            original = connection.reader.fetchone
            connection.reader.fetchone = lambda: ('OTHER',) if 'SYS_CONTEXT' in connection.reader.current else original()
        connections.append(connection)
        return connection
    result = probe_target(target, resolve, connect=connect)
    assert result['status'] == 'PASSED'
    assert resolved == ['demo-test-oracle-ro', 'other']
    assert len(connections) == 2 and all(c.closed for c in connections)


def test_credentials_have_no_repr_and_existing_environment_wins(tmp_path):
    path = tmp_path / 'credentials.env'
    path.write_text('DEMO_USER=APP\nDEMO_PASSWORD=file-secret\n', encoding='utf-8')
    resolver = EnvCredentialResolver(path, {'DEMO_PASSWORD': 'environment-secret'})
    credential = resolver('DEMO')
    assert credential.password == 'environment-secret'
    assert 'secret' not in repr(credential)
    with pytest.raises(ValueError):
        resolver('missing')


def test_provider_value_error_that_looks_like_code_is_not_echoed():
    from oracle_db_migration_generator.oracle.preflight import safe_error_code
    assert safe_error_code(ValueError('SYNTHETIC_SECRET')) == 'CONNECTION_OR_METADATA_ERROR'
