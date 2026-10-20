import json
from copy import deepcopy

import pytest

from tests.factories import ROOT
from tests.unit.test_jenkins_multi_schema import settings


def release_config(tmp_path):
    root=tmp_path/'release';config=root/'config';config.mkdir(parents=True)
    profile=json.loads((ROOT/'examples/source-profile.example.json').read_bytes())
    profile['schema_roots']=[{'path':owner.lower(),'source_schema':owner} for owner in ('INNOVA_ODI','TTBP')]
    sample=json.loads((ROOT/'examples/targets.example.json').read_bytes())['targets'][0]
    targets=[];sources=[]
    for owner,target_id,credential in (('INNOVA_ODI','LOCAL-ODI','GENERATOR_INNOVA_ODI'),('TTBP','LOCAL-TTBP','GENERATOR_TTBP')):
        target=deepcopy(sample);target.update(id=target_id,name=owner)
        target['schema_mappings']=[{'source_schema':owner,'target_schema':owner,'credential_id':credential}]
        if owner=='TTBP':target['schema_mappings'][0]['metadata_reader']='INNOVA_ODI'
        targets.append(target)
        sources.append({'schema':owner,'endpoint':target['endpoint'],'credential_id':'GENERATOR_SOURCE_'+('ODI' if owner=='INNOVA_ODI' else 'TTBP')})
    for name,data in {'source-profile.json':profile,'targets.json':{'schema_version':'targets/1.0','targets':targets},'job-settings.json':settings(),'source-metadata.json':{'sources':sources}}.items():
        (config/name).write_text(json.dumps(data),encoding='utf-8')
    return root


@pytest.mark.parametrize('schema,expected_id',[(None,'LOCAL-TTBP'),('INNOVA_ODI','LOCAL-ODI')])
def test_default_is_only_ttbp_and_odi_requires_explicit_selection(tmp_path,schema,expected_id):
    from tools.jenkins_scope import prepare_scope
    from oracle_db_migration_generator.config.loader import load_source_profile,load_targets
    from tools.jenkins_run import environment_check,validate_settings,validate_scope,metadata_sources
    release=release_config(tmp_path);before={p.name:p.read_bytes() for p in (release/'config').iterdir()}
    output=tmp_path/'scope'
    proof=prepare_scope(release,output,**({'schema':schema} if schema else {}))
    selected=schema or 'TTBP';config=output/'config'
    selected_settings=validate_settings(json.loads((config/'job-settings.json').read_bytes()))
    profile=load_source_profile(config/'source-profile.json');targets=load_targets(config/'targets.json',(expected_id,))
    validate_scope(profile,targets,selected_settings)
    assert targets[0].name=='PROD'
    assert selected_settings['schemas']==[selected] and selected_settings['target_ids']==[expected_id]
    assert [root.source_schema for root in profile.schema_roots]==[selected]
    assert [item['schema'] for item in metadata_sources(json.loads((config/'source-metadata.json').read_bytes()),[selected])]==[selected]
    assert len(json.loads((config/'targets.json').read_bytes())['targets'])==1
    assert environment_check(profile,[selected])['database_connections']==0
    assert proof['schemas']==[selected] and proof['target_ids']==[expected_id] and proof['read_only'] is True
    if selected=='TTBP':assert targets[0].schema_mappings[0].metadata_reader=='INNOVA_ODI'
    assert {p.name:p.read_bytes() for p in (release/'config').iterdir()}==before


def test_unapproved_schema_and_existing_output_are_rejected_before_writes(tmp_path):
    from tools.jenkins_scope import prepare_scope
    release=release_config(tmp_path);output=tmp_path/'scope'
    with pytest.raises(ValueError,match='JENKINS_SCHEMA_SELECTION_INVALID'):prepare_scope(release,output,schema='OTHER')
    assert not output.exists()
    output.mkdir();marker=output/'keep';marker.write_text('unchanged')
    with pytest.raises(ValueError,match='JENKINS_SCOPE_OUTPUT_UNSAFE'):prepare_scope(release,output)
    assert marker.read_text()=='unchanged'
