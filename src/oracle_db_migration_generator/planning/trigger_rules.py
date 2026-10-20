"""Bound the single sequence assignment allowed without an exporter inventory."""
from .._vendor.analyzer_core.oracle.ddl_tokens import identifier
from .table_ddl import source_projection
from .table_rules import column_fields


def sequence_only_insert(context,obj,table,tokens,body_start):
    if table.coverage.ddl!='COMPLETE':return False
    header=[token.upper for token in tokens[:body_start]]
    if (any(word in header for word in ('UPDATE','DELETE','WHEN','DECLARE','INSTEAD','FOLLOWS','PRECEDES'))
            or not any(header[i:i+2]==['BEFORE','INSERT'] for i in range(len(header)-1))
            or not any(header[i:i+3]==['FOR','EACH','ROW'] for i in range(len(header)-2))):return False
    if 'REFERENCING' in header:
        at=header.index('REFERENCING')+1
        try:
            while header[at] in {'NEW','OLD'}:
                original=header[at];at+=1
                if header[at]=='AS':at+=1
                if identifier(tokens[at])[0]!=original:return False
                at+=1
            if header[at:at+3]!=['FOR','EACH','ROW']:return False
        except (IndexError,ValueError):return False
    body=list(tokens[body_start:])
    if not body or body[0].upper!='BEGIN':return False
    at=1
    try:
        if body[at].upper!=':NEW' or body[at+1].text!='.':return False
        column=identifier(body[at+2])[0];at+=3
        if body[at].text!=':=':return False
        at+=1
        identifier(body[at]);at+=1
        if body[at].text!='.':return False
        at+=1
        if body[at].upper!='NEXTVAL':
            identifier(body[at]);at+=1
            if body[at].text!='.':return False
            at+=1
        if body[at].upper!='NEXTVAL':return False
        at+=1
        if body[at].text!=';' or body[at+1].upper!='END':return False
        at+=2
        if body[at].text!=';':
            if identifier(body[at])[0]!=obj.identity.name.effective_name:return False
            at+=1
        if body[at].text!=';' or at+1!=len(body):return False
    except (IndexError,ValueError):return False
    fields=column_fields(table,context.source,context.profile.policy).get(column)
    projection=source_projection(table)
    detail=projection.properties.get('columns',{}).get(column) if projection else None
    return bool(fields and fields['data_type'].state=='KNOWN' and fields['data_type'].value=='NUMBER'
                and detail and not detail.get('identity') and not detail.get('virtual_expression'))
