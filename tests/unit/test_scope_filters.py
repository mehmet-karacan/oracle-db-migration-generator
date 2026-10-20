import json
from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.config.loader import ConfigError, load_source_profile
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue
from tests.factories import ROOT, actual, profile, source


def policy(**changes):
    return replace(profile().policy, **changes)


def named(snapshot, names, kind='TABLE'):
    template = source('CREATE TABLE APP.BASE (ID NUMBER);').objects[0]
    objects = tuple(replace(template, identity=ObjectIdentity(snapshot.profile_id, Identifier.parse('APP'),
                            kind, Identifier.parse(name))) for name in names)
    return replace(snapshot, objects=objects)


def test_legacy_profile_defaults_keep_full_scope():
    selected = profile()
    assert selected.policy.exclude_system_generated is False
    assert selected.policy.excluded_object_types == ()
    desired = source('CREATE TABLE APP.C$_COPY (ID NUMBER); GRANT SELECT ON APP.C$_COPY TO READER;')
    assert len(compare_snapshots(desired, actual(), selected.policy).differences) == 2


def test_policy_schema_accepts_closed_optional_filters_and_changes_hash(tmp_path):
    from oracle_db_migration_generator.model.serialization import digest
    document = json.loads((ROOT/'examples/source-profile.example.json').read_text(encoding='utf-8'))
    before = digest(profile())
    document['policy'].update(exclude_system_generated=True, excluded_object_types=['GRANT'])
    path = tmp_path/'profile.json'
    path.write_text(json.dumps(document), encoding='utf-8')
    selected = load_source_profile(path)
    assert selected.policy.excluded_object_types == ('GRANT',)
    assert digest(selected) != before
    for key, value in [('exclude_system_generated', 'true'), ('excluded_object_types', ['NOT_A_TYPE']),
                       ('excluded_object_types', ['GRANT', 'GRANT']), ('filter_everything', True)]:
        invalid = json.loads(json.dumps(document))
        invalid['policy'][key] = value
        path.write_text(json.dumps(invalid), encoding='utf-8')
        with pytest.raises(ConfigError):
            load_source_profile(path)


def test_sync_technical_prefixes_filter_source_and_target_without_dollar_blanket():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    technical = ['BIN$123', 'ISEQ$$_123', 'MLOG$_T', 'I_MLOG$_T', 'RUPD$_T', 'SYS_IOT_OVER_1',
                 'SYS_IL123', 'SYS_FBA_HIST_1', 'SYS_TEMP_FBT1', 'C$_COPY', 'I$_FLOW', 'E$_ERR',
                 'J$JOURNAL', 'JV$JOURNAL', 'T$TRIGGER']
    desired = named(source(''), technical + ['APP$TABLE', 'S_0e13', '"c$_copy"'])
    target = named(actual(), [name+'X' for name in technical] + ['APP$OTHER'])
    selected = policy(exclude_system_generated=True)
    result = compare_snapshots(desired, target, selected)
    remaining = {obj.object_key for obj in (*desired.objects, *target.objects)
                 if obj.identity.name.effective_name in {'APP$TABLE', 'APP$OTHER', 'S_0E13', 'c$_copy'}}
    assert {diff.object_key for diff in result.differences} == remaining
    proof = scope_exclusions(desired, target, selected)
    assert len(proof) == 2*len(technical)
    assert {item['side'] for item in proof} == {'SOURCE', 'TARGET'}
    assert all(item['reason_code'] == 'SYSTEM_GENERATED_OBJECT' for item in proof)
    assert len(desired.objects) == len(technical)+3


def test_real_materialized_view_log_is_retained_beside_excluded_storage():
    selected = policy(exclude_system_generated=True)
    desired = named(source(''), ['MLOG$_APP_TABLE'])
    log = named(source(''), ['APP_TABLE'], 'MATERIALIZED_VIEW_LOG').objects[0]
    desired = replace(desired, objects=desired.objects+(log,))
    changes = compare_snapshots(desired, actual(), selected)
    assert [diff.object_key for diff in changes.differences] == [log.object_key]


def test_grant_exclusion_uses_type_not_synthetic_name():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    desired = source('CREATE TABLE APP.S_0e13 (ID NUMBER); GRANT SELECT ON APP.S_0e13 TO READER;')
    changes = compare_snapshots(desired, actual(), policy(excluded_object_types=('GRANT',)))
    table = next(obj for obj in desired.objects if obj.identity.object_type == 'TABLE')
    assert [diff.object_key for diff in changes.differences] == [table.object_key]
    proof = scope_exclusions(desired, actual(), policy(excluded_object_types=('GRANT',)))
    assert len(proof) == 1 and proof[0]['object_type'] == 'GRANT'
    assert proof[0]['reason_code'] == 'EXCLUDED_OBJECT_TYPE'


def test_verified_index_and_sidecars_follow_excluded_parent_but_business_reference_blocks():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    selected = replace(profile(), policy=policy(exclude_system_generated=True))
    desired = source("CREATE TABLE APP.C$_COPY (ID NUMBER); CREATE INDEX APP.I_ADDR_ID ON APP.C$_COPY(ID); "
                     "COMMENT ON TABLE APP.C$_COPY IS 'temp'; GRANT SELECT ON APP.C$_COPY TO READER; "
                     "CREATE VIEW APP.V AS SELECT ID FROM APP.C$_COPY;", selected)
    target = actual('', selected)
    changes = compare_snapshots(desired, target, selected.policy)
    view = next(obj for obj in desired.objects if obj.identity.object_type == 'VIEW')
    assert {diff.object_key for diff in changes.differences} == {view.object_key}
    proof = scope_exclusions(desired, target, selected.policy)
    assert len(proof) == 4
    assert len([item for item in proof if item['reason_code'] == 'EXCLUDED_PARENT_OBJECT']) == 3
    plan = plan_target(changes, PlanningContext(desired, target, selected, 'Test'))
    assert plan.operations and all(op.decision == 'BLOCKED' for op in plan.operations)
    assert all(op.identity.key == view.object_key for op in plan.operations)


def test_index_unknown_projection_does_not_claim_technical_parent():
    desired = source('CREATE TABLE APP.C$_COPY(ID NUMBER); CREATE INDEX APP.I_ADDR_ID ON APP.C$_COPY(ID);')
    index = next(obj for obj in desired.objects if obj.identity.object_type == 'INDEX')
    index = replace(index, properties={'projection': KnownValue('UNKNOWN', None, index.evidence_ids)},
                    coverage=Coverage('COMPLETE', 'PARTIAL', 'NOT_APPLICABLE'))
    desired = replace(desired, objects=tuple(index if obj.object_key == index.object_key else obj for obj in desired.objects),
                      completeness=replace(desired.completeness, ddl='PARTIAL'))
    changes = compare_snapshots(desired, actual(), policy(exclude_system_generated=True))
    assert {diff.object_key for diff in changes.differences} == {index.object_key}
    assert not changes.complete


def test_dictionary_parent_names_keep_quoted_case_and_do_not_use_generic_dependencies():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    desired = source('CREATE INDEX APP.I_ADDR_ID ON APP.BUSINESS(ID); CREATE VIEW APP.V AS SELECT ID FROM APP.BUSINESS;')
    objects = []
    for obj in desired.objects:
        props = dict(obj.properties)
        if obj.identity.object_type == 'INDEX':
            props['dictionary.indexes'] = KnownValue('KNOWN', [{'index_name': 'I_ADDR_ID', 'table_owner': 'APP',
                                                               'table_name': 'C$_COPY'}], obj.evidence_ids)
        else:
            props['dependencies'] = KnownValue('KNOWN', [{'owner':'APP','type':'TABLE','name':'C$_COPY'}], obj.evidence_ids)
        objects.append(replace(obj, properties=props))
    desired = replace(desired, objects=tuple(objects))
    selected = policy(exclude_system_generated=True)
    proof = scope_exclusions(desired, actual(), selected)
    assert len(proof) == 1 and proof[0]['object_type'] == 'INDEX'
    index = next(obj for obj in desired.objects if obj.identity.object_type == 'INDEX')
    props = dict(index.properties)
    props['dictionary.indexes'] = KnownValue('KNOWN', [{'index_name': 'I_ADDR_ID', 'table_owner': 'APP',
                                                       'table_name': 'c$_copy'}], index.evidence_ids)
    desired = replace(desired, objects=(replace(index, properties=props),))
    assert not scope_exclusions(desired, actual(), selected)


def test_scope_receipt_matches_only_schemas_compared_for_this_target():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    desired = source('CREATE TABLE APP.C$_COPY(ID NUMBER);')
    template = desired.objects[0]
    other = replace(template, identity=replace(template.identity, owner=Identifier.parse('OTHER')))
    desired = replace(desired, schemas=('APP', 'OTHER'), objects=(template, other))
    proof = scope_exclusions(desired, actual(), policy(exclude_system_generated=True))
    assert len(proof) == 1 and proof[0]['owner'] == 'APP'


def test_source_and_target_index_parent_projection_keep_quoted_case():
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    desired = source('CREATE INDEX APP.IX_UPPER ON APP."C$_COPY"(ID); '
                     'CREATE INDEX APP.IX_LOWER ON APP."c$_copy"(ID);')
    target = actual('CREATE INDEX APP.IX_TARGET ON APP.C$_TARGET(ID);')
    proof = scope_exclusions(desired, target, policy(exclude_system_generated=True))
    assert {item['name'] for item in proof} == {'IX_UPPER', 'IX_TARGET'}
    assert {diff.object_key for diff in compare_snapshots(desired, target, policy(exclude_system_generated=True)).differences} == {
        obj.object_key for obj in desired.objects if obj.identity.name.effective_name == 'IX_LOWER'}


def test_other_unsupported_application_object_still_blocks_with_filters_enabled():
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    selected = replace(profile(), policy=policy(exclude_system_generated=True, excluded_object_types=('GRANT',)))
    desired = source('CREATE MATERIALIZED VIEW APP.MV AS SELECT 1 N FROM DUAL;', selected)
    target = actual('', selected)
    changes = compare_snapshots(desired, target, selected.policy)
    assert changes.differences
    plan = plan_target(changes, PlanningContext(desired, target, selected, 'Test'))
    assert plan.operations and all(op.decision == 'BLOCKED' for op in plan.operations)
