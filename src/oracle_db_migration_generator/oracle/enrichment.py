"""Attach dictionary groups without converting unavailable groups to empty."""
from dataclasses import replace

from ..model.snapshot import KnownValue


def enrich_object(obj, groups, group_evidence):
    props = dict(obj.properties)
    name = obj.identity.name.effective_name
    kind = obj.identity.object_type
    for group, rows in groups.items():
        if group in {'grantees', 'nls'}:
            continue
        if rows is None:
            props['dictionary.' + group] = KnownValue('UNKNOWN', None, (group_evidence[group],))
            continue
        relevant = []
        for row in rows:
            # These keys are metadata identity fields, never user data fields.
            matches = row.get('table_name') == name or row.get('sequence_name') == name or row.get('synonym_name') == name
            if kind == 'INDEX':
                matches = row.get('index_name') == name or (group == 'constraints' and row.get('index_name') == name)
            if group in {'dependencies', 'errors'}:
                oracle_type = {'PACKAGE_SPEC':'PACKAGE','PACKAGE_BODY':'PACKAGE BODY','TYPE_SPEC':'TYPE','TYPE_BODY':'TYPE BODY'}.get(kind,kind.replace('_',' '))
                matches = row.get('name') == name and row.get('type') == oracle_type
            elif group == 'partition_keys':
                matches = row.get('name') == name and row.get('object_type') == ('INDEX' if kind == 'INDEX' else 'TABLE')
            elif group == 'materialized_view_logs':
                matches = row.get('master') == name
            if matches:
                relevant.append(row)
        props['dictionary.' + group] = KnownValue('KNOWN', relevant, (group_evidence[group],))
    return replace(obj, properties=props)
