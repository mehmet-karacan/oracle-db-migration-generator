"""Frozen source repairs must replay provenance rather than lose ALTER state."""
import importlib.util
from dataclasses import replace

import pytest

from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.model.serialization import thaw
from tests.factories import source, profile


CREATE = ('CREATE TABLE APP.T(ID NUMBER, C VARCHAR2(20), '
          'SUPPLEMENTAL LOG GROUP G1(ID) ALWAYS, SUPPLEMENTAL LOG GROUP G2(C) ALWAYS);')


def legacy(sql=CREATE, *, complete=False):
    snapshot = source(sql)
    obj = next(obj for obj in snapshot.objects if obj.identity.name.effective_name == 'T')
    props = thaw(obj.properties['projection'].value)
    props['columns']['SUPPLEMENTAL'] = {'data_type': 'LOG', 'position': '3'}
    props.pop('_generator_supplemental_logging', None)
    obj = replace(obj, projection=None, properties={**obj.properties,
        'projection': KnownValue('KNOWN', props, obj.properties['projection'].evidence_ids)},
        coverage=replace(obj.coverage, ddl='COMPLETE' if complete else 'PARTIAL',
                         diagnostics=() if complete else ('DUPLICATE_COLUMN',)))
    snapshot = replace(snapshot, objects=tuple(obj if item.object_key == obj.object_key else item for item in snapshot.objects),
        completeness=replace(snapshot.completeness, inventory='PARTIAL', ddl='PARTIAL',
                             diagnostics=('SOURCE_FILE_UNPARSED',)))
    return snapshot, {'app/fixture.sql': sql.encode()}


def reparse(snapshot, blobs, **kwargs):
    assert importlib.util.find_spec('oracle_db_migration_generator.parsing.reparse_source') is not None, 'Selective source reparse missing'
    from oracle_db_migration_generator.parsing.reparse_source import reparse_source_supplemental
    return reparse_source_supplemental(snapshot, read_blob=blobs.__getitem__, **kwargs)


@pytest.mark.parametrize('complete', [False, True])
def test_selective_reparse_repairs_logging_without_upgrading_snapshot_scope(complete):
    original, blobs = legacy(CREATE+' CREATE TABLE APP.U(ID NUMBER);', complete=complete)
    before = original.to_dict()
    updated, report = reparse(original, blobs)
    old = next(obj for obj in original.objects if obj.identity.name.effective_name == 'T')
    fixed = next(obj for obj in updated.objects if obj.identity.name.effective_name == 'T')
    assert set(fixed.properties['projection'].value['columns']) == {'ID', 'C'}
    assert fixed.coverage.ddl == 'COMPLETE'
    assert len(fixed.properties['projection'].value['_generator_supplemental_logging']) == 2
    assert fixed.raw_ddl == old.raw_ddl and fixed.ddl_sha256 == old.ddl_sha256
    assert fixed.identity == old.identity and fixed.ddl_path == old.ddl_path
    assert set(old.evidence_ids) <= set(fixed.evidence_ids)
    assert updated.source_commit == original.source_commit
    assert updated.completeness == original.completeness
    assert updated.capabilities == original.capabilities
    assert original.to_dict() == before
    untouched = next(obj for obj in original.objects if obj.identity.name.effective_name == 'U')
    assert next(obj for obj in updated.objects if obj.object_key == untouched.object_key) == untouched
    assert report['selected'] == report['updated'] == 1 and report['held'] == 0


def test_verified_alter_context_is_replayed_after_create_span_reparse():
    original, blobs = legacy(CREATE+" ALTER TABLE APP.T MODIFY C DEFAULT 'kept'; ALTER TABLE APP.T ADD D NUMBER;")
    updated, report = reparse(original, blobs)
    columns = updated.objects[0].properties['projection'].value['columns']
    assert set(columns) == {'ID', 'C', 'D'}
    assert columns['C']['default'] == "'kept'" and columns['D']['data_type'] == 'NUMBER'
    assert report['updated'] == 1 and report['held'] == 0


@pytest.mark.parametrize('failure', ['missing_blob', 'hash_drift', 'missing_context_evidence'])
def test_unverified_original_blob_or_alter_context_retains_hold(failure):
    original, blobs = legacy(CREATE+' ALTER TABLE APP.T ADD D NUMBER;', complete=True)
    if failure == 'missing_blob':
        blobs = {}
    elif failure == 'hash_drift':
        blobs['app/fixture.sql'] += b'-- changed'
    else:
        obj = original.objects[0]
        context_id = obj.evidence_ids[-1]
        original = replace(original, evidence=tuple(e for e in original.evidence if e.id != context_id))
    updated, report = reparse(original, blobs)
    assert report['held'] == 1 and report['updated'] == 0
    assert updated.objects[0].coverage.ddl == 'PARTIAL'
    assert 'SOURCE_REPARSE_PROVENANCE_UNVERIFIED' in updated.objects[0].coverage.diagnostics
    assert updated.objects[0].raw_ddl == original.objects[0].raw_ddl


def test_reconciled_column_facts_require_their_verified_original_proof(tmp_path):
    from tools.jenkins_source_semantics import reconcile_source
    from tests.unit.test_jenkins_source_semantics import observation
    sql = ('CREATE TABLE APP.T(C VARCHAR2(20), SUPPLEMENTAL LOG GROUP G1(C) ALWAYS);')
    original = source(sql, replace(profile(), source_length_semantics='UNKNOWN'))
    reconciled, proof = reconcile_source(original, observation(), tmp_path)
    assert proof['matched_tables'] == 1
    blobs = {'app/fixture.sql': sql.encode(),
             'metadata/source-column-semantics.json': (tmp_path/'metadata/source-column-semantics.json').read_bytes()}
    updated, report = reparse(reconciled, blobs)
    detail = updated.objects[0].properties['projection'].value['columns']['C']
    assert detail['length_semantics'] == 'BYTE' and detail['collation'] == 'USING_NLS_COMP'
    assert report['held'] == 0
    _, missing = reparse(reconciled, {'app/fixture.sql': sql.encode()})
    assert missing['held'] == 1


def test_unproven_projection_context_is_not_silently_discarded():
    original, blobs = legacy(complete=True)
    obj = original.objects[0]
    props = thaw(obj.properties['projection'].value)
    props['columns']['C']['default'] = "'unrecorded'"
    original = replace(original, objects=(replace(obj, properties={**obj.properties,
        'projection': KnownValue('KNOWN', props, obj.evidence_ids)}),))
    updated, report = reparse(original, blobs)
    assert report['held'] == 1 and report['updated'] == 0
    assert updated.objects[0].coverage.ddl == 'PARTIAL'


def test_unknown_projection_with_lost_alter_span_stays_blocked():
    original, blobs = legacy(CREATE+' ALTER TABLE APP.T ADD D NUMBER;')
    obj = original.objects[0]
    context_id = obj.evidence_ids[-1]
    ids = tuple(key for key in obj.evidence_ids if key != context_id)
    obj = replace(obj, evidence_ids=ids, properties={**obj.properties,
        'projection': KnownValue('UNKNOWN', None, ids)})
    original = replace(original, objects=(obj,), evidence=tuple(e for e in original.evidence if e.id != context_id))
    updated, report = reparse(original, blobs)
    assert report['held'] == 1 and report['updated'] == 0
    assert updated.objects[0].coverage.ddl == 'PARTIAL'


def test_target_direction_is_rejected():
    from tests.factories import actual
    with pytest.raises(ValueError, match='SOURCE_REPARSE_REQUIRES_SOURCE'):
        reparse(actual(), {})


@pytest.mark.parametrize('diagnostic', ['CONTEXT_UNRESOLVED', 'UNNAMED_CONSTRAINT_UNRESOLVED'])
def test_explicit_table_selection_replays_repaired_nonlogging_constraints(diagnostic):
    sql = ('CREATE TABLE APP.T(ID NUMBER, CHECK(ID >= 0), CHECK(ID >= 0)); '
           'ALTER TABLE APP.T ADD UNIQUE(ID) USING INDEX APP.I_T_ID ENABLE;')
    original = source(sql)
    obj = original.objects[0]
    assert obj.coverage.ddl == 'COMPLETE'
    props = thaw(obj.properties['projection'].value)
    if diagnostic == 'UNNAMED_CONSTRAINT_UNRESOLVED':
        props['constraints'] = {}
    legacy_obj = replace(obj, projection=None, coverage=replace(obj.coverage, ddl='PARTIAL', diagnostics=(diagnostic,)),
        properties={**obj.properties, 'projection': KnownValue('UNKNOWN' if diagnostic == 'CONTEXT_UNRESOLVED' else 'KNOWN',
            None if diagnostic == 'CONTEXT_UNRESOLVED' else props, obj.evidence_ids)})
    original = replace(original, objects=(legacy_obj,), completeness=replace(original.completeness, ddl='PARTIAL'))
    blobs = {'app/fixture.sql': sql.encode()}
    unchanged, unselected = reparse(original, blobs)
    assert unselected['selected'] == 0 and unchanged.objects[0] == legacy_obj
    updated, report = reparse(original, blobs, object_keys=(obj.object_key,))
    assert report['updated'] == 1 and report['held'] == 0
    restored = updated.objects[0]
    assert restored.coverage.ddl == 'COMPLETE'
    assert len(restored.properties['projection'].value['constraints']) == 3
    assert restored.raw_ddl == obj.raw_ddl and restored.identity == obj.identity
    assert updated.completeness == original.completeness


def test_explicit_selection_rejects_non_table_and_missing_identity():
    original = source('CREATE PROCEDURE APP.P AS BEGIN NULL; END;\n/')
    for key in (original.objects[0].object_key, 'f'*64):
        with pytest.raises(ValueError, match='SOURCE_REPARSE_TABLE_SELECTION_INVALID'):
            reparse(original, {}, object_keys=(key,))


def test_explicit_selection_cannot_clear_unrelated_diagnostics():
    original, blobs = legacy()
    obj = original.objects[0]
    obj = replace(obj, coverage=replace(obj.coverage, diagnostics=('SOURCE_DEPENDENCIES_CONFLICT',)))
    updated, report = reparse(replace(original, objects=(obj,)), blobs, object_keys=(obj.object_key,))
    assert report['held'] == 1 and updated.objects[0].coverage.ddl == 'PARTIAL'
    assert 'SOURCE_DEPENDENCIES_CONFLICT' in updated.objects[0].coverage.diagnostics


def test_explicit_selection_does_not_reparse_sibling_logging_table_without_its_blob():
    import hashlib
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
    selected = profile()
    payloads = [('app/T.sql', b'CREATE TABLE APP.T(ID NUMBER, CHECK(ID >= 0));'),
                ('app/U.sql', b'CREATE TABLE APP.U(ID NUMBER, SUPPLEMENTAL LOG GROUP G(ID) ALWAYS);')]
    artifacts = tuple(SourceArtifact(path, 'APP', 'DDL', 'TABLE', raw, hashlib.sha256(raw).hexdigest())
                      for path, raw in payloads)
    original = parse_source(SourceInput(SourceRevision('a'*40, None), artifacts, 'b'*64), selected)
    target = next(obj for obj in original.objects if obj.identity.name.effective_name == 'T')
    sibling = next(obj for obj in original.objects if obj.identity.name.effective_name == 'U')
    target = replace(target, coverage=replace(target.coverage, ddl='PARTIAL',
                     diagnostics=('UNNAMED_CONSTRAINT_UNRESOLVED',)))
    original = replace(original, objects=(target, sibling))
    updated, report = reparse(original, {'app/T.sql': payloads[0][1]}, object_keys=(target.object_key,))
    assert report['selected'] == report['updated'] == 1 and report['held'] == 0
    assert updated.objects[1] is sibling
    assert sibling.evidence_ids == original.objects[1].evidence_ids


def test_explicit_empty_selection_reparses_nothing():
    original, _ = legacy()
    updated, report = reparse(original, {}, object_keys=())
    assert report['selected'] == report['updated'] == report['held'] == 0
    assert updated.objects[0] is original.objects[0]
