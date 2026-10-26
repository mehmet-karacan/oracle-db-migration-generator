"""One-off report refresh from an already captured, verified comparison. No Oracle access."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from oracle_db_migration_generator.artifacts.bundle import verify_bundle,write_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.emission.sql import render_statement
from oracle_db_migration_generator.model.serialization import canonical_bytes,digest
from oracle_db_migration_generator.model.snapshot_io import load_snapshot,safe_path
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target


def refresh_plan(previous,source_path,target_path,profile,output):
    verify_bundle(previous)
    old=json.loads((previous/'plan.json').read_bytes())
    source=load_snapshot(source_path,require_ddl=True);target=load_snapshot(target_path,require_ddl=True)
    if (source.side!='SOURCE' or target.side!='TARGET' or source.source_commit!=old['source']['commit_sha']
        or source.semantic_digest!=old['source']['ddl_digest'] or target.semantic_digest!=old['target_snapshot_digest']
        or digest(profile)!=old['input_fingerprint']['profile_sha256']):
        raise ValueError('REFRESH_INPUT_MISMATCH')
    plan=plan_target(compare_snapshots(source,target,profile.policy),PlanningContext(source,target,profile,old['target']['name']))
    new=plan.to_dict()
    def decisions(document):
        return sorted((op['id'],op['decision'],op['reason_codes'],op['depends_on']) for op in document['operations'])
    if new['counts']!=old['counts'] or new['differences']!=old['differences'] or decisions(new)!=decisions(old):
        raise ValueError('REFRESH_DECISION_CHANGED')
    old_ops={op['id']:op for op in old['operations']};verified=0
    for op in plan.operations:
        if op.decision!='READY':continue
        old_sql=old_ops[op.operation_id]['sql']
        if not old_sql or render_statement(op,plan.plan_id).split(b'\n',1)[1]!=safe_path(previous,old_sql['path']).read_bytes().split(b'\n',1)[1]:
            raise ValueError('REFRESH_SQL_CHANGED')
        verified+=1
    from oracle_db_migration_generator.reporting.inventory import build_scan_summary
    result=write_bundle(plan,output,scan_summary=build_scan_summary(source,target,profile.policy,plan))
    return {**result,'database_connections':0,'sql_bodies_verified':verified,'source_commit':source.source_commit}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--previous-build',type=int,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();number=int(os.environ['BUILD_NUMBER']);output=args.output.resolve()
    if not 0<args.previous_build<number or output!=Path('output/runs').resolve()/('build-'+str(number)) or output.exists():
        raise ValueError('REFRESH_BUILD_INVALID')
    base=output.parent/('build-'+str(args.previous_build));target_id='LOCAL-ODI'
    receipt=json.loads((base/'observations'/target_id/'receipt.json').read_bytes())
    if receipt.get('status')!='CAPTURED' or receipt.get('read_only') is not True:raise ValueError('REFRESH_CAPTURE_UNVERIFIED')
    config=args.release/'config';profile=load_source_profile(config/'source-profile.json')
    source_path=output.parent/'source-snapshots'/('build-'+str(args.previous_build))/'source-snapshot.enriched.json'
    target_path=base/'observations'/target_id/'target-snapshot.json'
    result=refresh_plan(base/'targets'/target_id,source_path,target_path,profile,output/'targets'/target_id)
    plan=json.loads((output/'targets'/target_id/'plan.json').read_bytes())
    target={'id':target_id,'status':plan['status'],
            'difference_count':plan['counts']['observed_differences'] if result['comparison_complete'] else None,
            'plan_id':plan['plan_id'],'plan_path':'targets/'+target_id+'/plan.json',
            'captured_at':receipt['finished_at'],'error_code':None,'publication':'NOT_REQUESTED'}
    (output/'targets'/(target_id+'.result.json')).write_bytes(canonical_bytes(target)+b'\n')
    proof={'base_build':args.previous_build,'database_connections':0,'previous_capture_finished_at':receipt['finished_at'],
           'source_snapshot_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
           'target_snapshot_sha256':hashlib.sha256(target_path.read_bytes()).hexdigest(),'sql_bodies_verified':result['sql_bodies_verified']}
    (output/'refresh-receipt.json').write_bytes(canonical_bytes(proof)+b'\n')
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from jenkins_notification import write_notification
    run=aggregate_run(output,source_commit=result['source_commit'],build_number=number,build_url=os.environ['BUILD_URL'])
    settings=json.loads((config/'job-settings.json').read_bytes())
    write_notification(output,run,os.environ['BUILD_URL'],settings['job_url'],
        context_note=f"Bu rapor #{args.previous_build} karşılaştırmasının kaydedilmiş gözlemlerinden yenilendi; yeni Oracle bağlantısı açılmadı. Ayrıntılar Jenkins arşivindedir.")
    print(json.dumps({'status':'REFRESH_VERIFIED','counts':plan['counts'],'plan_id':plan['plan_id'],**proof}),flush=True)
    return run['exit_code']


if __name__=='__main__':raise SystemExit(main())
