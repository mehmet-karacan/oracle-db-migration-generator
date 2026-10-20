from dataclasses import replace

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle, verify_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def invalid_object(target,*,unparsed=False,status='INVALID',diagnostics=('PARSER_NOT_VERIFIED','PARSER_SYNTAX_ERROR')):
    obj=target.objects[0]
    props={**obj.properties,'object_status':KnownValue('KNOWN',status,obj.evidence_ids),
           'dictionary.errors':KnownValue('KNOWN',[{'text':'PLS-00103: synthetic-secret'}],obj.evidence_ids)}
    if unparsed:
        props.update(projection=KnownValue('UNKNOWN',None,obj.evidence_ids),
                     definition=KnownValue('UNKNOWN',None,obj.evidence_ids))
    obj=replace(obj,properties=props,projection=None if unparsed else obj.projection,
                coverage=replace(obj.coverage,ddl='PARTIAL' if unparsed else 'COMPLETE',
                                 diagnostics=diagnostics if unparsed else ()))
    return replace(target,objects=(obj,),completeness=replace(target.completeness,ddl='PARTIAL' if unparsed else 'COMPLETE'))


def make_plan(desired,target):
    selected=profile()
    differences=compare_snapshots(desired,target,selected.policy)
    return differences,plan_target(differences,PlanningContext(desired,target,selected,'Invalid target'))


def test_preserved_target_only_invalid_parse_failure_is_reported_without_blocking(tmp_path):
    desired=source('CREATE TABLE APP.T(ID NUMBER);')
    target=invalid_object(actual('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/'),unparsed=True)
    differences,plan=make_plan(desired,target)
    assert differences.complete and differences.scope.ddl=='COMPLETE'
    assert target.completeness.ddl=='PARTIAL'  # Original capture truth is retained.
    assert plan.status=='READY'
    assert any('TARGET_INVALID_OBJECT' in warning and 'APP.BAD' in warning for warning in plan.warnings)
    assert any('TARGET_INVALID_DDL_REPORTED' in warning for warning in plan.warnings)
    assert all('Hedefe özgü nesne korunuyor; parse hatası karşılaştırmayı engellemez' not in warning for warning in plan.warnings)
    assert any('TARGET_INVALID_DDL_REPORTED' in warning and 'APP.BAD' in warning
               and 'PARSER_SYNTAX_ERROR' in warning for warning in plan.warnings)
    assert all('synthetic-secret' not in warning for warning in plan.warnings)
    bad=next(op for op in plan.operations if op.identity.name.effective_name=='BAD')
    assert bad.decision=='INFORMATIONAL' and bad.intent is None
    write_bundle(plan,tmp_path/'bundle')
    assert (tmp_path/'bundle/migration.sql').exists()
    assert verify_bundle(tmp_path/'bundle')['status']=='VERIFIED'


@pytest.mark.parametrize('status,diagnostics',[
    ('VALID',('PARSER_NOT_VERIFIED','PARSER_SYNTAX_ERROR')),
    ('INVALID',('ORA-01031',)),
])
def test_real_metadata_failure_is_not_hidden_by_the_invalid_reporting_rule(status,diagnostics):
    desired=source('CREATE TABLE APP.T(ID NUMBER);')
    target=invalid_object(actual('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/'),
                          unparsed=True,status=status,diagnostics=diagnostics)
    differences,plan=make_plan(desired,target)
    assert not differences.complete and plan.status=='BLOCKED'


@pytest.mark.parametrize('unparsed',[False,True])
def test_existing_invalid_local_dependency_is_a_warning_not_a_presence_failure(unparsed):
    desired=source('CREATE VIEW APP.V AS SELECT ID FROM APP.X;')
    target=invalid_object(actual('CREATE VIEW APP.X AS SELECT 1 ID FROM DUAL;'),unparsed=unparsed)
    _,plan=make_plan(desired,target)
    view=next(op for op in plan.operations if op.identity.name.effective_name=='V')
    assert plan.status=='READY' and view.decision=='READY'
    assert any('TARGET_INVALID_OBJECT' in warning and 'APP.X' in warning for warning in plan.warnings)


def test_existing_invalid_external_reference_is_reported_without_blocking():
    desired=source('CREATE VIEW APP.V AS SELECT ID FROM OTHER.X;')
    target=actual()
    target=replace(target,capabilities={**target.capabilities,'reference_objects':KnownValue('KNOWN',
        [{'owner':'OTHER','name':'X','object_type':'VIEW','status':'INVALID'}],('ev-target-scope',))})
    _,plan=make_plan(desired,target)
    assert plan.status=='READY'
    assert any('TARGET_INVALID_REFERENCE' in warning and 'OTHER.X' in warning for warning in plan.warnings)


def test_invalid_status_does_not_bypass_required_foreign_key_structure():
    desired=source('CREATE TABLE APP.C(PID NUMBER, CONSTRAINT FK_C FOREIGN KEY(PID) REFERENCES APP.P(ID));')
    target=invalid_object(actual('CREATE TABLE APP.P(ID NUMBER);'))
    _,plan=make_plan(desired,target)
    constraint=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert constraint.decision=='BLOCKED' and constraint.intent is None


def test_required_shared_definition_is_not_made_known_by_invalid_status():
    desired=source('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/')
    target=invalid_object(actual('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/'),unparsed=True)
    differences,plan=make_plan(desired,target)
    assert not differences.complete and plan.status=='BLOCKED'
    assert any(diff.kind=='UNKNOWN' for diff in differences.differences)


def test_invalid_reporting_does_not_hide_missing_capture_bytes():
    desired=source('CREATE TABLE APP.T(ID NUMBER);')
    target=invalid_object(actual('CREATE PROCEDURE APP.BAD AS BEGIN NULL; END;\n/'),unparsed=True)
    target=replace(target,objects=(replace(target.objects[0],raw_ddl=None),))
    differences,plan=make_plan(desired,target)
    assert not differences.complete and plan.status=='BLOCKED'


@pytest.mark.parametrize('status',['VALID','INVALID'])
def test_external_object_presence_does_not_prove_foreign_key_columns_or_key(status):
    desired=source('CREATE TABLE APP.C(PID NUMBER, CONSTRAINT FK_C FOREIGN KEY(PID) REFERENCES OTHER.P(ID));')
    target=actual()
    target=replace(target,capabilities={**target.capabilities,'reference_objects':KnownValue('KNOWN',
        [{'owner':'OTHER','name':'P','object_type':'TABLE','status':status}],('ev-target-scope',))})
    _,plan=make_plan(desired,target)
    constraint=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert constraint.decision=='BLOCKED' and constraint.intent is None
    assert 'DEPENDENCY_UNVERIFIED' in constraint.reason_codes
