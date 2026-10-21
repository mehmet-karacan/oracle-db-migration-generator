"""Derive partitioned-index availability only from complete leaf metadata.

ALL_INDEXES.STATUS describes nonpartitioned indexes. Partitioned indexes
need ALL_IND_PARTITIONS and, for composite indexes, ALL_IND_SUBPARTITIONS.
An independent count of materialized index partitions and each partition's
SUBPARTITION_COUNT prove that no leaf is missing. Interval indexes can carry
the maximum possible count in ALL_PART_INDEXES.PARTITION_COUNT, rather than
the number already materialized. The same fields exist in the DBA views.
https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_INDEXES.html
https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_PART_INDEXES.html
https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_IND_PARTITIONS.html
https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_IND_SUBPARTITIONS.html
"""
from collections.abc import Mapping

from ..model.snapshot import KnownValue


def partition_index_availability(obj):
    """Return KNOWN VALID/UNUSABLE, UNKNOWN, or NOT_APPLICABLE.

    This does not infer health from a top-level N/A. Missing capture,
    unexpected statuses, duplicate identities, missing partitions or an
    incomplete composite partition all remain UNKNOWN.
    """
    groups=('indexes','index_partitioning','index_partitions','index_subpartitions','index_partition_counts')
    observed={name:obj.properties.get('dictionary.'+name) for name in groups}
    evidence=tuple(dict.fromkeys(eid for value in observed.values() if value is not None for eid in value.evidence_ids))
    unknown=KnownValue('UNKNOWN',None,evidence or obj.evidence_ids)
    if obj.identity.object_type!='INDEX':
        return KnownValue('NOT_APPLICABLE',None,obj.evidence_ids)
    name=obj.identity.name.effective_name

    def rows(group):
        value=observed[group]
        if value is None or value.state!='KNOWN' or not isinstance(value.value,(tuple,list)):
            return None
        result=value.value
        if any(not isinstance(row,Mapping) or row.get('index_name')!=name for row in result):
            return None
        return result

    top=rows('indexes')
    if top is None or len(top)!=1:return unknown
    if top[0].get('partitioned')=='NO':
        return KnownValue('NOT_APPLICABLE',None,observed['indexes'].evidence_ids)
    if top[0].get('partitioned')!='YES':return unknown
    header,partitions,subpartitions,counts=(rows(group) for group in groups[1:])
    if header is None or len(header)!=1 or not partitions or subpartitions is None or counts is None or len(counts)!=1:return unknown
    expected=counts[0].get('partition_count')
    if type(expected) is not int or expected<1 or len(partitions)!=expected:return unknown
    declared=header[0].get('partition_count')
    if type(declared) is not int or declared<1:return unknown
    interval=header[0].get('interval')
    if declared!=expected and not (declared==1048575 and isinstance(interval,str) and interval.strip()):return unknown
    subkind=header[0].get('subpartitioning_type')
    if subkind not in {'NONE','RANGE','HASH','SYSTEM','LIST','REFERENCE'}:return unknown
    composite=subkind!='NONE'
    parents={}
    for row in partitions:
        parent=row.get('partition_name')
        if not isinstance(parent,str) or not parent or parent in parents:return unknown
        if row.get('composite')!=('YES' if composite else 'NO'):return unknown
        if row.get('status') not in {'USABLE','UNUSABLE','N/A'}:return unknown
        parents[parent]=row
    if composite:
        children={parent:[] for parent in parents}
        seen=set()
        for row in subpartitions:
            parent,child=row.get('partition_name'),row.get('subpartition_name')
            if parent not in parents or not isinstance(child,str) or not child or child in seen:return unknown
            children[parent].append(row);seen.add(child)
        leaves=[]
        for parent,row in parents.items():
            count=row.get('subpartition_count')
            if type(count) is not int or count<1 or len(children[parent])!=count:return unknown
            leaves.extend(children[parent])
    else:
        if subpartitions or any(row.get('subpartition_count') not in (None,0) for row in partitions):return unknown
        leaves=partitions
    statuses=[row.get('status') for row in leaves]
    if not statuses or any(status not in {'USABLE','UNUSABLE'} for status in statuses):return unknown
    return KnownValue('KNOWN','UNUSABLE' if 'UNUSABLE' in statuses else 'VALID',evidence)
