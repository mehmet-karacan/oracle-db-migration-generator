from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_bundle import make_plan
from tests.unit.test_report_views import inputs


def test_general_mail_keeps_object_details_readable_without_redundant_counts():
    import re
    run,plans=inputs(2)
    html=render_email(build_run_view(run,plans)).decode()
    assert 'işlem /' not in html
    assert 'CREATE' in html and 'TARGET-000' in html and 'TARGET-001' in html
    header=next(row for row in re.findall(r'<thead>(.*?)</thead>',html,re.S) if 'Nesne / Fark' in row)
    widths=[int(value) for value in re.findall(r'<th\b[^>]*\bwidth="(\d+)%"',header)]
    assert len(widths)==4 and sum(widths)==100
    assert widths[0]>=55 and all(width<=20 for width in widths[1:])
    logo=re.search(r'<img\b[^>]*\balt="İnnova"[^>]*>',html).group()
    width=int(re.search(r'\bwidth="(\d+)"',logo).group(1))
    height=int(re.search(r'\bheight="(\d+)"',logo).group(1))
    from importlib.resources import files
    import struct
    original_width,original_height=struct.unpack('>II',files('oracle_db_migration_generator.reporting').joinpath('assets/innova-logo.png').read_bytes()[16:24])
    assert abs((width/height)/(original_width/original_height)-1)<0.02


def test_missing_relation_reason_names_the_dependency_and_location():
    plan=make_plan('CREATE VIEW APP.V AS SELECT ID FROM APP.MISSING;')
    blocked=next(op for op in plan.operations if op.decision=='BLOCKED')
    assert 'DEPENDENCY_UNVERIFIED' in blocked.reason_codes
    assert 'APP.MISSING' in blocked.reason_tr
    assert 'hedef' in blocked.reason_tr.lower() and 'bulunamadı' in blocked.reason_tr


def test_fk_reason_names_the_parent_columns_and_missing_key():
    plan=make_plan('CREATE TABLE APP.P(ID NUMBER); CREATE TABLE APP.C(PID NUMBER, CONSTRAINT FK_C FOREIGN KEY(PID) REFERENCES APP.P(ID));')
    blocked=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT' and op.decision=='BLOCKED')
    assert 'APP.P' in blocked.reason_tr and 'ID' in blocked.reason_tr
    assert 'PRIMARY KEY/UNIQUE' in blocked.reason_tr


def test_namespace_reason_names_both_conflicting_types():
    plan=make_plan('CREATE FUNCTION APP.F RETURN NUMBER IS BEGIN RETURN 1; END;\n/','CREATE PROCEDURE APP.F IS BEGIN NULL; END;\n/')
    blocked=next(op for op in plan.operations if 'TARGET_NAMESPACE_CONFLICT' in op.reason_codes)
    assert 'APP.F' in blocked.reason_tr and 'PROCEDURE' in blocked.reason_tr and 'FUNCTION' in blocked.reason_tr


def test_index_reason_names_the_missing_parent_table():
    plan=make_plan('CREATE INDEX APP.IX_T ON APP.MISSING(ID);')
    blocked=next(op for op in plan.operations if 'INDEX_PARENT_MISSING' in op.reason_codes)
    assert 'APP.MISSING' in blocked.reason_tr and 'TABLE' in blocked.reason_tr


def test_cycle_reason_identifies_each_unresolved_prerequisite():
    plan=make_plan('CREATE VIEW APP.A AS SELECT ID FROM APP.B; CREATE VIEW APP.B AS SELECT ID FROM APP.A;')
    cycle=[op for op in plan.operations if 'DEPENDENCY_CYCLE' in op.reason_codes]
    assert len(cycle)==2
    for op in cycle:
        parent='APP.B' if op.identity.name.effective_name=='A' else 'APP.A'
        assert parent in op.reason_tr and '[VIEW]' in op.reason_tr


def test_fk_reason_does_not_deny_an_existing_ready_column_operation():
    plan=make_plan('CREATE TABLE APP.P(ID NUMBER, N NUMBER, CONSTRAINT UQ_P UNIQUE(N)); CREATE TABLE APP.C(PID NUMBER, CONSTRAINT FK_C FOREIGN KEY(PID) REFERENCES APP.P(N));','CREATE TABLE APP.P(ID NUMBER);')
    assert any(op.kind=='ADD_COLUMN' and op.decision=='READY' for op in plan.operations)
    fk=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT' and op.identity.name.effective_name=='C')
    assert fk.decision=='BLOCKED' and 'APP.P' in fk.reason_tr and 'N' in fk.reason_tr
    assert 'hazır kolon işlemi yok' not in fk.reason_tr
    assert 'ADD_COLUMN' in fk.reason_tr
