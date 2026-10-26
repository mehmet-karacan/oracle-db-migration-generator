"""Presentation groups over canonical differences. No comparison or SQL decisions."""
from collections import Counter
import json


def pointer_parts(path):
    return [p.replace('~1','/').replace('~0','~') for p in path.strip('/').split('/')]


def presence_status(rows):
    for row in rows:
        if pointer_parts(row['property_path'])[-1] not in {'exists','presence'}:continue
        source,target=row['source'],row['target']
        def exists(value):
            if value['state']=='ABSENT':return False
            if value['state']=='KNOWN' and not value.get('omitted') and isinstance(value.get('value'),bool):return value['value']
            return None
        a,b=exists(source),exists(target)
        if a is True and b is False:return 'MISSING'
        if a is False and b is True:return 'EXTRA'
    return None


def constraint_type(rows):
    for row in rows:
        if pointer_parts(row['property_path'])[-1]!='kind':continue
        for side in ('source','target'):
            value=row[side]
            if value['state']!='KNOWN' or value.get('omitted'):continue
            raw=value.get('value')
            if isinstance(raw,str) and raw.startswith('[['):
                try:
                    tokens=json.loads(raw)
                    if not all(isinstance(t,list) and len(t)==2 and t[0]=='code' and isinstance(t[1],str) for t in tokens):continue
                    raw=' '.join(t[1] for t in tokens)
                except (ValueError,TypeError):continue
            kind={'FOREIGN KEY':'FOREIGN_KEY','PRIMARY KEY':'PRIMARY_KEY','UNIQUE':'UNIQUE_KEY','CHECK':'CHECK_CONSTRAINT'}.get(raw if isinstance(raw,str) else '')
            if kind:return kind
    return 'CONSTRAINT'


def structure_groups(obj):
    groups={}
    for row in obj['differences']:
        parts=pointer_parts(row['property_path']);root=parts[0]
        child=root in {'columns','constraints'} and len(parts)>=3
        key='/'+('/'.join(row['property_path'].strip('/').split('/')[:2]) if child else root)
        group=groups.setdefault(key,{'id':key,'name':parts[1] if child else '',
            'section':{'columns':'columns','constraints':'constraints','index':'indexes'}.get(root,'other'),
            'entity_type':{'columns':'COLUMN','constraints':'CONSTRAINT','index':'INDEX','sequence':'SEQUENCE'}.get(root,'OBJECT_PROPERTY'),
            'rows':[]})
        group['rows'].append(row)
    for group in groups.values():
        rows=group['rows'];kinds={r['kind'] for r in rows}
        group['difference_count']=len(rows)
        group['unknown_count']=sum(r['kind']=='UNKNOWN' or any(r[s]['state']=='UNKNOWN' for s in ('source','target')) for r in rows)
        group['status']=presence_status(rows) or ('UNKNOWN' if group['unknown_count'] else 'INFORMATIONAL' if kinds=={'INFORMATIONAL'} else 'CHANGED')
        if group['entity_type']=='CONSTRAINT':group['entity_type']=constraint_type(rows)
        ids={r['id'] for r in rows}
        group['operation_ids']=[op['id'] for op in obj['operations'] if ids.intersection(op['change_ids'])]
    return list(groups.values())


def structure_summary(obj,groups):
    counts=Counter((g['entity_type'],g['status']) for g in groups)
    root_rows=[r for r in obj['differences'] if pointer_parts(r['property_path'])[0] in {'presence','exists'}]
    return {'group_count':len(groups),'unknown_count':sum(g['unknown_count'] for g in groups),
        'object_presence':presence_status(root_rows),
        'items':[{'entity_type':entity,'status':status,'count':count} for (entity,status),count in sorted(counts.items())]}
