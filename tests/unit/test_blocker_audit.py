from dataclasses import replace

from oracle_db_migration_generator.artifacts.bundle import write_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.parsing.dependencies import references
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def plan(sql,observed=''):
    selected=profile();desired=source(sql,selected);target=actual(observed,selected)
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))


def test_existing_lob_storage_is_an_observation_and_does_not_hold_independent_columns():
    result=plan('CREATE TABLE APP.T(ID NUMBER, TXT CLOB, EXTRA NUMBER);',
                'CREATE TABLE APP.T(ID NUMBER, TXT CLOB) LOB(TXT) STORE AS BASICFILE (NOCACHE);')
    assert result.counts['blocked_operations']==0
    assert any(op.kind=='ADD_COLUMN' and op.decision=='READY' for op in result.operations)
    assert any('PHYSICAL_STORAGE_PRESERVED' in op.reason_codes and op.decision=='INFORMATIONAL' for op in result.operations)
    assert any('PHYSICAL_STORAGE_PRESERVED' in warning for warning in result.warnings)
    assert all(b'LOB(' not in op.intent.statement for op in result.operations if op.intent)


def test_existing_partition_drift_requires_review_without_holding_independent_default():
    result=plan('CREATE TABLE APP.T(ID NUMBER DEFAULT 7) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));',
                'CREATE TABLE APP.T(ID NUMBER DEFAULT 1) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(20));')
    assert any(op.decision=='REVIEW_REQUIRED' and 'PARTITION_LAYOUT_REQUIRES_REVIEW' in op.reason_codes for op in result.operations)
    assert any(op.decision=='READY' and b'DEFAULT 7' in op.intent.statement for op in result.operations)


def test_partition_parent_cannot_receive_a_long_column_in_partial_sql():
    for datatype in ('LONG','LONG RAW'):
        result=plan(f'CREATE TABLE APP.T(ID NUMBER, EXTRA {datatype});',
                    'CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));')
        assert not any(op.decision=='READY' for op in result.operations)


def test_cte_with_database_link_is_not_a_local_alias_even_if_local_table_exists():
    result=plan('CREATE VIEW APP.V AS WITH Q AS (SELECT ID FROM APP.BASE) SELECT ID FROM Q@REMOTE;',
                'CREATE TABLE APP.BASE(ID NUMBER); CREATE TABLE APP.Q(ID NUMBER);')
    assert all(op.decision=='BLOCKED' for op in result.operations if op.identity.object_type=='VIEW')


def test_comment_checks_its_actual_column_instead_of_unrelated_constraint_review():
    base='CREATE TABLE APP.T(ID NUMBER);'
    result=plan('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID)); COMMENT ON COLUMN APP.T.ID IS \'id\';',base)
    assert any(op.identity.object_type=='COMMENT' and op.decision=='READY' for op in result.operations)
    missing=plan('CREATE TABLE APP.T(ID NUMBER, X NUMBER NOT NULL); COMMENT ON COLUMN APP.T.X IS \'x\';',base)
    assert all(op.decision=='BLOCKED' for op in missing.operations if op.identity.object_type=='COMMENT')


def test_new_nullable_column_supplies_comment_and_index_dependencies():
    result=plan('CREATE TABLE APP.T(ID NUMBER, X NUMBER); COMMENT ON COLUMN APP.T.X IS \'x\'; CREATE INDEX APP.IX ON APP.T(X);',
                'CREATE TABLE APP.T(ID NUMBER);')
    added=next(op for op in result.operations if op.kind=='ADD_COLUMN')
    dependents=[op for op in result.operations if op.identity.object_type in {'COMMENT','INDEX'}]
    assert len(dependents)==2
    assert all(op.decision=='READY' and added.operation_id in op.dependencies for op in dependents)


def test_existing_relation_shape_allows_routine_before_unrelated_layout_change():
    table='CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));'
    routine=' CREATE PROCEDURE APP.P AS X NUMBER; BEGIN SELECT ID INTO X FROM APP.T; END;\n/'
    desired=source(table+routine);target=actual(table.replace('LESS THAN(10)','LESS THAN(20)'))
    objects=tuple(replace(obj,properties={**obj.properties,'dependencies':KnownValue('KNOWN',[],obj.evidence_ids)})
                  if obj.identity.object_type=='PROCEDURE' else obj for obj in desired.objects)
    desired=replace(desired,objects=objects);selected=profile()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert any(op.identity.object_type=='PROCEDURE' and op.decision=='READY' for op in result.operations)
    assert any(op.identity.object_type=='TABLE' and op.decision=='REVIEW_REQUIRED' for op in result.operations)


def test_partial_desired_table_cannot_use_its_stale_projection_as_shape_proof():
    desired=source('CREATE TABLE APP.T(ID NUMBER); ALTER TABLE APP.T RENAME COLUMN ID TO X; '
                   'CREATE PROCEDURE APP.P AS V NUMBER; BEGIN SELECT X INTO V FROM APP.T; END;\n/')
    objects=tuple(replace(obj,properties={**obj.properties,'dependencies':KnownValue('KNOWN',[],obj.evidence_ids)})
                  if obj.identity.object_type=='PROCEDURE' else obj for obj in desired.objects)
    desired=replace(desired,objects=objects);target=actual('CREATE TABLE APP.T(ID NUMBER);');selected=profile()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert all(op.decision=='BLOCKED' for op in result.operations)


def test_anonymous_constraint_owns_generated_backing_index_only_on_new_table():
    result=plan('CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID) USING INDEX ENABLE); CREATE UNIQUE INDEX APP.SYS_C123 ON APP.T(ID);')
    index=next(op for op in result.operations if op.identity.object_type=='INDEX')
    assert index.decision=='INFORMATIONAL' and index.intent is None
    assert any('BACKING_INDEX_CREATED_BY_CONSTRAINT' in warning for warning in result.warnings)
    unrelated=plan('CREATE TABLE APP.T(ID NUMBER); CREATE UNIQUE INDEX APP.SYS_C123 ON APP.T(ID);')
    assert any(op.decision=='BLOCKED' for op in unrelated.operations if op.identity.object_type=='INDEX')


def test_cte_alias_is_query_scoped_and_qualified_names_are_still_dependencies():
    sql='CREATE PROCEDURE APP.P AS BEGIN FOR R IN (WITH LOCAL_Q AS (SELECT ID FROM APP.T) SELECT * FROM LOCAL_Q) LOOP NULL; END LOOP; FOR R IN (SELECT * FROM LOCAL_Q) LOOP NULL; END LOOP; END;\n/'
    refs=references(source(sql).objects[0])
    assert sum(ref.name=='LOCAL_Q' for ref in refs)==1  # The later query is a real dependency.
    cte_only=source('CREATE VIEW APP.V AS WITH LOCAL_Q AS (SELECT ID FROM APP.T) SELECT * FROM LOCAL_Q;').objects[0]
    assert {ref.name for ref in references(cte_only)}=={'T'}
    qualified=source('CREATE VIEW APP.V AS WITH T AS (SELECT ID FROM APP.BASE) SELECT * FROM APP.T;').objects[0]
    assert {ref.name for ref in references(qualified)}=={'BASE','T'}


def test_signature_only_spec_does_not_inherit_body_only_exporter_dependencies():
    desired=source('CREATE PACKAGE APP.P AS PROCEDURE R(X NUMBER); END P;\n/')
    spec=desired.objects[0]
    spec=replace(spec,properties={**spec.properties,'dependencies':KnownValue('KNOWN',
        [{'owner':'APP','name':'BODY_TABLE','type':'TABLE'}],spec.evidence_ids)})
    desired=replace(desired,objects=(spec,));target=actual();selected=profile()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert result.status=='READY'
    typed=source('CREATE PACKAGE APP.P AS PROCEDURE R(X APP.MISSING_TYPE); END P;\n/')
    obj=typed.objects[0]
    typed=replace(typed,objects=(replace(obj,properties={**obj.properties,
        'dependencies':KnownValue('KNOWN',[],obj.evidence_ids)}),))
    result=plan_target(compare_snapshots(typed,target,selected.policy),PlanningContext(typed,target,selected,'Audit'))
    assert result.status=='BLOCKED'


def test_report_formats_counts_without_changing_json_numbers():
    from oracle_db_migration_generator.reporting.render import render_reports
    document=plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    document['counts']['observed_differences']=2353
    html=render_reports(document,{})['index.html'].decode()
    assert '<strong>2.353</strong>' in html and document['counts']['observed_differences']==2353


def test_report_uses_object_findings_without_parser_explanations(tmp_path):
    from tests.unit.test_invalid_target import invalid_object
    selected=profile();desired=source('CREATE TABLE APP.T(ID NUMBER);')
    target=invalid_object(actual('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/'),unparsed=True)
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    write_bundle(result,tmp_path/'report')
    html=(tmp_path/'report/index.html').read_text(encoding='utf8')
    assert 'APP.BAD' in html and 'INVALID' in html and 'PLS-00103' in html
    assert 'parse hatası karşılaştırmayı engellemez' not in html
    assert 'TARGET_INVALID_DDL_REPORTED' not in html


def test_report_does_not_promote_internal_index_deduplication_to_warning_banner():
    from oracle_db_migration_generator.reporting.render import render_reports
    document=plan('CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID)); CREATE UNIQUE INDEX APP.SYS_C1 ON APP.T(ID);').to_dict()
    html=render_reports(document,{})['index.html'].decode()
    assert '<p class="warning">PK/UK indeksi:' not in html
    blocked=plan('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10)); COMMENT ON TABLE APP.T IS \'test\';')
    comment=next(op for op in blocked.operations if op.identity.object_type=='COMMENT')
    assert 'yazılacak' not in comment.reason_tr
