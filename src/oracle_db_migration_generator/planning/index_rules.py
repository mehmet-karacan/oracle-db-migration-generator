"""Closed expression-index proof; return referenced columns, never rewritten SQL."""
from .._vendor.analyzer_core.oracle.ddl_tokens import top_level_items
from .partition_rules import _name,_literal
from .table_rules import column_fields


def index_key_columns(context,table,tokens):
    actual=context.lookup(table.identity.owner.effective_name,'TABLE',table.identity.name.effective_name,desired=False)
    proof=actual or table
    property_=proof.properties.get('projection')
    if proof.coverage.ddl!='COMPLETE' or not property_ or property_.state!='KNOWN':
        raise ValueError('INDEX_TABLE_SHAPE_UNVERIFIED')
    fields=column_fields(proof,context.target if actual else context.source,context.profile.policy)
    columns=[];expression=False;evidence_ids=set(proof.evidence_ids)
    for item in top_level_items(tokens) or ():
        if item and item[-1].upper in {'ASC','DESC'}:item=item[:-1]
        if len(item)==1:
            columns.append(_name(item[0]));continue
        if (len(item)!=6 or item[0].upper!='TO_CHAR' or item[1].text!='('
                or item[3].text!=',' or item[5].text!=')'):
            raise ValueError('INDEX_EXPRESSION_UNSUPPORTED')
        expression=True
        name=_name(item[2]);column=fields.get(name,{});datatype=column.get('data_type')
        if not datatype or datatype.state!='KNOWN' or datatype.value not in {'DATE','TIMESTAMP'}:
            raise ValueError('INDEX_EXPRESSION_TYPE_UNVERIFIED')
        if _literal(item[4]).upper() not in {'YYYYMM','YYYYMMDD','YYYY-MM-DD'}:
            raise ValueError('INDEX_EXPRESSION_FORMAT_UNSUPPORTED')
        if any(context.lookup(table.identity.owner.effective_name,'FUNCTION','TO_CHAR',desired=side) for side in (True,False)):
            raise ValueError('INDEX_EXPRESSION_FUNCTION_SHADOWED')
        calendar=context.target.capabilities.get('nls_calendar')
        if not calendar or calendar.state!='KNOWN' or calendar.value!='GREGORIAN':
            raise ValueError('INDEX_EXPRESSION_NLS_UNVERIFIED')
        evidence_ids.update(calendar.evidence_ids)
        evidence_ids.update(datatype.evidence_ids)
        columns.append(name)
    if not columns:raise ValueError('INDEX_KEYS_UNVERIFIED')
    return tuple(columns),expression,tuple(sorted(evidence_ids))
