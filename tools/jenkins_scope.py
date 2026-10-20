"""Select one approved schema in a per-build config; trusted release stays immutable."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def prepare_scope(release,output,*,schema='TTBP'):
    if schema not in {'TTBP','INNOVA_ODI'}:raise ValueError('JENKINS_SCHEMA_SELECTION_INVALID')
    release=Path(release).resolve();output=Path(output).resolve()
    if output.exists() or output.is_relative_to(release):raise ValueError('JENKINS_SCOPE_OUTPUT_UNSAFE')
    from oracle_db_migration_generator.config.loader import load_source_profile,load_targets
    try:
        from tools.jenkins_run import validate_settings,selected_target_ids,validate_scope,metadata_sources,TARGET_OWNERS
    except ModuleNotFoundError:
        sys.path.insert(0,str(release))
        from jenkins_run import validate_settings,selected_target_ids,validate_scope,metadata_sources,TARGET_OWNERS
    config=release/'config'
    read=lambda name:json.loads((config/name).read_bytes())
    settings=validate_settings(read('job-settings.json'))
    profile=load_source_profile(config/'source-profile.json')
    targets=load_targets(config/'targets.json',selected_target_ids(settings))
    validate_scope(profile,targets,settings)
    sources=metadata_sources(read('source-metadata.json'),settings['schemas'])
    if schema not in settings['schemas']:raise ValueError('JENKINS_SCHEMA_SELECTION_UNAVAILABLE')
    target_id=next(key for key,owner in TARGET_OWNERS.items() if owner==schema)
    profile_document=read('source-profile.json');target_document=read('targets.json')
    profile_document['schema_roots']=[root for root in profile_document['schema_roots'] if root['source_schema']==schema]
    target_document['targets']=[target for target in target_document['targets'] if target['id']==target_id]
    for target in target_document['targets']:target['name']='PROD'
    settings.pop('target_id',None);settings.update(schemas=[schema],target_ids=[target_id])
    documents={'job-settings.json':settings,'source-profile.json':profile_document,
               'targets.json':target_document,'source-metadata.json':{'sources':[row for row in sources if row['schema']==schema]}}
    shutil.copytree(config,output/'config')
    for name,document in documents.items():
        (output/'config'/name).write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    validate_scope(load_source_profile(output/'config/source-profile.json'),
                   load_targets(output/'config/targets.json',(target_id,)),validate_settings(settings))
    metadata_sources(documents['source-metadata.json'],[schema])
    proof={'target_name':'PROD','schemas':[schema],'target_ids':[target_id],'read_only':True,'database_connections':0,
           'config_sha256':{name:hashlib.sha256((output/'config'/name).read_bytes()).hexdigest() for name in sorted(documents)}}
    (output/'scope-receipt.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return proof


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--schema',choices=('TTBP','INNOVA_ODI'),default='TTBP')
    args=parser.parse_args()
    print(json.dumps(prepare_scope(args.release,args.output,schema=args.schema)))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,StopIteration):
        print(json.dumps({'status':'FAILED','error_code':'JENKINS_SCOPE_CONFIGURATION_ERROR'}))
        raise SystemExit(30)
