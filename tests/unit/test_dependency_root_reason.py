from oracle_db_migration_generator.reporting.labels import operation_reason
from oracle_db_migration_generator.model.serialization import thaw
from tests.unit.test_bundle import make_plan
from dataclasses import replace
from tests.factories import source,actual,profile
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target


def unknown_units_plan(sql):
    selected=replace(profile(),source_length_semantics='UNKNOWN')
    desired=source(sql,selected);target=actual('',selected)
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))


def test_missing_table_comment_keeps_the_real_column_blocker():
    plan=unknown_units_plan("CREATE TABLE APP.T(ID NUMBER, LABEL VARCHAR2(20)); COMMENT ON COLUMN APP.T.ID IS 'Key';")
    table=next(op for op in plan.operations if op.identity.object_type=='TABLE')
    comment=next(op for op in plan.operations if op.identity.object_type=='COMMENT')
    assert table.decision==comment.decision=='BLOCKED'
    assert 'LABEL' in table.reason_tr and 'uzunluk birimi' in table.reason_tr
    assert 'LABEL' in comment.reason_tr and 'uzunluk birimi' in comment.reason_tr
    assert 'kaynak işlemi yok' not in comment.reason_tr
    reason=operation_reason(thaw(comment))
    assert 'APP.T' in reason and 'LABEL' in reason and 'uzunluk birimi' in reason
    assert 'hazır değil' not in reason and 'BLOCKED' not in reason and '[TABLE]' not in reason


def test_source_missing_relation_reports_the_actual_absence():
    plan=make_plan('CREATE VIEW APP.V AS SELECT ID FROM APP.MISSING;')
    view=next(op for op in plan.operations if op.identity.object_type=='VIEW')
    reason=operation_reason(thaw(view))
    assert 'APP.MISSING' in reason and 'hedefte bulunamadı' in reason
    assert 'kaynakta oluşturma tanımı bulunmuyor' in reason


def test_transitive_failure_preserves_root_reason():
    plan=unknown_units_plan("CREATE TABLE APP.T(ID NUMBER, LABEL VARCHAR2(20)); CREATE VIEW APP.V AS SELECT ID FROM APP.T; COMMENT ON TABLE APP.V IS 'view';")
    view=next(op for op in plan.operations if op.identity.object_type=='VIEW')
    comment=next(op for op in plan.operations if op.identity.object_type=='COMMENT')
    assert view.decision==comment.decision=='BLOCKED'
    assert 'LABEL' in view.reason_tr and 'LABEL' in comment.reason_tr
