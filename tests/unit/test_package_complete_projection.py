from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.model.identity import Identifier,ObjectIdentity
HINT=ObjectIdentity('demo-source',Identifier.parse('APP'),'PACKAGE_BODY',Identifier.parse('P'))

def test_nested_package_routines_are_fully_verified_and_retained():
    raw=b'CREATE PACKAGE BODY APP.P AS PROCEDURE OUTER_R IS PROCEDURE INNER_R IS BEGIN COMMIT; END; BEGIN INNER_R; END; END P;'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE'
    item=result.objects[0]
    assert item.raw_ddl==raw
    routines=item.projection.properties['routines']
    assert [routine.name for routine in routines]==['OUTER_R','OUTER_R.INNER_R']
    assert routines[0].transactions==()
    assert routines[1].transactions==('COMMIT',)


def test_large_fully_parsed_package_retains_all_declarations():
    raw=('CREATE PACKAGE BODY APP.P AS '+''.join(f'V_{i} VARCHAR2(100);\n' for i in range(7000))+'END P;').encode()
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE'
    assert len(result.objects[0].projection.properties['declarations']['variable_declaration'])==7000


def test_nested_package_malformed_body_does_not_become_verified():
    result=parse_ddl(b'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN broken syntax; END; END P;',HINT)
    assert result.coverage!='COMPLETE'
