"""Trusted Jenkins entry point. It never applies SQL, pushes Git or sends mail."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

TARGET_OWNERS={'LOCAL-ODI':'INNOVA_ODI','LOCAL-TTBP':'TTBP'}
SOURCE_CREDENTIALS={'INNOVA_ODI':'GENERATOR_SOURCE_ODI','TTBP':'GENERATOR_SOURCE_TTBP'}


def selected_target_ids(settings):
    values=settings.get('target_ids') if 'target_ids' in settings else [settings.get('target_id')]
    if (not isinstance(values,list) or not values or any(not isinstance(item,str) or item not in TARGET_OWNERS for item in values)
        or len(set(values))!=len(values) or ('target_ids' in settings and 'target_id' in settings)):
        raise ValueError('JENKINS_SCOPE_INVALID')
    return tuple(sorted(values))


def validate_settings(settings):
    selected=selected_target_ids(settings);schemas=settings['schemas']
    p=urlsplit(settings['source_url'])
    if (not isinstance(schemas,list) or not schemas or any(not isinstance(owner,str) for owner in schemas)
        or len(set(schemas))!=len(schemas) or set(schemas)!={TARGET_OWNERS[key] for key in selected}
        or any(settings.get(k) is not False for k in ('publish','send_email','apply_sql'))
        or p.scheme!='https' or p.hostname!=settings['source_host'] or p.username or p.password or p.query or p.fragment
        or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,100}',settings['source_ref']) or '..' in settings['source_ref']):
        raise ValueError('JENKINS_SCOPE_INVALID')
    return settings


def metadata_sources(metadata,schemas):
    if set(metadata)=={'endpoint','credential_id'}:
        if set(schemas)!={'INNOVA_ODI'}:raise ValueError('JENKINS_SCOPE_INVALID')
        records=[{'schema':'INNOVA_ODI',**metadata}]
    elif set(metadata)=={'sources'} and isinstance(metadata['sources'],list):records=metadata['sources']
    else:raise ValueError('JENKINS_SCOPE_INVALID')
    seen=set()
    for record in records:
        if not isinstance(record,dict) or set(record)!={'schema','endpoint','credential_id'}:
            raise ValueError('JENKINS_SCOPE_INVALID')
        owner=record['schema'];endpoint=record['endpoint']
        if owner not in schemas or owner in seen or record['credential_id']!=SOURCE_CREDENTIALS.get(owner):
            raise ValueError('JENKINS_SCOPE_INVALID')
        if (not isinstance(endpoint,dict) or not {'host','port'}<=set(endpoint)
            or set(endpoint)-{'host','port','sid','service_name'} or ('sid' in endpoint)==('service_name' in endpoint)
            or not isinstance(endpoint['host'],str) or not endpoint['host']
            or any(c.isspace() or c in '/@\\:' for c in endpoint['host'])
            or type(endpoint['port']) is not int or not 1<=endpoint['port']<=65535
            or any(not isinstance(value,str) or not value for key,value in endpoint.items() if key in {'sid','service_name'})):
            raise ValueError('JENKINS_SCOPE_INVALID')
        seen.add(owner)
    if seen!=set(schemas):raise ValueError('JENKINS_SCOPE_INVALID')
    return tuple(sorted(records,key=lambda item:item['schema']))


def validate_scope(profile,targets,settings):
    owners=[root.source_schema for root in profile.schema_roots]
    if len(set(owners))!=len(owners) or set(owners)!=set(settings['schemas']):raise ValueError('JENKINS_SCOPE_INVALID')
    if tuple(target.id for target in targets)!=selected_target_ids(settings):raise ValueError('JENKINS_SCOPE_INVALID')
    credential_ids=[]
    for target in targets:
        expected=TARGET_OWNERS[target.id]
        if len(target.schema_mappings)!=1:raise ValueError('JENKINS_SCOPE_INVALID')
        mapping=target.schema_mappings[0]
        if mapping.source_schema!=expected or mapping.target_schema!=expected:raise ValueError('JENKINS_SCOPE_INVALID')
        credential_ids.append(mapping.credential_id)
    if len(set(credential_ids))!=len(credential_ids):raise ValueError('JENKINS_SCOPE_INVALID')
    if len({target.endpoint for target in targets})!=1:raise ValueError('JENKINS_SCOPE_INVALID')


def build_started_at():
    raw=os.environ.get('GENERATOR_BUILD_STARTED_AT_MS')
    if raw is None:return datetime.now(timezone.utc).isoformat()
    if not re.fullmatch(r'[0-9]{1,16}',raw):raise ValueError('JENKINS_BUILD_START_INVALID')
    try:
        result=datetime.fromtimestamp(int(raw)/1000,timezone.utc)
        if result>datetime.now(timezone.utc):raise ValueError('JENKINS_BUILD_START_INVALID')
        return result.isoformat()
    except (ValueError,OverflowError,OSError):raise ValueError('JENKINS_BUILD_START_INVALID') from None


def environment_check(profile,schemas):
    import oracledb
    import jinja2,jsonschema,antlr4
    if not (3,11)<=sys.version_info[:2]<=(3,13):raise ValueError('PYTHON_VERSION_UNSUPPORTED')
    return {'status':'ENVIRONMENT_VERIFIED','python_supported':True,'python':'.'.join(map(str,sys.version_info[:3])),
            'schemas':list(schemas),'database_connections':0,'read_only':True,'sql_execution':'NOT_IMPLEMENTED'}


def initialize_oracle_driver(targets,client_dir):
    import oracledb
    modes={target.driver_mode for target in targets}
    if modes=={'thin'}:return 'thin'
    if modes!={'thick'}:raise ValueError('JENKINS_ORACLE_DRIVER_MIXED_MODES')
    if not client_dir or not Path(client_dir).is_dir():raise ValueError('JENKINS_ORACLE_DRIVER_CLIENT_REQUIRED')
    try:
        oracledb.init_oracle_client(lib_dir=str(Path(client_dir).resolve()))
    except Exception:
        raise ValueError('JENKINS_ORACLE_DRIVER_CLIENT_LOAD_FAILED') from None
    if oracledb.is_thin_mode():raise ValueError('JENKINS_ORACLE_DRIVER_MODE_MISMATCH')
    return 'thick'


def reuse_prepared_source(cached,prepared,source_dir,commit,profile,*,snapshot_sha256):
    """Import a prior same-job source, checking every input against pinned Git.

    Only the explicit resume invocation uses this. Fresh owner metadata is
    still collected below; PARTIAL and UNKNOWN facts are never upgraded.
    """
    import hashlib
    from oracle_db_migration_generator.config.loader import load_source_profile,read_json
    from oracle_db_migration_generator.model.serialization import digest
    from oracle_db_migration_generator.model.snapshot_io import load_snapshot,safe_path,write_source_snapshot
    from oracle_db_migration_generator.source.git_reader import GitRepository,resolve_source,read_source
    cached=Path(cached).absolute();prepared=Path(prepared).absolute()
    old=re.fullmatch(r'build-([1-9][0-9]*)',cached.name)
    new=re.fullmatch(r'build-([1-9][0-9]*)',prepared.name)
    if (not old or not new or int(old[1])>=int(new[1]) or cached.parent!=prepared.parent
            or prepared.exists() or not cached.is_dir()
            or any(path.is_symlink() for path in (cached,*cached.parents))):
        raise ValueError('SOURCE_REUSE_INVALID')
    for name in ('source-snapshot.json','source-input.json','source-profile.json'):
        if (cached/name).is_symlink() or not (cached/name).is_file():raise ValueError('SOURCE_REUSE_INVALID')
    actual_sha=hashlib.sha256((cached/'source-snapshot.json').read_bytes()).hexdigest()
    if not isinstance(snapshot_sha256,str) or not re.fullmatch(r'[a-f0-9]{64}',snapshot_sha256) or actual_sha!=snapshot_sha256:
        raise ValueError('SOURCE_REUSE_SNAPSHOT_MISMATCH')
    if load_source_profile(cached/'source-profile.json')!=profile:raise ValueError('SOURCE_REUSE_PROFILE_MISMATCH')
    snapshot=load_snapshot(cached/'source-snapshot.json',require_ddl=True)
    if read_json(cached/'source-snapshot.json').get('semantic_digest')!=snapshot.semantic_digest:
        raise ValueError('SOURCE_REUSE_SNAPSHOT_MISMATCH')
    inputs=read_source(resolve_source(GitRepository(source_dir),commit),profile)
    manifest=read_json(cached/'source-input.json')
    expected={'source_commit':commit,'input_digest':inputs.input_digest,
              'files':[{'path':item.path,'sha256':item.sha256} for item in inputs.artifacts]}
    if (manifest!=expected or snapshot.side!='SOURCE' or snapshot.source_commit!=commit
            or snapshot.schemas!=tuple(root.source_schema for root in profile.schema_roots)):
        raise ValueError('SOURCE_REUSE_INPUT_MISMATCH')
    for key,value in (('source_profile_sha256',digest(profile)),('source_input_digest',inputs.input_digest)):
        recorded=snapshot.capabilities.get(key)
        if recorded is None or recorded.state!='KNOWN' or recorded.value!=value:
            raise ValueError('SOURCE_REUSE_INPUT_MISMATCH')
    for item in inputs.artifacts:
        path=safe_path(cached,item.path)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p.is_relative_to(cached)):
            raise ValueError('SOURCE_REUSE_INVALID')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item.sha256:
            raise ValueError('SOURCE_REUSE_BLOB_MISMATCH')
    write_source_snapshot(snapshot,inputs,prepared)
    imported=load_snapshot(prepared/'source-snapshot.json',require_ddl=True)
    if imported.semantic_digest!=snapshot.semantic_digest:raise ValueError('SOURCE_REUSE_INPUT_MISMATCH')
    return imported,{'status':'REUSED_VERIFIED','origin_build':int(old[1]),'source_commit':commit,
        'source_input_digest':inputs.input_digest,'source_semantic_digest':snapshot.semantic_digest,
        'snapshot_sha256':actual_sha,
        'inventory':snapshot.completeness.inventory,'ddl':snapshot.completeness.ddl,'read_only':True}


def main(argv=None):
    import hashlib
    started=build_started_at()
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
    parser.add_argument('--prepared-source',type=Path)
    parser.add_argument('--prepared-source-sha256')
    parser.add_argument('--mode',choices=('ENVIRONMENT_CHECK','COMPARE'),required=True);args=parser.parse_args(argv)
    config=args.release/'config';settings=validate_settings(json.loads((config/'job-settings.json').read_bytes()))
    profile=load_source_profile(config/'source-profile.json');targets=load_targets(config/'targets.json',selected_target_ids(settings))
    validate_scope(profile,targets,settings)
    output=args.output.resolve()
    if output.exists():raise ValueError('JENKINS_OUTPUT_EXISTS')
    output.mkdir(parents=True)
    check=environment_check(profile,settings['schemas'])
    (output/'environment-check.json').write_bytes(canonical_bytes(check)+b'\n')
    print(json.dumps(check),flush=True)
    if args.mode=='ENVIRONMENT_CHECK':return 0
    if not args.source_commit or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',args.source_commit):raise ValueError('SOURCE_SHA_REQUIRED')
    if args.source_dir is None:raise ValueError('SOURCE_CHECKOUT_REQUIRED')
    if (args.prepared_source is None)!=(args.prepared_source_sha256 is None):raise ValueError('SOURCE_REUSE_PIN_REQUIRED')
    prepared=output.parent/'source-snapshots'/('build-'+os.environ['BUILD_NUMBER'])
    if args.prepared_source is not None:
        source,proof=reuse_prepared_source(args.prepared_source,prepared,args.source_dir,args.source_commit,profile,
                                         snapshot_sha256=args.prepared_source_sha256)
        (output/'source-preparation.json').write_bytes(canonical_bytes(proof)+b'\n')
        print(json.dumps({'phase':'source_preparation',**proof}),flush=True)
    else:
        rc=cli(['prepare-source','--repo',str(args.source_dir),'--ref',args.source_commit,'--source-profile',str(config/'source-profile.json'),'--output',str(prepared)])
        # 10 means a saved PARTIAL source, not a failed preparation. Preserve its
        # UNKNOWN/coverage evidence and let both targets produce honest reports.
        if rc not in {0,10}:raise ValueError('SOURCE_PREPARATION_FAILED')
        source=load_snapshot(prepared/'source-snapshot.json',require_ddl=True)
        proof={'status':'PREPARED_VERIFIED','source_commit':source.source_commit,
            'source_semantic_digest':source.semantic_digest,
            'snapshot_sha256':hashlib.sha256((prepared/'source-snapshot.json').read_bytes()).hexdigest(),
            'inventory':source.completeness.inventory,'ddl':source.completeness.ddl,
            'preparation_exit_code':rc,'read_only':True}
        (output/'source-preparation.json').write_bytes(canonical_bytes(proof)+b'\n')
        print(json.dumps({'phase':'source_preparation',**proof}),flush=True)
    try:
        from .jenkins_source_semantics import capture_source_metadata,reconcile_source
    except ImportError:
        from jenkins_source_semantics import capture_source_metadata,reconcile_source
    from oracle_db_migration_generator.config.models import Endpoint,TargetConfig
    metadata=metadata_sources(json.loads((config/'source-metadata.json').read_bytes()),settings['schemas'])
    initialize_oracle_driver(targets,os.environ.get('GENERATOR_ORACLE_CLIENT_DIR'))
    for record in metadata:
        owner=record['schema'];suffix='.'+owner if len(metadata)>1 else ''
        mode=next(target.driver_mode for target in targets if TARGET_OWNERS[target.id]==owner)
        source_target=TargetConfig('SOURCE-METADATA-'+owner,'Source metadata',True,Endpoint(**record['endpoint']),mode,())
        try:
            capture=capture_source_metadata(source_target,EnvCredentialResolver()(record['credential_id']),owner=owner)
            enriched,proof=reconcile_source(source,capture,prepared)
            import hashlib
            receipt={'owner':owner,'status':capture['status'],'read_only':True,
                'started_at':capture['started_at'],'finished_at':capture['finished_at'],
                'capture_sha256':hashlib.sha256(canonical_bytes(capture)).hexdigest()}
            (prepared/('metadata/source-observation'+suffix+'.json')).write_bytes(canonical_bytes(capture)+b'\n')
            (output/('source-semantics'+suffix+'.json')).write_bytes(canonical_bytes(proof)+b'\n')
            source=enriched
            print(json.dumps({'phase':'source_metadata_correspondence','owner':owner,'matched_tables':proof['matched_tables'],
                              'rejected_tables':len(proof['rejected_tables']),'read_only':True}),flush=True)
        except Exception as error:
            receipt={'owner':owner,'status':'UNAVAILABLE','error_code':safe_error_code(error),'read_only':True}
            print(json.dumps({'phase':'source_metadata_correspondence',**receipt}),flush=True)
        (output/('source-metadata-receipt'+suffix+'.json')).write_bytes(canonical_bytes(receipt)+b'\n')
    (prepared/'source-snapshot.enriched.json').write_bytes(canonical_bytes(source.to_dict())+b'\n')
    from oracle_db_migration_generator.compare.scope import scope_exclusions
    from oracle_db_migration_generator.model.source_scope import source_for_schemas
    from oracle_db_migration_generator.model.serialization import thaw
    results=[];scope_receipts=[];source_scopes=[]
    for target in targets:
        owner_source=source_for_schemas(source,profile,tuple(mapping.source_schema for mapping in target.schema_mappings))
        source_scopes.append({'target_id':target.id,'schemas':owner_source.schemas,
            'semantic_digest':owner_source.semantic_digest,'coverage':asdict(owner_source.completeness),
            'proof':thaw(owner_source.capabilities['owner_scope_proof'].value)})
        (output/'source-scopes.json').write_bytes(canonical_bytes({'targets':source_scopes})+b'\n')
        result=run_target(owner_source,target,profile,EnvCredentialResolver(),output,
            progress=lambda i,n: print(json.dumps({'phase':'read_only_target_metadata','target_id':target.id,'processed':i,'total':n}),flush=True) if i%50==0 else None)
        results.append(result)
        snapshot=output/'observations'/target.id/'target-snapshot.json'
        if snapshot.is_file():
            excluded=scope_exclusions(source,load_snapshot(snapshot,require_ddl=True),profile.policy)
            summary={side:sum(item['side']==side for item in excluded) for side in ('SOURCE','TARGET')}
            scope_receipts.append({'target_id':target.id,'status':'VERIFIED','excluded_counts':summary,'objects':excluded})
            print(json.dumps({'phase':'comparison_scope','target_id':target.id,'excluded_counts':summary}),flush=True)
        else:
            scope_receipts.append({'target_id':target.id,'status':'NOT_AVAILABLE','excluded_counts':None,'objects':[]})
    (output/'scope-exclusions.json').write_bytes(canonical_bytes({'exclude_system_generated':profile.policy.exclude_system_generated,
        'excluded_object_types':profile.policy.excluded_object_types,'targets':scope_receipts})+b'\n')
    for result in results:
        if result['plan_path']:verify_bundle(output/result['plan_path'].rsplit('/',1)[0])
    run=aggregate_run(output,source_commit=source.source_commit,started_at=started,
        build_number=int(os.environ['BUILD_NUMBER']),build_url=os.environ['BUILD_URL'])
    try:
        from .jenkins_notification import write_notification
    except ImportError:
        from jenkins_notification import write_notification
    write_notification(output,run,os.environ['BUILD_URL'],settings['job_url'])
    print(json.dumps({'status':run['status'],'target_status':{result['id']:result['status'] for result in results},'run_id':run['run_id'],
                      'read_only':True,'execution_status':'NOT_EXECUTED'}),flush=True)
    return run['exit_code']


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError):
        print(json.dumps({'status':'FAILED','error_code':'GENERATOR_JENKINS_INPUT_OR_INTEGRITY_ERROR'}));raise SystemExit(30)
