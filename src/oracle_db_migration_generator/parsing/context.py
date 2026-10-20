"""Apply validated export context to projections using effective identities."""
from dataclasses import replace

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, enclosed, identifier, source_span, top_level_items
from .._vendor.analyzer_core.oracle.table import extract_table
from ..model.serialization import thaw
from ..model.snapshot import KnownValue
from .projections import anonymous_constraint_key,normalize_projection


def apply_context(obj, text, evidence_id, boundary):
    tokens = tuple(token for token in code_tokens(text) if token.text!=';')
    action = tokens[boundary].upper
    projection = obj.projection
    if projection is None:
        raise ValueError('CONTEXT_PROJECTION_UNAVAILABLE')
    properties = dict(projection.properties)
    if obj.identity.object_type=='TRIGGER':
        if action not in {'ENABLE','DISABLE'} or boundary!=len(tokens)-1:
            raise ValueError('TRIGGER_CONTEXT_UNSUPPORTED')
        properties['enabled_state'] = action
    elif obj.identity.object_type=='INDEX':
        if action!='UNUSABLE' or boundary!=len(tokens)-1:
            raise ValueError('INDEX_CONTEXT_UNSUPPORTED')
        properties['availability']='UNUSABLE'
    else:
        columns = {name:dict(value) for name,value in properties.get('columns',{}).items()}
        constraints = dict(properties.get('constraints',{}))
        table_properties = dict(properties.get('table_properties',{}))
        changed = set(properties.get('_context_changed_columns',()))
        payload = tokens[boundary+1:]
        if action in {'ADD','MODIFY'}:
            if payload and payload[0].text=='(':
                group = enclosed(payload,0)
                if group is None or group[1]!=len(payload):
                    raise ValueError('TABLE_CONTEXT_UNRESOLVED')
                items = top_level_items(group[0])
            else:
                items = (payload,)
            if not items:
                raise ValueError('TABLE_CONTEXT_UNRESOLVED')
            for item in items:
                name = identifier(item[0])[0]
                if action=='MODIFY' and name not in columns:
                    raise ValueError('ALTER_COLUMN_NOT_IN_CREATE')
                words = tuple(token.upper for token in item[1:])
                if action=='MODIFY' and words in {('NOT','NULL'),('NULL',)}:
                    columns[name]['nullable'] = 'NOT NULL' if words[0]=='NOT' else 'NULL'
                    changed.add(name)
                    continue
                if action=='MODIFY' and words and words[0]=='DEFAULT':
                    start = 4 if words[1:3]==('ON','NULL') else 2
                    if start>=len(item) or any(word in {'CASE','SELECT','NOT','CONSTRAINT'} for word in words[start-1:]):
                        raise ValueError('COMPLEX_DEFAULT_CONTEXT_UNSUPPORTED')
                    if columns[name].get('default_on_null') and start!=4:
                        raise ValueError('DEFAULT_ON_NULL_CONTEXT_UNRESOLVED')
                    columns[name]['default'] = source_span(text,item[start:])
                    columns[name]['default_on_null'] = 'DEFAULT ON NULL' if start==4 else None
                    changed.add(name)
                    continue
                incoming_text='CREATE TABLE X ('+source_span(text,item)+');'
                extracted = extract_table(incoming_text)
                incoming=normalize_projection(replace(projection,properties={
                    'columns':extracted.columns,'constraints':extracted.constraints,
                    '_unresolved_columns':extracted.unresolved_columns},diagnostics=extracted.diagnostics),incoming_text)
                if incoming.diagnostics:
                    raise ValueError('TABLE_CONTEXT_COMPONENT_UNRESOLVED')
                incoming_columns = incoming.properties['columns']
                incoming_constraints = incoming.properties['constraints']
                if action=='ADD':
                    if set(incoming_columns)&set(columns):
                        raise ValueError('DUPLICATE_CONTEXT_COMPONENT')
                    combined=dict(constraints)
                    for key,definition in incoming_constraints.items():
                        if key.startswith('@anonymous-') and code_tokens(definition)[0].upper!='CONSTRAINT':
                            key=anonymous_constraint_key(definition,combined)
                        if key is None or key in combined:raise ValueError('DUPLICATE_CONTEXT_COMPONENT')
                        combined[key]=definition
                    for key,value in incoming_columns.items():
                        value = dict(value);value['position'] = str(len(columns)+1)
                        columns[key] = value
                    constraints=combined
                elif len(incoming_columns)==1 and not incoming_constraints:
                    incoming = incoming_columns[name]
                    for key in ('data_type','length','length_semantics','precision','scale'):
                        columns[name][key] = incoming.get(key)
                    for key,value in incoming.items():
                        if key not in {'position','data_type','length','length_semantics','precision','scale'} and value is not None:
                            columns[name][key] = value
                    changed.add(name)
                else:
                    raise ValueError('ALTER_CONSTRAINT_CONTEXT_UNSUPPORTED')
        elif action=='DROP' and len(payload)==2 and payload[0].upper in {'COLUMN','CONSTRAINT'}:
            name = identifier(payload[1])[0]
            collection = columns if payload[0].upper=='COLUMN' else constraints
            if name not in collection:
                raise ValueError('DROP_CONTEXT_COMPONENT_UNRESOLVED')
            collection.pop(name)
        elif action in {'PARALLEL','NOPARALLEL','LOGGING','NOLOGGING'}:
            if len(payload)>1 or payload and not payload[0].text.isdecimal():
                raise ValueError('TABLE_PHYSICAL_CONTEXT_UNRESOLVED')
            table_properties['parallel' if 'PARALLEL' in action else 'logging'] = source_span(text,tokens[boundary:])
        else:
            raise ValueError('TABLE_CONTEXT_UNSUPPORTED')
        properties.update(columns=columns,constraints=constraints,table_properties=table_properties,
                          _context_changed_columns=tuple(sorted(changed)))
    projection = replace(projection,properties=properties)
    props = dict(obj.properties)
    props['projection'] = KnownValue('KNOWN',thaw(projection.properties),obj.evidence_ids+(evidence_id,))
    return replace(obj,properties=props,projection=projection,evidence_ids=obj.evidence_ids+(evidence_id,))
