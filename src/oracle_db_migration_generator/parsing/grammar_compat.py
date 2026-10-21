"""Narrow Oracle header compatibility for the pinned generated grammar.

Oracle 19c supports [NON]EDITIONABLE before PROCEDURE/TRIGGER. The pinned
grammar omits that production. Mask just this recognized header token with
equal-length whitespace for parsing, retaining every source/body offset.
https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/CREATE-PROCEDURE-statement.html
https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/CREATE-TRIGGER-statement.html
"""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed
from antlr4 import CommonTokenStream
from antlr4.atn.ATNDeserializer import ATNDeserializer
from antlr4.atn.Transition import RuleTransition
from antlr4.dfa.DFA import DFA
from antlr4.PredictionContext import PredictionContextCache

from .._vendor.analyzer_core.oracle.generated.PlSqlParser import PlSqlParser, serializedATN


def _in_select_atn():
    """Clone the pinned ATN and extend only IN's existing query alternative.

    The generated in_elements calls subquery, whose rule excludes WITH. Its
    enclosing adaptive predictions therefore reject CTEs before an overridden
    method can run. select_only_statement already validates WITH + subquery;
    point this one rule call at that production in an independent ATN. Neither
    the generated ATN nor its shared prediction caches are modified.
    """
    atn = ATNDeserializer().deserialize(serializedATN())
    matches = []
    for state in atn.states:
        if state is None or state.ruleIndex != PlSqlParser.RULE_in_elements:
            continue
        for index, transition in enumerate(state.transitions):
            if isinstance(transition, RuleTransition) and transition.ruleIndex == PlSqlParser.RULE_subquery:
                matches.append((state, index, transition))
    if len(matches) != 1:
        raise RuntimeError('PINNED_IN_SUBQUERY_RULE_DRIFT')
    state, index, transition = matches[0]
    state.transitions[index] = RuleTransition(
        atn.ruleToStartState[PlSqlParser.RULE_select_only_statement],
        PlSqlParser.RULE_select_only_statement, transition.precedence, transition.followState,
    )
    return atn


class CompatiblePlSqlParser(PlSqlParser):
    """Full pinned parser with Oracle CTE support in IN query expressions.

    No token, SQL text, source position or EOF handling is changed. The
    adapter uses the generated WITH and SELECT productions, including their
    normal error reporting, rather than accepting an opaque query fragment.
    """
    atn = _in_select_atn()
    decisionsToDFA = [DFA(state, index) for index, state in enumerate(atn.decisionToState)]
    sharedContextCache = PredictionContextCache()

    def subquery(self):
        if isinstance(self._ctx, self.In_elementsContext):
            return self.select_only_statement()
        return super().subquery()


def grammar_token_stream(lexer,object_type):
    """Keep TRG's identifier semantics inside stored Oracle program units.

    The pinned lexer treats TRG as a SQL*Plus filename extension everywhere.
    It is not an Oracle reserved word. Change token type only in stored units;
    preserve text, positions, literals and SQL*Plus tokenization outside them.
    """
    stream=CommonTokenStream(lexer)
    if object_type in {'PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','TRIGGER'}:
        stream.fill()
        for token in stream.tokens:
            if token.type==lexer.FILE_EXT and token.text.upper()=='TRG':
                token.type=lexer.REGULAR_ID
    return stream


def view_query_masks(tokens,at):
    """Unwrap only the entire ordinary VIEW query, retaining source offsets.

    Oracle permits parentheses around a compound subquery followed by its
    ORDER BY. The pinned CREATE VIEW grammar/extractor mishandles that outer
    pair. Inner subqueries and grouped set-operator branches remain untouched;
    all query tokens must still pass the complete grammar.
    https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/SELECT.html
    """
    while at<len(tokens) and tokens[at].upper in {'FORCE','NOFORCE','EDITIONABLE','NONEDITIONABLE'}:
        at+=1
    if at>=len(tokens) or tokens[at].upper!='VIEW':return []
    depth=0;query_at=None
    for index in range(at+1,len(tokens)):
        token=tokens[index]
        if token.text=='(':depth+=1
        elif token.text==')':depth-=1
        elif depth==0 and token.upper=='AS':
            query_at=index+1;break
    if query_at is None or query_at>=len(tokens) or tokens[query_at].text!='(':return []
    group=enclosed(tokens,query_at)
    if not group or not group[0] or group[0][0].upper!='SELECT':return []
    suffix=list(tokens[group[1]:])
    if suffix and suffix[-1].text=='/':suffix.pop()
    if suffix and suffix[-1].text==';':suffix.pop()
    if suffix and [token.upper for token in suffix[:2]]!=['ORDER','BY']:return []
    opening,closing=tokens[query_at],tokens[group[1]-1]
    return [(opening.start,opening.end),(closing.start,closing.end)]


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
    masks=view_query_masks(tokens,at)
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
