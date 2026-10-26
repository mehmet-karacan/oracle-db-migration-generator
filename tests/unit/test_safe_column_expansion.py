from dataclasses import replace

import pytest

from test_rules import plan
from tests.factories import source, actual, profile
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target


@pytest.mark.parametrize(('old','new'), [(50,255),(255,255)])
def test_varchar_byte_to_char_is_ready_when_character_and_byte_capacity_expand(old,new):
    result=plan(f'CREATE TABLE APP.T(C VARCHAR2({new} CHAR));',f'CREATE TABLE APP.T(C VARCHAR2({old} BYTE));')
    ready=[o for o in result.operations if o.decision=='READY']
    assert len(ready)==1 and ready[0].kind=='MODIFY_COLUMN'
    assert f'VARCHAR2({new} CHAR)'.encode() in ready[0].intent.statement


@pytest.mark.parametrize(('old','new'), [('300 BYTE','200 CHAR'),('50 BYTE','2000 CHAR'),('255 CHAR','500 BYTE')])
def test_semantics_change_with_possible_capacity_loss_stays_held(old,new):
    result=plan(f'CREATE TABLE APP.T(C VARCHAR2({new}));',f'CREATE TABLE APP.T(C VARCHAR2({old}));')
    assert result.operations and not any(o.decision=='READY' for o in result.operations)


def nullable_plan(*,primary=False,missing=False,missing_nn_column=False,default_on_null=False):
    selected=profile();desired=source('CREATE TABLE APP.T(C NUMBER'+(' DEFAULT 0' if default_on_null else '')+');',selected)
    target=actual('CREATE TABLE APP.T(C NUMBER'+(' DEFAULT ON NULL 0' if default_on_null else '')+' CONSTRAINT NN_T_C NOT NULL);',selected)
    obj=target.objects[0];ids=('ev-target-scope',)
    constraints=[{'table_name':'T','constraint_name':'NN_T_C','constraint_type':'C',
        'search_condition':'"C" IS NOT NULL','status':'ENABLED','deferrable':'NOT DEFERRABLE','validated':'VALIDATED'}]
    columns=[{'table_name':'T','constraint_name':'NN_T_C','column_name':'C','position':1}]
    if missing_nn_column:columns=[]
    if primary:
        constraints.append({'table_name':'T','constraint_name':'PK_T','constraint_type':'P','status':'ENABLED'})
        columns.append({'table_name':'T','constraint_name':'PK_T','column_name':'C','position':1})
    obj=replace(obj,properties={**obj.properties,
        'dictionary.constraints':KnownValue('UNKNOWN' if missing else 'KNOWN',None if missing else constraints,ids),
        'dictionary.constraint_columns':KnownValue('KNOWN',columns,ids)})
    target=replace(target,objects=(obj,))
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Target'))


def test_explicit_not_null_can_be_relaxed_with_complete_non_pk_proof():
    result=nullable_plan()
    ready=[o for o in result.operations if o.decision=='READY']
    assert len(ready)==1 and ready[0].intent.statement==b'ALTER TABLE "APP"."T" MODIFY ("C" NULL);'
    assert 'RELAX_VERIFIED_NOT_NULL' in ready[0].reason_codes


@pytest.mark.parametrize('kwargs',[{'primary':True},{'missing':True},{'missing_nn_column':True},{'default_on_null':True}])
def test_primary_key_or_missing_constraint_inventory_never_relaxes_null(kwargs):
    result=nullable_plan(**kwargs)
    assert not any(o.decision=='READY' for o in result.operations)
