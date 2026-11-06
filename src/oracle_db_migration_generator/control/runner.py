"""Real engine orchestration. All SQL is emitted offline, never applied."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ..config.models import Endpoint,Policy,SchemaMapping,SchemaRoot,SourceProfile,TargetConfig
from ..model.serialization import canonical_bytes,digest
from ..oracle.collector import collect_target
from ..oracle.connection import connect_read_only
from ..oracle.preflight import safe_error_code
from ..runtime.worker import run_target,save_observation
from ..runtime.aggregate import aggregate_run
from ..source.oracle_reader import collect_source,save_source
from ..model.snapshot_io import write_source_snapshot
from ..source.git_reader import GitRepository,read_source,resolve_source
from ..source.access import git_read_environment
from ..source.prepared_cache import PreparedSourceCache
from ..parsing.adapter import parse_source
from .runtime import runtime_settings
from .store import now


def make_profile(spec):
    data=spec['profile'];source=data['source']
    types=set(data['object_types']);excluded=set(data['excluded_object_types'])
    scope=data.get('capture_filter')
    if scope and scope.get('include_related',True) and types&{'TABLE','VIEW','MATERIALIZED_VIEW'}:
        types.update(('INDEX','TRIGGER','COMMENT'));excluded.difference_update(('INDEX','TRIGGER','COMMENT'))
    return SourceProfile('source-profile/1.0',data['id'],source['layout'],1,
        tuple(SchemaRoot(source['roots'].get(s,s.lower()),s) for s in source['schemas']),tuple(sorted(types)) if scope else tuple(data['object_types']),
        data['source_length_semantics'],Policy(False,False,data['compare_physical_storage'],(),'REPORT_ONLY',True,
                                              data['exclude_system_generated'],tuple(sorted(excluded)) if scope else tuple(data['excluded_object_types'])))


def target_config(connection,schemas,settings,*,mappings=None,username=None):
    endpoint=Endpoint(connection['host'],connection['port'],connection.get('service_name'),connection.get('sid'))
    pairs=mappings if mappings is not None else [{'source_schema':s,'target_schema':s} for s in schemas]
    def reader(owner):
        return connection.get('metadata_reader') or (username if username and username.upper()!=owner else None)
    return TargetConfig(connection['id'],connection['name'],True,endpoint,connection['driver_mode'],
        tuple(SchemaMapping(m['source_schema'],m['target_schema'],connection['id'],reader(m['target_schema'])) for m in pairs),settings['capture_timeout_seconds'])


def initialize_driver(connections):
    import oracledb
    modes={c['driver_mode'] for c in connections if c['kind']=='ORACLE'}
    if len(modes)>1:raise ValueError('MIXED_ORACLE_DRIVER_MODES')
    if modes=={'thick'} and oracledb.is_thin_mode():
        client=os.environ.get('ODMG_ORACLE_CLIENT_DIR')
        if not client:raise ValueError('ORACLE_CLIENT_REQUIRED')
        oracledb.init_oracle_client(lib_dir=client)


def git_checkout(connection,selection,folder,credentials,settings):
    source={'repository':connection['repository'],'credential_id':connection['id']}
    if connection['credential_configured']:
        with git_read_environment(source,credentials) as env:
            return _git_clone(connection,selection,folder,env,settings)
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='3',
             GIT_CONFIG_KEY_0='credential.helper',GIT_CONFIG_VALUE_0='',
             GIT_CONFIG_KEY_1='http.followRedirects',GIT_CONFIG_VALUE_1='false',
             GIT_CONFIG_KEY_2='http.sslVerify',GIT_CONFIG_VALUE_2='true')
    return _git_clone(connection,selection,folder,env,settings)


def _git_clone(connection,selection,folder,env,settings):
    folder=Path(folder)
    for attempt in range(settings['git_attempts']):
        if not folder.exists():
            args=['git','-c','protocol.file.allow=never','clone','--no-checkout','--no-recurse-submodules',connection['repository'],str(folder)]
        else:args=['git','-C',str(folder),'fetch','--no-recurse-submodules','origin']
        result=subprocess.run(args,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
        if result.returncode==0:return folder
        if attempt+1<settings['git_attempts']:time.sleep(settings['git_retry_seconds'])
    raise ValueError('GIT_FETCH_FAILED')


def resolve_git_revision(folder,ref):
    import re
    repo=GitRepository(folder)
    if ref=='HEAD' or re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',ref):return resolve_source(repo,ref)
    if not ref or ref.startswith('-') or any(c in ref for c in '\x00\r\n'):raise ValueError('GIT_REF_INVALID')
    names=[ref] if ref.startswith('refs/') else ['refs/remotes/origin/'+ref,'refs/tags/'+ref]
    found=[]
    for name in names:
        result=subprocess.run(['git','-C',str(folder),'show-ref','--verify','--quiet',name],capture_output=True,timeout=15)
        if result.returncode==0:found.append(name)
    if len(found)>1:raise ValueError('GIT_REF_AMBIGUOUS')
    if not found:raise ValueError('GIT_REF_NOT_FOUND')
    return resolve_source(repo,found[0])


def isolated_connection_test(store,connection,*,schemas=()):
    if connection['kind']=='SNAPSHOT':
        capture=store.load_capture(connection)
        if not set(schemas).issubset(capture.schemas):raise ValueError('CAPTURE_SCHEMA_NOT_EXPORTED')
        return {'status':'CONNECTED','read_only':True,'note':'Dosya bütünlüğü doğrulandı. Veri tabanına bağlantı açılmadı.'}
    settings=store.settings(connection.get('project_id'))
    result=subprocess.run([sys.executable,'-m','oracle_db_migration_generator.control.connection_probe',
        '--root',str(store.root),'--connection',connection['id'],'--revision',str(connection['revision'])],
        input=json.dumps({'schemas':list(schemas),'settings':settings}).encode(),capture_output=True,
        timeout=min(settings['capture_timeout_seconds'],settings['connect_timeout_seconds']+len(schemas or [None])*settings['call_timeout_ms']/1000*4+30),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:result_data=json.loads(result.stdout)
    except (ValueError,TypeError):raise ValueError('CONNECTION_TEST_FAILED') from None
    if result.returncode:raise ValueError(result_data.get('error_code','CONNECTION_TEST_FAILED'))
    return result_data


def test_connection(store,connection,*,schemas=(),connect=connect_read_only,settings=None):
    credentials=lambda _:store.credentials(connection['id'],connection['revision'])
    if connection['kind']=='GIT':
        source={'repository':connection['repository'],'credential_id':connection['id']}
        if connection['credential_configured']:
            with git_read_environment(source,credentials) as env:
                result=subprocess.run(['git','ls-remote',connection['repository'],'HEAD'],env=env,
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        else:
            env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='credential.helper',GIT_CONFIG_VALUE_0='')
            result=subprocess.run(['git','-c','http.followRedirects=false','ls-remote',connection['repository'],'HEAD'],env=env,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        if result.returncode:raise ValueError('GIT_ACCESS_FAILED')
        return {'status':'CONNECTED','read_only':True,'metadata_verified':False}
    initialize_driver([connection]);credential=credentials(connection['id'])
    owners=tuple(schemas) or (credential.username.upper(),)
    config=target_config(connection,owners,settings or store.settings(connection.get('project_id')),username=credential.username);db=cursor=None
    try:
        db=connect(config,credential);cursor=db.cursor()
        from ..oracle.queries import READ_ONLY_TRANSACTION,IDENTITY,CAPTURE_INVENTORY
        cursor.execute(READ_ONLY_TRANSACTION)
        for mapping in config.schema_mappings:
            owner=mapping.target_schema
            reader=cursor
            if mapping.metadata_reader:
                from ..oracle.catalog_reader import authorize_catalog_reader,CatalogCursor
                authorize_catalog_reader(cursor,mapping.metadata_reader,owner);reader=CatalogCursor(cursor)
            else:
                cursor.execute(IDENTITY)
                if cursor.fetchone()!=(owner,):raise ValueError('SESSION_OWNER_MISMATCH')
            reader.execute(CAPTURE_INVENTORY,{'owner':owner});reader.fetchall()
        return {'status':'CONNECTED','read_only':True,'schemas':owners,'inventory_access_verified':True,
                'ddl_access_verified':False,'note':'DDL ve dictionary tamlığı karşılaştırma sırasında ayrıca doğrulanır.'}
    finally:
        if cursor:cursor.close()
        if db:db.rollback();db.close()


def execute_run(store,id,*,source_collector=collect_source,target_collector=collect_target,checkout=git_checkout):
    run=store.run(id);spec=run['spec'];settings=spec['settings'];profile=make_profile(spec)
    if not store.begin_run(id):return
    root=store.root/'runs'/id;root.mkdir(parents=True,exist_ok=True)
    last_write=[0,None,None]
    def stage(name,**details):
        clock=time.monotonic()
        if (last_write[1:]==[name,details.get('target_id')] and clock-last_write[0]<.5
                and details.get('processed')!=details.get('total')):return
        last_write[:]=[clock,name,details.get('target_id')]
        current=store.run(id);events=current['events'][-99:]
        if not events or events[-1]['stage']!=name:events.append({'stage':name,'at':now()})
        store.update_run(id,stage=name,events=events,progress=details)
    credentials=lambda key:store.credentials(key,spec['connections'][key]['revision'])
    def configured_scope(snapshot):
        value=spec['profile'].get('capture_filter')
        if value is None:return snapshot
        from ..model.snapshot import KnownValue
        from ..model.evidence import Evidence
        eid='ev-'+digest([id,'comparison-filter',value])
        evidence=Evidence(eid,'SOURCE_METADATA','SOURCE',None,digest(value),None,None,'comparison.filter','Çalışmanın kayıtlı nesne seçim parametreleri.')
        return replace(snapshot,capabilities={**snapshot.capabilities,'comparison_filter':KnownValue('KNOWN',value,(eid,))},evidence=(*snapshot.evidence,evidence))
    prior_cache=os.environ.get('GENERATOR_PARSER_CACHE_DIR')
    if settings['cache_enabled']:os.environ['GENERATOR_PARSER_CACHE_DIR']=str(store.root/'parser-cache')
    else:os.environ.pop('GENERATOR_PARSER_CACHE_DIR',None)
    try:
        with runtime_settings(settings):
            oracle_connections=[c for c in spec['connections'].values() if c['kind']=='ORACLE']
            if oracle_connections:initialize_driver(oracle_connections)
            selection=spec['profile']['source'];connection=spec['connections'][selection['connection_id']]
            started=time.perf_counter();performance={'cache_status':'NOT_APPLICABLE'}
            if selection['kind']=='GIT':
                stage('GIT_FETCH');repo=checkout(connection,selection,root/'repository',credentials,settings)
                revision=resolve_git_revision(repo,selection['ref'])
                inputs=read_source(revision,profile)
                cache=PreparedSourceCache(store.root/'prepared-cache',inputs,runtime_fingerprint=digest(settings),
                    max_entries=settings['cache_entries'],max_bytes=settings['cache_megabytes']*1024*1024) if settings['cache_enabled'] else None
                source=cache.load() if cache else None
                performance['cache_status']='HIT_VERIFIED' if source else 'MISS' if cache else 'DISABLED'
                if source is None:
                    stage('SOURCE_PARSE')
                    source=parse_source(inputs,profile,progress=lambda i,n:stage('SOURCE_PARSE',processed=i,total=n))
                    if cache:cache.store(source)
                source=configured_scope(source)
                write_source_snapshot(source,inputs,root/'source')
            elif selection['kind']=='SNAPSHOT':
                stage('SOURCE_IMPORT')
                from ..portable.adapter import observation_from_capture
                from ..source.oracle_reader import from_observation
                observation=from_observation(observation_from_capture(store.load_capture(connection),profile,
                    target_id='source-'+connection['id'],schemas=selection['schemas']),connection_id=connection['id'])
                source=configured_scope(observation.snapshot)
                save_source(observation if source is observation.snapshot else replace(observation,snapshot=source),root/'source')
            else:
                stage('SOURCE_CAPTURE')
                observation=source_collector(target_config(connection,selection['schemas'],settings,
                    username=credentials(connection['id']).username),credentials,profile,
                    progress=lambda i,n:stage('SOURCE_CAPTURE',processed=i,total=n))
                if observation.snapshot is None:raise ValueError('SOURCE_CAPTURE_'+observation.receipt['status'])
                source=configured_scope(observation.snapshot)
                save_source(observation if source is observation.snapshot else replace(observation,snapshot=source),root/'source')
            performance.update(seconds=time.perf_counter()-started,source_kind=selection['kind'])
            (root/'source-preparation-performance.json').write_bytes(canonical_bytes(performance)+b'\n')
            results=[]
            for target_id in spec['profile']['target_ids']:
                target_connection=spec['connections'][target_id]
                if target_connection['kind']=='SNAPSHOT':
                    from ..portable.adapter import observation_from_capture
                    from ..runtime.worker import offline_plan
                    stage('TARGET_IMPORT',target_id=target_id)
                    pairs=(spec['profile'].get('target_mappings') or {}).get(target_id)
                    schemas=[p['target_schema'] for p in pairs] if pairs else selection['schemas']
                    observation=observation_from_capture(store.load_capture(target_connection),profile,target_id=target_id,schemas=schemas)
                    save_observation(observation,root/'observations'/target_id)
                    bundle=root/'targets'/target_id
                    written=offline_plan(source,observation.snapshot,profile,bundle,name=target_connection['name'])
                    result={'id':target_id,'status':written['decision'],'plan_id':written['plan_id'],'plan_path':'targets/'+target_id+'/plan.json',
                        'difference_count':written['counts']['observed_differences'] if written['comparison_complete'] else None,
                        'captured_at':observation.receipt['captured_at'],'error_code':None,'publication':'NOT_REQUESTED'}
                    (bundle.parent/(target_id+'.result.json')).write_bytes(canonical_bytes(result)+b'\n')
                    results.append(result);store.update_run(id,targets=results);continue
                target=target_config(spec['connections'][target_id],selection['schemas'],settings,
                    mappings=(spec['profile'].get('target_mappings') or {}).get(target_id),
                    username=credentials(target_id).username)
                stage('TARGET_CAPTURE',target_id=target_id)
                result=run_target(source,target,profile,credentials,root,collect=target_collector,
                    progress=lambda i,n:stage('TARGET_CAPTURE',target_id=target_id,processed=i,total=n))
                results.append(result);store.update_run(id,targets=results)
            stage('REPORT')
            summary=aggregate_run(root,source_commit=source.source_commit,
                source_origin=dict(source.source_origin) if source.source_origin else None,started_at=store.run(id)['started_at'])
            store.update_run(id,status=summary['status'],stage='FINISHED',finished_at=now(),targets=results,
                source_performance=performance,source_origin=summary.get('source_origin'),source_commit=summary['source_commit'],
                report_available=True,notification_status='NOT_SENT_LOCAL_DEVELOPMENT')
    except Exception as error:
        import traceback
        # Private structural diagnostics only: no exception text, SQL or credentials.
        frames=[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)]
        try:(root/'failure-diagnostic.json').write_bytes(canonical_bytes({'exception_type':type(error).__name__,'frames':frames})+b'\n')
        except OSError:pass
        code=str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() and len(str(error))<100 else safe_error_code(error)
        store.update_run(id,status='FAILED',stage='FAILED',error_code=code,finished_at=now())
    finally:
        if prior_cache is None:os.environ.pop('GENERATOR_PARSER_CACHE_DIR',None)
        else:os.environ['GENERATOR_PARSER_CACHE_DIR']=prior_cache
