"""Oracle DB Migration Generator planının nesne aramalarını sentetik olarak sınar.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from dataclasses import replace

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.difference import Difference
from oracle_db_migration_generator.model.identity import Identifier
from oracle_db_migration_generator.model.snapshot import KnownValue
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


def test_missing_sequences_emit_source_ddl_with_existing_consumers():
    context = sequence_fixture()
    sequences = [obj for obj in context.source.objects if obj.identity.object_type == 'SEQUENCE']
    decisions = [missing_sequence_change(context, obj) for obj in sequences]
    assert len(decisions) == 4
    assert all(op.decision == 'READY' and op.intent for op in decisions)
    assert all(op.intent.statement==obj.raw_ddl for op,obj in zip(decisions,sequences))


def test_filtered_existing_consumer_does_not_hide_missing_sequence_ddl():
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
    assert sequence.decision == 'READY' and sequence.intent is not None


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
