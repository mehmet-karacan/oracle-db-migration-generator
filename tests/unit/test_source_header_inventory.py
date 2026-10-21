from dataclasses import replace
import hashlib

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.model.serialization import thaw
from oracle_db_migration_generator.model.serialization import digest
from oracle_db_migration_generator.parsing import adapter
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
from tests.factories import actual, profile


def timed_out_source(monkeypatch, texts):
    selected = profile()
    artifacts = tuple(SourceArtifact(f'app/file-{i}.sql', 'APP', 'DDL', 'PACKAGE_BODY',
                     text.encode(), hashlib.sha256(text.encode()).hexdigest()) for i, text in enumerate(texts))
    monkeypatch.setattr(adapter, 'parse_ddl', lambda *a, **k: adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE'))
    fingerprint = digest({'commit':'a'*40,'profile':selected,
                          'files':[[item.path,item.kind,item.sha256] for item in artifacts]})
    inputs = SourceInput(SourceRevision('a'*40, None), artifacts, fingerprint)
    return adapter.parse_source(inputs, selected)


def proof_types(snapshot):
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    return verified_inventory_types(snapshot)


def test_timeout_preserves_positive_header_identity_without_semantic_success(monkeypatch):
    desired = timed_out_source(monkeypatch, ['CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/'])
    assert len(desired.objects) == 1
    obj = desired.objects[0]
    assert obj.identity.object_type == 'PACKAGE_BODY' and obj.identity.name.effective_name == 'P'
    assert obj.coverage.inventory == 'COMPLETE' and obj.coverage.ddl == 'PARTIAL'
    assert 'PARSER_TIMEOUT' in obj.coverage.diagnostics
    assert obj.properties['definition'].state == obj.properties['projection'].state == 'UNKNOWN'
    assert desired.completeness.inventory == desired.completeness.ddl == 'PARTIAL'
    assert 'TABLE' in proof_types(desired) and 'PACKAGE_BODY' in proof_types(desired)
    assert not {'COMMENT', 'GRANT'} & proof_types(desired)


def test_header_proof_confirms_only_other_create_types_and_never_makes_body_ready(monkeypatch):
    target = actual('CREATE TABLE APP.T(ID NUMBER); CREATE PACKAGE BODY APP.P AS END P;\n/')
    desired = timed_out_source(monkeypatch, ['CREATE PACKAGE BODY APP.P AS END P;\n/'])
    changes = compare_snapshots(desired, target, profile().policy)
    table_key = next(obj.object_key for obj in target.objects if obj.identity.object_type == 'TABLE')
    presence = [diff for diff in changes.differences if diff.object_key == table_key]
    assert len(presence) == 1 and presence[0].kind == 'EXTRA' and presence[0].after.state == 'ABSENT'
    body_changes = [diff for diff in changes.differences if diff.object_key != table_key]
    assert body_changes and all(diff.kind == 'UNKNOWN' for diff in body_changes)
    assert not changes.complete
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    plan = plan_target(changes, PlanningContext(desired,target,profile(),'Sentetik'))
    body_operations = [op for op in plan.operations if op.identity.object_type=='PACKAGE_BODY']
    assert body_operations and all(op.decision=='BLOCKED' and op.intent is None for op in body_operations)


@pytest.mark.parametrize('sql', [
    'CREATE SHARDED TABLE APP.X(ID NUMBER);',
    'CREATE TABLE OTHER.X(ID NUMBER);',
    "CREATE PACKAGE BODY APP.P AS X VARCHAR2(10):='unclosed; END P; /",
    'CREATE TABLE APP."unterminated (ID NUMBER);',
])
def test_unknown_create_or_lexer_or_owner_prevents_all_type_absence(monkeypatch, sql):
    desired = timed_out_source(monkeypatch, [sql])
    assert not proof_types(desired)


def test_all_headers_accounted_and_create_in_strings_comments_and_names_ignored(monkeypatch):
    sql = '''-- CREATE TABLE APP.FALSE_COMMENT(ID NUMBER);
CREATE PACKAGE BODY APP."CREATE TABLE APP.FALSE_NAME" AS
  X VARCHAR2(100):=q'[CREATE TABLE APP.FALSE_STRING(ID NUMBER)]';
END;
/
CREATE TABLE APP.REAL(ID NUMBER);
'''
    desired = timed_out_source(monkeypatch, [sql])
    assert {(obj.identity.object_type, obj.identity.name.effective_name) for obj in desired.objects} == {
        ('PACKAGE_BODY', 'CREATE TABLE APP.FALSE_NAME'), ('TABLE', 'REAL')}
    body = next(obj for obj in desired.objects if obj.identity.object_type=='PACKAGE_BODY')
    assert b'FALSE_STRING' in body.raw_ddl and body.raw_ddl.rstrip().endswith(b'/')
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert not verified_inventory_types(desired,context=True)


@pytest.mark.parametrize('mutation', ['proof_value', 'proof_evidence', 'input_digest', 'profile_hash',
                                     'object_identity', 'unexplained_failure'])
def test_tampered_or_unattributed_inventory_proof_never_confirms_absence(monkeypatch, mutation):
    desired = timed_out_source(monkeypatch, ['CREATE PACKAGE BODY APP.P AS END P;\n/'])
    caps = dict(desired.capabilities)
    proof = caps['source_inventory_proof']
    if mutation == 'proof_value':
        data = thaw(proof.value); data['source_commit'] = 'c'*40
        caps['source_inventory_proof'] = KnownValue('KNOWN', data, proof.evidence_ids)
    elif mutation == 'proof_evidence':
        caps['source_inventory_proof'] = KnownValue('KNOWN', thaw(proof.value), ())
    elif mutation in {'input_digest', 'profile_hash'}:
        key = 'source_input_digest' if mutation == 'input_digest' else 'source_profile_sha256'
        caps[key] = KnownValue('KNOWN', 'c'*64, caps[key].evidence_ids)
    elif mutation == 'object_identity':
        desired = replace(desired, objects=())
    else:
        desired = replace(desired, completeness=replace(desired.completeness,
            diagnostics=(*desired.completeness.diagnostics, 'UNATTRIBUTED_FAILURE')))
    assert not proof_types(replace(desired, capabilities=caps))


@pytest.mark.parametrize('mutation', ['deleted_record','record_errors','tainted_type','duplicate_header',
                                     'header_name','header_kind','malformed_record','malformed_headers'])
def test_rehashed_proof_still_requires_complete_manifest_and_recomputed_type_coverage(monkeypatch, mutation):
    desired = timed_out_source(monkeypatch, ['CREATE PACKAGE BODY APP.P AS END P;\n/'])
    cap = desired.capabilities['source_inventory_proof']
    data = thaw(cap.value)
    if mutation=='deleted_record':
        data['artifacts']=[]
    elif mutation=='record_errors':
        data['artifacts'][0]['errors']=['INVENTORY_CREATE_HEADER_UNRESOLVED']
    elif mutation=='tainted_type':
        data['artifacts'][0]['tainted_types']=['TABLE']
    elif mutation=='duplicate_header':
        data['artifacts'][0]['headers']*=2
    elif mutation=='header_name':
        data['artifacts'][0]['headers'][0]['name']='OTHER'
    elif mutation=='header_kind':
        data['artifacts'][0]['headers'][0]['kind']='TABLE'
    elif mutation=='malformed_record':
        data['artifacts'][0]=None
    else:
        data['artifacts'][0]['headers']=None
    new_hash=digest(data)
    evidence=tuple(replace(ev,id='ev-'+new_hash,sha256=new_hash) if ev.id in cap.evidence_ids else ev
                   for ev in desired.evidence)
    desired=replace(desired,evidence=evidence,capabilities={**desired.capabilities,
        'source_inventory_proof':KnownValue('KNOWN',data,('ev-'+new_hash,))})
    assert not proof_types(desired)


def source_with_failed_context(monkeypatch, failed_sql):
    original_parse=adapter.parse_ddl
    selected=profile()
    texts=['CREATE TABLE APP.T(ID NUMBER);',failed_sql]
    artifacts=tuple(SourceArtifact(f'app/file-{i}.sql','APP','DDL','TABLE',text.encode(),
        hashlib.sha256(text.encode()).hexdigest()) for i,text in enumerate(texts))
    monkeypatch.setattr(adapter,'parse_ddl',lambda raw,*a,**k:
        adapter.ParseResult((),(),('PARSER_TIMEOUT',),'UNAVAILABLE') if raw==texts[1].encode()
        else original_parse(raw,*a,**k))
    fingerprint=digest({'commit':'a'*40,'profile':selected,
        'files':[[item.path,item.kind,item.sha256] for item in artifacts]})
    return adapter.parse_source(SourceInput(SourceRevision('a'*40,None),artifacts,fingerprint),selected)


@pytest.mark.parametrize('failed_sql', ['ALTER TABLE APP.T ADD EXTRA NUMBER;',
    'CREATE PACKAGE BODY APP.P AS END P;\n/\nALTER TABLE APP.T ADD EXTRA NUMBER;',
    'CREATE PACKAGE BODY APP.P AS END P;\n/\nDROP TABLE APP.T;'])
def test_timeout_in_separate_alter_file_cannot_prove_local_column_absence(monkeypatch, failed_sql):
    target=actual('CREATE TABLE APP.T(ID NUMBER, EXTRA NUMBER);')
    desired=source_with_failed_context(monkeypatch,failed_sql)
    obj=next(obj for obj in desired.objects if obj.identity.object_type=='TABLE')
    assert obj.coverage.ddl=='COMPLETE'
    rows=[diff for diff in compare_snapshots(desired,target,profile().policy).differences
          if diff.object_key==obj.object_key and diff.property_path.startswith('/columns/EXTRA/')]
    assert rows and all(diff.kind=='UNKNOWN' and diff.after.state=='UNKNOWN' for diff in rows)


def test_proven_unrelated_package_timeout_does_not_taint_complete_table_fields(monkeypatch):
    target=actual('CREATE TABLE APP.T(ID NUMBER, EXTRA NUMBER);')
    desired=source_with_failed_context(monkeypatch,'CREATE PACKAGE BODY APP.P AS END P;\n/')
    obj=next(obj for obj in desired.objects if obj.identity.object_type=='TABLE')
    rows=[diff for diff in compare_snapshots(desired,target,profile().policy).differences
          if diff.object_key==obj.object_key and diff.property_path.startswith('/columns/EXTRA/')]
    assert rows and all(diff.after.state=='ABSENT' for diff in rows)


def test_global_temporary_header_is_an_identity_only_when_parser_times_out(monkeypatch):
    desired=timed_out_source(monkeypatch,['CREATE GLOBAL TEMPORARY TABLE APP.T(ID NUMBER);'])
    assert len(desired.objects)==1 and desired.objects[0].identity.object_type=='TABLE'
    assert desired.objects[0].properties['projection'].state=='UNKNOWN'
    assert 'TABLE' in proof_types(desired)


@pytest.mark.parametrize('conflicting',[False,True])
def test_duplicate_headers_need_equivalent_known_definitions_and_both_evidence_paths(conflicting):
    selected=profile()
    texts=['CREATE TABLE APP.T(ID NUMBER, N NUMBER); CREATE INDEX APP.I ON APP.T(ID);',
           'CREATE INDEX APP.I ON APP.T('+('N' if conflicting else 'ID')+');']
    artifacts=tuple(SourceArtifact(f'app/file-{i}.sql','APP','DDL','TABLE',text.encode(),
        hashlib.sha256(text.encode()).hexdigest()) for i,text in enumerate(texts))
    fingerprint=digest({'commit':'a'*40,'profile':selected,
        'files':[[item.path,item.kind,item.sha256] for item in artifacts]})
    desired=adapter.parse_source(SourceInput(SourceRevision('a'*40,None),artifacts,fingerprint),selected)
    index=next(obj for obj in desired.objects if obj.identity.object_type=='INDEX')
    assert len(index.evidence_ids)==2
    if conflicting:
        assert index.coverage.ddl=='PARTIAL' and not proof_types(desired)
    else:
        assert index.coverage.ddl=='COMPLETE' and 'INDEX' in proof_types(desired)


@pytest.mark.parametrize('statement,affected', [
    ('DROP TABLE APP.T;',{'TABLE','INDEX','TRIGGER'}),
    ('TRUNCATE TABLE APP.T;',{'TABLE'}),
    ('RENAME APP.T TO T2;',{'TABLE','PACKAGE_BODY'}),
    ('FLASHBACK TABLE APP.T TO BEFORE DROP;',{'TABLE','PACKAGE_BODY'}),
    ("COMMENT ON TABLE APP.T IS 'x';",{'COMMENT'}),
    ('GRANT SELECT ON APP.T TO READER;',{'GRANT'}),
    ('REVOKE SELECT ON APP.T FROM READER;',{'GRANT'}),
    ('PURGE RECYCLEBIN;',{'TABLE','PACKAGE_BODY'}),
])
def test_unverified_mutating_ddl_suffix_taints_the_appropriate_context(monkeypatch,statement,affected):
    desired=timed_out_source(monkeypatch,['CREATE PACKAGE BODY APP.P AS END P;\n/\n'+statement])
    proof=thaw(desired.capabilities['source_inventory_proof'].value)
    assert affected.issubset(set(proof['artifacts'][0]['context_tainted_types']))
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert not (affected & verified_inventory_types(desired,context=True))


@pytest.mark.parametrize('suffix',['@evil.sql','@@evil.sql','START evil.sql','HOST x',
                                   'CONNECT app','EXEC APP.P;','EXECUTE APP.P;','APP.P;',
                                   'BEGIN APP.P; END;\n/'])
def test_unparsed_package_suffix_external_code_never_proves_unrelated_scope(monkeypatch,suffix):
    desired=timed_out_source(monkeypatch,['CREATE PACKAGE BODY APP.P AS END P;\n/\n'+suffix])
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert not verified_inventory_types(desired,context=True)


@pytest.mark.parametrize('tail',['BEGIN NULL;','END OTHER;\n/'])
def test_incomplete_package_unit_cannot_prove_context_closure(monkeypatch,tail):
    desired=timed_out_source(monkeypatch,['CREATE PACKAGE BODY APP.P AS '+tail])
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert not verified_inventory_types(desired,context=True)


def test_deferred_sql_strings_comments_and_common_sql_terms_are_not_external_commands(monkeypatch):
    sql='''CREATE PACKAGE BODY APP.P AS PROCEDURE R IS X NUMBER; BEGIN
EXECUTE IMMEDIATE q'[DROP TABLE APP.T; @evil.sql START evil.sql]';
SELECT 1 INTO X FROM DUAL@LINK
START WITH 1=1
CONNECT BY LEVEL<2;
-- @evil.sql
END R; END P;
/
'''
    desired=timed_out_source(monkeypatch,[sql])
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert 'TABLE' in verified_inventory_types(desired,context=True)


def test_same_line_external_call_after_unverified_view_cannot_close_context(monkeypatch):
    desired=timed_out_source(monkeypatch,['CREATE VIEW APP.V AS SELECT 1 X FROM DUAL; EXEC APP.P;'])
    from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
    assert not verified_inventory_types(desired,context=True)
