from dataclasses import replace
from pathlib import Path

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle, verify_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def make_plan(sql,observed=''):
    selected=profile(); desired=source(sql,selected); target=actual(observed,selected)
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Sentetik <Hedef>'))


def test_bundle_is_deterministic_complete_and_tamper_evident(tmp_path):
    plan=make_plan("CREATE TABLE APP.T (ID NUMBER(12,2), TXT VARCHAR2(80 CHAR) DEFAULT 'a  B');")
    first=write_bundle(plan,tmp_path/'one'); second=write_bundle(plan,tmp_path/'two')
    assert first['plan_id']==second['plan_id']==plan.plan_id
    left={p.relative_to(tmp_path/'one').as_posix():p.read_bytes() for p in (tmp_path/'one').rglob('*') if p.is_file()}
    right={p.relative_to(tmp_path/'two').as_posix():p.read_bytes() for p in (tmp_path/'two').rglob('*') if p.is_file()}
    assert left==right
    assert b'@@objects/' in left['migration.sql'] and b'Veritaban' in left['README.md']
    assert any(b'NUMBER(12,2)' in raw for path,raw in left.items() if path.startswith('objects/'))
    assert b'&lt;Hedef&gt;' in left['index.html']
    assert verify_bundle(tmp_path/'one')['status']=='VERIFIED'
    (tmp_path/'one'/'extra.sql').write_text('DROP TABLE APP.T;')
    with pytest.raises(ValueError,match='BUNDLE_UNEXPECTED_FILES'): verify_bundle(tmp_path/'one')


def test_partial_bundle_never_looks_like_deployment(tmp_path):
    plan=make_plan('CREATE TABLE APP.T (ID NUMBER NOT NULL); CREATE TABLE APP.NEW_T (ID NUMBER);','CREATE TABLE APP.T (ID NUMBER);')
    write_bundle(plan,tmp_path/'partial')
    assert not (tmp_path/'partial'/'migration.sql').exists()
    assert (tmp_path/'partial'/'partial-ready.sql').is_file()
    assert 'REVIEW_REQUIRED' in (tmp_path/'partial'/'plan.json').read_text()


def test_secret_or_invalid_emission_is_not_published(tmp_path):
    plan=make_plan("CREATE TABLE APP.T (TXT VARCHAR2(80 CHAR) DEFAULT 'private-token-value');")
    with pytest.raises(ValueError,match='SENSITIVE_CONTENT_DETECTED'):
        write_bundle(plan,tmp_path/'secret',secret_values=('private-token-value',))
    assert not (tmp_path/'secret').exists()
    op=plan.operations[0]
    broken=replace(op,intent=replace(op.intent,statement=b'CREATE TABLE APP.T (TXT NUMBER); DROP TABLE APP.OTHER;'))
    with pytest.raises(ValueError,match='EMITTED_SQL'):
        write_bundle(plan.with_operations((broken,)),tmp_path/'broken')
    assert not (tmp_path/'broken').exists()


def test_foreign_key_cycles_are_ordered_after_both_tables(tmp_path):
    plan=make_plan('CREATE TABLE APP.A (ID NUMBER, BID NUMBER, CONSTRAINT PK_A PRIMARY KEY(ID), CONSTRAINT FK_A FOREIGN KEY(BID) REFERENCES APP.B(ID)); '
                   'CREATE TABLE APP.B (ID NUMBER, AID NUMBER, CONSTRAINT PK_B PRIMARY KEY(ID), CONSTRAINT FK_B FOREIGN KEY(AID) REFERENCES APP.A(ID));')
    assert plan.status=='READY'
    kinds=[op.kind for op in plan.operations]
    assert kinds[:2]==['CREATE','CREATE']
    assert all(plan.operations.index(op)>1 for op in plan.operations if op.intent and op.intent.phase==50)
    write_bundle(plan,tmp_path/'fk')


def test_missing_foreign_key_parent_blocks_dependent_sql():
    plan=make_plan('CREATE TABLE APP.A (ID NUMBER, CONSTRAINT FK_A FOREIGN KEY(ID) REFERENCES OTHER.MISSING(ID));')
    assert plan.status=='BLOCKED'
    assert any('DEPENDENCY_UNVERIFIED' in op.reason_codes for op in plan.operations)


def test_foreign_key_parent_without_unique_key_is_blocked():
    plan=make_plan('CREATE TABLE APP.A (ID NUMBER, CONSTRAINT FK_A FOREIGN KEY(ID) REFERENCES APP.B(ID)); CREATE TABLE APP.B(ID NUMBER);')
    assert plan.status=='BLOCKED'
    assert all(op.decision=='BLOCKED' for op in plan.operations if op.intent and op.intent.phase==50)
    assert any(op.kind=='ADD_CONSTRAINT' and 'DEPENDENCY_UNVERIFIED' in op.reason_codes for op in plan.operations)


def test_report_bounds_and_escaping(tmp_path):
    from oracle_db_migration_generator.reporting.render import preview
    assert len(preview(('x'*500+'\n')*200))<=2048
    assert len(preview('x\n'*100).splitlines())<=30
    plan=make_plan("CREATE TABLE APP.T (ID NUMBER); COMMENT ON TABLE APP.T IS '<script>alert(1)</script>';" )
    write_bundle(plan,tmp_path/'html')
    html=(tmp_path/'html'/'index.html').read_text(encoding='utf-8')
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert len(html.encode())<=200*1024


def test_trigger_and_synonym_emissions_reparse_and_use_single_plsql_slash(tmp_path):
    plan=make_plan('CREATE TABLE APP.T(ID NUMBER); CREATE SYNONYM APP.S FOR APP.T; CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T FOR EACH ROW BEGIN NULL; END;\n/\nALTER TRIGGER APP.TR DISABLE;')
    assert plan.status=='READY'
    write_bundle(plan,tmp_path/'trigger')
    files=list((tmp_path/'trigger'/'objects').rglob('*.sql'))
    trigger=next(path.read_bytes() for path in files if b'TRIGGER' in path.read_bytes())
    assert b'DISABLE' in trigger and trigger.count(b'\n/\n')==1


def test_anonymous_primary_key_using_implicit_index_is_not_lost(tmp_path):
    plan=make_plan('CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID) USING INDEX ENABLE);')
    assert plan.status=='READY'
    assert any(op.kind=='ADD_CONSTRAINT' and b'PRIMARY KEY(ID)' in op.intent.statement for op in plan.operations)
    write_bundle(plan,tmp_path/'anonymous')


@pytest.mark.parametrize('key_kind,index_unique', [('PRIMARY KEY','UNIQUE '),('UNIQUE','')])
def test_named_backing_index_is_created_once_before_new_constraint(tmp_path,key_kind,index_unique):
    plan=make_plan(f'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T {key_kind}(ID) USING INDEX "APP"."IX_T" ENABLE); '
                   f'CREATE {index_unique}INDEX APP.IX_T ON APP.T(ID);')
    assert plan.status=='READY'
    table=next(op for op in plan.operations if op.kind=='CREATE')
    index=next(op for op in plan.operations if op.kind=='CREATE_INDEX')
    constraint=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert table.operation_id in index.dependencies
    assert index.operation_id in constraint.dependencies
    assert plan.operations.index(table)<plan.operations.index(index)<plan.operations.index(constraint)
    write_bundle(plan,tmp_path/'named')
    emitted=[path.read_bytes() for path in (tmp_path/'named/objects').rglob('*.sql')]
    assert sum(b'INDEX APP.IX_T ON APP.T' in sql for sql in emitted)==1
    assert sum(b'USING INDEX "APP"."IX_T" ENABLE' in sql for sql in emitted)==1


@pytest.mark.parametrize('index_sql',[
    '', 'CREATE INDEX APP.IX_T ON APP.T(OTHER_ID);',
    'CREATE INDEX APP.IX_T ON APP.OTHER(ID);',
    'CREATE INDEX APP.IX_T ON APP.T(ID); ALTER INDEX APP.IX_T UNUSABLE;',
    'CREATE INDEX APP.IX_T ON APP.T(ID) UNUSABLE;',
])
def test_unverified_backing_index_cannot_make_a_ready_constraint(index_sql):
    plan=make_plan('CREATE TABLE APP.OTHER(ID NUMBER); '
                   'CREATE TABLE APP.T(ID NUMBER, OTHER_ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX APP.IX_T ENABLE); '+index_sql)
    affected=[op for op in plan.operations if op.identity.name.effective_name=='T' and op.kind=='ADD_CONSTRAINT']
    assert affected and all(op.decision=='BLOCKED' and op.intent is None for op in affected)


def test_named_backing_index_preserves_normal_storage_without_false_expression_block(tmp_path):
    plan=make_plan('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX IX_T ENABLE); '
                   'CREATE UNIQUE INDEX APP.IX_T ON APP.T(ID) STORAGE(INITIAL 65536 MAXSIZE UNLIMITED);')
    assert plan.status=='READY'
    index=next(op for op in plan.operations if op.kind=='CREATE_INDEX')
    assert b'STORAGE(INITIAL 65536 MAXSIZE UNLIMITED)' in index.intent.statement
    write_bundle(plan,tmp_path/'storage')


def test_inline_named_backing_index_moves_key_to_its_dependency_phase(tmp_path):
    plan=make_plan('CREATE TABLE APP.T(ID NUMBER DEFAULT 7 CONSTRAINT PK_T PRIMARY KEY USING INDEX APP.IX_T ENABLE); '
                   'CREATE UNIQUE INDEX APP.IX_T ON APP.T(ID);')
    assert plan.status=='READY'
    table=next(op for op in plan.operations if op.kind=='CREATE')
    index=next(op for op in plan.operations if op.kind=='CREATE_INDEX')
    key=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert b'DEFAULT 7' in table.intent.statement and b'USING INDEX' not in table.intent.statement
    assert b'PRIMARY KEY' not in table.intent.statement
    assert b'PRIMARY KEY("ID") USING INDEX APP.IX_T ENABLE' in key.intent.statement
    assert index.operation_id in key.dependencies
    write_bundle(plan,tmp_path/'inline')


def test_inline_index_key_preserves_other_column_constraints_and_anonymous_identity(tmp_path):
    plan=make_plan('CREATE TABLE APP.T("Id" NUMBER DEFAULT 7 CONSTRAINT NN NOT NULL '
                   'PRIMARY KEY USING INDEX IX_T CONSTRAINT CK CHECK("Id">0)); '
                   'CREATE UNIQUE INDEX APP.IX_T ON APP.T("Id");')
    assert plan.status=='READY'
    table=next(op for op in plan.operations if op.kind=='CREATE')
    key=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert b'CONSTRAINT NN NOT NULL' in table.intent.statement and b'CONSTRAINT CK CHECK("Id">0)' in table.intent.statement
    assert b'PRIMARY KEY("Id") USING INDEX IX_T' in key.intent.statement
    assert b'CONSTRAINT @anonymous-' not in key.intent.statement
    write_bundle(plan,tmp_path/'inline_anonymous')


@pytest.mark.parametrize('semantics',['CHAR','BYTE'])
@pytest.mark.parametrize('datatype,length',[('VARCHAR2(20)',20),('VARCHAR(20)',20),('CHAR(20)',20),('CHAR',1)])
def test_profile_length_semantics_survive_create_and_add_emission(tmp_path,semantics,datatype,length):
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    selected=replace(profile(),source_length_semantics=semantics)
    for observed in ('','CREATE TABLE APP.T(ID NUMBER);'):
        suffix=" DEFAULT q'[keep BYTE CHAR]'" if not observed else ''
        table=f'CREATE TABLE APP.T(TXT {datatype}{suffix});'
        desired,target=source(table,selected),actual(observed,selected)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Semantik'))
        op=next(op for op in plan.operations if op.decision=='READY')
        assert (datatype.split('(')[0]+'('+str(length)+' '+semantics+')').encode() in op.intent.statement
        if not observed:assert b"q'[keep BYTE CHAR]'" in op.intent.statement
        if observed:
            projection=source('CREATE TABLE APP.T(ID NUMBER); '+op.intent.statement.decode(),selected).objects[0].projection
        else:
            projection=parse_ddl(op.intent.statement,op.identity).objects[0].projection
        assert projection.properties['columns']['TXT']['length_semantics']==semantics
        write_bundle(plan,tmp_path/('add' if observed else 'create'))


def test_explicit_column_semantics_override_profile_and_preserve_comments():
    selected=replace(profile(),source_length_semantics='CHAR')
    desired=source("CREATE TABLE APP.T(A VARCHAR2(20 BYTE), B VARCHAR2(20 /*keep*/) DEFAULT 'CHAR BYTE');",selected)
    target=actual('',selected)
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Semantik'))
    sql=next(op.intent.statement for op in plan.operations if op.decision=='READY')
    assert b'A VARCHAR2(20 BYTE)' in sql
    assert b"B VARCHAR2(20 /*keep*/ CHAR) DEFAULT 'CHAR BYTE'" in sql



