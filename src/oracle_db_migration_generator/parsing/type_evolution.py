"""Sequential, closed TYPE object attribute evolution; never execute SQL."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed,top_level_items,source_span,identifier
from .statements import qualified_parts
from .canonicalize import canonical_sql


def effective_type_definition(source, validate, *, include_create=False):
    """Return final scalar object CREATE for a verified MODIFY ATTRIBUTE chain.

    The pinned ALTER TYPE grammar does not have MODIFY ATTRIBUTE. Recognize
    only that exact production here, requiring every intermediate final CREATE
    to pass the complete object-type grammar. Other ALTER productions remain
    unsupported; foreign identities and missing attributes cannot be hidden.
    """
    tokens=code_tokens(source)
    if not tokens:return None
    object_at=next((i for i,t in enumerate(tokens) if t.upper=='OBJECT'),None)
    if object_at is None or object_at+1>=len(tokens) or tokens[object_at+1].text!='(':return None
    group=enclosed(tokens,object_at+1)
    if not group:return None
    tail=group[1]
    if not any(t.upper=='ALTER' for t in tokens[tail:]):return None
    type_at=next((i for i,t in enumerate(tokens[:object_at]) if t.upper=='TYPE'),None)
    if type_at is None:raise ValueError('TYPE_EVOLUTION_CREATE_UNVERIFIED')
    names_end=next((i for i in range(type_at+1,object_at) if tokens[i].upper in {'AS','IS'}),None)
    if names_end is None:raise ValueError('TYPE_EVOLUTION_CREATE_UNVERIFIED')
    name=qualified_parts(tokens[type_at+1:names_end])
    items=top_level_items(group[0])
    if not items:raise ValueError('TYPE_EVOLUTION_ATTRIBUTES_UNVERIFIED')
    attributes=[];seen=set();changes_by_name={}
    for item in items:
        if len(item)<2:raise ValueError('TYPE_EVOLUTION_ATTRIBUTE_UNVERIFIED')
        key=identifier(item[0])[0]
        if key in seen:raise ValueError('TYPE_EVOLUTION_DUPLICATE_ATTRIBUTE')
        seen.add(key);attributes.append((key,item[1].start,item[-1].end))
    base=source[:tokens[tail-1].end]
    def final_text():
        result=base
        for key,start,end in reversed(attributes):
            if key in changes_by_name:result=result[:start]+changes_by_name[key]+result[end:]
        return result
    if not validate(final_text()):raise ValueError('TYPE_EVOLUTION_CREATE_UNVERIFIED')
    while tail<len(tokens):
        if tokens[tail].text in {';','/'}:
            if tokens[tail].text=='/':
                before=source.rfind('\n',0,tokens[tail].start)+1
                after=source.find('\n',tokens[tail].end)
                after=len(source) if after<0 else after
                if source[before:tokens[tail].start].strip() or source[tokens[tail].end:after].strip():
                    raise ValueError('TYPE_EVOLUTION_RUNNER_DELIMITER_UNVERIFIED')
            tail+=1
            if tail==len(tokens):break
            continue
        if [t.upper for t in tokens[tail:tail+2]]!=['ALTER','TYPE']:
            raise ValueError('TYPE_EVOLUTION_TRAILING_INPUT')
        end=next((i for i in range(tail+2,len(tokens)) if tokens[i].upper=='MODIFY'),None)
        if end is None or qualified_parts(tokens[tail+2:end])!=name:
            raise ValueError('TYPE_EVOLUTION_FOREIGN_IDENTITY')
        if [t.upper for t in tokens[end:end+2]]!=['MODIFY','ATTRIBUTE']:
            raise ValueError('TYPE_EVOLUTION_UNSUPPORTED_ALTER')
        changes=enclosed(tokens,end+2)
        if not changes:raise ValueError('TYPE_EVOLUTION_MODIFY_UNVERIFIED')
        updates=top_level_items(changes[0])
        changed=set()
        for item in updates or ():
            if len(item)<2:raise ValueError('TYPE_EVOLUTION_MODIFY_UNVERIFIED')
            key=identifier(item[0])[0]
            if key not in seen or key in changed:raise ValueError('TYPE_EVOLUTION_UNKNOWN_ATTRIBUTE')
            changed.add(key)
            changes_by_name[key]=source_span(source,item[1:])
        if not changed or not validate(final_text()):raise ValueError('TYPE_EVOLUTION_MODIFY_UNVERIFIED')
        tail=changes[1]
        if tail<len(tokens) and tokens[tail].upper=='CASCADE':tail+=1
    final=final_text()
    # VARCHAR is Oracle's documented synonym, normalized only for equality;
    # emitted SQL keeps the user's actual datatype and all unrelated bytes.
    semantic=final
    for token in reversed(code_tokens(final) or ()):
        if token.upper=='VARCHAR':semantic=semantic[:token.start]+'VARCHAR2'+semantic[token.end:]
    result=canonical_sql(semantic)
    return (result,final) if include_create else result
