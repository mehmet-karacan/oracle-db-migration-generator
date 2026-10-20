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


def test_selected_reparse_retains_unselected_objects_and_capture_uncertainty(monkeypatch):
    snapshot=actual('CREATE TABLE APP.T(ID NUMBER); CREATE TABLE APP.OTHER(ID NUMBER);')
    selected=next(obj for obj in snapshot.objects if obj.identity.name.effective_name=='T')
    other=next(obj for obj in snapshot.objects if obj.identity.name.effective_name=='OTHER')
    props=dict(other.properties);props['projection']=KnownValue('UNKNOWN',None,other.evidence_ids)
    other=replace(other,properties=props,projection=None,coverage=replace(other.coverage,ddl='PARTIAL'))
    snapshot=replace(snapshot,objects=(selected,other),completeness=replace(snapshot.completeness,inventory='PARTIAL',ddl='PARTIAL'))
    calls=[]
    import oracle_db_migration_generator.oracle.reparse as module
    real=module.project_target_object
    def record(obj):
        calls.append(obj.object_key)
        return real(obj)
    monkeypatch.setattr(module,'project_target_object',record)
    updated=reparse_target(snapshot,object_keys=(selected.object_key,))
    assert calls==[selected.object_key]
    assert next(obj for obj in updated.objects if obj.object_key==other.object_key)==other
    assert updated.completeness.inventory=='PARTIAL' and updated.completeness.ddl=='PARTIAL'
    assert updated.observed_consistency==snapshot.observed_consistency
    assert updated.capabilities['reparsed_object_keys'].value==(selected.object_key,)


def test_selected_reparse_rejects_unknown_object_key():
    with pytest.raises(ValueError,match='REPARSE_OBJECT_KEY_UNKNOWN'):
        reparse_target(actual('CREATE TABLE APP.T(ID NUMBER);'),object_keys=('unknown',))


def test_selected_reparse_preserves_captured_sidecars_and_their_diagnostics(monkeypatch):
    snapshot=actual("CREATE TABLE APP.T(ID NUMBER); COMMENT ON TABLE APP.T IS 'kept';")
    table=next(obj for obj in snapshot.objects if obj.identity.object_type=='TABLE')
    sidecars=tuple(obj for obj in snapshot.objects if obj.identity.object_type=='COMMENT')
    caps={**snapshot.capabilities,'sidecar_diagnostics':KnownValue('KNOWN',['unchanged'],table.evidence_ids)}
    snapshot=replace(snapshot,capabilities=caps,completeness=replace(snapshot.completeness,ddl='PARTIAL',diagnostics=('SOURCE_SIDECAR_UNRESOLVED',)))
    def forbidden(*args,**kwargs):raise AssertionError('UNCHANGED_DICTIONARY_SIDECARS_MUST_NOT_BE_REGENERATED')
    monkeypatch.setattr('oracle_db_migration_generator.oracle.reparse.merge_sidecars',forbidden)
    updated=reparse_target(snapshot,object_keys=(table.object_key,))
    assert tuple(obj for obj in updated.objects if obj.identity.object_type=='COMMENT')==sidecars
    assert updated.capabilities['sidecar_diagnostics']==caps['sidecar_diagnostics']
    assert updated.completeness.ddl=='PARTIAL'
    assert updated.completeness.diagnostics==snapshot.completeness.diagnostics


def test_empty_selected_reparse_cannot_upgrade_capture_level_ddl_coverage():
    snapshot=actual('CREATE TABLE APP.T(ID NUMBER);')
    snapshot=replace(snapshot,completeness=replace(snapshot.completeness,ddl='PARTIAL'))
    updated=reparse_target(snapshot,object_keys=())
    assert updated.completeness.ddl=='PARTIAL'
    assert updated.objects==snapshot.objects


def test_selected_reparse_deduplicates_existing_context_evidence():
    import hashlib
    from oracle_db_migration_generator.oracle.ddl_model import project_target_object
    snapshot=actual('CREATE TABLE APP.T(ID NUMBER);')
    raw=b'CREATE TABLE APP.T(ID NUMBER) ALTER TABLE APP.T ADD(CODE NUMBER)'
    original=replace(snapshot.objects[0],raw_ddl=raw,ddl_sha256=hashlib.sha256(raw).hexdigest())
    captured,context=project_target_object(original)
    snapshot=replace(snapshot,objects=(captured,),evidence=snapshot.evidence+context)
    updated=reparse_target(snapshot,object_keys=(captured.object_key,))
    assert len(updated.evidence)==len({item.id for item in updated.evidence})
    assert updated.objects[0].properties['projection'].value['columns']['CODE']['data_type']=='NUMBER'


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
