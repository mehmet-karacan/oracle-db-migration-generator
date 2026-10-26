from dataclasses import replace

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def plan(desired_sql,actual_sql='',selected_profile=None):
    selected_profile = selected_profile or profile()
    desired, observed = source(desired_sql,selected_profile),actual(actual_sql,selected_profile)
    return plan_target(compare_snapshots(desired,observed,selected_profile.policy),
                       PlanningContext(desired,observed,selected_profile,'Sentetik Hedef'))


def test_empty_target_generates_complete_table_definition():
    result = plan("CREATE TABLE APP.T (TITLE VARCHAR2(100 CHAR) DEFAULT 'a  B' NOT NULL, PRICE NUMBER(12,2));")
    ready = [op for op in result.operations if op.decision=='READY']
    assert ready and result.status=='READY'
    sql = b'\n'.join(op.intent.statement for op in ready)
    assert b'VARCHAR2(100 CHAR)' in sql and b'NUMBER(12,2)' in sql
    assert b"'a  B'" in sql and b'NOT NULL' in sql


def test_create_table_as_select_never_emits_a_data_copy():
    result=plan('CREATE TABLE APP.OTHER(ID NUMBER); CREATE TABLE APP.T(ID NUMBER) AS SELECT ID FROM APP.OTHER;')
    operations=[op for op in result.operations if op.identity.name.effective_name=='T']
    assert operations and all(op.decision=='BLOCKED' and op.intent is None for op in operations)


def test_existing_table_adds_only_missing_nullable_column():
    result = plan('CREATE TABLE APP.T (ID NUMBER, TITLE VARCHAR2(80 CHAR));','CREATE TABLE APP.T (ID NUMBER);')
    ready = [op for op in result.operations if op.decision=='READY']
    assert len(ready)==1 and ready[0].kind=='ADD_COLUMN'
    assert b'ALTER TABLE' in ready[0].intent.statement
    assert b'CREATE TABLE' not in ready[0].intent.statement


def test_safe_varchar_widening_emits_modify():
    result = plan('CREATE TABLE APP.T (TITLE VARCHAR2(80 CHAR));','CREATE TABLE APP.T (TITLE VARCHAR2(40 CHAR));')
    ready = [op for op in result.operations if op.decision=='READY']
    assert len(ready)==1 and ready[0].kind=='MODIFY_COLUMN'
    assert b'VARCHAR2(80 CHAR)' in ready[0].intent.statement


def test_numeric_scale_or_shrink_requires_review():
    result = plan('CREATE TABLE APP.T (AMOUNT NUMBER(8,3));','CREATE TABLE APP.T (AMOUNT NUMBER(10,2));')
    assert result.status=='REVIEW_REQUIRED'
    assert any(op.decision=='REVIEW_REQUIRED' for op in result.operations)
    assert not any(op.decision=='READY' for op in result.operations)


def test_not_null_on_existing_table_requires_review():
    result = plan('CREATE TABLE APP.T (ID NUMBER NOT NULL);','CREATE TABLE APP.T (ID NUMBER);')
    assert any(op.decision=='REVIEW_REQUIRED' for op in result.operations)
    assert not any(op.decision=='READY' for op in result.operations)


def test_package_body_change_does_not_recreate_spec():
    spec = 'CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
    before = 'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/\n'
    after = 'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; NULL; END; END P;\n/\n'
    result = plan(spec+after,spec+before)
    ready = [op for op in result.operations if op.decision=='READY']
    assert len(ready)==1 and ready[0].identity.object_type=='PACKAGE_BODY'
    assert b'NULL; NULL;' in ready[0].intent.statement


def test_unique_index_on_populated_unknown_table_review():
    table = 'CREATE TABLE APP.T (ID NUMBER);'
    result = plan(table+' CREATE UNIQUE INDEX APP.I ON APP.T(ID);',table)
    assert any(op.identity.object_type=='INDEX' and op.decision=='REVIEW_REQUIRED' for op in result.operations)


def test_backing_index_not_emitted_twice():
    ddl = 'CREATE TABLE APP.T (ID NUMBER, CONSTRAINT PK_T PRIMARY KEY (ID)); CREATE UNIQUE INDEX APP.PK_T ON APP.T(ID);'
    result = plan(ddl)
    assert any('BACKING_INDEX_CREATED_BY_CONSTRAINT' in op.reason_codes for op in result.operations)
    assert sum(op.kind=='CREATE_INDEX' and op.decision=='READY' for op in result.operations)==0


def test_target_only_object_is_preserved():
    desired = 'CREATE TABLE APP.T (ID NUMBER);'
    result = plan(desired,desired+' CREATE TABLE APP.EXTRA_T (ID NUMBER);')
    assert result.status=='NO_ACTION'
    assert all(op.decision=='INFORMATIONAL' for op in result.operations)
    assert not any(op.intent for op in result.operations)


def test_missing_grantee_is_not_auto_granted():
    selected = profile()
    selected = replace(selected,policy=replace(selected.policy,grant_allowlist=('MISSING_READER',)))
    table = 'CREATE TABLE APP.T (ID NUMBER);'
    result = plan(table+' GRANT SELECT ON APP.T TO MISSING_READER;',table,selected)
    assert any(op.identity.object_type=='GRANT' and op.decision!='READY' for op in result.operations)


def test_supported_range_partition_not_silently_removed():
    result = plan('CREATE TABLE APP.T (ID NUMBER) PARTITION BY RANGE (ID) (PARTITION P1 VALUES LESS THAN (100));')
    assert result.status=='READY'
    table=next(op for op in result.operations if op.kind=='CREATE')
    assert b'PARTITION BY RANGE (ID) (PARTITION P1 VALUES LESS THAN (100))' in table.intent.statement
    assert 'CREATE_VERIFIED_RANGE_TABLE' in table.reason_codes


def test_schema_remap_is_not_global_replace():
    selected = profile()
    desired,observed = source('CREATE TABLE APP.T (ID NUMBER);'),actual()
    observed = replace(observed,schemas=('OTHER',))
    import pytest
    with pytest.raises(ValueError,match='SNAPSHOT_PROFILE_OR_SCHEMA_MISMATCH'):
        compare_snapshots(desired,observed,selected.policy)


def test_changed_body_cannot_bypass_review_of_new_spec():
    before='CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\nCREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/\n'
    after='CREATE PACKAGE APP.P AS PROCEDURE R; PROCEDURE S; END P;\n/\nCREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; PROCEDURE S IS BEGIN NULL; END; END P;\n/\n'
    result=plan(after,before)
    assert any(op.identity.object_type=='PACKAGE_SPEC' and op.decision=='REVIEW_REQUIRED' for op in result.operations)
    assert all(op.decision=='BLOCKED' for op in result.operations if op.identity.object_type=='PACKAGE_BODY')


def test_transitive_view_failure_cannot_bypass_existing_target_definition():
    desired='CREATE VIEW APP.A AS SELECT ID FROM OTHER.MISSING; CREATE VIEW APP.B AS SELECT ID FROM APP.A WHERE ID > 2;'
    observed='CREATE TABLE APP.T (ID NUMBER); CREATE VIEW APP.A AS SELECT ID FROM APP.T; CREATE VIEW APP.B AS SELECT ID FROM APP.A;'
    result=plan(desired,observed)
    assert all(op.decision=='BLOCKED' for op in result.operations if op.identity.object_type=='VIEW')


def test_unknown_user_type_and_external_routine_cannot_be_ready():
    for ddl in ('CREATE TABLE APP.T(C APP.MISSING_TYPE);',
                'CREATE PROCEDURE APP.P(X IN APP.MISSING_TYPE) AS BEGIN NULL; END;\n/',
                'CREATE PROCEDURE APP.P AS BEGIN APP.MISSING_PROC; END;\n/',
                'CREATE FUNCTION APP.F RETURN MISSING_TYPE AS BEGIN RETURN NULL; END;\n/'):
        result=plan(ddl)
        assert not any(op.decision=='READY' for op in result.operations),ddl


def test_context_column_does_not_lose_inline_constraint():
    result=plan('CREATE TABLE APP.T(ID NUMBER PRIMARY KEY); ALTER TABLE APP.T MODIFY (ID DEFAULT 1);')
    assert not any(op.decision=='READY' for op in result.operations)


def test_new_sequence_with_existing_consumer_requires_review():
    table='CREATE TABLE APP.T(ID NUMBER DEFAULT APP.S.NEXTVAL);'
    result=plan('CREATE SEQUENCE APP.S START WITH 1 NOCACHE; '+table,table)
    assert any(op.identity.object_type=='SEQUENCE' and op.decision=='REVIEW_REQUIRED' for op in result.operations)


def test_verified_private_synonym_and_empty_table_trigger_are_generated():
    result=plan('CREATE TABLE APP.T(ID NUMBER); CREATE SYNONYM APP.S FOR APP.T; CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T FOR EACH ROW BEGIN NULL; END;\n/')
    assert result.status=='READY'
    assert any(op.identity.object_type=='SYNONYM' and op.decision=='READY' for op in result.operations)
    assert any(op.identity.object_type=='TRIGGER' and op.decision=='READY' for op in result.operations)


def test_disabled_trigger_state_is_preserved_in_new_table_sql():
    result=plan('CREATE TABLE APP.T(ID NUMBER); CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T FOR EACH ROW BEGIN NULL; END;\n/\nALTER TRIGGER APP.TR DISABLE;')
    trigger=next(op for op in result.operations if op.identity.object_type=='TRIGGER')
    assert trigger.decision=='READY' and b'DISABLE' in trigger.intent.statement


def test_new_type_requires_attribute_type_dependencies():
    good=plan('CREATE TYPE APP.T AS OBJECT (ID NUMBER);\n/')
    assert good.status=='READY'
    for ddl in ('CREATE TYPE APP.T AS OBJECT (ID APP.MISSING_TYPE);\n/',
                'CREATE TYPE APP.T AS TABLE OF MISSING_TYPE;\n/'):
        result=plan(ddl)
        assert not any(op.decision=='READY' for op in result.operations)


def test_new_unusable_index_is_not_silently_created_as_usable():
    result=plan('CREATE TABLE APP.T(ID NUMBER); CREATE INDEX APP.I ON APP.T(ID); ALTER INDEX APP.I UNUSABLE;')
    assert any(op.identity.object_type=='INDEX' and op.decision=='REVIEW_REQUIRED' for op in result.operations)
    direct=plan('CREATE TABLE APP.T(ID NUMBER); CREATE INDEX APP.I ON APP.T(ID) UNUSABLE;')
    assert any(op.identity.object_type=='INDEX' and op.decision=='REVIEW_REQUIRED' for op in direct.operations)


def test_verified_unusable_index_on_new_heap_table_keeps_source_availability(tmp_path):
    from oracle_db_migration_generator.artifacts.bundle import write_bundle
    from oracle_db_migration_generator.model.snapshot import KnownValue
    from oracle_db_migration_generator.planning.object_rules import _verified_unusable_index_sql
    from oracle_db_migration_generator.planning.table_ddl import source_projection
    for suffix in ('CREATE INDEX APP.I ON APP.T(ID); ALTER INDEX APP.I UNUSABLE;',
                   'CREATE INDEX APP.I ON APP.T(ID) UNUSABLE;'):
        selected=profile()
        desired=source('CREATE TABLE APP.T(ID NUMBER); '+suffix)
        objects=[]
        for obj in desired.objects:
            props=dict(obj.properties)
            if obj.identity.object_type=='TABLE':
                props['dictionary.tables']=KnownValue('KNOWN',[{
                    'table_name':'T','temporary':'N','partitioned':'NO','cluster_name':None,
                    'iot_type':None,'nested':'NO'}],obj.evidence_ids)
            if obj.identity.object_type=='INDEX':
                props['dictionary.indexes']=KnownValue('KNOWN',[{
                    'index_name':'I','index_type':'NORMAL','status':'UNUSABLE',
                    'partitioned':'NO','uniqueness':'NONUNIQUE','table_owner':'APP',
                    'table_name':'T','generated':'N','visibility':'VISIBLE'}],obj.evidence_ids)
                for group in ('index_expressions','index_partitioning','index_partition_counts',
                              'index_partitions','index_subpartitions'):
                    props['dictionary.'+group]=KnownValue('KNOWN',[],obj.evidence_ids)
            objects.append(replace(obj,properties=props))
        desired=replace(desired,objects=tuple(objects))
        observed=actual('',selected)
        diff=compare_snapshots(desired,observed,selected.policy)
        result=plan_target(diff,
                           PlanningContext(desired,observed,selected,'Synthetic'))
        index=next(op for op in result.operations if op.identity.object_type=='INDEX')
        assert index.decision=='READY', (index.reason_codes, desired.objects[-1].coverage, [(d.kind,d.property_path) for d in diff.differences if d.object_key==index.identity.key])
        assert index.intent is not None
        sql=index.intent.statement.upper()
        assert sql.count(b'CREATE INDEX')==1 and b'UNUSABLE' in sql
        assert b'ALTER INDEX' not in sql
        write_bundle(result,tmp_path/('inline' if ' ON APP.T(ID) UNUSABLE;' in suffix else 'sidecar'))
        index_obj=next(obj for obj in desired.objects if obj.identity.object_type=='INDEX')
        context=PlanningContext(desired,observed,selected,'Synthetic')
        assert _verified_unusable_index_sql(context,index_obj,source_projection(index_obj)) is not None
        bad_props=dict(index_obj.properties)
        bad_props['dictionary.indexes']=KnownValue('KNOWN',[{
            'index_name':'I','index_type':'NORMAL','status':'VALID',
            'partitioned':'NO','uniqueness':'NONUNIQUE','table_owner':'APP',
            'table_name':'T','generated':'N','visibility':'VISIBLE'}],index_obj.evidence_ids)
        bad_index=replace(index_obj,properties=bad_props)
        assert _verified_unusable_index_sql(context,bad_index,source_projection(bad_index)) is None
        with_parent=PlanningContext(desired,actual('CREATE TABLE APP.T(ID NUMBER);',selected),selected,'Synthetic')
        assert _verified_unusable_index_sql(with_parent,index_obj,source_projection(index_obj)) is None
        bad_raw=replace(index_obj,raw_ddl=b'CREATE INDEX APP.I ON APP.T(ID); ALTER INDEX APP.OTHER UNUSABLE;')
        assert _verified_unusable_index_sql(context,bad_raw,source_projection(bad_raw)) is None


def test_invalid_target_compile_status_is_visible_even_without_ddl_drift():
    from oracle_db_migration_generator.model.snapshot import KnownValue
    selected=profile();desired=source('CREATE PROCEDURE APP.P AS BEGIN NULL; END;\n/')
    target=actual('CREATE PROCEDURE APP.P AS BEGIN NULL; END;\n/')
    obj=target.objects[0];props=dict(obj.properties)
    props['object_status']=KnownValue('KNOWN','INVALID',obj.evidence_ids)
    props['dictionary.errors']=KnownValue('KNOWN',[{'text':'PLS-00201: synthetic-secret'}],obj.evidence_ids)
    target=replace(target,objects=(replace(obj,properties=props),))
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Synthetic'))
    assert result.status=='NO_CHANGE'
    assert any('TARGET_INVALID_OBJECT' in warning and 'APP.P' in warning and 'PLS-00201' in warning for warning in result.warnings)
    assert all('synthetic-secret' not in warning for warning in result.warnings)
