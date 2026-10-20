import hashlib
import json
from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
from oracle_db_migration_generator.source.models import SourceArtifact
from oracle_db_migration_generator.source.sidecars import merge_sidecars
from tests.factories import actual,profile,source


def dependency_artifact(kind='PACKAGE',name='P',owner='APP',refs=None):
    raw=json.dumps({'schema':owner,'object':{'type':kind,'name':name},
                    'depends_on':refs if refs is not None else [{'owner':'APP','type':'TABLE','name':'T'}],
                    'used_by':[]}).encode()
    return SourceArtifact('app/packages/P/dependencies.json',owner,'DEPENDENCIES','PACKAGE_SPEC',raw,hashlib.sha256(raw).hexdigest())


def test_exporter_package_union_dependencies_bind_spec_and_body_idempotently():
    desired=source('CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
                   'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/')
    artifact=dependency_artifact()
    merged=merge_sidecars(desired,(artifact,))
    for obj in merged.objects:
        assert obj.properties['dependencies'].state=='KNOWN'
        assert obj.properties['dependencies'].value[0]['name']=='T'
        assert obj.properties['dependencies'].evidence_ids[0] in obj.evidence_ids
    again=merge_sidecars(merged,(artifact,))
    assert again.semantic_digest==merged.semantic_digest and again.evidence==merged.evidence


def test_explicit_package_body_inventory_does_not_mark_spec_complete():
    desired=source('CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
                   'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/')
    merged=merge_sidecars(desired,(dependency_artifact('PACKAGE BODY'),))
    assert 'dependencies' not in next(o for o in merged.objects if o.identity.object_type=='PACKAGE_SPEC').properties
    assert next(o for o in merged.objects if o.identity.object_type=='PACKAGE_BODY').properties['dependencies'].state=='KNOWN'


def test_dependency_rebinding_preserves_ddl_span_order_and_snapshot_roundtrip(tmp_path):
    from oracle_db_migration_generator.model.snapshot_io import load_snapshot
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    sql='CREATE TABLE APP.T(ID NUMBER); ALTER TABLE APP.T ADD(X NUMBER);'
    desired=source(sql);before=desired.objects[0]
    merged=merge_sidecars(desired,(dependency_artifact('TABLE','T',refs=[]),))
    after=merged.objects[0]
    assert after.evidence_ids[:len(before.evidence_ids)]==before.evidence_ids
    path=tmp_path/'app/fixture.sql';path.parent.mkdir();path.write_text(sql,encoding='utf8')
    (tmp_path/'source-snapshot.json').write_bytes(canonical_bytes(merged.to_dict()))
    loaded=load_snapshot(tmp_path/'source-snapshot.json',require_ddl=True)
    assert loaded.objects[0].raw_ddl==before.raw_ddl


def test_conflicting_dependency_inventories_block_the_affected_body():
    desired=source('CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
                   'CREATE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;\n/')
    merged=merge_sidecars(desired,(dependency_artifact(),dependency_artifact('PACKAGE BODY',refs=[])))
    body=next(obj for obj in merged.objects if obj.identity.object_type=='PACKAGE_BODY')
    assert body.coverage.ddl=='PARTIAL' and body.properties['dependencies'].state=='UNKNOWN'
    assert 'SOURCE_DEPENDENCIES_CONFLICT' in body.coverage.diagnostics


def test_dependency_owner_mismatch_does_not_mark_any_package_complete():
    desired=source('CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/')
    merged=merge_sidecars(desired,(dependency_artifact(owner='OTHER'),))
    assert merged.completeness.ddl=='PARTIAL'
    assert 'dependencies' not in merged.objects[0].properties


@pytest.mark.parametrize('sql',[
    "CREATE PROCEDURE APP.P AS BEGIN EXECUTE IMMEDIATE 'DELETE FROM APP.UNKNOWN_T'; END;\n/",
    "CREATE PROCEDURE APP.P AS C SYS_REFCURSOR; S VARCHAR2(100) := 'SELECT * FROM APP.UNKNOWN_T'; BEGIN OPEN C FOR S; END;\n/",
    'CREATE PROCEDURE APP.P AS C INTEGER; S VARCHAR2(100); BEGIN SYS."DBMS_SQL".PARSE(C,S,1); END;\n/',
    'CREATE PROCEDURE APP.P AS C INTEGER; S VARCHAR2(100); BEGIN "DBMS_SQL".PARSE(C,S,1); END;\n/',
])
def test_dictionary_inventory_cannot_prove_dynamic_sql_dependencies(sql):
    desired=source(sql);obj=desired.objects[0]
    desired=replace(desired,objects=(replace(obj,properties={**obj.properties,
        'dependencies':KnownValue('KNOWN',[],obj.evidence_ids)}),))
    selected=profile();target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    op=next(o for o in result.operations if o.identity.object_type=='PROCEDURE')
    assert op.decision=='REVIEW_REQUIRED' and 'DYNAMIC_SQL_DEPENDENCY_REQUIRES_REVIEW' in op.reason_codes
    assert op.intent is None


def index_plan(*,alter=None,explicit=False):
    desired=source('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID) USING INDEX '+
                   ('APP.PK_T ' if explicit else '')+'ENABLE); CREATE UNIQUE INDEX APP.PK_T ON APP.T(ID);')
    target=actual('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT OLD_KEY PRIMARY KEY(ID)); CREATE UNIQUE INDEX APP.OLD_KEY ON APP.T(ID);')
    table=next(o for o in target.objects if o.identity.object_type=='TABLE')
    facts={
        'constraints':[{'constraint_name':'OLD_KEY','constraint_type':'P','status':'ENABLED','validated':'VALIDATED',
                        'deferrable':'NOT DEFERRABLE','deferred':'IMMEDIATE','index_owner':'APP','index_name':'OLD_KEY','table_name':'T'}],
        'constraint_columns':[{'constraint_name':'OLD_KEY','column_name':'ID','position':1,'table_name':'T'}],
        'indexes':[{'index_name':'OLD_KEY','table_name':'T','table_owner':'APP','index_type':'NORMAL','uniqueness':'UNIQUE',
                    'status':'VALID','partitioned':'NO','visibility':'VISIBLE'}],
        'index_columns':[{'index_name':'OLD_KEY','table_name':'T','column_name':'ID','column_position':1,'descend':'ASC'}],
    }
    if alter:alter(facts)
    props={**table.properties,**{'dictionary.'+key:KnownValue('KNOWN',value,table.evidence_ids) for key,value in facts.items()}}
    table=replace(table,properties=props)
    target=replace(target,objects=tuple(table if o.object_key==table.object_key else o for o in target.objects))
    selected=profile()
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Index audit'))


def test_existing_dictionary_verified_implicit_backing_index_is_not_duplicated():
    result=index_plan()
    index=next(o for o in result.operations if o.identity.name.effective_name=='PK_T' and o.identity.object_type=='INDEX')
    assert index.decision=='INFORMATIONAL' and index.intent is None
    assert 'EXISTING_BACKING_INDEX_PRESERVED' in index.reason_codes
    assert any(o.decision=='REVIEW_REQUIRED' for o in result.operations if o.identity.object_type=='TABLE')


@pytest.mark.parametrize('alter',[
    lambda f:f['constraints'][0].update(status='DISABLED'),
    lambda f:f['constraints'][0].update(validated='NOT VALIDATED'),
    lambda f:f['indexes'][0].update(status='UNUSABLE'),
    lambda f:f['index_columns'][0].update(column_name='OTHER_ID'),
    lambda f:f['constraint_columns'][0].update(column_name='OTHER_ID'),
    lambda f:f['constraint_columns'][0].update(position=2),
    lambda f:f['index_columns'][0].update(column_position=2),
    lambda f:f['indexes'][0].update(visibility='INVISIBLE'),
    lambda f:f['indexes'][0].update(partitioned='YES'),
    lambda f:f.update(indexes=[]),
])
def test_unverified_existing_index_cannot_satisfy_source_key(alter):
    result=index_plan(alter=alter)
    index=next(o for o in result.operations if o.identity.name.effective_name=='PK_T' and o.identity.object_type=='INDEX')
    assert index.decision=='REVIEW_REQUIRED'


def test_explicit_source_index_name_is_not_replaced_by_another_existing_index():
    result=index_plan(explicit=True)
    index=next(o for o in result.operations if o.identity.name.effective_name=='PK_T' and o.identity.object_type=='INDEX')
    assert index.decision=='REVIEW_REQUIRED'


def trigger_plan(body=':NEW.ID := APP.S.NEXTVAL;',*,observed='',sequence=True,column='ID NUMBER'):
    sql=('CREATE SEQUENCE APP.S START WITH 1 NOCACHE;' if sequence else '')+f'CREATE TABLE APP.T({column}); '
    sql+='CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T FOR EACH ROW BEGIN '+body+' END TR;\n/'
    desired=source(sql);target=actual(observed);selected=profile()
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Trigger audit'))


def test_sequence_only_trigger_on_new_empty_table_has_verified_prerequisites():
    result=trigger_plan();trigger=next(o for o in result.operations if o.identity.object_type=='TRIGGER')
    assert trigger.decision=='READY'
    assert b':NEW.ID := APP.S.NEXTVAL;' in trigger.intent.statement
    required={o.operation_id for o in result.operations if o.identity.object_type in {'TABLE','SEQUENCE'}}
    assert required<=set(trigger.dependencies)


@pytest.mark.parametrize('kwargs',[
    {'body':':NEW.ID := APP.S.NEXTVAL; DELETE FROM APP.T;'},
    {'body':':NEW.ID := APP.S.NEXTVAL; APP.CALL_SOMETHING;'},
    {'column':'OTHER_ID NUMBER'},
    {'column':'ID VARCHAR2(50 CHAR)'},
    {'column':'ID NUMBER GENERATED ALWAYS AS IDENTITY'},
    {'observed':'CREATE TABLE APP.T(ID NUMBER);'},
])
def test_sequence_trigger_cannot_hide_other_effects_or_unknown_row_shape(kwargs):
    result=trigger_plan(**kwargs)
    trigger=next(o for o in result.operations if o.identity.object_type=='TRIGGER')
    assert trigger.decision!='READY'


def test_sequence_trigger_still_blocks_a_missing_sequence():
    result=trigger_plan(sequence=False)
    trigger=next(o for o in result.operations if o.identity.object_type=='TRIGGER')
    assert trigger.decision=='BLOCKED' and trigger.intent is None


def test_sequence_trigger_referencing_alias_must_match_the_assignment():
    desired=source('CREATE SEQUENCE APP.S; CREATE TABLE APP.T(ID NUMBER); '
                   'CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T REFERENCING NEW AS OTHER_ROW FOR EACH ROW '
                   'BEGIN :NEW.ID := APP.S.NEXTVAL; END TR;\n/')
    selected=profile();target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert all(op.decision!='READY' for op in result.operations if op.identity.object_type=='TRIGGER')


@pytest.mark.parametrize('ordering',['FOLLOWS','PRECEDES'])
def test_sequence_trigger_ordering_requires_separate_dependency_proof(ordering):
    desired=source('CREATE SEQUENCE APP.S; CREATE TABLE APP.T(ID NUMBER); '
                   'CREATE TRIGGER APP.TR BEFORE INSERT ON APP.T FOR EACH ROW '+ordering+' TR_MISSING '
                   'BEGIN :NEW.ID := APP.S.NEXTVAL; END TR;\n/')
    selected=profile();target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    trigger=next(op for op in result.operations if op.identity.object_type=='TRIGGER')
    assert trigger.decision!='READY' and trigger.intent is None
