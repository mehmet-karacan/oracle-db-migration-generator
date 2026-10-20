from dataclasses import replace
from pathlib import Path

from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.parsing.adapter import parse_ddl, parse_source
from oracle_db_migration_generator.parsing.canonicalize import canonical_sql
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision

ROOT = Path(__file__).resolve().parents[2]
HINT = ObjectIdentity('demo-source', Identifier.parse('APP'), 'TABLE', Identifier.parse('DEMO'))


def test_utf8_bom_crlf_quoted_names_and_qquote():
    raw = '\ufeffCREATE TABLE "APP"."Türkçe,Tablo" ("A,B" VARCHAR2(80 CHAR) DEFAULT q\'[a; b]\');\r\n'.encode()
    result = parse_ddl(raw, HINT)
    assert result.coverage == 'COMPLETE'
    item = result.objects[0]
    assert item.identity.name.effective_name == 'Türkçe,Tablo'
    assert item.raw_ddl.startswith(b'CREATE TABLE')
    assert raw[item.start_byte:item.end_byte] == item.raw_ddl
    assert 'A,B' in item.projection.properties['columns']


def test_comment_semicolon_does_not_split_package():
    raw = b"CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\nCREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/\n"
    result = parse_ddl(raw, HINT)
    assert result.coverage == 'COMPLETE'
    assert [obj.identity.object_type for obj in result.objects] == ['PACKAGE_SPEC', 'PACKAGE_BODY']
    assert b'BEGIN NULL; END;' in result.objects[1].raw_ddl


def test_unknown_syntax_blocks_only_affected_object():
    result = parse_ddl(b'CREATE TABLE APP.BAD (ID WHAT EVER BAD);\nCREATE TABLE APP.GOOD (ID NUMBER);', HINT)
    by_name = {obj.identity.name.effective_name: obj for obj in result.objects}
    assert by_name['BAD'].diagnostics
    assert by_name['GOOD'].parse_ok
    assert result.coverage == 'PARTIAL'


def test_sidecar_grant_without_create_is_collected():
    result = parse_ddl(b"GRANT SELECT ON APP.DEMO TO READER; COMMENT ON COLUMN APP.DEMO.ID IS 'a; b';", HINT)
    assert result.coverage == 'COMPLETE'
    assert len(result.sidecars) == 2
    assert not result.objects


def test_literal_whitespace_case_is_not_normalized_away():
    assert canonical_sql("SELECT 'a  B' FROM dual") != canonical_sql("select 'a B' from dual")
    assert canonical_sql('select "Foo" from dual') != canonical_sql('select FOO from dual')
    assert canonical_sql('select "FOO" from dual') == canonical_sql('SELECT foo FROM DUAL')
    assert canonical_sql('select /*+ FULL(t) */ x from t') != canonical_sql('select x from t')
    assert canonical_sql('select "NULL" from dual') != canonical_sql('select NULL from dual')


def test_parser_timeout_is_not_parse_success(monkeypatch):
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.request_parse', lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()))
    result = parse_ddl(b'CREATE TABLE APP.DEMO (ID NUMBER);', HINT)
    assert result.coverage == 'UNAVAILABLE'
    assert 'PARSER_TIMEOUT' in result.diagnostics
    assert not any(obj.parse_ok for obj in result.objects)


def test_duplicate_conflicting_definitions_block_and_equal_definitions_keep_evidence():
    import hashlib
    profile = load_source_profile(ROOT / 'examples/source-profile.example.json')
    def artifact(path, raw):
        return SourceArtifact(path, 'APP', 'DDL', 'TABLE', raw, hashlib.sha256(raw).hexdigest())
    first = artifact('app/tables/DEMO/ddl.sql', b'CREATE TABLE APP.DEMO (ID NUMBER);')
    same = artifact('app/tables/DEMO/copy.sql', first.raw)
    snapshot = parse_source(SourceInput(SourceRevision('a' * 40, None), (first, same), 'b' * 64), profile)
    assert len(snapshot.objects) == 1 and len(snapshot.objects[0].evidence_ids) == 2
    changed = artifact('app/tables/DEMO/other.sql', b'CREATE TABLE APP.DEMO (ID NUMBER, X DATE);')
    snapshot = parse_source(SourceInput(SourceRevision('a' * 40, None), (first, changed), 'b' * 64), profile)
    assert snapshot.objects[0].coverage.ddl == 'PARTIAL'
    assert 'DUPLICATE_DEFINITION_CONFLICT' in snapshot.objects[0].coverage.diagnostics


def test_trailing_destructive_statement_cannot_enter_create_payload():
    result = parse_ddl(b'CREATE TABLE APP.DEMO (ID NUMBER); DROP TABLE APP.OTHER;', HINT)
    assert result.coverage == 'PARTIAL'
    assert b'DROP' not in result.objects[0].raw_ddl
    assert 'UNSUPPORTED_STATEMENT' in result.diagnostics


def test_source_sidecars_become_independent_evidenced_objects():
    import hashlib
    profile = load_source_profile(ROOT / 'examples/source-profile.example.json')
    def artifact(path, kind, raw):
        return SourceArtifact(path, 'APP', kind, 'TABLE', raw, hashlib.sha256(raw).hexdigest())
    items = (artifact('app/tables/DEMO/ddl.sql','DDL', b'CREATE TABLE APP.DEMO (ID NUMBER);'),
             artifact('app/tables/DEMO/comments.sql','COMMENT', b"COMMENT ON COLUMN APP.DEMO.ID IS q'[a; b]';"),
             artifact('app/tables/DEMO/grants.sql','GRANT', b'GRANT SELECT, UPDATE ON APP.DEMO TO READER, OTHER_READER;'))
    snapshot = parse_source(SourceInput(SourceRevision('a'*40,None),items,'b'*64), profile)
    comments = [obj for obj in snapshot.objects if obj.identity.object_type == 'COMMENT']
    grants = [obj for obj in snapshot.objects if obj.identity.object_type == 'GRANT']
    assert len(comments) == 1 and len(grants) == 4
    assert comments[0].properties['text'].value == 'a; b'
    assert all(obj.identity.parent_key for obj in comments + grants)
    assert all(len(obj.evidence_ids) == 1 for obj in comments + grants)
    assert all(not (b'READER,' in obj.raw_ddl) for obj in grants)


def test_context_alter_matches_effective_quoted_names_and_resets_numeric_precision():
    import hashlib
    profile = load_source_profile(ROOT/'examples/source-profile.example.json')
    raw = b'CREATE TABLE "APP"."DEMO" ("ID" NUMBER(10,2)); ALTER TABLE APP.DEMO MODIFY (ID NUMBER); ALTER TABLE APP.DEMO ADD (TITLE VARCHAR2(80 CHAR));'
    artifact = SourceArtifact('app/tables/DEMO/ddl.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    result = parse_source(SourceInput(SourceRevision('a'*40,None),(artifact,),'b'*64),profile)
    obj = result.objects[0]
    assert obj.coverage.ddl=='COMPLETE'
    columns = obj.projection.properties['columns']
    assert set(columns)=={'ID','TITLE'}
    assert columns['ID']['precision'] is None and columns['ID']['scale'] is None


def test_sqlplus_command_is_never_unaccounted_scope():
    from tests.factories import source
    snapshot=source('CREATE TABLE APP.T (ID NUMBER);\nSET DEFINE OFF\n')
    assert snapshot.completeness.ddl!='COMPLETE'


def test_editionable_procedure_and_trigger_keep_original_spans_and_literals():
    statements=(
        'CREATE OR REPLACE /* header */ NONEDITIONABLE PROCEDURE "APP"."P" AS BEGIN NULL; END;\n/',
        'CREATE OR REPLACE EDITIONABLE TRIGGER APP.TR BEFORE INSERT ON APP.T BEGIN :NEW.X := \'EDITIONABLE PROCEDURE\'; END;\n/\nALTER TRIGGER APP.TR ENABLE;',
    )
    for text in statements:
        raw=text.encode()
        parsed=parse_ddl(raw,HINT)
        assert parsed.coverage=='COMPLETE'
        obj=parsed.objects[0]
        assert obj.parse_ok and not obj.diagnostics
        assert raw[obj.start_byte:obj.end_byte]==obj.raw_ddl
        assert b'EDITIONABLE' in obj.raw_ddl
    invalid=parse_ddl(b'CREATE EDITIONABLE PROCEDURE APP.P AS BEGIN WHAT EVER BAD; END;\n/',HINT)
    assert invalid.coverage!='COMPLETE'


def test_anonymous_table_constraints_are_captured_instead_of_discarded():
    raw=b'CREATE TABLE APP.DEMO (ID NUMBER, CODE VARCHAR2(20 CHAR), PRIMARY KEY(ID) USING INDEX ENABLE, UNIQUE(CODE), CHECK(ID > 0));'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE'
    constraints=result.objects[0].projection.properties['constraints']
    assert len(constraints)==3
    assert any(value.startswith('PRIMARY KEY') for value in constraints.values())
    assert any(value.startswith('CHECK') for value in constraints.values())
    formatted=parse_ddl(raw.replace(b'PRIMARY KEY(ID)',b'primary key ("ID")'),HINT)
    assert set(formatted.objects[0].projection.properties['constraints'])==set(constraints)


def test_index_unusable_export_context_is_a_known_state():
    from tests.factories import source
    snapshot=source('CREATE TABLE APP.T(ID NUMBER); CREATE INDEX APP.I ON APP.T(ID); ALTER INDEX APP.I UNUSABLE;')
    assert snapshot.completeness.ddl=='COMPLETE'
    index=next(obj for obj in snapshot.objects if obj.identity.object_type=='INDEX')
    assert index.projection.properties['availability']=='UNUSABLE'


def test_unsupported_context_marks_the_affected_object_and_records_reason():
    from tests.factories import source
    snapshot=source('CREATE TABLE APP.T(ID NUMBER); ALTER TABLE APP.T SHRINK SPACE;')
    obj=snapshot.objects[0]
    assert obj.coverage.ddl=='PARTIAL'
    assert snapshot.capabilities['sidecar_diagnostics'].value[0]['reason_code']=='TABLE_CONTEXT_UNSUPPORTED'


def test_on_commit_refresh_privilege_uses_the_object_on_delimiter():
    from tests.factories import source
    snapshot=source('CREATE TABLE APP.T(ID NUMBER); GRANT SELECT, ON COMMIT REFRESH ON APP.T TO READER;')
    assert snapshot.completeness.ddl=='COMPLETE'
    grants=[obj for obj in snapshot.objects if obj.identity.object_type=='GRANT']
    assert {obj.properties['privilege'].value for obj in grants}=={'SELECT','ON COMMIT REFRESH'}
    assert all(obj.properties['target'].value=='T' and obj.identity.parent_key for obj in grants)


def test_global_temporary_table_identity_and_storage_semantics_are_retained():
    raw=b'CREATE GLOBAL TEMPORARY TABLE APP.T(ID NUMBER) ON COMMIT PRESERVE ROWS;'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE' and len(result.objects)==1
    obj=result.objects[0]
    assert obj.identity.name.effective_name=='T'
    assert b'GLOBAL TEMPORARY' in obj.raw_ddl
    assert obj.projection.properties['table_properties']['temporary']
    assert 'PRESERVE ROWS' in obj.projection.properties['table_properties']['on_commit']


def test_verified_routine_tree_is_reused_without_a_second_grammar_parse(monkeypatch):
    import base64
    from oracle_db_migration_generator.parsing.worker import parse_payload
    from oracle_db_migration_generator._vendor.analyzer_core.oracle import package
    def unexpected(*args): raise AssertionError('second grammar parse')
    monkeypatch.setattr(package,'_parse',unexpected)
    for raw in (b'CREATE PACKAGE APP.P AS PROCEDURE R; END P;',
                b'CREATE PROCEDURE APP.R AS BEGIN NULL; END;'):
        result=parse_payload({'raw':base64.b64encode(raw).decode(),'default_schema':'APP'})
        assert result['objects'][0]['parse_ok'] and not result['diagnostics']


def test_nested_view_arithmetic_uses_bounded_complete_grammar():
    raw=b'CREATE VIEW APP.V AS SELECT ROUND(ABS((SUM(TO_NUMBER(SUBSTR(X,1,2)*60)+TO_NUMBER(SUBSTR(X,4,2))/60)))/60) AS RESULT FROM APP.T;'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE' and result.objects[0].parse_ok
