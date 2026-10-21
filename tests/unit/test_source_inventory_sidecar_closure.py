from dataclasses import replace
import hashlib
import pytest

from oracle_db_migration_generator.parsing import adapter
from oracle_db_migration_generator.parsing.inventory import verified_inventory_types
from oracle_db_migration_generator.model.serialization import digest
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
from tests.factories import profile, actual
from oracle_db_migration_generator.compare.snapshots import compare_snapshots


def inputs_for(texts):
    selected = profile()
    artifacts = tuple(SourceArtifact(f'app/file-{i}.sql', 'APP', kind, None,
        text.encode(), hashlib.sha256(text.encode()).hexdigest()) for i, (kind, text) in enumerate(texts))
    fingerprint = digest({'commit': 'a'*40, 'profile': selected,
        'files': [[a.path, a.kind, a.sha256] for a in artifacts]})
    return SourceInput(SourceRevision('a'*40, None), artifacts, fingerprint), selected


def test_closed_comment_identity_inventory_survives_unrelated_package_timeout(monkeypatch):
    original = adapter.parse_ddl
    monkeypatch.setattr(adapter, 'parse_ddl', lambda raw, *a, **kw:
        adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE') if b'PACKAGE BODY' in raw
        else original(raw, *a, **kw))
    inputs, selected = inputs_for([
        ('DDL', 'CREATE TABLE APP.T(ID NUMBER);'),
        ('COMMENT', "COMMENT ON COLUMN APP.T.ID IS 'identifier';"),
        ('DDL', 'CREATE PACKAGE BODY APP.P AS END P;\n/'),
    ])
    desired = adapter.parse_source(inputs, selected)
    assert desired.completeness.inventory == 'PARTIAL'
    assert 'COMMENT' in verified_inventory_types(desired)
    comment = next(obj for obj in desired.objects if obj.identity.object_type == 'COMMENT')
    assert comment.properties['column'].value == 'ID'
    assert 'COMMENT' not in verified_inventory_types(replace(desired,
        objects=tuple(o for o in desired.objects if o is not comment)))
    detached = replace(comment, identity=replace(comment.identity, parent_key=None))
    assert 'COMMENT' not in verified_inventory_types(replace(desired,
        objects=tuple(detached if o is comment else o for o in desired.objects)))


def test_comment_unparsed_tail_cannot_close_comment_inventory(monkeypatch):
    original = adapter.parse_ddl
    monkeypatch.setattr(adapter, 'parse_ddl', lambda raw, *a, **kw:
        adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE') if b'PACKAGE BODY' in raw
        else original(raw, *a, **kw))
    inputs, selected = inputs_for([
        ('DDL', 'CREATE TABLE APP.T(ID NUMBER);'),
        ('COMMENT', "COMMENT ON COLUMN APP.T.ID IS 'identifier'; COMMENT ON COLUMN APP.T.OTHER IS"),
        ('DDL', 'CREATE PACKAGE BODY APP.P AS END P;\n/'),
    ])
    assert 'COMMENT' not in verified_inventory_types(adapter.parse_source(inputs, selected))


def test_unrelated_comment_absence_is_proven_while_declared_ambiguous_parent_stays_unknown(monkeypatch):
    original = adapter.parse_ddl
    monkeypatch.setattr(adapter, 'parse_ddl', lambda raw, *a, **kw:
        adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE') if b'PACKAGE BODY' in raw
        else original(raw, *a, **kw))
    inputs, selected = inputs_for([
        ('DDL', 'CREATE TABLE APP.T(ID NUMBER, EXTRA NUMBER);'),
        ('DDL', 'CREATE MATERIALIZED VIEW APP.T AS SELECT ID FROM APP.OTHER;'),
        ('COMMENT', "COMMENT ON COLUMN APP.T.ID IS 'identifier';"),
        ('DDL', 'CREATE PACKAGE BODY APP.P AS END P;\n/'),
    ])
    desired = adapter.parse_source(inputs, selected)
    target = actual("CREATE TABLE APP.T(ID NUMBER, EXTRA NUMBER); COMMENT ON COLUMN APP.T.ID IS 'identifier'; COMMENT ON COLUMN APP.T.EXTRA IS 'extra';")
    changes = compare_snapshots(desired, target, selected.policy)
    keys = {obj.properties['column'].value: obj.object_key for obj in target.objects if obj.identity.object_type=='COMMENT'}
    assert next(d for d in changes.differences if d.object_key==keys['ID']).kind=='UNKNOWN'
    extra=next(d for d in changes.differences if d.object_key==keys['EXTRA'])
    assert extra.kind=='EXTRA' and extra.after.state=='ABSENT'
    assert desired.completeness.inventory=='PARTIAL'


@pytest.mark.parametrize('script', [
    "BEGIN EXECUTE IMMEDIATE 'COMMENT ON COLUMN APP.T.ID IS NULL'; END;\n/",
    "COMMENT ON TABLE APP.T IS 'table'; BEGIN APP.SET_COMMENTS; END;\n/",
    "BEGIN APP.SET_COMMENTS; END;\n/\nCOMMENT ON TABLE APP.T IS 'table';",
])
def test_unverified_runtime_block_in_comment_artifact_cannot_prove_comment_absence(script):
    from oracle_db_migration_generator.parsing.inventory import verified_comment_identity_names
    inputs, selected = inputs_for([
        ('DDL', 'CREATE TABLE APP.T(ID NUMBER);'),
        ('COMMENT', script),
    ])
    desired = adapter.parse_source(inputs, selected)
    assert desired.completeness.ddl == 'PARTIAL'
    assert 'COMMENT' not in verified_inventory_types(desired)
    assert verified_comment_identity_names(desired) is None
    target = actual("CREATE TABLE APP.T(ID NUMBER); COMMENT ON COLUMN APP.T.ID IS 'id';")
    comment = next(obj for obj in target.objects if obj.identity.object_type == 'COMMENT')
    difference = next(diff for diff in compare_snapshots(desired, target, selected.policy).differences
                      if diff.object_key == comment.object_key)
    assert difference.kind == 'UNKNOWN' and difference.after.state == 'UNKNOWN'


def test_literal_comment_artifact_with_standalone_runner_delimiters_keeps_inventory_closed():
    inputs, selected = inputs_for([
        ('DDL', 'CREATE TABLE APP.T(ID NUMBER);'),
        ('COMMENT', "COMMENT ON TABLE APP.T IS 'table';\n/\nCOMMENT ON COLUMN APP.T.ID IS 'id';\n/"),
    ])
    assert 'COMMENT' in verified_inventory_types(adapter.parse_source(inputs, selected))


def test_old_comment_closure_proof_is_rejected_even_with_matching_rehashed_evidence():
    from oracle_db_migration_generator.model.serialization import thaw
    from oracle_db_migration_generator.model.snapshot import KnownValue
    inputs, selected = inputs_for([('DDL', 'CREATE TABLE APP.T(ID NUMBER);')])
    desired = adapter.parse_source(inputs, selected)
    assert 'COMMENT' in verified_inventory_types(desired)
    capability = desired.capabilities['source_inventory_proof']
    proof = thaw(capability.value)
    proof['version'] = 'source-header-inventory/1.3'
    fingerprint = digest(proof)
    evidence = tuple(replace(item, id='ev-'+fingerprint, sha256=fingerprint)
                     if item.id in capability.evidence_ids else item for item in desired.evidence)
    legacy = replace(desired, evidence=evidence, capabilities={**desired.capabilities,
        'source_inventory_proof': KnownValue('KNOWN', proof, ('ev-'+fingerprint,))})
    assert not verified_inventory_types(legacy)


def test_known_function_with_fully_parsed_insert_suffix_does_not_taint_function_inventory():
    inputs, selected = inputs_for([('DDL', '''CREATE FUNCTION APP.F RETURN NUMBER IS
BEGIN RETURN 1; END;
INSERT ALL INTO APP.T VALUES (1) INTO APP.T VALUES (2)
SELECT 1 FROM DUAL;
/''')])
    desired = adapter.parse_source(inputs, selected)
    assert 'UNSUPPORTED_STATEMENT' in desired.completeness.diagnostics
    assert 'FUNCTION' in verified_inventory_types(desired)
    assert len(desired.objects) == 1


def test_malformed_insert_suffix_keeps_function_inventory_unknown():
    inputs, selected = inputs_for([('DDL', '''CREATE FUNCTION APP.F RETURN NUMBER IS
BEGIN RETURN 1; END;
INSERT ALL INTO APP.T VALUES (1) SELECT FROM;
/''')])
    assert 'FUNCTION' not in verified_inventory_types(adapter.parse_source(inputs, selected))


def test_broken_trigger_and_exact_disable_suffix_prove_only_trigger_identity(monkeypatch):
    monkeypatch.setattr(adapter, 'parse_ddl', lambda *a, **kw:
        adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE'))
    inputs, selected = inputs_for([('DDL', '''CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T
BEGIN APP.P
/
ALTER TRIGGER APP.TRG DISABLE;''')])
    desired = adapter.parse_source(inputs, selected)
    assert desired.objects[0].properties['definition'].state == 'UNKNOWN'
    assert 'TRIGGER' in verified_inventory_types(desired)
    assert 'TRIGGER' not in verified_inventory_types(desired, context=True)


@pytest.mark.parametrize('suffix', [
    'ALTER TRIGGER APP.TRG RENAME TO OTHER;',
    'ALTER TRIGGER OTHER.TRG DISABLE;',
    'ALTER TRIGGER APP.TRG DISABLE; DROP TRIGGER APP.OTHER;',
    'ALTER TRIGGER APP.TRG DISABLE; @extra.sql',
])
def test_trigger_suffix_requires_exact_same_identity_and_closed_statement(monkeypatch, suffix):
    monkeypatch.setattr(adapter, 'parse_ddl', lambda *a, **kw:
        adapter.ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE'))
    inputs, selected = inputs_for([('DDL', 'CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T\nBEGIN APP.P\n/\n'+suffix)])
    assert 'TRIGGER' not in verified_inventory_types(adapter.parse_source(inputs, selected))


@pytest.mark.parametrize('suffix', [
    'CREATE FUNCTION APP.OTHER RETURN NUMBER IS BEGIN RETURN 2; END;',
    'EXEC APP.P;',
    '@extra.sql',
    'DROP FUNCTION APP.OTHER;',
])
def test_insert_neutrality_requires_entire_grammar_input_to_close(suffix):
    inputs, selected = inputs_for([('DDL', '''CREATE FUNCTION APP.F RETURN NUMBER IS
BEGIN RETURN 1; END;
INSERT INTO APP.T VALUES (1);
'''+suffix)])
    assert 'FUNCTION' not in verified_inventory_types(adapter.parse_source(inputs, selected))
