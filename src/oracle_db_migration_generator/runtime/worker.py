from datetime import datetime, timezone
from pathlib import Path

from ..artifacts.bundle import write_bundle
from ..compare.snapshots import compare_snapshots
from ..config.loader import validate_document
from ..model.serialization import canonical_bytes, digest
from ..model.snapshot_io import safe_path
from ..oracle.collector import collect_target
from ..planning.rules import PlanningContext, plan_target


def offline_plan(source,target,profile,output,*,name=None,secret_values=()):
    recorded=source.capabilities.get('source_profile_sha256')
    if recorded and (recorded.state!='KNOWN' or recorded.value!=digest(profile)):
        raise ValueError('SOURCE_PROFILE_FINGERPRINT_MISMATCH')
    differences=compare_snapshots(source,target,profile.policy)
    plan=plan_target(differences,PlanningContext(source,target,profile,name or target.target_id))
    return write_bundle(plan,output,secret_values=secret_values)


def save_observation(observation,output):
    output=Path(output)
    if output.exists(): raise ValueError('CAPTURE_OUTPUT_ALREADY_EXISTS')
    output.mkdir(parents=True)
    (output/'receipt.json').write_bytes(canonical_bytes(observation.receipt)+b'\n')
    snapshot=observation.snapshot
    if snapshot is not None:
        document=snapshot.to_dict();validate_document(document,'snapshot.schema.json')
        for obj in snapshot.objects:
            if obj.ddl_path and obj.raw_ddl:
                path=safe_path(output,obj.ddl_path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(obj.raw_ddl)
        (output/'target-snapshot.json').write_bytes(canonical_bytes(document)+b'\n')


def run_target(source,target,profile,credentials,output,*,collect=collect_target,progress=None):
    output=Path(output).resolve()
    bundle=output/'targets'/target.id
    capture=output/'observations'/target.id
    if bundle.exists() or capture.exists(): raise ValueError('TARGET_OUTPUT_ALREADY_EXISTS')
    # No schema remapping is permitted. Each account collects its own schema.
    if any(mapping.source_schema!=mapping.target_schema for mapping in target.schema_mappings):
        raise ValueError('SCHEMA_REMAP_NOT_SUPPORTED')
    if any(mapping.source_schema not in source.schemas for mapping in target.schema_mappings):
        raise ValueError('TARGET_SCHEMA_OUTSIDE_SOURCE_SCOPE')
    observation=collect(target,credentials,profile,progress=progress,source=source)
    save_observation(observation,capture)
    result={'id':target.id,'status':'ERROR','difference_count':None,'plan_id':None,'plan_path':None,
            'captured_at':observation.receipt.get('finished_at'),'error_code':None,'publication':'NOT_REQUESTED'}
    if observation.snapshot is None:
        result['status']='INCONSISTENT' if observation.receipt['status']=='INCONSISTENT' else 'ERROR'
        result['error_code']=next((item.get('error_code') for item in observation.receipt.get('schemas',()) if item.get('error_code')),'TARGET_CAPTURE_FAILED')
        bundle.mkdir(parents=True)
        (bundle/'target-error.json').write_bytes(canonical_bytes(result)+b'\n')
        return result
    passwords=[]
    if credentials:
        passwords=[credentials(mapping.credential_id).password for mapping in target.schema_mappings]
    try:
        written=offline_plan(source,observation.snapshot,profile,bundle,name=target.name,secret_values=passwords)
    except ValueError as error:
        # Suspected credentials cannot enter normal plan/report artifacts.
        if str(error)!='SENSITIVE_CONTENT_DETECTED': raise
        result['error_code']='SENSITIVE_CONTENT_DETECTED'
        bundle.mkdir(parents=True)
        (bundle/'target-error.json').write_bytes(canonical_bytes(result)+b'\n')
        return result
    result.update(status=written['decision'],plan_id=written['plan_id'],plan_path='targets/'+target.id+'/plan.json',
                  difference_count=written['counts']['observed_differences'] if written['comparison_complete'] else None)
    (bundle.parent/(target.id+'.result.json')).write_bytes(canonical_bytes(result)+b'\n')
    return result
