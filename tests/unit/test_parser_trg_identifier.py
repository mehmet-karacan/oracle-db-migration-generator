"""TRG is a legal Oracle SQL alias, not a filename suffix in stored units."""
import pytest

from oracle_db_migration_generator.model.identity import Identifier,ObjectIdentity
from oracle_db_migration_generator.parsing.adapter import parse_ddl

HINT=ObjectIdentity('demo-source',Identifier.parse('APP'),'PACKAGE_BODY',Identifier.parse('P'))


@pytest.mark.parametrize('alias',['trg','TRG','Trg'])
def test_merge_trg_alias_parses_and_preserves_real_routine_facts(alias):
    raw=(f'CREATE OR REPLACE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN '
         f'MERGE INTO APP.T {alias} USING (SELECT ID FROM APP.U) src '
         f'ON ({alias}.ID=src.ID) WHEN MATCHED THEN UPDATE SET {alias}.A=src.ID; '
         "DBMS_OUTPUT.PUT_LINE('trg'); END; END P;\n/").encode()
    parsed=parse_ddl(raw,HINT)
    assert parsed.coverage=='COMPLETE'
    obj=parsed.objects[0]
    assert obj.parse_ok and not obj.diagnostics
    assert obj.raw_ddl==raw.removesuffix(b'\n/')
    assert obj.raw_ddl==raw[obj.start_byte:obj.end_byte]
    routine=obj.projection.properties['routines'][0]
    assert routine.name=='R'
    assert any(f'MERGE INTO APP.T {alias}' in statement for statement in routine.sql_statements)
    assert "DBMS_OUTPUT.PUT_LINE('trg')" in routine.source


@pytest.mark.parametrize('statement',[
    'MERGE INTO APP.T trg USING (SELECT ID FROM APP.U) src WHEN MATCHED THEN UPDATE SET trg.A=src.ID;',
    'MERGE INTO APP.T trg USING (SELECT ID FROM APP.U) src ON (trg.ID=) WHEN MATCHED THEN UPDATE SET trg.A=src.ID;',
])
def test_trg_token_compatibility_keeps_full_grammar_rejection(statement):
    raw=('CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN '+statement+' END; END P;\n/').encode()
    parsed=parse_ddl(raw,HINT)
    assert parsed.coverage!='COMPLETE'
    assert not any(obj.parse_ok and not obj.diagnostics for obj in parsed.objects)


def test_trg_token_correction_preserves_offsets_and_stays_inside_stored_units():
    from antlr4 import InputStream
    from oracle_db_migration_generator._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
    from oracle_db_migration_generator.parsing.grammar_compat import grammar_token_stream
    text="trg 'trg' -- trg\n TRG"
    for kind,expected in [('PACKAGE_BODY',PlSqlLexer.REGULAR_ID),(None,PlSqlLexer.FILE_EXT)]:
        stream=grammar_token_stream(PlSqlLexer(InputStream(text)),kind);stream.fill()
        aliases=[token for token in stream.tokens if token.text in {'trg','TRG'} and token.channel==0]
        assert len(aliases)==2 and all(token.type==expected for token in aliases)
        assert all(text[token.start:token.stop+1]==token.text for token in aliases)
        assert any(token.text=="'trg'" for token in stream.tokens)
