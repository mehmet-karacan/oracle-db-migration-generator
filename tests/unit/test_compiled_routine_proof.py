"""Compiler evidence must never bypass source, privilege or target-shape proof."""
from copy import deepcopy
from dataclasses import replace
import hashlib

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.evidence import Evidence
from oracle_db_migration_generator.model.serialization import digest, thaw
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.oracle.routine_metadata import snapshot_binding_digest, snapshot_scope_state
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import source, actual, profile


def known(rows):
    return {'state':'KNOWN','rows':rows}


def record(owner,name,kind,sha):
    stamp=known([[kind,'VALID','2026-10-26T10:00:00',None]])
    return {'owner':owner,'name':name,'kind':kind,'before':stamp,'after':deepcopy(stamp),
            'ddl':{'state':'KNOWN','sha256':sha},'dependency_ddl':{'state':'KNOWN','sha256':sha},
            'columns':known([]),'procedures':known([]),'arguments':known([]),'privileges':known([])}


def fixture(sql='CREATE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT MAX(ID) INTO N FROM APP.T; END;',new_table=False):
    desired=source('CREATE TABLE APP.T(ID NUMBER); '+sql)
    desired=replace(desired,source_commit=None,source_origin={'kind':'ORACLE','connection_id':'source-db','snapshot_id':'1'*64})
    desired=replace(desired,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)}) if obj.identity.object_type=='PROCEDURE' else obj
        for obj in desired.objects))
    target=actual('' if new_table else 'CREATE TABLE APP.T(ID NUMBER);')
    objects={(o.identity.object_type,o.identity.name.effective_name):o for o in desired.objects}
    routine=objects[('PROCEDURE','P')];table=objects[('TABLE','T')]
    unit=record('APP','P','PROCEDURE',routine.ddl_sha256)
    unit.update(dependencies=known([['P','PROCEDURE','APP','T','TABLE',None,'HARD']]),
                dependencies_after=known([['P','PROCEDURE','APP','T','TABLE',None,'HARD']]),
                errors=known([]),settings=known([['PROCEDURE',2,'INTERPRETED','FALSE','DISABLE:ALL','BYTE',None,'IDENTIFIERS:NONE']]),
                procedures=known([[None,1,None,'PROCEDURE','DEFINER','NO','NO','NO','NO','NO','NO']]))
    parent=record('APP','T','TABLE',table.ddl_sha256);parent['columns']=known([['ID','NUMBER',None,22,None,None,0,None,'Y',1,'NO','NO','NO','NO',None]])
    dest=deepcopy(parent)
    if new_table:dest.update(before=known([]),after=known([]),columns=known([]),dependency_ddl={'state':'UNKNOWN'})
    target_unit=record('APP','P','PROCEDURE',routine.ddl_sha256)
    target_unit.update(before=known([]),after=known([]))
    caps=[{'identity':known([['APP']]),'records':[unit,parent]}, {'identity':known([['APP']]),'records':[dest,target_unit]}]
    return desired,target,caps


def attach(snapshot,data):
    document={**data,'base_snapshot_digest':snapshot.semantic_digest,
              'base_snapshot_binding':snapshot_binding_digest(snapshot),
              'base_scope':snapshot_scope_state(snapshot),'oracle_version':'19.0.0.0.0'}
    ev=Evidence('ev-'+digest(document),'SOURCE_METADATA' if snapshot.side=='SOURCE' else 'TARGET_METADATA',snapshot.side,None,digest(document),None,None,'oracle.compiled-static/v1','Sentetik derleyici kanıtı.')
    return replace(snapshot,capabilities={**snapshot.capabilities,'routine_metadata':KnownValue('KNOWN',document,(ev.id,))},evidence=(*snapshot.evidence,ev))


def planned(desired,target,caps):
    desired,target=attach(desired,caps[0]),attach(target,caps[1])
    p=profile()
    return plan_target(compare_snapshots(desired,target,p.policy),PlanningContext(desired,target,p,'Target'))


def test_fresh_valid_static_unit_emits_original_body_after_dependency_check():
    desired,target,caps=fixture()
    result=planned(desired,target,caps)
    op=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert op.decision=='READY'
    assert op.intent.statement==b'CREATE OR REPLACE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT MAX(ID) INTO N FROM APP.T; END;'
    assert 'COMPILED_STATIC' in op.reason_codes[0]
    assert len(op.evidence_ids)>=3


def test_missing_local_relation_is_created_before_certified_program_unit():
    desired,target,caps=fixture(new_table=True)
    result=planned(desired,target,caps)
    table=next(o for o in result.operations if o.identity.name.effective_name=='T')
    routine=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert routine.decision=='READY'
    assert table.operation_id in routine.dependencies
    assert list(result.operations).index(table)<list(result.operations).index(routine)


@pytest.mark.parametrize(('catalog_case','expected'),[
    ('spec_and_body','READY'),
    ('spec_only','REVIEW_REQUIRED'),
    ('duplicate_body','REVIEW_REQUIRED'),
    ('unrelated_kind','REVIEW_REQUIRED'),
    ('target_spec_drift','REVIEW_REQUIRED'),
    ('source_spec_drift','REVIEW_REQUIRED'),
])
def test_existing_package_body_accepts_stable_spec_and_body_catalog_rows(catalog_case,expected):
    table_sql='CREATE TABLE APP.T(ID NUMBER);'
    spec_sql='CREATE PACKAGE APP.PKG AS PROCEDURE RUN; END;'
    body_sql='CREATE PACKAGE BODY APP.PKG AS PROCEDURE RUN IS N NUMBER; BEGIN SELECT MAX(ID) INTO N FROM APP.T; END; END;'
    old_body_sql='CREATE PACKAGE BODY APP.PKG AS PROCEDURE RUN IS BEGIN NULL; END; END;'
    desired=source(' '.join((table_sql,spec_sql,body_sql)))
    desired=replace(desired,source_commit=None,
                    source_origin={'kind':'ORACLE','connection_id':'source-db','snapshot_id':'1'*64})
    desired=replace(desired,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)})
        if obj.identity.object_type=='PACKAGE_BODY' else obj for obj in desired.objects))
    target=actual(' '.join((table_sql,spec_sql,old_body_sql)))
    source_body=next(obj for obj in desired.objects if obj.identity.object_type=='PACKAGE_BODY')
    target_body=next(obj for obj in target.objects if obj.identity.object_type=='PACKAGE_BODY')
    source_spec=next(obj for obj in desired.objects if obj.identity.object_type=='PACKAGE_SPEC')
    target_spec=next(obj for obj in target.objects if obj.identity.object_type=='PACKAGE_SPEC')
    table=next(obj for obj in desired.objects if obj.identity.object_type=='TABLE')
    catalog_rows=[['PACKAGE','VALID','2026-10-26T10:00:00',None],
                  ['PACKAGE BODY','VALID','2026-10-26T10:00:00',None]]
    unit=record('APP','PKG','PACKAGE BODY',source_body.ddl_sha256)
    unit.update(before=known(deepcopy(catalog_rows)),after=known(deepcopy(catalog_rows)),
                dependencies=known([['PKG','PACKAGE BODY','APP','T','TABLE',None,'HARD']]),
                dependencies_after=known([['PKG','PACKAGE BODY','APP','T','TABLE',None,'HARD']]),
                errors=known([]),
                settings=known([['PACKAGE BODY',2,'INTERPRETED','FALSE','DISABLE:ALL','BYTE',None,'IDENTIFIERS:NONE']]),
                procedures=known([[None,1,None,'PACKAGE BODY','DEFINER','NO','NO','NO','NO','NO','NO']]))
    source_table=record('APP','T','TABLE',table.ddl_sha256)
    source_table['columns']=known([['ID','NUMBER',None,22,None,None,0,None,'Y',1,'NO','NO','NO','NO',None]])
    target_table=deepcopy(source_table)
    target_unit=record('APP','PKG','PACKAGE BODY',target_body.ddl_sha256)
    source_spec_record=record('APP','PKG','PACKAGE',source_spec.ddl_sha256)
    target_spec_record=record('APP','PKG','PACKAGE',target_spec.ddl_sha256)
    if catalog_case=='target_spec_drift':target_spec_record['ddl']['sha256']='0'*64
    if catalog_case=='source_spec_drift':source_spec_record['ddl']['sha256']='0'*64
    target_rows=deepcopy(catalog_rows)
    if catalog_case=='spec_only':target_rows.pop()
    elif catalog_case=='duplicate_body':target_rows.append(deepcopy(target_rows[-1]))
    elif catalog_case=='unrelated_kind':target_rows.append(['FUNCTION','VALID','2026-10-26T10:00:00',None])
    target_unit.update(before=known(target_rows),after=known(deepcopy(target_rows)))
    result=planned(desired,target,[
        {'identity':known([['APP']]),'records':[unit,source_spec_record,source_table]},
        {'identity':known([['APP']]),'records':[target_unit,target_spec_record,target_table]},
    ])
    body=next(op for op in result.operations if op.identity.object_type=='PACKAGE_BODY'
              and op.identity.name.effective_name=='PKG')
    assert body.decision==expected, body.reason_tr
    if expected=='READY':
        assert body.intent is not None and b'SELECT MAX(ID) INTO N FROM APP.T' in body.intent.statement
    else:assert body.intent is None


@pytest.mark.parametrize('failure',[
    'invalid','changed_hash','changed_stamp','unknown_dependencies','remote','invoker','compiler_error',
    'ccflags','target_shape','target_invalid','target_ddl_drift','dependency_source_drift','wrong_identity',
    'wrong_root','empty_dependencies','missing_settings',
])
def test_unproven_compiler_or_dependency_fact_keeps_unit_without_executable_sql(failure):
    desired,target,caps=fixture();unit,parent=caps[0]['records'];dest=caps[1]['records'][0]
    if failure=='invalid':unit['before']['rows'][0][1]=unit['after']['rows'][0][1]='INVALID'
    elif failure=='changed_hash':unit['ddl']['sha256']='0'*64
    elif failure=='changed_stamp':unit['after']['rows'][0][2]='2026-10-26T10:00:01'
    elif failure=='unknown_dependencies':unit['dependencies']={'state':'UNKNOWN','error_code':'ORA-01031'}
    elif failure=='remote':unit['dependencies']['rows'][0][5]='REMOTE_DB'
    elif failure=='invoker':unit['procedures']['rows'][0][4]='CURRENT_USER'
    elif failure=='compiler_error':unit['errors']=known([['P','PROCEDURE','ERROR',201]])
    elif failure=='ccflags':unit['settings']['rows'][0][6]='MODE:TRUE'
    elif failure=='target_shape':dest['columns']['rows'][0][1]='VARCHAR2'
    elif failure=='target_invalid':dest['before']['rows'][0][1]=dest['after']['rows'][0][1]='INVALID'
    elif failure=='target_ddl_drift':dest['dependency_ddl']['sha256']='0'*64
    elif failure=='dependency_source_drift':parent['dependency_ddl']['sha256']='0'*64
    elif failure=='wrong_identity':caps[1]['identity']=known([['OTHER']])
    elif failure=='wrong_root':unit['dependencies']['rows'][0][0]='ANOTHER_UNIT'
    elif failure=='empty_dependencies':unit['dependencies']=known([])
    elif failure=='missing_settings':unit['settings']=known([])
    result=planned(desired,target,caps)
    op=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED'
    assert op.intent is None


def test_dynamic_sql_stays_held_even_with_valid_compiler_metadata():
    desired,target,caps=fixture("CREATE PROCEDURE APP.P IS BEGIN EXECUTE IMMEDIATE 'delete from APP.T'; END;")
    result=planned(desired,target,caps)
    op=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED' and op.intent is None
    assert 'DYNAMIC_SQL_DEPENDENCY_REQUIRES_REVIEW' in op.reason_codes


def test_proof_cannot_be_copied_to_another_snapshot():
    desired,target,caps=fixture();desired=attach(desired,caps[0]);target=attach(target,caps[1])
    stale=desired.capabilities['routine_metadata'];data=thaw(stale.value);data['base_snapshot_digest']='0'*64
    desired=replace(desired,capabilities={**desired.capabilities,'routine_metadata':KnownValue('KNOWN',data,stale.evidence_ids)})
    p=profile();result=plan_target(compare_snapshots(desired,target,p.policy),PlanningContext(desired,target,p,'Target'))
    assert next(o for o in result.operations if o.identity.name.effective_name=='P').decision=='REVIEW_REQUIRED'


@pytest.mark.parametrize('changed_side',['SOURCE','TARGET'])
def test_compiler_proof_is_bound_to_exact_connection_observation(changed_side):
    desired,target,caps=fixture()
    desired,target=attach(desired,caps[0]),attach(target,caps[1])
    if changed_side=='SOURCE':
        desired=replace(desired,source_origin={**thaw(desired.source_origin),'snapshot_id':'2'*64})
    else:
        target=replace(target,target_id='different-target-observation')
    p=profile()
    result=plan_target(compare_snapshots(desired,target,p.policy),PlanningContext(desired,target,p,'Target'))
    assert next(o for o in result.operations if o.identity.name.effective_name=='P').decision=='REVIEW_REQUIRED'


def test_ui_filter_added_after_read_only_capture_keeps_same_observation_proof():
    desired,target,caps=fixture()
    desired,target=attach(desired,caps[0]),attach(target,caps[1])
    desired=replace(desired,capabilities={**desired.capabilities,
        'comparison_filter':KnownValue('KNOWN',{'object_types':['PROCEDURE']},())})
    p=profile()
    result=plan_target(compare_snapshots(desired,target,p.policy),PlanningContext(desired,target,p,'Target'))
    assert next(o for o in result.operations if o.identity.name.effective_name=='P').decision=='READY'


def test_scoped_comparison_retains_proof_when_only_unrelated_object_is_removed():
    from oracle_db_migration_generator.portable.adapter import scope_comparison
    from oracle_db_migration_generator.portable.selection import CaptureFilter
    desired,target,caps=fixture()
    sql='CREATE SEQUENCE APP.UNUSED; CREATE TABLE APP.T(ID NUMBER); '
    procedure='CREATE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT MAX(ID) INTO N FROM APP.T; END;'
    desired=source(sql+procedure)
    desired=replace(desired,source_commit=None,
                    source_origin={'kind':'ORACLE','connection_id':'source-db','snapshot_id':'1'*64})
    desired=replace(desired,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)}) if obj.identity.object_type=='PROCEDURE'
        else obj for obj in desired.objects))
    target=actual(sql)
    desired,target=attach(desired,caps[0]),attach(target,caps[1])
    selection=CaptureFilter.from_dict({'schemas':['APP'],'object_types':['TABLE','PROCEDURE'],
                                       'object_names':['T','P']})
    desired,target=scope_comparison(desired,target,selection)
    p=profile()
    result=plan_target(compare_snapshots(desired,target,p.policy),PlanningContext(desired,target,p,'Target'))
    assert next(o for o in result.operations if o.identity.name.effective_name=='P').decision=='READY'


def test_target_root_created_after_snapshot_cannot_be_replaced_by_stale_plan():
    desired,target,caps=fixture()
    target_unit=caps[1]['records'][1]
    target_unit['before']=target_unit['after']=known([['PROCEDURE','VALID','2026-10-26T10:01:00',None]])
    result=planned(desired,target,caps)
    assert next(o for o in result.operations if o.identity.name.effective_name=='P').decision=='REVIEW_REQUIRED'


def test_unchanged_local_package_with_effective_argument_drift_keeps_caller_held():
    package='CREATE PACKAGE APP.PKG AS PROCEDURE GO(P_ID NUMBER); END;'
    procedure='CREATE PROCEDURE APP.P IS BEGIN APP.PKG.GO(1); END;'
    desired=source(package+' '+procedure)
    desired=replace(desired,source_commit=None,
                    source_origin={'kind':'ORACLE','connection_id':'source-db','snapshot_id':'1'*64})
    desired=replace(desired,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)}) if obj.identity.object_type=='PROCEDURE'
        else obj for obj in desired.objects))
    target=actual(package)
    routine=next(obj for obj in desired.objects if obj.identity.object_type=='PROCEDURE')
    spec=next(obj for obj in desired.objects if obj.identity.object_type=='PACKAGE_SPEC')
    unit=record('APP','P','PROCEDURE',routine.ddl_sha256)
    unit.update(dependencies=known([['P','PROCEDURE','APP','PKG','PACKAGE',None,'HARD']]),
                dependencies_after=known([['P','PROCEDURE','APP','PKG','PACKAGE',None,'HARD']]),
                errors=known([]),settings=known([['PROCEDURE',2,'INTERPRETED','FALSE','DISABLE:ALL','BYTE',None,'IDENTIFIERS:NONE']]),
                procedures=known([[None,1,None,'PROCEDURE','DEFINER','NO','NO','NO','NO','NO','NO']]))
    source_package=record('APP','PKG','PACKAGE',spec.ddl_sha256)
    source_package['arguments']=known([['GO','NUMBER']])
    target_package=deepcopy(source_package)
    target_package['arguments']=known([['GO','DATE']])
    target_root=record('APP','P','PROCEDURE',routine.ddl_sha256)
    target_root.update(before=known([]),after=known([]))
    caps=[{'identity':known([['APP']]),'records':[unit,source_package]},
          {'identity':known([['APP']]),'records':[target_root,target_package]}]
    result=planned(desired,target,caps)
    assert next(op for op in result.operations if op.identity.name.effective_name=='P').decision=='REVIEW_REQUIRED'


def external_fixture():
    desired,target,caps=fixture('CREATE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT 1 INTO N FROM DUAL; END;')
    unit=caps[0]['records'][0]
    unit['dependencies']=known([['P','PROCEDURE','PUBLIC','DUAL','SYNONYM',None,'HARD'],['P','PROCEDURE','SYS','STANDARD','PACKAGE',None,'HARD'],['P','PROCEDURE','SYS','SYS_STUB_FOR_PURITY_ANALYSIS','PACKAGE',None,'HARD']])
    unit['dependencies_after']=deepcopy(unit['dependencies'])
    synonym=record('PUBLIC','DUAL','SYNONYM','2'*64)
    synonym.update(synonym=known([['SYS','DUAL',None]]),local_shadow=known([]))
    dual=record('SYS','DUAL','RESOLVED','3'*64)
    dual['before']=dual['after']=known([['TABLE','VALID','2026-10-26T10:00:00',None]])
    dual['columns']=known([['DUMMY','VARCHAR2',None,1,None,None,1,'B','Y',1,'NO','NO','NO','NO','USING_NLS_COMP']])
    dual['privileges']=known([['PUBLIC','SELECT']])
    standard=record('SYS','STANDARD','PACKAGE','4'*64);standard['privileges']=known([['PUBLIC','EXECUTE']])
    for cap in caps:
        cap['records'] += deepcopy([synonym,dual,standard])
        cap['compiler_runtime']={'objects':known([['PACKAGE','VALID']]),'source_sha256':'5'*64}
    return desired,target,caps


def test_verified_public_synonym_and_compiler_intrinsic_allow_static_sql():
    desired,target,caps=external_fixture();result=planned(desired,target,caps)
    op=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert op.decision=='READY'
    assert b'SELECT 1 INTO N FROM DUAL' in op.intent.statement


def test_local_dml_does_not_require_write_grant_on_sys_dual():
    desired,target,caps=external_fixture()
    original=next(o for o in desired.objects if o.identity.object_type=='PROCEDURE')
    sql='CREATE PROCEDURE APP.P IS N NUMBER; BEGIN SELECT 1 INTO N FROM DUAL; UPDATE APP.T SET ID=1; END;'
    desired=source('CREATE TABLE APP.T(ID NUMBER); '+sql)
    desired=replace(desired,source_commit=None,source_origin={'kind':'ORACLE','connection_id':'source-db','snapshot_id':'1'*64})
    desired=replace(desired,objects=tuple(replace(obj,properties={**obj.properties,
        'object_status':KnownValue('KNOWN','VALID',obj.evidence_ids)}) if obj.identity.object_type=='PROCEDURE' else obj
        for obj in desired.objects))
    current=next(o for o in desired.objects if o.identity.object_type=='PROCEDURE')
    caps[0]['records'][0]['ddl']['sha256']=current.ddl_sha256
    caps[0]['records'][0]['dependencies']['rows'].append(['P','PROCEDURE','APP','T','TABLE',None,'HARD'])
    caps[0]['records'][0]['dependencies_after']=deepcopy(caps[0]['records'][0]['dependencies'])
    op=next(o for o in planned(desired,target,caps).operations if o.identity.name.effective_name=='P')
    assert op.decision=='READY'
    assert b'UPDATE APP.T SET ID=1' in op.intent.statement


@pytest.mark.parametrize('failure',['shadow','remote_synonym','changed_synonym','missing_grant','role_only_grant',
                                  'changed_package','invalid_external','unknown_external','missing_intrinsic','changed_intrinsic',
                                  'effective_argument_drift','effective_procedure_drift','unknown_arguments'])
def test_external_resolution_must_prove_signature_and_direct_access(failure):
    desired,target,caps=external_fixture()
    synonym=next(item for item in caps[1]['records'] if item['kind']=='SYNONYM')
    dual=next(item for item in caps[1]['records'] if item['kind']=='RESOLVED')
    standard=next(item for item in caps[1]['records'] if item['name']=='STANDARD')
    if failure=='shadow':synonym['local_shadow']=known([['TABLE','VALID']])
    elif failure=='remote_synonym':synonym['synonym']['rows'][0][2]='REMOTE_DB'
    elif failure=='changed_synonym':synonym['synonym']['rows'][0][1]='OTHER'
    elif failure=='missing_grant':dual['privileges']=known([])
    elif failure=='role_only_grant':dual['privileges']=known([['SELECT_CATALOG_ROLE','SELECT']])
    elif failure=='changed_package':standard['ddl']['sha256']='6'*64
    elif failure=='invalid_external':standard['before']['rows'][0][1]=standard['after']['rows'][0][1]='INVALID'
    elif failure=='unknown_external':standard['before']={'state':'UNKNOWN','error_code':'ORA-01031'}
    elif failure=='missing_intrinsic':caps[1]['compiler_runtime']['objects']=known([])
    elif failure=='changed_intrinsic':caps[1]['compiler_runtime']['source_sha256']='7'*64
    elif failure=='effective_argument_drift':
        source_standard=next(item for item in caps[0]['records'] if item['name']=='STANDARD')
        source_standard['arguments']=known([['CALL','NUMBER']])
        standard['arguments']=known([['CALL','DATE']])
    elif failure=='effective_procedure_drift':
        source_standard=next(item for item in caps[0]['records'] if item['name']=='STANDARD')
        source_standard['procedures']=known([['CALL',1,None,'PACKAGE','DEFINER']])
        standard['procedures']=known([['CALL',1,None,'PACKAGE','CURRENT_USER']])
    elif failure=='unknown_arguments':standard['arguments']={'state':'UNKNOWN','error_code':'ORA-01031'}
    op=next(o for o in planned(desired,target,caps).operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED' and op.intent is None


def test_held_relation_creation_cannot_be_bypassed_by_compiler_certificate():
    desired,target,caps=fixture(new_table=True)
    # Metadata read failure remains a held prerequisite even though the unit
    # was VALID on its source database.
    table=next(o for o in desired.objects if o.identity.object_type=='TABLE')
    desired=replace(desired,objects=tuple(replace(o,coverage=replace(o.coverage,ddl='PARTIAL')) if o==table else o for o in desired.objects))
    result=planned(desired,target,caps);op=next(o for o in result.operations if o.identity.name.effective_name=='P')
    assert op.decision=='BLOCKED' and op.intent is None
    assert 'PREREQUISITE_NOT_READY' in op.reason_codes or 'DEPENDENCY_UNVERIFIED' in op.reason_codes


def test_dependency_list_drift_during_collection_cannot_certify_a_unit():
    desired,target,caps=fixture();caps[0]['records'][0]['dependencies_after']=known([])
    op=next(o for o in planned(desired,target,caps).operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED' and op.intent is None


def test_invalid_status_in_original_source_snapshot_cannot_be_overridden_by_fresh_catalog():
    desired,target,caps=fixture()
    objects=[]
    for obj in desired.objects:
        if obj.identity.object_type=='PROCEDURE':
            obj=replace(obj,properties={**obj.properties,'object_status':KnownValue('KNOWN','INVALID',obj.evidence_ids)})
        objects.append(obj)
    desired=replace(desired,objects=tuple(objects))
    op=next(o for o in planned(desired,target,caps).operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED' and op.intent is None


def test_missing_source_status_is_not_implicitly_valid():
    desired,target,caps=fixture()
    desired=replace(desired,objects=tuple(replace(obj,properties={k:v for k,v in obj.properties.items() if k!='object_status'})
                                          if obj.identity.object_type=='PROCEDURE' else obj for obj in desired.objects))
    op=next(o for o in planned(desired,target,caps).operations if o.identity.name.effective_name=='P')
    assert op.decision=='REVIEW_REQUIRED' and op.intent is None
