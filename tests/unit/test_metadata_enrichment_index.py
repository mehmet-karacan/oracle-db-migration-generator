from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import Coverage, SnapshotObject
from oracle_db_migration_generator.oracle.enrichment import enrich_object
from tests.unit.test_collector import FakeConnection, FakeCursor, inputs


def make_object(name='T', kind='TABLE'):
    return SnapshotObject(ObjectIdentity('test', Identifier.parse('APP'), kind, Identifier.parse(name)),
                          {}, None, None, Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'), ())


def test_metadata_matching_keeps_row_order_duplicates_and_group_overrides():
    first = {'table_name': 'T', 'index_name': 'IX', 'tag': 'first'}
    second = {'table_name': 'T', 'sequence_name': 'T', 'index_name': 'OTHER', 'tag': 'second'}
    groups = {
        'columns': [first, second, first],
        'dependencies': [{'name': 'T', 'type': 'TABLE'}, {'name': 'T', 'type': 'PACKAGE BODY'}],
        'partition_keys': [{'name': 'T', 'object_type': 'TABLE'}, {'name': 'T', 'object_type': 'INDEX'}],
        'materialized_view_logs': [{'master': 'T', 'table_name': 'OTHER'}],
        'errors': None,
        'grantees': [{'username': 'T'}],
        'nls': [],
    }
    evidence = {group: 'ev-'+group for group in groups}
    table = enrich_object(make_object(), groups, evidence)
    assert [row['tag'] for row in table.properties['dictionary.columns'].value] == ['first', 'second', 'first']
    assert len(table.properties['dictionary.dependencies'].value) == 1
    assert table.properties['dictionary.partition_keys'].value[0]['object_type'] == 'TABLE'
    assert len(table.properties['dictionary.materialized_view_logs'].value) == 1
    assert table.properties['dictionary.errors'].state == 'UNKNOWN'
    assert table.properties['dictionary.errors'].evidence_ids == ('ev-errors',)
    assert 'dictionary.grantees' not in table.properties and 'dictionary.nls' not in table.properties
    index = enrich_object(make_object('IX', 'INDEX'), groups, evidence)
    assert [row['tag'] for row in index.properties['dictionary.columns'].value] == ['first', 'first']
    body = enrich_object(make_object('T', 'PACKAGE_BODY'), groups, evidence)
    assert body.properties['dictionary.dependencies'].value[0]['type'] == 'PACKAGE BODY'


def test_collector_indexes_metadata_rows_once_for_all_objects(monkeypatch):
    from oracle_db_migration_generator.config.credentials import Credentials
    from oracle_db_migration_generator.oracle import collector
    from oracle_db_migration_generator.oracle.queries import CAPTURE_QUERIES

    reads = []

    class MeasuredRow(dict):
        def get(self, key, default=None):
            reads.append(key)
            return super().get(key, default)

    rows = [MeasuredRow(table_name='T'+str(i), column_name='ID') for i in range(40)]
    groups = {group: [] for group in CAPTURE_QUERIES}
    groups['columns'] = rows
    monkeypatch.setattr(collector, '_read_groups', lambda *_: (groups, {}))

    class Cursor(FakeCursor):
        def execute(self, query, binds=None):
            self.binds = binds
            super().execute(query, binds)

        def fetchone(self):
            if 'GET_DDL' in self.current.upper():
                return ('CREATE TABLE APP.'+self.binds['name']+' (ID NUMBER);',)
            return super().fetchone()

    connection = FakeConnection()
    connection.reader = Cursor(inventory=[('TABLE', 'T'+str(i), 'VALID', '1') for i in range(40)])
    target, profile = inputs()
    result = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile,
                                      connect=lambda *_: connection)
    assert result.snapshot is not None and len(result.snapshot.objects) == 40
    timings = result.receipt['schemas'][0]['phase_timings_seconds']
    assert set(timings) == {'dictionary_group_reads', 'reference_metadata', 'ddl_reads',
                           'grammar_projection', 'dictionary_enrichment', 'sidecar_merge', 'total'}
    assert all(isinstance(value, float) and value >= 0 for value in timings.values())
    assert timings['total'] >= sum(value for key, value in timings.items() if key != 'total')
    assert 'phase_timings_seconds' not in result.snapshot.to_dict()
    for obj in result.snapshot.objects:
        assert obj.properties['dictionary.columns'].value[0]['table_name'] == obj.identity.name.effective_name
    # Metadata indexing may inspect each row's identity fields once; it must
    # not scan every row again for each captured object.
    assert len(reads) <= 6 * len(rows)
