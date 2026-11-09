"""Schema Compare hedef çözümlemesinde aynı SQL'in tekrar okunmasını denetler.

Literal, hint ve geçersiz karakter kontrolleri gerçek lexer ile çalışır.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from dataclasses import replace

import pytest

from oracle_db_migration_generator.oracle import ddl_model
from oracle_db_migration_generator.parsing.canonicalize import canonical_sql
from oracle_db_migration_generator._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
from tests.unit.test_package_sha_reuse import SQL, object_for


def test_checked_package_uses_one_lexer_pass(monkeypatch):
    text=SQL.decode()+'\n/\n'
    expected=canonical_sql(text)
    calls=[]
    original=PlSqlLexer.__init__
    def tracked(self,*args,**kwargs):
        calls.append(1)
        original(self,*args,**kwargs)
    monkeypatch.setattr(PlSqlLexer,'__init__',tracked)
    # Büyük metin kısa SQL önbelleğini kullanmaz.
    text=text.replace('NULL;', 'NULL; '+(' ' * 2100))
    actual,protected=ddl_model._checked_canonical(text)
    assert actual==expected and protected==()
    assert len(calls)==1


@pytest.mark.parametrize('text',[
    SQL.decode(), '\ufeff'+SQL.decode()+'\n /\n',
    'create or replace view "APP"."V" as select "DATE", "X" from "APP"."T";',
    "CREATE VIEW APP.V AS SELECT q'[A\n/\nB]' X FROM DUAL;\n/\n",
    "CREATE VIEW APP.V AS SELECT 'A\n/\nB' X FROM DUAL;\n/\n",
    "CREATE VIEW APP.V AS SELECT /*+ A\n/\nB */ 1 X FROM DUAL;\n/\n",
    "CREATE VIEW APP.V AS SELECT --+ A\n 1 X FROM DUAL;\n/\n",
    "CREATE VIEW APP.V AS SELECT N'Mixed Case' X FROM DUAL;\n/\n",
])
def test_checked_canonical_matches_existing_format(text):
    assert ddl_model._checked_canonical(text)[0]==canonical_sql(text)


def test_effective_definition_does_not_relex_target(monkeypatch):
    raw=b'CREATE TYPE APP.P AS OBJECT (X VARCHAR2(100)); ALTER TYPE APP.P MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;'
    obj=object_for(raw,kind='TYPE_SPEC')
    baseline=ddl_model.project_target_object(obj)
    real=ddl_model.parse_ddl
    def parsed(*args,**kwargs):
        result=real(*args,**kwargs)
        assert '_generator_effective_definition' in result.objects[0].projection.properties
        return result
    monkeypatch.setattr(ddl_model,'parse_ddl',parsed)
    monkeypatch.setattr(ddl_model,'canonical_sql',lambda *a:pytest.fail('verified effective definition was re-lexed'))
    actual=ddl_model.project_target_object(obj)
    assert actual[0].to_dict()==baseline[0].to_dict() and actual[1]==baseline[1]


def test_capture_extracts_source_references_only_once(monkeypatch):
    from tests.factories import source
    from tests.unit.test_collector import inputs,FakeConnection
    from oracle_db_migration_generator.config.credentials import Credentials
    from oracle_db_migration_generator.oracle.collector import collect_target
    from oracle_db_migration_generator.parsing import dependencies
    selected=source('CREATE VIEW APP.V AS SELECT X FROM OTHER.T;')
    calls=[];original=dependencies.references
    def tracked(obj):
        calls.append(obj.object_key)
        return original(obj)
    monkeypatch.setattr(dependencies,'references',tracked)
    monkeypatch.setattr('oracle_db_migration_generator.oracle.reference_metadata.references',tracked)
    target,profile=inputs()
    result=collect_target(target,lambda _:Credentials('APP','secret'),profile,
                          connect=lambda *_:FakeConnection(),source=selected)
    assert result.snapshot is not None
    assert calls==[obj.object_key for obj in selected.objects]
