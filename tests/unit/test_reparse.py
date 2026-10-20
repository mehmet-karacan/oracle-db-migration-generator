from dataclasses import replace

import pytest

from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.oracle.reparse import reparse_target
from tests.factories import actual,source


def test_reparse_recovers_old_parser_failure_without_opening_a_connection(monkeypatch):
    monkeypatch.setattr('socket.create_connection',lambda *a,**k: (_ for _ in ()).throw(AssertionError('network')))
    snapshot=actual('CREATE EDITIONABLE PROCEDURE APP.P AS BEGIN NULL; END;\n/')
    obj=snapshot.objects[0]
    props=dict(obj.properties);props['projection']=KnownValue('UNKNOWN',None,obj.evidence_ids)
    obj=replace(obj,projection=None,properties=props,coverage=replace(obj.coverage,ddl='PARTIAL',diagnostics=('PARSER_SYNTAX_ERROR',)))
    old=replace(snapshot,objects=(obj,),completeness=replace(snapshot.completeness,ddl='PARTIAL'))
    updated=reparse_target(old)
    assert updated.completeness.ddl=='COMPLETE'
    assert updated.objects[0].properties['projection'].state=='KNOWN'
    assert updated.objects[0].raw_ddl==obj.raw_ddl
    assert updated.capabilities['reparsed_from_snapshot'].value==old.semantic_digest


def test_reparse_keeps_metadata_unknown_and_rejects_source_direction():
    with pytest.raises(ValueError,match='TARGET_SNAPSHOT_REQUIRED'):
        reparse_target(source('CREATE TABLE APP.T(ID NUMBER);'))
    snapshot=actual('CREATE TABLE APP.T(ID NUMBER);')
    obj=snapshot.objects[0]
    props=dict(obj.properties);props['dictionary.columns']=KnownValue('UNKNOWN',None,obj.evidence_ids)
    old=replace(snapshot,objects=(replace(obj,properties=props),),completeness=replace(snapshot.completeness,dictionary='PARTIAL'))
    result=reparse_target(old)
    assert result.completeness.dictionary=='PARTIAL'
    assert result.objects[0].properties['dictionary.columns'].state=='UNKNOWN'


def test_reparse_does_not_drop_sidecars_when_dictionary_rows_are_unavailable():
    snapshot=actual("CREATE TABLE APP.T(ID NUMBER); COMMENT ON TABLE APP.T IS 'kept'; GRANT SELECT ON APP.T TO READER;")
    result=reparse_target(snapshot)
    assert {obj.object_key for obj in snapshot.objects}<={obj.object_key for obj in result.objects}
    assert any(obj.properties.get('text') and obj.properties['text'].value=='kept' for obj in result.objects)


def test_metadata_without_sql_terminators_preserves_backing_index_context():
    import hashlib
    from oracle_db_migration_generator.oracle.ddl_model import project_target_object
    snapshot=actual('CREATE TABLE APP.T(ID NUMBER);')
    raw=b'CREATE TABLE APP.T(ID NUMBER) CREATE UNIQUE INDEX APP.PK_T ON APP.T(ID) ALTER TABLE APP.T ADD CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX APP.PK_T ENABLE'
    obj=replace(snapshot.objects[0],raw_ddl=raw,ddl_sha256=hashlib.sha256(raw).hexdigest())
    updated,evidence=project_target_object(obj)
    assert updated.coverage.ddl=='COMPLETE'
    assert 'PK_T' in updated.projection.properties['constraints']
    assert b'CREATE UNIQUE INDEX' in updated.raw_ddl
    assert evidence and all(item.sha256==obj.ddl_sha256 for item in evidence)


def test_storage_maxsize_is_validated_without_losing_the_original_clause():
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    raw=b'CREATE TABLE APP.T(ID NUMBER) STORAGE(INITIAL 65536 MAXSIZE UNLIMITED BUFFER_POOL DEFAULT);'
    result=parse_ddl(raw,None)
    assert result.coverage=='COMPLETE'
    assert 'MAXSIZE UNLIMITED' in result.objects[0].projection.properties['table_properties']['storage']
    invalid=parse_ddl(raw.replace(b'MAXSIZE UNLIMITED',b'MAXSIZE WHAT EVER'),None)
    assert invalid.coverage!='COMPLETE'


@pytest.mark.parametrize('sql',[
    b'CREATE TABLE APP.T(C NUMBER DEFAULT STORAGE(MAXSIZE 1));',
    b'CREATE TABLE APP.T(C NUMBER) STORAGE(MAXSIZE 1 MAXSIZE 2 INITIAL 65536);',
    b'CREATE TABLE APP.T AS SELECT STORAGE(MAXSIZE 1) C FROM DUAL;',
])
def test_maxsize_compatibility_cannot_validate_an_expression_or_duplicate(sql):
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    result=parse_ddl(sql,None)
    assert result.coverage!='COMPLETE'
    assert not any(obj.parse_ok for obj in result.objects)


def test_maxsize_in_constraint_backing_index_is_a_real_storage_clause():
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    raw=b'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX STORAGE(INITIAL 65536 MAXSIZE UNLIMITED) ENABLE);'
    assert parse_ddl(raw,None).coverage=='COMPLETE'


def test_metadata_mode_still_accounts_for_every_trailing_statement():
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    raw=b'CREATE TABLE APP.T(ID NUMBER) ALTER TABLE APP.T ADD(CODE NUMBER)'
    assert parse_ddl(raw,None).coverage!='COMPLETE'
    parsed=parse_ddl(raw,None,metadata=True)
    assert parsed.coverage=='COMPLETE' and len(parsed.sidecars)==1
    destructive=parse_ddl(b'CREATE TABLE APP.T(ID NUMBER) DROP TABLE APP.OTHER',None,metadata=True)
    assert destructive.coverage!='COMPLETE' and 'UNSUPPORTED_STATEMENT' in destructive.diagnostics
