"""Schema Compare iç içe fonksiyonları tam grammar ile hızlı doğrular.

Referans parser ağacı, geçersiz SQL ve fonksiyon olmayan adlar denetlenir.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import pytest
from antlr4 import CommonTokenStream,InputStream
from antlr4.atn.ParserATNSimulator import ParserATNSimulator
from antlr4.error.ErrorListener import ErrorListener

from oracle_db_migration_generator.parsing.grammar_compat import CompatiblePlSqlParser
from oracle_db_migration_generator._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer


class Errors(ErrorListener):
    """Testte lexer ve parser hata bildirimlerini birlikte toplar.

    Author: Mehmet KARACAN
    Date: 2026-11-09
    """
    def __init__(self):self.errors=[]
    def syntaxError(self,*args):self.errors.append(True)


def tree(sql,*,reference=False):
    lexer=PlSqlLexer(InputStream(sql));errors=Errors()
    lexer.removeErrorListeners();lexer.addErrorListener(errors)
    parser=CompatiblePlSqlParser(CommonTokenStream(lexer))
    if reference:
        parser._interp=ParserATNSimulator(parser,parser.atn,parser.decisionsToDFA,parser.sharedContextCache)
    parser.removeErrorListeners();parser.addErrorListener(errors)
    result=parser.sql_script()
    return result.toStringTree(recog=parser),errors.errors


def test_nested_numeric_functions_do_not_expand_full_expression_lookahead(monkeypatch):
    sql='CREATE VIEW APP.V AS SELECT TO_CHAR(NVL(MIN(ROUND(X,2)),0)) X FROM APP.T;'
    expected=tree(sql,reference=True)
    original=ParserATNSimulator.adaptivePredict
    def guarded(self,input,decision,context):
        if decision==2575 and input.LT(1).text.upper()=='TO_CHAR':
            pytest.fail('nested built-in expression expanded instead of using its grammar branch')
        return original(self,input,decision,context)
    monkeypatch.setattr(ParserATNSimulator,'adaptivePredict',guarded)
    actual=tree(sql)
    assert not expected[1] and actual==expected


@pytest.mark.parametrize('expression',[
    'TO_CHAR(X)','TO_CHAR(NVL(X,0))','TO_CHAR(NVL(X,0)+1)',
    "TO_DATE(NVL(X,'20260101'),'YYYYMMDD')",
    'MIN(ROUND(X,2)) OVER (PARTITION BY Y)',
    'SUM(X) KEEP (DENSE_RANK FIRST ORDER BY Y)',
    'COUNT(*)','COUNT(DISTINCT X)','LEAST(X,Y)',
    '"TO_CHAR"(X)','APP.TO_CHAR(X)','TO_CHAR.X',
    'TRIM(LEADING X FROM Y)','SUBSTR(X,1,2)','DECODE(X,1,Y,0)',
    'NVL(X)','ROUND(X,)','TO_CHAR(NVL(X,0) garbage)',
])
def test_function_tree_and_errors_match_reference(expression):
    sql=f'CREATE VIEW APP.V AS SELECT {expression} RESULT FROM APP.T;'
    expected,errors=tree(sql,reference=True)
    actual,actual_errors=tree(sql)
    if errors:
        assert actual_errors
    else:
        assert not actual_errors and actual==expected


def test_legacy_outer_join_is_not_consumed_as_function_arguments():
    sql=('CREATE VIEW APP.V AS SELECT A.ID FROM APP.A A, APP.B B '
         'WHERE A.ID = B.ID(+) AND A.X = B.X(+);')
    expected,errors=tree(sql,reference=True)
    actual,actual_errors=tree(sql)
    assert not errors
    assert not actual_errors and actual==expected
