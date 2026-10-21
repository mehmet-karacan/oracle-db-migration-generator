from dataclasses import replace
from types import SimpleNamespace

from oracle_db_migration_generator.compare.scope import _exclusions
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import KnownValue
from tests.factories import profile


def scope_object(name, kind, *, target=None, parent_key=None, probes=None):
    identity = ObjectIdentity('test', Identifier.parse('APP'), kind, Identifier.parse(name), parent_key)
    key = identity.key
    if probes is not None:
        original = identity

        class CountingIdentity:
            @property
            def owner(self):
                probes.append('owner')
                return original.owner

            def __getattr__(self, attribute):
                return getattr(original, attribute)

        identity = CountingIdentity()
    properties = {}
    if target:
        properties['dictionary.indexes'] = KnownValue('KNOWN', [{'index_name': name,
            'table_owner': 'APP', 'table_name': target}], ())
    return SimpleNamespace(object_key=key, identity=identity, properties=properties)


def snapshot(objects):
    return SimpleNamespace(profile_id='test', objects=tuple(objects))


def test_parent_resolution_reads_candidate_identities_linearly():
    probes = []
    objects = [scope_object('TABLE_'+str(i), 'TABLE', probes=probes) for i in range(40)]
    objects += [scope_object('INDEX_'+str(i), 'INDEX', target='TABLE_'+str(i % 40), probes=probes)
                for i in range(80)]
    assert _exclusions(snapshot(objects), profile().policy) == {}
    # An unrelated identity must not be reread for every child. Count actual
    # candidate work rather than using machine-dependent elapsed thresholds.
    assert len(probes) <= 10 * len(objects)


def test_ambiguous_parent_names_do_not_inherit_one_candidates_exclusion():
    table = scope_object('BUSINESS', 'TABLE')
    view = scope_object('BUSINESS', 'VIEW')
    index = scope_object('IX_BUSINESS', 'INDEX', target='BUSINESS')
    selected = replace(profile().policy, excluded_object_types=('TABLE',))
    assert _exclusions(snapshot([table, view, index]), selected) == {
        table.object_key: ('EXCLUDED_OBJECT_TYPE', None)}
    assert _exclusions(snapshot([table, index]), selected) == {
        table.object_key: ('EXCLUDED_OBJECT_TYPE', None),
        index.object_key: ('EXCLUDED_PARENT_OBJECT', table.object_key)}


def test_explicit_parent_key_retains_precedence_over_ambiguous_names():
    table = scope_object('BUSINESS', 'TABLE')
    view = scope_object('BUSINESS', 'VIEW')
    index = scope_object('IX_BUSINESS', 'INDEX', target='BUSINESS', parent_key=table.object_key)
    selected = replace(profile().policy, excluded_object_types=('TABLE',))
    assert _exclusions(snapshot([index, view, table]), selected) == {
        table.object_key: ('EXCLUDED_OBJECT_TYPE', None),
        index.object_key: ('EXCLUDED_PARENT_OBJECT', table.object_key)}
