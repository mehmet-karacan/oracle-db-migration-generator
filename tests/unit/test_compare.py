import hashlib
from dataclasses import replace
from pathlib import Path

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue
from oracle_db_migration_generator.parsing.adapter import parse_source
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision

ROOT = Path(__file__).resolve().parents[2]
PROFILE = load_source_profile(ROOT/'examples/source-profile.example.json')


def snapshot(sql, side='SOURCE'):
    raw = sql.encode()
    artifact = SourceArtifact('app/tables/DEMO/ddl.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    result = parse_source(SourceInput(SourceRevision('a'*40,None),(artifact,),'b'*64),PROFILE)
    if side=='TARGET':
        result = replace(result,side='TARGET',source_commit=None,target_id='DEMO-TEST',
                         completeness=replace(result.completeness,dictionary='COMPLETE'),observed_consistency='OBSERVED_STABLE')
    return result


def test_before_is_actual_after_is_desired():
    desired = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(80 CHAR));')
    actual = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(40 CHAR));','TARGET')
    result = compare_snapshots(desired,actual,PROFILE.policy)
    widths = [diff for diff in result.differences if diff.property_path.endswith('/length')]
    assert len(widths)==1 and widths[0].before.value==40 and widths[0].after.value==80


def test_target_lag_is_not_limited_to_last_commit():
    desired = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(80 CHAR), DESCRIPTION VARCHAR2(100 CHAR));')
    actual = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(40 CHAR));','TARGET')
    result = compare_snapshots(desired,actual,PROFILE.policy)
    assert any('/DESCRIPTION/' in diff.property_path and diff.kind=='MISSING' for diff in result.differences)
    assert any(diff.property_path.endswith('/length') and diff.before.value==40 for diff in result.differences)


def test_unknown_field_diff_is_not_same():
    desired = snapshot('CREATE TABLE APP.DEMO (ID NUMBER);')
    actual = snapshot('CREATE TABLE APP.DEMO (ID NUMBER);','TARGET')
    obj = actual.objects[0]
    obj = replace(obj,properties={'projection':KnownValue('UNKNOWN',None,obj.evidence_ids)},
                  coverage=Coverage('COMPLETE','PARTIAL','PARTIAL',('METADATA_UNAVAILABLE',)))
    result = compare_snapshots(desired,replace(actual,objects=(obj,)),PROFILE.policy)
    assert any(diff.kind=='UNKNOWN' for diff in result.differences)
    assert not result.complete


def test_uppercase_quoted_identity_matches_unquoted():
    desired = snapshot('CREATE TABLE APP.DEMO (ID NUMBER);')
    actual = snapshot('create table "APP"."DEMO" ("ID" number);','TARGET')
    result = compare_snapshots(desired,actual,PROFILE.policy)
    assert not result.differences


def test_sequence_runtime_counter_is_informational():
    desired = snapshot('CREATE SEQUENCE APP.S START WITH 10 INCREMENT BY 1 NOCACHE;')
    actual = snapshot('CREATE SEQUENCE APP.S START WITH 99 INCREMENT BY 1 NOCACHE;','TARGET')
    result = compare_snapshots(desired,actual,PROFILE.policy)
    assert result.differences and all(diff.kind=='INFORMATIONAL' for diff in result.differences)


def test_format_only_change_emits_no_difference_and_literal_change_does():
    desired = snapshot("CREATE TABLE APP.DEMO (TITLE VARCHAR2(80 CHAR) DEFAULT 'a  B');")
    actual = snapshot("create table app.demo( title varchar2(80 char) default 'a  B' );",'TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences
    changed = snapshot("create table app.demo( title varchar2(80 char) default 'a B' );",'TARGET')
    assert any(diff.property_path.endswith('/default') for diff in compare_snapshots(desired,changed,PROFILE.policy).differences)


def test_dictionary_timestamp_scale_is_fractional_precision_and_not_number_scale():
    desired = snapshot('CREATE TABLE APP.DEMO (STAMP TIMESTAMP(6));')
    actual = snapshot('CREATE TABLE APP.DEMO (STAMP TIMESTAMP(6));','TARGET')
    obj = actual.objects[0]
    row = {'table_name':'DEMO','column_name':'STAMP','data_type':'TIMESTAMP(6)','data_type_owner':None,
           'data_length':11,'char_length':0,'char_used':None,'data_precision':None,'data_scale':6,
           'nullable':'Y','data_default':None,'column_id':1,'hidden_column':'NO','virtual_column':'NO',
           'identity_column':'NO','default_on_null':'NO','user_generated':'YES','collation':None}
    properties = dict(obj.properties)
    properties['dictionary.columns'] = KnownValue('KNOWN',[row],obj.evidence_ids)
    actual = replace(actual,objects=(replace(obj,properties=properties),))
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences


def test_source_implicit_collation_is_unknown_and_not_a_claimed_removal():
    desired = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(80 CHAR));')
    actual = snapshot('CREATE TABLE APP.DEMO (TITLE VARCHAR2(80 CHAR));','TARGET')
    obj = actual.objects[0]
    row = {'table_name':'DEMO','column_name':'TITLE','data_type':'VARCHAR2','data_type_owner':None,
           'data_length':320,'char_length':80,'char_used':'C','data_precision':None,'data_scale':None,
           'nullable':'Y','data_default':None,'column_id':1,'hidden_column':'NO','virtual_column':'NO',
           'identity_column':'NO','default_on_null':'NO','user_generated':'YES','collation':'USING_NLS_COMP'}
    props = dict(obj.properties);props['dictionary.columns'] = KnownValue('KNOWN',[row],obj.evidence_ids)
    actual = replace(actual,objects=(replace(obj,properties=props),))
    changes = compare_snapshots(desired,actual,PROFILE.policy).differences
    assert changes and all(diff.kind=='UNKNOWN' for diff in changes)
    assert all(diff.property_path.endswith('/collation') for diff in changes)


def test_metadata_force_and_explicit_default_editionability_do_not_recreate_code():
    desired = snapshot('CREATE VIEW APP.V AS SELECT 1 X FROM DUAL;')
    actual = snapshot('CREATE OR REPLACE FORCE EDITIONABLE VIEW "APP"."V" AS SELECT 1 X FROM DUAL;','TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences
    spec = 'CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
    body = 'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/\n'
    source = snapshot(spec+body)
    target = snapshot((spec+body).replace('CREATE PACKAGE','CREATE OR REPLACE EDITIONABLE PACKAGE'),'TARGET')
    assert not compare_snapshots(source,target,PROFILE.policy).differences


def test_anonymous_source_constraint_matches_target_name_without_hiding_changes():
    desired=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, PRIMARY KEY(ID));')
    actual=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, CONSTRAINT SYS_C00001 PRIMARY KEY(ID));','TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences
    disabled=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, CONSTRAINT SYS_C00001 PRIMARY KEY(ID) DISABLE);','TARGET')
    changes=compare_snapshots(desired,disabled,PROFILE.policy).differences
    # Disabling a primary key also changes its inferred NOT NULL semantics.
    assert len(changes)==2 and sum(change.property_path.endswith('/enabled') for change in changes)==1
    assert any(change.property_path=='/columns/ID/nullable' and change.before.value is True
               and change.after.value is False for change in changes)
    named=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, CONSTRAINT PK_DEMO PRIMARY KEY(ID));')
    assert compare_snapshots(named,actual,PROFILE.policy).differences


def test_anonymous_matching_does_not_consume_a_source_named_constraint():
    desired=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, CONSTRAINT CK CHECK(ID>0), CHECK(ID>0));')
    actual=snapshot('CREATE TABLE APP.DEMO(ID NUMBER, CONSTRAINT CK CHECK(ID>0), CONSTRAINT SYS_C1 CHECK(ID>0));','TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences


def test_inline_index_backed_key_matches_its_separate_target_constraint():
    desired=snapshot('CREATE TABLE APP.DEMO(ID NUMBER DEFAULT 7 CONSTRAINT PK_T PRIMARY KEY USING INDEX APP.IX_T ENABLE);')
    actual=snapshot('CREATE TABLE APP.DEMO(ID NUMBER DEFAULT 7, CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX APP.IX_T ENABLE);','TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences


def test_lob_intrinsic_collation_does_not_require_a_source_schema_default():
    for datatype in ('CLOB','NCLOB'):
        desired=snapshot(f'CREATE TABLE APP.DEMO(PAYLOAD {datatype});')
        actual=snapshot(f'CREATE TABLE APP.DEMO(PAYLOAD {datatype});','TARGET')
        obj=actual.objects[0]
        row={'table_name':'DEMO','column_name':'PAYLOAD','data_type':datatype,'data_type_owner':None,
             'data_length':4000,'char_length':0,'char_used':None,'data_precision':None,'data_scale':None,
             'nullable':'Y','data_default':None,'column_id':1,'hidden_column':'NO','virtual_column':'NO',
             'identity_column':'NO','default_on_null':'NO','user_generated':'YES','collation':'USING_NLS_COMP'}
        props=dict(obj.properties);props['dictionary.columns']=KnownValue('KNOWN',[row],obj.evidence_ids)
        actual=replace(actual,objects=(replace(obj,properties=props),))
        assert not compare_snapshots(desired,actual,PROFILE.policy).differences


def test_varchar_alias_matches_varchar2_and_unknown_semantics_still_block():
    desired=snapshot('CREATE TABLE APP.DEMO(TXT VARCHAR(20 CHAR));')
    actual=snapshot('CREATE TABLE APP.DEMO(TXT VARCHAR2(20 CHAR));','TARGET')
    assert not compare_snapshots(desired,actual,PROFILE.policy).differences
    from tests.factories import source,actual as empty_actual,profile
    from oracle_db_migration_generator.planning.rules import plan_target,PlanningContext
    selected=replace(profile(),source_length_semantics='UNKNOWN')
    desired=source('CREATE TABLE APP.DEMO(TXT VARCHAR(20));',selected);target=empty_actual('',selected)
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Semantik'))
    assert all(op.decision=='BLOCKED' for op in plan.operations)


def test_character_to_number_change_has_no_unknown_source_collation():
    desired=snapshot('CREATE TABLE APP.DEMO(TITLE NUMBER);')
    actual=snapshot('CREATE TABLE APP.DEMO(TITLE VARCHAR2(10 BYTE) COLLATE USING_NLS_COMP);','TARGET')
    changes=compare_snapshots(desired,actual,PROFILE.policy)
    assert changes.complete
    assert not any(diff.kind=='UNKNOWN' for diff in changes.differences)
    datatype=next(diff for diff in changes.differences if diff.property_path.endswith('/data_type'))
    assert datatype.before.value=='VARCHAR2' and datatype.after.value=='NUMBER'
    collation=next(diff for diff in changes.differences if diff.property_path.endswith('/collation'))
    assert collation.after.state=='KNOWN' and collation.after.value is None
    # A real type conversion stays subject to review despite complete metadata.
    from oracle_db_migration_generator.planning.rules import plan_target,PlanningContext
    plan=plan_target(changes,PlanningContext(desired,actual,PROFILE,'Tip değişimi'))
    assert not any(op.decision=='READY' for op in plan.operations)
    assert any('TYPE_CHANGE_REQUIRES_REVIEW' in op.reason_codes for op in plan.operations)
