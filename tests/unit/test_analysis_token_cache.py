"""Schema Compare aynı SQL metninin bağımlılık ve başlıkta tekrar okunmasını denetler.

Lexer hataları saklanmaz. Saf token önbelleğinin kayıt ve boyut sınırları ölçülür.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import pytest
from dataclasses import replace

from oracle_db_migration_generator.parsing.dependencies import references
from oracle_db_migration_generator.planning.object_rules import replace_header
from oracle_db_migration_generator._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
from tests.unit.test_package_sha_reuse import SQL,object_for


def test_dependency_and_header_share_one_exact_sql_lexer_pass(monkeypatch):
    raw=SQL.replace(b'BEGIN ',b'BEGIN /*'+b'X'*2200+b'*/ ')
    original=PlSqlLexer.__init__;calls=[]
    def tracked(self,*a,**k):
        calls.append(1);original(self,*a,**k)
    monkeypatch.setattr(PlSqlLexer,'__init__',tracked)
    assert references(object_for(raw))==()
    assert replace_header(raw)==raw
    assert len(calls)==1


def test_analysis_cache_keeps_original_offsets_and_tokens():
    from oracle_db_migration_generator.parsing.token_cache import analysis_tokens,clear_cache
    from oracle_db_migration_generator._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
    clear_cache()
    text='/*'+('X'*2200)+'*/ CREATE VIEW "APP"."V" AS SELECT q\'[A "B";]\' X FROM "APP"."T";'
    expected=code_tokens(text)
    assert analysis_tokens(text)==expected
    assert analysis_tokens(text)==expected


def test_analysis_cache_enforces_entry_byte_and_token_limits(monkeypatch):
    from oracle_db_migration_generator.parsing import token_cache
    token_cache.clear_cache()
    monkeypatch.setattr(token_cache,'MIN_TEXT_BYTES',0)
    monkeypatch.setattr(token_cache,'MAX_ENTRIES',2)
    monkeypatch.setattr(token_cache,'MAX_TOTAL_BYTES',160)
    monkeypatch.setattr(token_cache,'MAX_TOTAL_TOKENS',15)
    for index in range(20):
        assert token_cache.analysis_tokens(f'SELECT C{index} FROM T /*'+('X'*70)+'*/') is not None
        stats=token_cache.cache_stats()
        assert 0<stats['entries']<=2 and stats['bytes']<=160 and stats['tokens']<=15
    token_cache.clear_cache()


def test_lexer_errors_are_not_cached(monkeypatch):
    from oracle_db_migration_generator.parsing import token_cache
    token_cache.clear_cache();monkeypatch.setattr(token_cache,'MIN_TEXT_BYTES',0)
    assert token_cache.analysis_tokens('SELECT '+chr(0)) is None
    assert token_cache.cache_stats()['entries']==0
    assert token_cache.cache_stats()['small_entries']==0


def test_shared_tokens_do_not_share_project_or_default_schema():
    from oracle_db_migration_generator.model.identity import Identifier
    raw=('CREATE VIEW V AS SELECT ID FROM T /*'+('X'*2200)+'*/;').encode()
    first=object_for(raw,kind='VIEW')
    second=replace(first,identity=replace(first.identity,profile_id='another-project',owner=Identifier.parse('OTHER')))
    desired=references(first);other=references(second)
    assert {(r.owner,r.name,r.role) for r in desired}=={('APP','T','QUERY_RELATION')}
    assert {(r.owner,r.name,r.role) for r in other}=={('OTHER','T','QUERY_RELATION')}
    assert first.object_key!=second.object_key
