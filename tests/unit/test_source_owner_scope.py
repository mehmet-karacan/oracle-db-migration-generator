import json
from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.config.loader import validate_document
from oracle_db_migration_generator.config.models import SchemaRoot
from oracle_db_migration_generator.model.evidence import Evidence
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.serialization import digest, thaw
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue, SchemaSnapshot, SnapshotObject
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from tests.factories import profile


def fixture():
    selected = replace(profile(), schema_roots=(SchemaRoot('app', 'APP'), SchemaRoot('ttbp', 'TTBP')))
    evidence = (
        Evidence('scope', 'ABSENCE_SCOPE', 'SOURCE', None, 'b'*64, None, None, None, 'Sabit kaynak kapsamı.'),
        Evidence('profile', 'POLICY', 'POLICY', None, digest(selected), None, None, None, 'Kaynak profili.'),
        Evidence('clean', 'SOURCE_SPAN', 'SOURCE', 'app/tables/A/ddl.sql', 'c'*64, 1, 1, None, 'Temiz nesne.'),
        Evidence('broken', 'SOURCE_SPAN', 'SOURCE', 'ttbp/tables/B/ddl.sql', 'd'*64, 1, 1, None, 'Bozuk nesne.'),
    )
    objects = []
    for owner, name, ev_id, path in [('APP', 'A', 'clean', 'app/tables/A/ddl.sql'),
                                      ('TTBP', 'B', 'broken', 'ttbp/tables/B/ddl.sql')]:
        good = owner == 'APP'
        objects.append(SnapshotObject(ObjectIdentity(selected.id, Identifier.parse(owner), 'TABLE', Identifier.parse(name)),
                                      {'definition': KnownValue('KNOWN' if good else 'UNKNOWN', 'CREATE TABLE APP.A (ID NUMBER)' if good else None, (ev_id,))},
                                      path, ('e' if good else 'f')*64,
                                      Coverage('COMPLETE', 'COMPLETE' if good else 'PARTIAL', 'NOT_APPLICABLE',
                                               () if good else ('PARSER_SYNTAX_ERROR',)), (ev_id,)))
    capabilities = {
        'source_profile_sha256': KnownValue('KNOWN', digest(selected), ('profile',)),
        'source_input_digest': KnownValue('KNOWN', 'b'*64, ('scope',)),
        'file_diagnostics': KnownValue('KNOWN', [
            {'path': 'ttbp/tables/B/ddl.sql', 'codes': ['PARSER_SYNTAX_ERROR'], 'coverage': 'PARTIAL'},
            {'path': 'ttbp/tables/C/ddl.sql', 'codes': ['PARSER_TIMEOUT'], 'coverage': 'UNAVAILABLE'},
        ], ('scope',)),
    }
    snapshot = SchemaSnapshot('snapshot/1.0', True, 'SOURCE', selected.id, ('APP', 'TTBP'), 'a'*40, None,
                              tuple(objects), Coverage('PARTIAL', 'PARTIAL', 'NOT_APPLICABLE',
                              ('PARSER_SYNTAX_ERROR', 'PARSER_TIMEOUT', 'SOURCE_FILE_UNPARSED')),
                              capabilities, evidence, 'NOT_APPLICABLE')
    return snapshot, selected


def scope(source, selected, schemas=('APP',)):
    # Import inside the test keeps the red phase an explicit missing behavior failure.
    import oracle_db_migration_generator.model.source_scope as implementation
    return implementation.source_for_schemas(source, selected, schemas)


def test_clean_owner_is_complete_and_raw_snapshot_remains_identical():
    source, selected = fixture()
    before = source.to_dict()
    derived = scope(source, selected)
    assert derived.completeness == Coverage('COMPLETE', 'COMPLETE', 'NOT_APPLICABLE')
    assert derived.schemas == ('APP',)
    assert [obj.identity.owner.effective_name for obj in derived.objects] == ['APP']
    assert source.to_dict() == before
    proof = thaw(derived.capabilities['owner_scope_proof'].value)
    assert proof['raw_snapshot_digest'] == source.semantic_digest
    assert proof['source_input_digest'] == 'b'*64
    assert proof['source_commit'] == 'a'*40
    assert proof['schemas'] == ['APP'] and proof['status'] == 'VERIFIED'
    assert derived.capabilities['source_profile_sha256'] == source.capabilities['source_profile_sha256']
    assert derived == scope(source, selected)


def test_broken_owner_and_combined_owner_remain_partial():
    source, selected = fixture()
    for schemas in [('TTBP',), ('APP', 'TTBP')]:
        derived = scope(source, selected, schemas)
        assert derived.completeness.inventory == derived.completeness.ddl == 'PARTIAL'
        assert derived.capabilities['owner_scope_proof'].value['status'] == 'UNVERIFIED'


@pytest.mark.parametrize('code', ['UNEXPLAINED_FAILURE', 'SOURCE_SCOPE_EMPTY', 'SOURCE_SCOPE_MISSING',
                                 'SOURCE_DEPENDENCIES_UNRESOLVED', 'SOURCE_OWNER_MISMATCH'])
def test_unassigned_global_errors_never_become_complete(code):
    source, selected = fixture()
    source = replace(source, completeness=replace(source.completeness, diagnostics=(*source.completeness.diagnostics, code)))
    assert scope(source, selected).completeness.inventory == 'PARTIAL'


@pytest.mark.parametrize('capability', ['file_diagnostics', 'sidecar_diagnostics', 'source_input_digest', 'source_profile_sha256'])
def test_unknown_diagnostic_or_provenance_capabilities_prevent_absence(capability):
    source, selected = fixture()
    source = replace(source, capabilities={**source.capabilities, capability: KnownValue('UNKNOWN', None, ())})
    assert scope(source, selected).completeness.inventory == 'PARTIAL'


@pytest.mark.parametrize('change', ['missing_input', 'bad_profile_hash', 'missing_scope_evidence', 'empty_diagnostics',
                                    'unassigned_path', 'object_root_mismatch', 'empty_object_evidence', 'unknown_object_property',
                                    'unknown_global_inventory', 'overlapping_roots', 'missing_owner', 'empty_selected_owner'])
def test_incomplete_or_ambiguous_proof_is_conservative(change):
    source, selected = fixture()
    caps = dict(source.capabilities)
    if change == 'missing_input':
        del caps['source_input_digest']
    elif change == 'bad_profile_hash':
        caps['source_profile_sha256'] = KnownValue('KNOWN', '0'*64, ('profile',))
    elif change == 'missing_scope_evidence':
        source = replace(source, evidence=tuple(ev for ev in source.evidence if ev.id != 'scope'))
    elif change == 'empty_diagnostics':
        caps['file_diagnostics'] = KnownValue('KNOWN', [], ('scope',))
        source = replace(source, objects=(source.objects[0],), completeness=replace(source.completeness, diagnostics=()))
    elif change == 'unassigned_path':
        caps['file_diagnostics'] = KnownValue('KNOWN', [{'path': 'elsewhere/x.sql', 'codes': ['PARSER_TIMEOUT'], 'coverage': 'UNAVAILABLE'}], ('scope',))
    elif change == 'object_root_mismatch':
        source = replace(source, objects=(source.objects[0], replace(source.objects[1], ddl_path='app/tables/B/ddl.sql')))
    elif change == 'empty_object_evidence':
        source = replace(source, objects=(replace(source.objects[0], evidence_ids=()), source.objects[1]))
    elif change == 'unknown_object_property':
        source = replace(source, objects=(replace(source.objects[0], properties={'definition': KnownValue('UNKNOWN', None, ('clean',))}), source.objects[1]))
    elif change == 'unknown_global_inventory':
        source = replace(source, completeness=replace(source.completeness, inventory='UNAVAILABLE'))
    elif change == 'overlapping_roots':
        selected = replace(selected, schema_roots=(SchemaRoot('app', 'APP'), SchemaRoot('app/other', 'TTBP')))
        caps['source_profile_sha256'] = KnownValue('KNOWN', digest(selected), ('profile',))
        source = replace(source, evidence=tuple(replace(ev, sha256=digest(selected)) if ev.id == 'profile' else ev for ev in source.evidence))
    elif change == 'missing_owner':
        source = replace(source, schemas=('APP',))
    elif change == 'empty_selected_owner':
        source = replace(source, objects=(source.objects[1],))
    source = replace(source, capabilities=caps)
    assert scope(source, selected).completeness.inventory == 'PARTIAL'


def test_sidecar_failures_must_have_matching_path_and_evidence():
    source, selected = fixture()
    ev = Evidence('sidecar', 'SOURCE_SPAN', 'SOURCE', 'ttbp/tables/B/grants.sql', '9'*64, 1, 1, None, 'Sidecar hatası.')
    row = {'path': ev.path, 'kind': 'GRANT', 'reason_code': 'SIDECAR_FACT_UNRESOLVED', 'evidence_id': ev.id}
    caps = {**source.capabilities, 'sidecar_diagnostics': KnownValue('KNOWN', [row], (ev.id,))}
    source = replace(source, capabilities=caps, evidence=(*source.evidence, ev),
                     completeness=replace(source.completeness, diagnostics=(*source.completeness.diagnostics, 'SOURCE_SIDECAR_UNRESOLVED')))
    assert scope(source, selected).completeness.inventory == 'COMPLETE'
    for row in ({**row, 'path': 'app/tables/A/grants.sql'}, {**row, 'evidence_id': 'missing'}):
        assert scope(replace(source, capabilities={**caps, 'sidecar_diagnostics': KnownValue('KNOWN', [row], (ev.id,))}), selected).completeness.inventory == 'PARTIAL'


def test_quoted_owner_case_is_preserved_and_wrong_case_is_rejected():
    source, selected = fixture()
    selected = replace(selected, schema_roots=(SchemaRoot('app', '"App"'), SchemaRoot('ttbp', 'TTBP')))
    obj = source.objects[0]
    obj = replace(obj, identity=replace(obj.identity, owner=Identifier.parse('"App"')))
    source = replace(source, schemas=('App', 'TTBP'), objects=(obj, source.objects[1]),
                     capabilities={**source.capabilities, 'source_profile_sha256': KnownValue('KNOWN', digest(selected), ('profile',))},
                     evidence=tuple(replace(ev, sha256=digest(selected)) if ev.id == 'profile' else ev for ev in source.evidence))
    assert scope(source, selected, ('"App"',)).schemas == ('App',)
    assert scope(source, selected, ('"App"',)).completeness.inventory == 'COMPLETE'
    with pytest.raises(ValueError, match='SOURCE_SCOPE_SCHEMA'):
        scope(source, selected, ('APP',))


def target_with_extra(source, owner):
    obj = next(obj for obj in source.objects if obj.identity.owner.effective_name == owner)
    extra = replace(obj, identity=replace(obj.identity, name=Identifier.parse('TARGET_ONLY')),
                    coverage=Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'))
    ev = Evidence('target-scope', 'ABSENCE_SCOPE', 'TARGET', None, '8'*64, None, None, None, 'Tam hedef envanteri.')
    return replace(source, side='TARGET', source_commit=None, target_id='DEMO', schemas=(owner,), objects=(extra,),
                   completeness=Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'), capabilities={}, evidence=(ev,), observed_consistency='OBSERVED_STABLE')


def test_compare_proves_absence_only_for_verified_clean_owner():
    source, selected = fixture()
    clean = compare_snapshots(scope(source, selected), target_with_extra(source, 'APP'), selected.policy)
    assert clean.complete
    assert [(diff.kind, diff.after.state) for diff in clean.differences if diff.before.state == 'KNOWN'] == [('EXTRA', 'ABSENT')]
    broken = compare_snapshots(scope(source, selected, ('TTBP',)), target_with_extra(source, 'TTBP'), selected.policy)
    assert not broken.complete
    assert [(diff.kind, diff.after.state) for diff in broken.differences if diff.before.state == 'KNOWN'] == [('UNKNOWN', 'UNKNOWN')]


def test_derived_snapshot_closed_schema_roundtrip(tmp_path):
    source, selected = fixture()
    derived = scope(source, selected)
    document = derived.to_dict()
    validate_document(document, 'snapshot.schema.json')
    path = tmp_path/'source.json'
    path.write_text(json.dumps(document), encoding='utf-8')
    restored = load_snapshot(path)
    assert restored.semantic_digest == derived.semantic_digest
    assert restored.capabilities['owner_scope_proof'] == derived.capabilities['owner_scope_proof']


def test_owner_scope_does_not_expand_dependency_references():
    source, selected = fixture()
    obj = source.objects[0]
    refs = KnownValue('KNOWN', [{'owner': 'TTBP', 'type': 'TABLE', 'name': 'B'}], ('clean',))
    source = replace(source, objects=(replace(obj, properties={**obj.properties, 'dependencies': refs}), source.objects[1]))
    derived = scope(source, selected)
    assert len(derived.objects) == 1
    assert derived.objects[0].properties['dependencies'] == refs


@pytest.mark.parametrize('change', ['file_diagnostic_policy_evidence', 'property_other_owner_evidence',
                                    'input_hash_wrong_scope', 'global_sidecar_without_capability',
                                    'empty_capability_evidence', 'unknown_full_coverage'])
def test_evidence_cannot_borrow_unrelated_scope_or_owner(change):
    source, selected = fixture()
    caps = dict(source.capabilities)
    if change == 'file_diagnostic_policy_evidence':
        caps['file_diagnostics'] = KnownValue('KNOWN', thaw(caps['file_diagnostics'].value), ('profile',))
    elif change == 'property_other_owner_evidence':
        obj = source.objects[0]
        source = replace(source, objects=(replace(obj, properties={'definition': KnownValue('KNOWN', obj.properties['definition'].value, ('broken',))}), source.objects[1]))
    elif change == 'input_hash_wrong_scope':
        caps['source_input_digest'] = KnownValue('KNOWN', '0'*64, ('scope',))
    elif change == 'global_sidecar_without_capability':
        source = replace(source, completeness=replace(source.completeness, diagnostics=(*source.completeness.diagnostics, 'SOURCE_SIDECAR_UNRESOLVED')))
    elif change == 'empty_capability_evidence':
        caps['file_diagnostics'] = KnownValue('KNOWN', thaw(caps['file_diagnostics'].value), ())
    elif change == 'unknown_full_coverage':
        source = replace(source, completeness=replace(source.completeness, ddl='UNAVAILABLE'))
    source = replace(source, capabilities=caps)
    assert scope(source, selected).completeness.inventory == 'PARTIAL'


def test_target_outside_derived_owner_set_cannot_gain_source_absence():
    source, selected = fixture()
    with pytest.raises(ValueError, match='SNAPSHOT_PROFILE_OR_SCHEMA_MISMATCH'):
        compare_snapshots(scope(source, selected), target_with_extra(source, 'TTBP'), selected.policy)


def test_complete_raw_source_can_derive_without_failure_diagnostics():
    source, selected = fixture()
    obj = source.objects[1]
    source = replace(source, objects=(source.objects[0], replace(obj,
                     properties={'definition': KnownValue('KNOWN', 'CREATE TABLE TTBP.B (ID NUMBER)', obj.evidence_ids)},
                     coverage=Coverage('COMPLETE', 'COMPLETE', 'NOT_APPLICABLE'))),
                     completeness=Coverage('COMPLETE', 'COMPLETE', 'NOT_APPLICABLE'),
                     capabilities={**source.capabilities, 'file_diagnostics': KnownValue('KNOWN', [], ('scope',))})
    assert scope(source, selected).completeness.inventory == 'COMPLETE'


def test_selected_unparsed_file_with_no_object_blocks_source_absence():
    source, selected = fixture()
    caps = dict(source.capabilities)
    caps['file_diagnostics'] = KnownValue('KNOWN', [*thaw(caps['file_diagnostics'].value),
        {'path': 'app/tables/MISSING/ddl.sql', 'codes': ['PARSER_TIMEOUT'], 'coverage': 'UNAVAILABLE'}], ('scope',))
    derived = scope(replace(source, capabilities=caps), selected)
    assert derived.completeness.inventory == derived.completeness.ddl == 'PARTIAL'


def with_reconciliation_span(source, **changes):
    ev = Evidence('metadata', 'SOURCE_SPAN', 'SOURCE', 'metadata/source-column-semantics.APP.json',
                  '7'*64, 1, 1, 'SOURCE_COLUMNS_KNOWN_FACTS_MATCH', 'Doğrulanmış kaynak kolon eşleştirmesi.')
    ev = replace(ev, **changes)
    obj = source.objects[0]
    properties = {key: replace(value, evidence_ids=(*value.evidence_ids, ev.id)) for key, value in obj.properties.items()}
    obj = replace(obj, properties=properties, evidence_ids=(*obj.evidence_ids, ev.id))
    return replace(source, objects=(obj, *source.objects[1:]), evidence=(*source.evidence, ev))


def test_verified_owner_reconciliation_span_supplements_original_ddl_span():
    source, selected = fixture()
    reconciled = with_reconciliation_span(source)
    before = reconciled.to_dict()
    derived = scope(reconciled, selected)
    assert derived.completeness.inventory == derived.completeness.ddl == 'COMPLETE'
    assert derived.capabilities['owner_scope_proof'].value['status'] == 'VERIFIED'
    assert reconciled.to_dict() == before
    assert derived.objects[0].ddl_path == 'app/tables/A/ddl.sql'
    assert derived.objects[0].ddl_sha256 == source.objects[0].ddl_sha256
    assert 'clean' in derived.objects[0].evidence_ids


@pytest.mark.parametrize('changes', [
    {'path': 'metadata/source-column-semantics.TTBP.json'},
    {'path': 'metadata/source-column-semantics.json'},
    {'path': 'metadata/source-column-semantics.APP.json.fake'},
    {'path': 'metadata/other.APP.json'},
    {'query_id': 'UNVERIFIED_SOURCE_COLUMNS'},
    {'query_id': None},
    {'kind': 'DEPENDENCY'},
    {'side': 'TARGET'},
    {'sha256': 'invalid'},
    {'path': None},
])
def test_reconciliation_exception_rejects_wrong_owner_path_origin_or_hash(changes):
    source, selected = fixture()
    assert scope(with_reconciliation_span(source, **changes), selected).completeness.inventory == 'PARTIAL'


def test_reconciliation_cannot_replace_original_own_root_ddl_span():
    source, selected = fixture()
    source = with_reconciliation_span(source)
    source = replace(source, objects=(replace(source.objects[0], evidence_ids=('metadata',)), source.objects[1]))
    assert scope(source, selected).completeness.inventory == 'PARTIAL'


@pytest.mark.parametrize('multi_owner', [False, True])
def test_real_read_only_reconciliation_then_owner_scope_keeps_coverage_complete(tmp_path, multi_owner):
    import hashlib
    from tools.jenkins_source_semantics import reconcile_source
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
    from tests.unit.test_jenkins_source_semantics import observation

    roots = (SchemaRoot('app', 'APP'), SchemaRoot('ttbp', 'TTBP')) if multi_owner else (SchemaRoot('app', 'APP'),)
    selected = replace(profile(), source_length_semantics='UNKNOWN', schema_roots=roots)
    artifacts = []
    for root in roots:
        raw = f'CREATE TABLE {root.source_schema}.T (C VARCHAR2(20));'.encode()
        artifacts.append(SourceArtifact(root.path+'/tables/T/ddl.sql', root.source_schema, 'DDL', 'TABLE', raw,
                                        hashlib.sha256(raw).hexdigest()))
    original = parse_source(SourceInput(SourceRevision('a'*40, None), tuple(artifacts), 'b'*64), selected)
    reconciled, proof = reconcile_source(original, observation(), tmp_path)
    assert proof['matched_tables'] == 1 and proof['rejected_tables'] == []
    if multi_owner:
        reconciled, second_proof = reconcile_source(reconciled, {**observation(), 'owner': 'TTBP'}, tmp_path)
        assert second_proof['matched_tables'] == 1 and second_proof['rejected_tables'] == []
    derived = scope(reconciled, selected)
    assert derived.completeness.inventory == derived.completeness.ddl == 'COMPLETE'
    assert derived.objects[0].ddl_sha256 == next(obj.ddl_sha256 for obj in original.objects if obj.identity.owner.effective_name == 'APP')
    detail = thaw(derived.objects[0].properties['projection'].value)['columns']['C']
    assert detail['length_semantics'] == 'BYTE' and detail['collation'] == 'USING_NLS_COMP'
    expected = 'metadata/source-column-semantics'+('.APP' if multi_owner else '')+'.json'
    assert any(ev.path == expected and ev.query_id == 'SOURCE_COLUMNS_KNOWN_FACTS_MATCH' for ev in derived.evidence)
