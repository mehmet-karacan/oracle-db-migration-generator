"""Separate grammar-validated supplemental logging from relational columns."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed,identifier,source_span,top_level_items


def table_projection_input(text):
    """Called only after full Oracle grammar validation; raw DDL is unchanged."""
    tokens=code_tokens(text) or ()
    table_at=next((i for i,t in enumerate(tokens) if t.upper=='TABLE'),None)
    opening=next((i for i in range(table_at+1,len(tokens)) if tokens[i].text=='('),None) if table_at is not None else None
    body=enclosed(tokens,opening) if opening is not None else None
    items=top_level_items(body[0]) if body else None
    if not items:return text,()
    columns=[];logging=[]
    for item in items:
        if len(item)>=3 and [t.text.upper() for t in item[:3]] in (['SUPPLEMENTAL','LOG','GROUP'],['SUPPLEMENTAL','LOG','DATA']):
            names=[]
            if item[2].upper=='GROUP':
                group=enclosed(item,4)
                if group is None:raise ValueError('SUPPLEMENTAL_LOG_DEFINITION_UNVERIFIED')
                names=[identifier(part[0])[0] for part in top_level_items(group[0]) or ()]
            logging.append({'definition':source_span(text,item),'columns':names})
        else:columns.append(source_span(text,item))
    if not logging:return text,()
    projection_text=text[:tokens[opening].end]+', '.join(columns)+text[tokens[body[1]-1].start:]
    return projection_text,tuple(logging)
