"""Generator identity semantics layered over unchanged Analyzer projections."""
from dataclasses import replace
from ..model.serialization import digest
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed,top_level_items,source_span
from .._vendor.analyzer_core.oracle.table import constraint_properties
from .canonicalize import canonical_sql
from ..model.identity import Identifier


def effective_key(key: str) -> str:
    return key[2:] if key.startswith(('U:', 'Q:')) else key


def anonymous_constraint_key(definition, existing):
    """Keep repeated identical CHECKs without inventing Oracle constraint names.

    PK/UK/FK identity collisions and differing CHECK states stay ambiguous.
    The first occurrence retains the existing semantic key.
    """
    details=constraint_properties(definition)
    if not details['kind'] or not (details['columns'] or details['condition']):return None
    signature=[details['kind'],canonical_sql(details['columns'] or details['condition'])]
    base='@anonymous-'+digest(signature)
    key=base;occurrence=1
    while key in existing:
        if details['kind']!='CHECK' or canonical_sql(existing[key])!=canonical_sql(definition):return None
        occurrence+=1;key=base+'-'+str(occurrence)
    return key


def normalize_projection(projection,source_text=None):
    if projection.object_type=='INDEX' and source_text is not None:
        tokens=code_tokens(source_text) or ()
        on=next((i for i,token in enumerate(tokens) if token.upper=='ON'),None)
        opening=next((i for i in range(on+1,len(tokens)) if tokens[i].text=='('),None) if on is not None else None
        body=enclosed(tokens,opening) if opening is not None else None
        depth=0
        for token in tokens[body[1]:] if body else ():
            if token.text=='(': depth+=1
            elif token.text==')': depth-=1
            elif depth==0 and token.upper=='UNUSABLE':
                properties=dict(projection.properties);properties['availability']='UNUSABLE'
                return replace(projection,properties=properties)
    if projection.object_type != 'TABLE':
        return projection
    properties = dict(projection.properties)
    diagnostics = list(projection.diagnostics)
    for family in ('columns', 'constraints', 'comments', 'partitions'):
        values = properties.get(family, {})
        normalized = {effective_key(key): value for key, value in values.items()}
        if len(normalized) != len(values):
            diagnostics.append('DUPLICATE_EFFECTIVE_COMPONENT_IDENTITY')
        properties[family] = normalized
    properties['_unresolved_columns'] = tuple(effective_key(key) for key in properties.get('_unresolved_columns', ()))
    for record in properties.pop('_generator_inline_backing_keys',()):
        column=Identifier.parse(record['column']).effective_name
        definition=record['definition'];details=constraint_properties(definition)
        key=(Identifier.parse(record['name']).effective_name if record['name'] else
             '@anonymous-'+digest([details['kind'],canonical_sql(details['columns'])]))
        if column not in properties['columns'] or key in properties['constraints']:
            diagnostics.append('INLINE_BACKING_KEY_IDENTITY_CONFLICT');continue
        detail=dict(properties['columns'][column]);detail['definition']=record['column_definition']
        properties['columns'][column]=detail;properties['constraints'][key]=definition
    if source_text is not None and 'UNNAMED_CONSTRAINT_UNRESOLVED' in diagnostics:
        tokens=code_tokens(source_text) or ()
        opening=next((index for index,token in enumerate(tokens) if token.text=='('),None)
        group=enclosed(tokens,opening) if opening is not None else None
        items=top_level_items(group[0]) if group else None
        found=[];complete=items is not None
        for item in items or ():
            if item[0].upper not in {'PRIMARY','UNIQUE','FOREIGN','CHECK'}:
                continue
            definition=source_span(source_text,item)
            # Anonymous constraints have no source-controlled Oracle name.
            # Their logical key uses kind+column/expression identity, not a
            # manufactured CONSTRAINT name that would alter emitted DDL.
            key=anonymous_constraint_key(definition,{**properties['constraints'],**dict(found)})
            if key is None:
                complete=False;break
            found.append((key,definition))
        if complete and found:
            properties['constraints'].update(found)
            diagnostics=[code for code in diagnostics if code!='UNNAMED_CONSTRAINT_UNRESOLVED']
    return replace(projection, properties=properties, diagnostics=tuple(sorted(set(diagnostics))))
