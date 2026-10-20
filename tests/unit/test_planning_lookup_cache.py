from collections import Counter
from dataclasses import replace

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.difference import Difference
from oracle_db_migration_generator.model.identity import Identifier
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.parsing import dependencies
from oracle_db_migration_generator.planning.context import PlanningContext
from oracle_db_migration_generator.planning.object_rules import object_change
from oracle_db_migration_generator.planning.rules import plan_target
from tests.factories import actual, profile, source


def sequence_fixture(sequence_count=4, consumer_count=3):
    selected = profile()
    definitions = ' '.join(f'CREATE SEQUENCE APP.S{i} START WITH 1 NOCACHE;' for i in range(sequence_count))
    references = ' + '.join(f'APP.S{i}.NEXTVAL' for i in range(sequence_count))
    consumers = ' '.join(f'CREATE TABLE APP.T{i}(ID NUMBER DEFAULT {references});' for i in range(consumer_count))
    desired = source(definitions + consumers, selected)
    observed = actual(consumers, selected)
    return PlanningContext(desired, observed, selected, 'Sentetik hedef')


def missing_sequence_change(context, obj):
    ids = tuple(ev.id for ev in context.target.evidence if ev.kind == 'ABSENCE_SCOPE')
    before = KnownValue('ABSENT', None, ids)
    after = KnownValue('KNOWN', True, obj.evidence_ids)
    change = Difference('diff-' + obj.object_key, obj.object_key, '/presence', before, after,
                        'MISSING', (*before.evidence_ids, *after.evidence_ids))
    return object_change(context, obj, None, (change,))[0]


def test_missing_sequences_analyze_each_existing_source_consumer_once(monkeypatch):
    context = sequence_fixture()
    calls = Counter()
    original = dependencies.references

    def counted(obj):
        calls[obj.object_key] += 1
        return original(obj)

    monkeypatch.setattr(dependencies, 'references', counted)
    sequences = [obj for obj in context.source.objects if obj.identity.object_type == 'SEQUENCE']
    decisions = [missing_sequence_change(context, obj) for obj in sequences]
    assert len(decisions) == 4
    assert all(op.decision == 'REVIEW_REQUIRED' and op.intent is None for op in decisions)
    assert all('SEQUENCE_EXISTING_DATA_COLLISION_UNKNOWN' in op.reason_codes for op in decisions)
    existing = {obj.object_key for obj in context.source.objects if obj.object_key in context.target_objects}
    assert len(existing) == 3
    assert calls == Counter({key: 1 for key in existing})
    for obj in sequences:
        assert missing_sequence_change(context, obj).decision == 'REVIEW_REQUIRED'
    assert calls == Counter({key: 1 for key in existing})


def test_existing_consumer_outside_filtered_report_scope_still_prevents_ready_sequence():
    selected = profile()
    selected = replace(selected, policy=replace(selected.policy, exclude_system_generated=True))
    consumer = 'CREATE TABLE APP.C$_CONSUMER(ID NUMBER DEFAULT APP.S.NEXTVAL);'
    desired = source('CREATE SEQUENCE APP.S START WITH 1 NOCACHE;' + consumer, selected)
    observed = actual(consumer, selected)
    differences = compare_snapshots(desired, observed, selected.policy)
    assert len(differences.differences) == 1
    context = PlanningContext(desired, observed, selected, 'Sentetik hedef')
    plan = plan_target(differences, context)
    sequence = next(op for op in plan.operations if op.identity.object_type == 'SEQUENCE')
    assert sequence.decision == 'REVIEW_REQUIRED' and sequence.intent is None
    assert 'SEQUENCE_EXISTING_DATA_COLLISION_UNKNOWN' in sequence.reason_codes


def test_sequence_consumer_cache_is_isolated_by_target_and_source_context(monkeypatch):
    first = sequence_fixture(sequence_count=1, consumer_count=1)
    sequence = next(obj for obj in first.source.objects if obj.identity.object_type == 'SEQUENCE')
    without_existing = PlanningContext(first.source, actual(), first.profile, 'Boş hedef')
    consumer = next(obj for obj in first.source.objects if obj.identity.object_type == 'TABLE')
    replacement = source('CREATE TABLE APP.T0(ID NUMBER);').objects[0]
    changed_source = replace(first.source, objects=tuple(replacement if obj.object_key == consumer.object_key else obj
                                                        for obj in first.source.objects))
    changed = PlanningContext(changed_source, first.target, first.profile, 'Başka kaynak')
    calls = Counter()
    original = dependencies.references

    def counted(obj):
        calls[obj.object_key] += 1
        return original(obj)

    monkeypatch.setattr(dependencies, 'references', counted)
    assert missing_sequence_change(first, sequence).decision == 'REVIEW_REQUIRED'
    assert missing_sequence_change(without_existing, sequence).decision == 'READY'
    assert missing_sequence_change(changed, sequence).decision == 'READY'
    assert missing_sequence_change(first, sequence).decision == 'REVIEW_REQUIRED'
    assert calls == Counter({consumer.object_key: 2})


def test_new_consumers_do_not_get_treated_as_existing_or_analyzed_for_collision(monkeypatch):
    context = sequence_fixture(sequence_count=2, consumer_count=2)
    context = PlanningContext(context.source, actual(), context.profile, 'Boş hedef')
    calls = []
    original = dependencies.references

    def counted(obj):
        calls.append(obj.object_key)
        return original(obj)

    monkeypatch.setattr(dependencies, 'references', counted)
    for obj in context.source.objects:
        if obj.identity.object_type == 'SEQUENCE':
            op = missing_sequence_change(context, obj)
            assert op.decision == 'READY' and op.intent is not None
            assert op.intent.statement == obj.raw_ddl
    assert calls == []


def test_indexed_lookup_preserves_side_type_case_parent_and_first_match():
    original = source('CREATE TABLE APP.T(ID NUMBER);').objects[0]
    first = replace(original, identity=replace(original.identity, parent_key='first-parent'))
    later = replace(original, identity=replace(original.identity, parent_key='later-parent'))
    quoted_same = replace(original, identity=replace(original.identity, owner=Identifier.parse('"APP"'),
                           name=Identifier.parse('"T"'), parent_key='quoted-parent'))
    mixed = replace(original, identity=replace(original.identity, name=Identifier.parse('"t"')))
    view = replace(original, identity=replace(original.identity, object_type='VIEW'))
    other_owner = replace(original, identity=replace(original.identity, owner=Identifier.parse('"App"')))
    desired = replace(source('CREATE TABLE APP.T(ID NUMBER);'), schemas=('APP', 'App'),
                      objects=(first, later, quoted_same, mixed, view, other_owner))
    target_first = replace(first, raw_ddl=b'actual target marker')
    observed = replace(actual(), objects=(target_first, later, quoted_same, view))
    context = PlanningContext(desired, observed, profile(), 'Sentetik hedef')
    assert context.lookup('APP', 'TABLE', 'T') is first
    assert context.lookup('APP', 'TABLE', 'T', desired=False) is target_first
    assert context.lookup('APP', 'TABLE', 't') is mixed
    assert context.lookup('App', 'TABLE', 'T') is other_owner
    assert context.lookup('APP', 'VIEW', 'T') is view
    assert context.lookup('APP', 'VIEW', 'T', desired=False) is view
    assert context.lookup('APP', 'TABLE', 't', desired=False) is None
    assert context.lookup('APP', 'SEQUENCE', 'T') is None
    assert context.lookup('MISSING', 'TABLE', 'T') is None
    assert not context.new_table('APP', 'T')
    assert context.new_table('APP', 't')


def test_consumer_index_preserves_raw_source_order_and_deduplicates_reference_roles():
    context = sequence_fixture(sequence_count=1, consumer_count=3)
    consumers = [obj for obj in context.source.objects if obj.identity.object_type == 'TABLE']
    # A declared edge and a token NEXTVAL edge to the same sequence are one consumer.
    repeated = replace(consumers[0], properties={**consumers[0].properties,
        'dependencies': KnownValue('KNOWN', [{'owner': 'APP', 'type': 'SEQUENCE', 'name': 'S0'}],
                                   consumers[0].evidence_ids)})
    expected = (consumers[2], repeated, consumers[1])
    sequences = tuple(obj for obj in context.source.objects if obj.identity.object_type == 'SEQUENCE')
    desired = replace(context.source, objects=(*expected, *sequences))
    context = PlanningContext(desired, context.target, context.profile, 'Sentetik hedef')
    assert context.existing_sequence_consumers('APP', 'S0') == expected
    assert context.existing_sequence_consumers('APP', 's0') == ()
    assert context.existing_sequence_consumers('OTHER', 'S0') == ()
