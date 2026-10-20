"""Synthetic regressions for independently verified index blocker causes."""
from dataclasses import replace

import pytest

from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.backing_index import existing_backing_index
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def backing_context(*, source_key='PRIMARY KEY(ID) USING INDEX ENABLE', index_name='SYS_C123', alter=None):
    desired=source(f'CREATE TABLE APP.T(ID NUMBER, {source_key}); '
                   f'CREATE UNIQUE INDEX APP.{index_name} ON APP.T(ID);')
    target=actual('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT TARGET_KEY PRIMARY KEY(ID)); '
                  'CREATE UNIQUE INDEX APP.TARGET_KEY ON APP.T(ID);')
    table=next(obj for obj in target.objects if obj.identity.object_type=='TABLE')
    facts={
        'constraints':[{'constraint_name':'TARGET_KEY','constraint_type':'P','status':'ENABLED',
                        'validated':'VALIDATED','deferrable':'NOT DEFERRABLE','deferred':'IMMEDIATE',
                        'index_owner':'APP','index_name':'TARGET_KEY','table_name':'T'}],
        'constraint_columns':[{'constraint_name':'TARGET_KEY','column_name':'ID','position':1,'table_name':'T'}],
        'indexes':[{'index_name':'TARGET_KEY','table_name':'T','table_owner':'APP','index_type':'NORMAL',
                    'uniqueness':'UNIQUE','status':'VALID','partitioned':'NO','visibility':'VISIBLE'}],
        'index_columns':[{'index_name':'TARGET_KEY','table_name':'T','column_name':'ID','column_position':1,'descend':'ASC'}],
    }
    if alter:alter(facts)
    table=replace(table,properties={**table.properties,**{
        'dictionary.'+key:KnownValue('KNOWN',rows,table.evidence_ids) for key,rows in facts.items()}})
    target=replace(target,objects=tuple(table if obj.object_key==table.object_key else obj for obj in target.objects))
    context=PlanningContext(desired,target,profile(),'Index audit')
    return context,next(obj for obj in desired.objects if obj.identity.object_type=='INDEX'),next(
        obj for obj in desired.objects if obj.identity.object_type=='TABLE')


def test_anonymous_source_key_can_prove_an_equivalent_existing_backing_index():
    context,index,table=backing_context()
    proof=existing_backing_index(context,index,table,('ID',))
    assert proof and set(proof)<={item.id for item in context.evidence}
    assert set(table.evidence_ids)<=set(proof)


@pytest.mark.parametrize('source_key',[
    'PRIMARY KEY(ID) USING INDEX ENABLE',
    'CONSTRAINT SYS_C123 PRIMARY KEY(ID) USING INDEX ENABLE',
])
def test_proven_existing_backing_index_precedes_reserved_name_guard(source_key):
    context,index,_=backing_context(source_key=source_key)
    result=plan_target(compare_snapshots(context.source,context.target,context.profile.policy),context)
    operation=next(op for op in result.operations if op.identity.key==index.object_key)
    assert operation.decision=='INFORMATIONAL'
    assert operation.reason_codes==('EXISTING_BACKING_INDEX_PRESERVED',)
    assert operation.intent is None


@pytest.mark.parametrize('alter',[
    lambda facts:facts['constraints'][0].update(status='DISABLED'),
    lambda facts:facts['constraints'][0].update(validated='NOT VALIDATED'),
    lambda facts:facts['constraints'][0].update(index_owner='OTHER'),
    lambda facts:facts['indexes'][0].update(status='UNUSABLE'),
    lambda facts:facts['index_columns'][0].update(column_name='OTHER_ID'),
    lambda facts:facts['constraint_columns'][0].update(position=2),
    lambda facts:facts.update(indexes=[]),
])
def test_anonymous_source_key_still_requires_complete_target_backing_proof(alter):
    context,index,table=backing_context(alter=alter)
    assert existing_backing_index(context,index,table,('ID',)) is None


@pytest.mark.parametrize('index_name',['USER_INDEX','SYS_C_BUSINESS'])
def test_anonymous_key_does_not_claim_an_arbitrary_named_index(index_name):
    context,index,table=backing_context(index_name=index_name)
    assert existing_backing_index(context,index,table,('ID',)) is None
