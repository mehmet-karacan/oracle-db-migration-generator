from dataclasses import replace

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle, verify_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.serialization import thaw
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def metadata_source(collation='USING_NLS_COMP', *, explicit=False, default=''):
    selected=profile()
    clause=' COLLATE '+collation if explicit else ''
    desired=source('CREATE TABLE APP.T(TXT VARCHAR2(20)'+clause+default+');',selected)
    obj=desired.objects[0]
    projection=thaw(obj.properties['projection'].value)
    projection['columns']['TXT'].update(length_semantics='BYTE',collation=collation)
    updated=replace(obj,projection=None,properties={**obj.properties,
        'projection':KnownValue('KNOWN',projection,obj.evidence_ids)})
    return replace(desired,objects=(updated,)),selected


def target_with_capability(observed,selected,enabled):
    target=actual(observed,selected)
    state='UNKNOWN' if enabled is None else 'KNOWN'
    value=KnownValue(state,enabled,('ev-target-scope',))
    return replace(target,capabilities={**target.capabilities,'data_bound_collation_enabled':value})


@pytest.mark.parametrize('enabled,collation',[(True,'BINARY_CI'),(True,'USING_NLS_COMP'),(False,'USING_NLS_COMP')])
def test_effective_source_collation_survives_create_and_add(tmp_path,enabled,collation):
    for observed in ('','CREATE TABLE APP.T(ID NUMBER);'):
        default=" DEFAULT q'[keep COLLATE BYTE CHAR]'" if not observed else ''
        desired,selected=metadata_source(collation,default=default)
        target=target_with_capability(observed,selected,enabled)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Collation'))
        op=next(op for op in plan.operations if op.kind==('ADD_COLUMN' if observed else 'CREATE'))
        assert op.decision=='READY'
        assert b'VARCHAR2(20 BYTE)' in op.intent.statement
        if enabled:
            assert ('VARCHAR2(20 BYTE) COLLATE '+collation).encode() in op.intent.statement
        else:
            assert b' COLLATE USING_NLS_COMP' not in op.intent.statement
        if default:assert default.encode() in op.intent.statement
        if not observed:
            parsed=parse_ddl(op.intent.statement,op.identity)
            assert parsed.coverage=='COMPLETE'
            assert parsed.objects[0].projection.properties['columns']['TXT']['collation']==(collation if enabled else None)
        folder=tmp_path/('add' if observed else 'create')
        write_bundle(plan,folder)
        assert verify_bundle(folder)['status']=='VERIFIED'


@pytest.mark.parametrize('enabled,collation,explicit',[
    (None,'USING_NLS_COMP',False),(False,'BINARY_CI',False),
    (None,'BINARY_CI',True),(False,'USING_NLS_COMP',True),
])
def test_unproved_or_unavailable_collation_support_blocks_only_affected_sql(enabled,collation,explicit):
    for observed in ('','CREATE TABLE APP.T(ID NUMBER);'):
        desired,selected=metadata_source(collation,explicit=explicit)
        target=target_with_capability(observed,selected,enabled)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Collation'))
        ops=[op for op in plan.operations if op.identity.name.effective_name=='T' and op.kind!='PRESERVE']
        assert ops and all(op.decision=='BLOCKED' and op.intent is None for op in ops)
        assert any(any('COLLATION' in reason for reason in op.reason_codes) for op in ops)


def test_parameter_access_denial_is_unknown_capability_not_empty_target():
    from tests.unit.test_collector import FakeConnection, inputs
    from oracle_db_migration_generator.config.credentials import Credentials
    from oracle_db_migration_generator.oracle.collector import collect_target
    target,selected=inputs()
    connection=FakeConnection(denied='V$PARAMETER')
    observed=collect_target(target,lambda _:Credentials('APP','synthetic-password'),selected,connect=lambda *_:connection)
    assert observed.snapshot is not None and observed.snapshot.completeness.dictionary=='COMPLETE'
    capability=observed.snapshot.capabilities.get('data_bound_collation_enabled')
    assert capability is not None and capability.state=='UNKNOWN'
    assert observed.receipt['schemas'][0]['capability_errors']['collation_parameters']=='ORA-01031'
    assert connection.closed


def test_parameter_observation_controls_capability_without_using_the_version_floor():
    from tests.unit.test_collector import FakeConnection, FakeCursor, inputs
    from oracle_db_migration_generator.config.credentials import Credentials
    from oracle_db_migration_generator.oracle.collector import collect_target
    class ParameterCursor(FakeCursor):
        def fetchall(self):
            if 'V$PARAMETER' in self.current.upper():return [('compatible','19.0.0'),('max_string_size','EXTENDED')]
            return super().fetchall()
    connection=FakeConnection();connection.reader=ParameterCursor()
    target,selected=inputs()
    observed=collect_target(target,lambda _:Credentials('APP','secret'),selected,connect=lambda *_:connection)
    capability=observed.snapshot.capabilities.get('data_bound_collation_enabled')
    assert capability is not None and capability.state=='KNOWN' and capability.value is True
    assert all(any(ev.id==key and ev.query_id=='v$parameter.collation' for ev in observed.snapshot.evidence) for key in capability.evidence_ids)


@pytest.mark.parametrize('rows,expected',[
    ([{'name':'compatible','value':'19.0.0'},{'name':'max_string_size','value':'STANDARD'}],False),
    ([{'name':'compatible','value':'12.1.0'},{'name':'max_string_size','value':'EXTENDED'}],False),
    ([{'name':'compatible','value':'19.0.0'}],None),
])
def test_collation_parameter_requirements_are_independent_of_oracle_major(rows,expected):
    from oracle_db_migration_generator.oracle.capabilities import collation_capabilities
    capability=collation_capabilities(rows,'ev-parameters')['data_bound_collation_enabled']
    assert capability.state==('UNKNOWN' if expected is None else 'KNOWN')
    assert capability.value is expected


def test_reconstructed_column_does_not_invent_unsupported_collate_syntax():
    desired,selected=metadata_source()
    obj=desired.objects[0];projection=thaw(obj.properties['projection'].value)
    projection['_context_changed_columns']=['TXT']
    desired=replace(desired,objects=(replace(obj,properties={**obj.properties,
        'projection':KnownValue('KNOWN',projection,obj.evidence_ids)}),))
    target=target_with_capability('',selected,False)
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Collation'))
    create=plan.operations[0]
    assert create.kind=='CREATE' and create.decision=='READY'
    assert b'VARCHAR2(20 BYTE)' in create.intent.statement and b'COLLATE' not in create.intent.statement


def test_table_default_collation_declaration_also_requires_target_support():
    selected=profile()
    desired=source('CREATE TABLE APP.T(ID NUMBER) DEFAULT COLLATION USING_NLS_COMP;',selected)
    assert desired.completeness.ddl=='COMPLETE'
    for enabled in (False,None):
        target=target_with_capability('',selected,enabled)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Collation'))
        assert plan.operations and all(op.decision=='BLOCKED' and op.intent is None for op in plan.operations)
        assert any('COLLATION' in code for op in plan.operations for code in op.reason_codes)


@pytest.mark.parametrize('datatype',['CLOB','NCLOB'])
def test_lob_intrinsic_collation_does_not_bypass_explicit_syntax_gate(datatype):
    selected=profile()
    for enabled in (False,None):
        target=target_with_capability('',selected,enabled)
        desired=source(f'CREATE TABLE APP.T(TXT {datatype} COLLATE USING_NLS_COMP);',selected)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'LOB collation'))
        assert desired.completeness.ddl=='COMPLETE'
        assert plan.operations and all(op.decision=='BLOCKED' and op.intent is None for op in plan.operations)
        intrinsic=source(f'CREATE TABLE APP.T(TXT {datatype});',selected)
        normal=plan_target(compare_snapshots(intrinsic,target,selected.policy),PlanningContext(intrinsic,target,selected,'LOB intrinsic'))
        assert normal.status=='READY'
        assert all(b'COLLATE' not in op.intent.statement for op in normal.operations if op.intent)


@pytest.mark.parametrize('datatype',['NUMBER','DATE','RAW(20)'])
def test_collation_on_a_noncharacter_column_is_never_ready(datatype):
    selected=profile()
    desired=source(f'CREATE TABLE APP.T(TXT {datatype} COLLATE USING_NLS_COMP);',selected)
    assert desired.completeness.ddl=='COMPLETE'
    for enabled in (True,False,None):
        target=target_with_capability('',selected,enabled)
        plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Invalid collation'))
        assert plan.operations and all(op.decision=='BLOCKED' and op.intent is None for op in plan.operations)
