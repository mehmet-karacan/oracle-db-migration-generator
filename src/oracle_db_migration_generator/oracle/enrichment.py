"""Attach dictionary groups without converting unavailable groups to empty."""
from dataclasses import replace

from ..model.snapshot import KnownValue


def index_metadata_groups(groups):
    """Index captured rows once, retaining source order and duplicate rows."""
    result = {}
    for group, rows in groups.items():
        if group in {'grantees', 'nls'} or rows is None:
            continue
        generic, indexes = {}, {}
        for row in rows:
            if group in {'dependencies', 'errors'}:
                keys = {(row.get('name'), row.get('type'))}
            elif group == 'partition_keys':
                keys = {(row.get('name'), row.get('object_type'))}
            elif group == 'materialized_view_logs':
                keys = {row.get('master')}
            else:
                keys = {row.get(field) for field in ('table_name', 'sequence_name', 'synonym_name')}
                indexes.setdefault(row.get('index_name'), []).append(row)
            # A row matching multiple identity fields is still attached once.
            for key in keys:
                generic.setdefault(key, []).append(row)
        result[group] = (generic, indexes)
    return result


def enrich_object(obj, groups, group_evidence, *, row_index=None):
    if row_index is None:
        row_index = index_metadata_groups(groups)
    props = dict(obj.properties)
    name = obj.identity.name.effective_name
    kind = obj.identity.object_type
    oracle_type = {'PACKAGE_SPEC':'PACKAGE','PACKAGE_BODY':'PACKAGE BODY',
                   'TYPE_SPEC':'TYPE','TYPE_BODY':'TYPE BODY'}.get(kind,kind.replace('_',' '))
    for group, rows in groups.items():
        if group in {'grantees', 'nls'}:
            continue
        if rows is None:
            props['dictionary.' + group] = KnownValue('UNKNOWN', None, (group_evidence[group],))
            continue
        generic, indexes = row_index[group]
        if group in {'dependencies', 'errors'}:
            relevant = generic.get((name, oracle_type), [])
        elif group == 'partition_keys':
            relevant = generic.get((name, 'INDEX' if kind == 'INDEX' else 'TABLE'), [])
        elif group == 'materialized_view_logs':
            relevant = generic.get(name, [])
        elif kind == 'INDEX':
            relevant = indexes.get(name, [])
        else:
            relevant = generic.get(name, [])
        props['dictionary.' + group] = KnownValue('KNOWN', relevant, (group_evidence[group],))
    return replace(obj, properties=props)
