"""Allowlisted Jenkins owner/target configuration and isolated offline orchestration."""
import json
from dataclasses import replace

import pytest


def settings():
    return {'schemas':['TTBP','INNOVA_ODI'],'target_ids':['LOCAL-TTBP','LOCAL-ODI'],
            'source_url':'https://example.invalid/scm/sky/sky-db.git','source_host':'example.invalid','source_ref':'master',
            'publish':False,'send_email':False,'apply_sql':False,'job_url':'https://jenkins.example/job/generator/'}


def test_settings_allow_two_owners_with_sorted_target_selection_and_legacy_support():
    from tools.jenkins_run import validate_settings,selected_target_ids
    assert validate_settings(settings())==settings()
    assert selected_target_ids(settings())==('LOCAL-ODI','LOCAL-TTBP')
    legacy={**settings(),'schemas':['INNOVA_ODI'],'target_id':'LOCAL-ODI'};legacy.pop('target_ids')
    assert selected_target_ids(validate_settings(legacy))==('LOCAL-ODI',)


@pytest.mark.parametrize('change',[{'schemas':[]},{'schemas':['TTBP','OTHER']},{'schemas':['TTBP','TTBP']},
    {'target_ids':['LOCAL-ODI']},{'target_ids':['LOCAL-TTBP','LOCAL-TTBP']},{'target_ids':['LOCAL-OTHER']},
    {'target_id':'LOCAL-ODI'},{'apply_sql':True}])
def test_scope_rejects_unapproved_or_mismatched_owner_target_selection(change):
    from tools.jenkins_run import validate_settings
    with pytest.raises(ValueError,match='JENKINS_SCOPE_INVALID'):validate_settings({**settings(),**change})


def test_metadata_config_requires_owner_specific_credentials_and_supports_legacy():
    from tools.jenkins_run import metadata_sources
    endpoint={'host':'oracle.example.invalid','port':1521,'service_name':'demo'}
    modern={'sources':[{'schema':'TTBP','endpoint':endpoint,'credential_id':'GENERATOR_SOURCE_TTBP'},
                        {'schema':'INNOVA_ODI','endpoint':endpoint,'credential_id':'GENERATOR_SOURCE_ODI'}]}
    assert [item['schema'] for item in metadata_sources(modern,settings()['schemas'])]==['INNOVA_ODI','TTBP']
    assert metadata_sources({'endpoint':endpoint,'credential_id':'GENERATOR_SOURCE_ODI'},['INNOVA_ODI'])[0]['schema']=='INNOVA_ODI'
    for bad in [modern['sources'][:1],[modern['sources'][0]]*2,
                [{**modern['sources'][0],'credential_id':'GENERATOR_SOURCE_ODI'},modern['sources'][1]]]:
        with pytest.raises(ValueError,match='JENKINS_SCOPE_INVALID'):metadata_sources({'sources':bad},settings()['schemas'])


def test_report_start_time_uses_jenkins_build_start_and_rejects_unsafe_values(monkeypatch):
    from tools.jenkins_run import build_started_at
    monkeypatch.setenv('GENERATOR_BUILD_STARTED_AT_MS','1792440000000')
    assert build_started_at()=='2026-10-19T20:00:00+00:00'
    monkeypatch.setenv('GENERATOR_BUILD_STARTED_AT_MS','NaN')
    with pytest.raises(ValueError,match='JENKINS_BUILD_START_INVALID'):build_started_at()


@pytest.mark.parametrize('unavailable',[False,True])
@pytest.mark.parametrize('prepare_code',[0,10,30])
def test_two_owner_runner_prepares_once_enriches_before_capture_and_preserves_failed_target(tmp_path,monkeypatch,unavailable,prepare_code):
    import hashlib
    from tools import jenkins_run,jenkins_source_semantics
    from tests.factories import profile,ROOT
    from tests.unit.test_jenkins_source_semantics import observation
    from oracle_db_migration_generator.config.models import SchemaRoot
    from oracle_db_migration_generator.model.snapshot import Coverage
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.source.models import SourceArtifact,SourceInput,SourceRevision
    from oracle_db_migration_generator.oracle.collector import TargetObservation
    from oracle_db_migration_generator.runtime.worker import run_target as real_run_target
    selected=replace(profile(),schema_roots=(SchemaRoot('odi','INNOVA_ODI'),SchemaRoot('ttbp','TTBP')),source_length_semantics='UNKNOWN')
    artifacts=[]
    for owner in settings()['schemas']:
        raw=f'CREATE TABLE {owner}.T (C VARCHAR2(20));'.encode()
        root='odi' if owner=='INNOVA_ODI' else 'ttbp'
        artifacts.append(SourceArtifact(root+'/table.sql',owner,'DDL','TABLE',raw,hashlib.sha256(raw).hexdigest()))
    source=parse_source(SourceInput(SourceRevision('a'*40,None),tuple(artifacts),'b'*64),selected)
    prepared_partial=prepare_code==10
    if prepared_partial:
        source=replace(source,completeness=Coverage('PARTIAL','PARTIAL','NOT_APPLICABLE',('SOURCE_FILE_UNPARSED',)))
    config=tmp_path/'release/config';config.mkdir(parents=True)
    document=json.loads((ROOT/'examples/source-profile.example.json').read_bytes())
    document['schema_roots']=[{'path':'odi','source_schema':'INNOVA_ODI'},{'path':'ttbp','source_schema':'TTBP'}]
    document['source_length_semantics']='UNKNOWN'
    (config/'source-profile.json').write_text(json.dumps(document));(config/'job-settings.json').write_text(json.dumps(settings()))
    endpoint={'host':'oracle.example.invalid','port':1521,'service_name':'demo'}
    targets=[];sources=[]
    for owner,key,suffix in [('INNOVA_ODI','LOCAL-ODI','ODI'),('TTBP','LOCAL-TTBP','TTBP')]:
        targets.append({'id':key,'name':key,'enabled':True,'endpoint':endpoint,'driver_mode':'thin',
                        'schema_mappings':[{'source_schema':owner,'target_schema':owner,'credential_id':'TARGET_'+suffix}]})
        sources.append({'schema':owner,'endpoint':endpoint,'credential_id':'GENERATOR_SOURCE_'+suffix})
        for credential in ['TARGET_'+suffix,'GENERATOR_SOURCE_'+suffix]:
            monkeypatch.setenv(credential+'_USER',owner);monkeypatch.setenv(credential+'_PASSWORD','synthetic-'+owner)
    (config/'targets.json').write_text(json.dumps({'schema_version':'targets/1.0','targets':targets}))
    (config/'source-metadata.json').write_text(json.dumps({'sources':sources}))
    monkeypatch.setenv('BUILD_NUMBER','42');monkeypatch.setenv('BUILD_URL',settings()['job_url']+'42/')
    monkeypatch.setenv('GENERATOR_BUILD_STARTED_AT_MS','1792440000000')
    monkeypatch.setattr('oracledb.connect',lambda *a,**kw:pytest.fail('Live Oracle access forbidden'))
    assert jenkins_run.main(['--release',str(config.parent),'--output',str(tmp_path/'environment'),
        '--mode','ENVIRONMENT_CHECK'])==0
    assert json.loads((tmp_path/'environment/environment-check.json').read_bytes())['database_connections']==0
    phases=[]
    def prepare(argv):
        phases.append('prepare');path=__import__('pathlib').Path(argv[argv.index('--output')+1]);path.mkdir(parents=True)
        (path/'source-snapshot.json').write_text(json.dumps(source.to_dict()))
        return prepare_code
    monkeypatch.setattr('oracle_db_migration_generator.cli.main',prepare)
    monkeypatch.setattr('oracle_db_migration_generator.model.snapshot_io.load_snapshot',lambda *a,**kw:source)
    def capture(target,credentials,*,owner):
        assert credentials.username==owner and credentials.password=='synthetic-'+owner
        phases.append('source-'+owner)
        if unavailable and owner=='INNOVA_ODI':raise ValueError('secret Oracle DSN synthetic-password')
        return {**observation(),'owner':owner,'started_at':'2026-10-20T00:00:00Z','finished_at':'2026-10-20T00:00:01Z'}
    monkeypatch.setattr(jenkins_source_semantics,'capture_source_metadata',capture)
    def collect(target,credentials,profile,*,source,progress):
        owner=target.schema_mappings[0].source_schema
        assert source.schemas==(owner,)
        assert {obj.identity.owner.effective_name for obj in source.objects}=={owner}
        assert credentials(target.schema_mappings[0].credential_id).username==owner
        phases.append('target-'+owner)
        for obj in source.objects:
            semantics=next(iter(obj.properties['projection'].value['columns'].values()))['length_semantics']
            assert semantics==(None if unavailable and obj.identity.owner.effective_name=='INNOVA_ODI' else 'BYTE')
            if unavailable and obj.identity.owner.effective_name=='INNOVA_ODI':
                from oracle_db_migration_generator.compare.projection_adapter import table_columns
                assert table_columns(obj,source)['C']['length_semantics'].state=='UNKNOWN'
        receipt={'status':'FAILED' if owner=='INNOVA_ODI' else 'CAPTURED','finished_at':'2026-10-20T00:00:02Z',
                 'schemas':[{'error_code':'ORA-01031'}] if owner=='INNOVA_ODI' else []}
        if owner=='INNOVA_ODI':return TargetObservation(None,receipt)
        objects=tuple(replace(obj,coverage=Coverage('COMPLETE','COMPLETE','COMPLETE')) for obj in source.objects if obj.identity.owner.effective_name==owner)
        actual=replace(source,side='TARGET',source_commit=None,target_id=target.id,schemas=(owner,),objects=objects,
                       completeness=Coverage('COMPLETE','COMPLETE','COMPLETE'),observed_consistency='OBSERVED_STABLE')
        return TargetObservation(actual,receipt)
    monkeypatch.setattr('oracle_db_migration_generator.runtime.worker.run_target',lambda *a,**kw:real_run_target(*a,**kw,collect=collect))
    import tools.jenkins_notification as notification
    monkeypatch.setattr(notification,'write_notification',lambda *a,**kw:None)
    output=tmp_path/'output/runs/build-42'
    arguments=['--release',str(config.parent),'--source-dir',str(tmp_path/'source'),
        '--source-commit','a'*40,'--output',str(output),'--mode','COMPARE']
    if prepare_code==30:
        with pytest.raises(ValueError,match='SOURCE_PREPARATION_FAILED'):jenkins_run.main(arguments)
        assert phases==['prepare'] and not (output/'run.json').exists()
        return
    code=jenkins_run.main(arguments)
    run=json.loads((output/'run.json').read_bytes())
    assert phases==['prepare','source-INNOVA_ODI','source-TTBP','target-INNOVA_ODI','target-TTBP']
    assert code==10 and [(item['id'],item['status']) for item in run['targets']]==[('LOCAL-ODI','ERROR'),('LOCAL-TTBP','BLOCKED' if prepared_partial else 'NO_CHANGE')]
    if prepared_partial:
        assert run['targets'][1]['difference_count'] is None
        plan=json.loads((output/'targets/LOCAL-TTBP/plan.json').read_bytes())
        assert plan['scope']['inventory']==plan['scope']['ddl']=='PARTIAL'
    assert run['started_at']=='2026-10-19T20:00:00+00:00' and run['build_url']==settings()['job_url']+'42/'
    preparation=json.loads((output/'source-preparation.json').read_bytes())
    assert preparation['preparation_exit_code']==prepare_code
    assert preparation['inventory']==('PARTIAL' if prepared_partial else 'COMPLETE')
    assert len(preparation['snapshot_sha256'])==64
    scopes=json.loads((output/'source-scopes.json').read_bytes())['targets']
    assert [item['target_id'] for item in scopes]==['LOCAL-ODI','LOCAL-TTBP']
    assert all(item['proof']['status']==('UNVERIFIED' if prepared_partial else 'VERIFIED') for item in scopes)
    assert (output/'source-metadata-receipt.INNOVA_ODI.json').is_file() and (output/'source-metadata-receipt.TTBP.json').is_file()
    if unavailable:
        receipt=json.loads((output/'source-metadata-receipt.INNOVA_ODI.json').read_bytes())
        assert receipt['status']=='UNAVAILABLE' and receipt['error_code']=='CONNECTION_OR_METADATA_ERROR'
        assert 'synthetic-password' not in json.dumps(receipt)


@pytest.mark.parametrize('case',['profile-owner','target-owner','remap','shared-credential','other-endpoint','duplicate-mapping'])
def test_scope_requires_exact_owner_per_target_and_independent_credentials(case):
    from tools.jenkins_run import validate_scope
    from tests.factories import profile
    from oracle_db_migration_generator.config.models import SchemaRoot,Endpoint,TargetConfig,SchemaMapping
    selected=replace(profile(),schema_roots=(SchemaRoot('odi','INNOVA_ODI'),SchemaRoot('ttbp','TTBP')))
    endpoint=Endpoint('oracle.example.invalid',1521,service_name='demo')
    targets=[TargetConfig('LOCAL-ODI','ODI',True,endpoint,'thin',(SchemaMapping('INNOVA_ODI','INNOVA_ODI','TARGET_ODI'),)),
             TargetConfig('LOCAL-TTBP','TTBP',True,endpoint,'thin',(SchemaMapping('TTBP','TTBP','TARGET_TTBP'),))]
    validate_scope(selected,tuple(targets),settings())
    if case=='profile-owner':selected=replace(selected,schema_roots=(SchemaRoot('odi','INNOVA_ODI'),))
    if case=='target-owner':targets[1]=replace(targets[1],schema_mappings=(SchemaMapping('INNOVA_ODI','INNOVA_ODI','TARGET_TTBP'),))
    if case=='remap':targets[1]=replace(targets[1],schema_mappings=(SchemaMapping('TTBP','INNOVA_ODI','TARGET_TTBP'),))
    if case=='shared-credential':targets[1]=replace(targets[1],schema_mappings=(SchemaMapping('TTBP','TTBP','TARGET_ODI'),))
    if case=='other-endpoint':targets[1]=replace(targets[1],endpoint=replace(endpoint,host='other.example.invalid'))
    if case=='duplicate-mapping':targets[1]=replace(targets[1],schema_mappings=targets[1].schema_mappings*2)
    with pytest.raises(ValueError,match='JENKINS_SCOPE_INVALID'):validate_scope(selected,tuple(targets),settings())
