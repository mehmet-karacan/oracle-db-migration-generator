"""Metadata proofs for independent, non-destructive column changes."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier, enclosed
from .table_ddl import source_projection


def not_null_relaxation_evidence(actual,name,before,after):
    for fields,nullable in ((before,False),(after,True)):
        value=fields.get('nullable')
        if not value or value.state!='KNOWN' or value.value is not nullable:return None
        default_on_null=fields.get('default_on_null')
        if not default_on_null or default_on_null.state!='KNOWN' or default_on_null.value is not False:return None
        for key in ('identity','virtual_expression'):
            value=fields.get(key)
            if not value or value.state!='KNOWN' or value.value is not None:return None
    constraints=actual.properties.get('dictionary.constraints')
    columns=actual.properties.get('dictionary.constraint_columns')
    if not constraints or not columns or constraints.state!='KNOWN' or columns.state!='KNOWN':return None
    table=actual.identity.name.effective_name
    if any(row.get('table_name')!=table for row in (*constraints.value,*columns.value)):return None
    for row in constraints.value:
        if row.get('constraint_type')!='P':continue
        members=[c.get('column_name') for c in columns.value if c.get('constraint_name')==row.get('constraint_name')]
        if not members or name in members:return None
    projection=source_projection(actual)
    detail=projection.properties.get('columns',{}).get(name) if projection else None
    if not detail or detail.get('nullable')!='NOT NULL':return None
    proof=[]
    for row in constraints.value:
        if (row.get('constraint_type')!='C' or row.get('status')!='ENABLED'
                or row.get('deferrable')!='NOT DEFERRABLE' or row.get('validated')!='VALIDATED'):continue
        tokens=code_tokens(row.get('search_condition') or '') or ()
        while tokens and tokens[0].text=='(':
            group=enclosed(tokens,0)
            if group is None or group[1]!=len(tokens):break
            tokens=group[0]
        try:
            exact=len(tokens)==4 and identifier(tokens[0])[0]==name and [t.upper for t in tokens[1:]]==['IS','NOT','NULL']
        except ValueError:exact=False
        members=[c.get('column_name') for c in columns.value if c.get('constraint_name')==row.get('constraint_name')]
        if exact and members==[name]:proof.append(row)
    if len(proof)!=1:return None
    return tuple(sorted(set(constraints.evidence_ids+columns.evidence_ids)))
