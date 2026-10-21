"""Partition index availability requires complete observed leaf metadata."""
from dataclasses import replace

import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import SnapshotObject, Coverage, KnownValue
from oracle_db_migration_generator.oracle import queries


def index(*, composite=False, statuses=('USABLE','USABLE')):
    identity=ObjectIdentity('test',Identifier.parse('APP'),'INDEX',Identifier.parse('IDX'))
    groups={
        'indexes':[dict(index_name='IDX',partitioned='YES',status='N/A')],
        'index_partitioning':[dict(index_name='IDX',partition_count=2,subpartitioning_type='HASH' if composite else 'NONE',interval=None)],
        'index_partition_counts':[dict(index_name='IDX',partition_count=2)],
        'index_partitions':[dict(index_name='IDX',partition_name=f'P{pos}',composite='YES' if composite else 'NO',
                                 subpartition_count=1 if composite else 0,status='N/A' if composite else status)
                            for pos,status in enumerate(statuses)],
        'index_subpartitions':[dict(index_name='IDX',partition_name=f'P{pos}',subpartition_name=f'SP{pos}',status=status)
                               for pos,status in enumerate(statuses)] if composite else [],
    }
    return SnapshotObject(identity,{f'dictionary.{name}':KnownValue('KNOWN',rows,(name,)) for name,rows in groups.items()},
                          None,None,Coverage('COMPLETE','COMPLETE','COMPLETE'),('object',))


def availability(obj):
    from oracle_db_migration_generator.oracle.index_status import partition_index_availability
    return partition_index_availability(obj)


@pytest.mark.parametrize(('group','view'),[
    ('index_partitioning','part_indexes'),('index_partitions','ind_partitions'),
    ('index_subpartitions','ind_subpartitions'),
    ('index_partition_counts','ind_partitions'),
])
def test_capture_allowlist_includes_all_and_dba_partition_index_metadata(group,view):
    assert group in queries.CAPTURE_QUERIES
    from oracle_db_migration_generator.oracle.catalog_reader import CATALOG_QUERIES
    columns,sql=queries.CAPTURE_QUERIES[group]
    dba_columns,dba_sql=CATALOG_QUERIES[group]
    assert columns==dba_columns
    assert 'FROM all_'+view in ' '.join(sql.split())
    assert 'FROM dba_'+view in ' '.join(dba_sql.split())
    assert ':owner' in sql and ':owner' in dba_sql


@pytest.mark.parametrize('composite',[False,True])
@pytest.mark.parametrize(('statuses','expected'),[(('USABLE','USABLE'),'VALID'),(('USABLE','UNUSABLE'),'UNUSABLE')])
def test_complete_leaf_statuses_determine_availability(composite,statuses,expected):
    result=availability(index(composite=composite,statuses=statuses))
    assert (result.state,result.value)==('KNOWN',expected)
    assert 'indexes' in result.evidence_ids and 'index_partitions' in result.evidence_ids
    if composite:assert 'index_subpartitions' in result.evidence_ids


@pytest.mark.parametrize('group',['indexes','index_partitioning','index_partition_counts','index_partitions','index_subpartitions'])
def test_unavailable_groups_never_become_valid(group):
    obj=index(composite=True)
    properties=dict(obj.properties);properties['dictionary.'+group]=KnownValue('UNKNOWN',None,('failed',))
    assert availability(replace(obj,properties=properties)).state=='UNKNOWN'


@pytest.mark.parametrize('group',['index_partitioning','index_partitions','index_subpartitions'])
def test_empty_groups_never_prove_composite_index_usable(group):
    obj=index(composite=True)
    properties=dict(obj.properties);properties['dictionary.'+group]=KnownValue('KNOWN',[],('empty',))
    assert availability(replace(obj,properties=properties)).state=='UNKNOWN'


@pytest.mark.parametrize(('group','mutation'),[
    ('index_partitions',lambda rows: rows[:1]),
    ('index_partitions',lambda rows: rows+rows[:1]),
    ('index_partitions',lambda rows: [dict(row,status=None) for row in rows]),
    ('index_partitions',lambda rows: [dict(row,composite=None) for row in rows]),
    ('index_subpartitions',lambda rows: rows[:1]),
    ('index_subpartitions',lambda rows: rows+rows[:1]),
    ('index_subpartitions',lambda rows: [dict(row,status='N/A') for row in rows]),
    ('index_subpartitions',lambda rows: [dict(row,partition_name='MISSING') for row in rows]),
    ('index_subpartitions',lambda rows: [dict(row,index_name='OTHER') for row in rows]),
])
def test_partial_duplicate_unscoped_and_unknown_leaf_metadata_fails_closed(group,mutation):
    obj=index(composite=True)
    properties=dict(obj.properties);value=properties['dictionary.'+group]
    properties['dictionary.'+group]=KnownValue('KNOWN',mutation([dict(row) for row in value.value]),value.evidence_ids)
    assert availability(replace(obj,properties=properties)).state=='UNKNOWN'


def test_na_top_level_status_alone_and_missing_capture_remain_unknown():
    obj=index()
    only_top={key:value for key,value in obj.properties.items() if key=='dictionary.indexes'}
    assert availability(replace(obj,properties=only_top)).state=='UNKNOWN'


def test_nonpartitioned_index_is_outside_leaf_availability_rule():
    obj=index();properties=dict(obj.properties)
    properties['dictionary.indexes']=KnownValue('KNOWN',[dict(index_name='IDX',partitioned='NO',status='VALID')],('indexes',))
    assert availability(replace(obj,properties=properties)).state=='NOT_APPLICABLE'


def test_interval_summary_maximum_uses_independently_observed_materialized_partition_count():
    obj=index();properties=dict(obj.properties)
    properties['dictionary.index_partitioning']=KnownValue('KNOWN',[
        dict(index_name='IDX',partition_count=1048575,subpartitioning_type='NONE',interval="NUMTOYMINTERVAL(1,'MONTH')")
    ],('index_partitioning',))
    assert availability(replace(obj,properties=properties)).value=='VALID'


def test_interval_summary_maximum_never_replaces_missing_materialized_count():
    obj=index();properties=dict(obj.properties)
    properties['dictionary.index_partitioning']=KnownValue('KNOWN',[
        dict(index_name='IDX',partition_count=1048575,subpartitioning_type='NONE',interval="NUMTOYMINTERVAL(1,'MONTH')")
    ],('index_partitioning',))
    properties.pop('dictionary.index_partition_counts')
    assert availability(replace(obj,properties=properties)).state=='UNKNOWN'
