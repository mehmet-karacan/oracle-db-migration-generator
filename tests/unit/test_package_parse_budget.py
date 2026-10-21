import base64
import pytest
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.parsing.worker import parse_payload
from oracle_db_migration_generator.model.identity import Identifier,ObjectIdentity


def hint(kind):return ObjectIdentity('demo-source',Identifier.parse('APP'),kind,Identifier.parse('P'))


@pytest.mark.parametrize('kind,size,seconds,complete',[
    ('PACKAGE_BODY',128*1024+1,202,True),
    ('PACKAGE_BODY',128*1024,202,False),
    ('PACKAGE_SPEC',128*1024+1,202,False),
    ('TABLE',128*1024+1,202,False),
    ('PACKAGE_BODY',128*1024+1,241,False),
])
def test_measured_large_body_budget_is_bounded_and_does_not_expand_other_units(monkeypatch,kind,size,seconds,complete):
    statement={'PACKAGE_BODY':b'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;',
               'PACKAGE_SPEC':b'CREATE PACKAGE APP.P AS PROCEDURE R; END P;',
               'TABLE':b'CREATE TABLE APP.P (ID NUMBER);'}[kind]
    raw=statement+b' '*(size-len(statement))
    def response(payload,owner,timeout,metadata=False):
        # The real grammar still validates successful requests. Only elapsed
        # worker time is simulated so the 202/241-second boundary is deterministic.
        if timeout<seconds:raise TimeoutError('PARSER_TIMEOUT')
        return parse_payload({'raw':base64.b64encode(payload).decode(),'default_schema':owner,'metadata':metadata})
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.request_parse',response)
    result=parse_ddl(raw,hint(kind))
    assert (result.coverage=='COMPLETE') is complete
    if not complete:assert result.diagnostics==('PARSER_TIMEOUT',)
