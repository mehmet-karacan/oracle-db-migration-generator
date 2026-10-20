"""Narrow Oracle header compatibility for the pinned generated grammar.

Oracle 19c supports [NON]EDITIONABLE before PROCEDURE/TRIGGER. The pinned
grammar omits that production. Mask just this recognized header token with
equal-length whitespace for parsing, retaining every source/body offset.
https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/CREATE-PROCEDURE-statement.html
https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/CREATE-TRIGGER-statement.html
"""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed


def storage_masks(text):
    """Return (start, end, STORAGE start) candidates, pending AST scope proof."""
    tokens=code_tokens(text) or ()
    masks=[]
    for index,token in enumerate(tokens[:-1]):
        if token.upper!='STORAGE' or tokens[index+1].text!='(': continue
        group=enclosed(tokens,index+1)
        if not group: continue
        values=group[0]
        positions=[];depth=0
        for position,value in enumerate(values):
            if value.text=='(': depth+=1
            elif value.text==')': depth-=1
            elif depth==0 and value.upper=='MAXSIZE': positions.append(position)
        if len(positions)!=1: continue
        position=positions[0]
        if position+1>=len(values): continue
        value=values[position];size=values[position+1];end=size.end
        if size.upper=='UNLIMITED': pass
        elif size.text.isdecimal() and int(size.text)>0:
            if position+2<len(values) and values[position+2].upper in {'K','M','G','T','P','E'}:
                end=values[position+2].end
        else: continue
        masks.append((value.start,end,token.start))
    return masks


def grammar_text(text):
    tokens=code_tokens(text)
    if not tokens or tokens[0].upper!='CREATE':
        return text
    at=3 if len(tokens)>2 and [t.upper for t in tokens[1:3]]==['OR','REPLACE'] else 1
    masks=[]
    if (at+1<len(tokens) and tokens[at].upper in {'EDITIONABLE','NONEDITIONABLE'}
            and tokens[at+1].upper in {'PROCEDURE','TRIGGER'}):
        modifier=tokens[at]
        masks.append((modifier.start,modifier.end))
    kind_at=at
    while kind_at<len(tokens) and tokens[kind_at].upper in {'EDITIONABLE','NONEDITIONABLE','GLOBAL','TEMPORARY','UNIQUE','BITMAP'}:
        kind_at+=1
    if kind_at<len(tokens) and tokens[kind_at].upper in {'TABLE','INDEX'}:
        # The pinned storage_clause predates Oracle's MAXSIZE attribute.
        # Validate its narrow size syntax independently; all other STORAGE
        # syntax still goes through the complete grammar. Projection/emission
        # retain the original clause, including MAXSIZE.
        # https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/storage_clause.html
        masks.extend((start,end) for start,end,_ in storage_masks(text))
    for start,end in sorted(set(masks),reverse=True):
        text=text[:start]+''.join(char if char in '\r\n' else ' ' for char in text[start:end])+text[end:]
    return text


def storage_scope_valid(original,statements):
    """A masked STORAGE function argument must never become valid SQL.

    Equal-length masks retain token offsets, allowing the complete grammar's
    actual Storage_clauseContext to prove every compatibility clause's scope.
    """
    candidates=storage_masks(original)
    if not candidates: return True
    scopes={}
    pending=list(statements)
    while pending:
        node=pending.pop()
        if type(node).__name__=='Storage_clauseContext':
            scopes[node.start.start]=node.stop.stop+1
        pending.extend(getattr(node,'children',None) or ())
    return all(storage in scopes and end<=scopes[storage] for _,end,storage in candidates)


def scanner_text(text):
    tokens=code_tokens(text) or ()
    # Scanner identity extraction predates GLOBAL TEMPORARY TABLE. Parsing
    # still receives the complete original clause and validates its semantics.
    if len(tokens)>3 and [token.upper for token in tokens[:4]]==['CREATE','GLOBAL','TEMPORARY','TABLE']:
        start,end=tokens[1].start,tokens[2].end
        return text[:start]+''.join('\n' if char=='\n' else '\r' if char=='\r' else ' ' for char in text[start:end])+text[end:]
    return text
