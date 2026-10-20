"""Trusted Jenkins entry point. It never applies SQL, pushes Git or sends mail."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


def validate_settings(settings):
    p=urlsplit(settings['source_url'])
    if (settings['schemas']!=['INNOVA_ODI'] or settings['target_id']!='LOCAL-ODI'
        or any(settings.get(k) is not False for k in ('publish','send_email','apply_sql'))
        or p.scheme!='https' or p.hostname!=settings['source_host'] or p.username or p.password or p.query or p.fragment
        or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,100}',settings['source_ref']) or '..' in settings['source_ref']):
        raise ValueError('JENKINS_SCOPE_INVALID')
    return settings


def environment_check(profile,schemas):
    import oracledb
    import jinja2,jsonschema,antlr4
    if not (3,11)<=sys.version_info[:2]<=(3,13):raise ValueError('PYTHON_VERSION_UNSUPPORTED')
    return {'status':'ENVIRONMENT_VERIFIED','python_supported':True,'python':'.'.join(map(str,sys.version_info[:3])),
            'schemas':list(schemas),'database_connections':0,'read_only':True,'sql_execution':'NOT_IMPLEMENTED'}


def main(argv=None):
    from oracle_db_migration_generator.artifacts.bundle import verify_bundle
    from oracle_db_migration_generator.cli import main as cli
    from oracle_db_migration_generator.config.loader import load_source_profile,load_targets
    from oracle_db_migration_generator.config.credentials import EnvCredentialResolver
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    from oracle_db_migration_generator.model.snapshot_io import load_snapshot
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.runtime.worker import run_target
    from oracle_db_migration_generator.oracle.preflight import safe_error_code
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--source-dir',type=Path);parser.add_argument('--source-commit');parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=('ENVIRONMENT_CHECK','COMPARE'),required=True);args=parser.parse_args(argv)
    config=args.release/'config';settings=validate_settings(json.loads((config/'job-settings.json').read_bytes()))
    profile=load_source_profile(config/'source-profile.json');targets=load_targets(config/'targets.json',('LOCAL-ODI',))
    if len(targets)!=1 or any(m.source_schema!='INNOVA_ODI' or m.target_schema!='INNOVA_ODI' for t in targets for m in t.schema_mappings):raise ValueError('JENKINS_SCOPE_INVALID')
    output=args.output.resolve()
    if output.exists():raise ValueError('JENKINS_OUTPUT_EXISTS')
    output.mkdir(parents=True)
    check=environment_check(profile,settings['schemas'])
    (output/'environment-check.json').write_bytes(canonical_bytes(check)+b'\n')
    print(json.dumps(check),flush=True)
    if args.mode=='ENVIRONMENT_CHECK':return 0
    if not args.source_commit or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',args.source_commit):raise ValueError('SOURCE_SHA_REQUIRED')
    if args.source_dir is None:raise ValueError('SOURCE_CHECKOUT_REQUIRED')
    prepared=output.parent/'source-snapshots'/('build-'+os.environ['BUILD_NUMBER'])
    rc=cli(['prepare-source','--repo',str(args.source_dir),'--ref',args.source_commit,'--source-profile',str(config/'source-profile.json'),'--output',str(prepared)])
    if rc:raise ValueError('SOURCE_PREPARATION_FAILED')
    source=load_snapshot(prepared/'source-snapshot.json',require_ddl=True)
    from jenkins_source_semantics import capture_source_metadata,reconcile_source
    from oracle_db_migration_generator.config.models import Endpoint,TargetConfig
    metadata=json.loads((config/'source-metadata.json').read_bytes())
    if set(metadata)!={'endpoint','credential_id'} or metadata['credential_id']!='GENERATOR_SOURCE_ODI':raise ValueError('JENKINS_SCOPE_INVALID')
    source_target=TargetConfig('SOURCE-METADATA','Source metadata',True,Endpoint(**metadata['endpoint']),'thin',())
    try:
        capture=capture_source_metadata(source_target,EnvCredentialResolver()(metadata['credential_id']))
        source,proof=reconcile_source(source,capture,prepared)
        import hashlib
        (output/'source-metadata-receipt.json').write_bytes(canonical_bytes({'status':capture['status'],'read_only':True,
            'started_at':capture['started_at'],'finished_at':capture['finished_at'],
            'capture_sha256':hashlib.sha256(canonical_bytes(capture)).hexdigest()})+b'\n')
        (prepared/'metadata/source-observation.json').write_bytes(canonical_bytes(capture)+b'\n')
        (output/'source-semantics.json').write_bytes(canonical_bytes(proof)+b'\n')
        (prepared/'source-snapshot.enriched.json').write_bytes(canonical_bytes(source.to_dict())+b'\n')
        print(json.dumps({'phase':'source_metadata_correspondence','matched_tables':proof['matched_tables'],
                          'rejected_tables':len(proof['rejected_tables']),'read_only':True}),flush=True)
    except Exception as error:
        print(json.dumps({'phase':'source_metadata_correspondence','status':'UNAVAILABLE',
                          'error_code':safe_error_code(error),'read_only':True}),flush=True)
    target=targets[0]
    result=run_target(source,target,profile,EnvCredentialResolver(),output,
                     progress=lambda i,n: print(json.dumps({'phase':'read_only_target_metadata','processed':i,'total':n}),flush=True) if i%50==0 else None)
    run=aggregate_run(output,source_commit=source.source_commit,build_number=int(os.environ['BUILD_NUMBER']),build_url=os.environ['BUILD_URL'])
    if result['plan_path']:verify_bundle(output/result['plan_path'].rsplit('/',1)[0])
    from jenkins_notification import write_notification
    write_notification(output,run,os.environ['BUILD_URL'],settings['job_url'])
    print(json.dumps({'status':run['status'],'target_status':result['status'],'run_id':run['run_id'],
                      'difference_count':result['difference_count'],'read_only':True,'execution_status':'NOT_EXECUTED'}),flush=True)
    return run['exit_code']


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError):
        print(json.dumps({'status':'FAILED','error_code':'GENERATOR_JENKINS_INPUT_OR_INTEGRITY_ERROR'}));raise SystemExit(30)
