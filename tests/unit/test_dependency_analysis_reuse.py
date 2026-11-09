"""Schema Compare bağımlılık çözümlemesinde aynı lexer işinin tekrarını denetler.

Kısa adların sonucu değişmez. Çağrı adı önbelleği uzun SQL parçalarını tutmaz.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import pytest

from oracle_db_migration_generator.parsing import dependencies
from tests.unit.test_package_sha_reuse import object_for


def test_repeated_callee_name_is_lexed_once(monkeypatch):
    original=dependencies.code_tokens;calls=[]
    def tracked(text):
        calls.append(text)
        return original(text)
    monkeypatch.setattr(dependencies,'code_tokens',tracked)
    text='APP.CACHE_REPEAT_REGRESSION(1)'
    assert dependencies._callee_parts(text)==('APP','CACHE_REPEAT_REGRESSION')
    assert dependencies._callee_parts(text)==('APP','CACHE_REPEAT_REGRESSION')
    assert calls==[text]


def test_long_callee_input_is_not_retained(monkeypatch):
    original=dependencies.code_tokens;calls=[]
    def tracked(text):
        calls.append(len(text))
        return original(text)
    monkeypatch.setattr(dependencies,'code_tokens',tracked)
    text='APP.LONG_CALLEE('+"'"+('X'*2200)+"')"
    assert dependencies._callee_parts(text)==('APP','LONG_CALLEE')
    assert dependencies._callee_parts(text)==('APP','LONG_CALLEE')
    assert calls==[len(text),len(text)]


@pytest.mark.parametrize('body',[
    'BEGIN EXECUTE IMMEDIATE X; END;',
    'BEGIN OPEN C FOR X; END;',
    'BEGIN OPEN C FOR SELECT ID FROM APP.T; END;',
    'BEGIN DBMS_SQL.PARSE(C,X,1); END;',
    "BEGIN P('EXECUTE IMMEDIATE'); /* OPEN C FOR X */ END;",
])
def test_dynamic_sql_uses_existing_tokens_without_changing_result(monkeypatch,body):
    obj=object_for(('CREATE PACKAGE BODY APP.P AS PROCEDURE R IS '+body+' END P;').encode())
    expected=dependencies.has_dynamic_sql(obj)
    tokens=dependencies.code_tokens(obj.raw_ddl.decode())
    monkeypatch.setattr(dependencies,'code_tokens',lambda *a:pytest.fail('same routine was lexed again'))
    assert dependencies.has_dynamic_sql(obj,tokens=tokens)==expected
