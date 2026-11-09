"""Oracle DB Migration Generator hedef snapshot'ını salt okunur karşılaştırır.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
import os

from ..artifacts.bundle import write_bundle
from ..compare.snapshots import compare_snapshots
from ..config.loader import validate_document
from ..model.serialization import canonical_bytes, digest
from ..model.snapshot_io import safe_path
from ..oracle.collector import collect_target
from ..planning.rules import PlanningContext, plan_target


def offline_plan(source,target,profile,output,*,name=None,secret_values=(),timings=None):
    started=perf_counter()
    recorded=source.capabilities.get('source_profile_sha256')
    if recorded and (recorded.state!='KNOWN' or recorded.value!=digest(profile)):
        raise ValueError('SOURCE_PROFILE_FINGERPRINT_MISMATCH')
    from ..portable.adapter import scope_comparison
    from ..model.serialization import thaw
    selected=source.capabilities.get('comparison_filter')
    source,target=scope_comparison(source,target,thaw(selected.value) if selected and selected.state=='KNOWN' else None)
    if timings is not None:timings['scope_seconds']=perf_counter()-started
    started=perf_counter()
    differences=compare_snapshots(source,target,profile.policy)
    if timings is not None:timings['compare_seconds']=perf_counter()-started
    started=perf_counter()
    plan=plan_target(differences,PlanningContext(source,target,profile,name or target.target_id))
    if timings is not None:timings['plan_seconds']=perf_counter()-started
    started=perf_counter()
    from ..reporting.inventory import build_scan_summary
    result=write_bundle(plan,output,secret_values=secret_values,source=source,
                        scan_summary=build_scan_summary(source,target,profile.policy,plan))
    if timings is not None:timings['bundle_seconds']=perf_counter()-started
    return result


def save_observation(observation,output):
    """Metadata sözleşmesini doğrular ve bağımsız ham dosyaları sınırlı paralellikle yazar."""
    output=Path(output)
    if output.exists(): raise ValueError('CAPTURE_OUTPUT_ALREADY_EXISTS')
    output.mkdir(parents=True)
    (output/'receipt.json').write_bytes(canonical_bytes(observation.receipt)+b'\n')
    snapshot=observation.snapshot
    if snapshot is not None:
        document=snapshot.to_dict();validate_document(document,'snapshot.schema.json')
        payloads = {}
        for obj in snapshot.objects:
            if obj.ddl_path and obj.raw_ddl:
                path=safe_path(output,obj.ddl_path)
                if path in payloads and payloads[path] != obj.raw_ddl:
                    raise ValueError('CAPTURE_DDL_PATH_CONFLICT')
                payloads[path] = obj.raw_ddl
        for evidence in snapshot.evidence:
            if evidence.query_id!='oracle.compiled-static/v1' or not evidence.path:continue
            artifact=next((item for item in observation.artifacts
                           if item.path==evidence.path and item.sha256==evidence.sha256),None)
            if artifact is None:raise ValueError('ROUTINE_METADATA_EVIDENCE_BLOB_MISSING')
            path=safe_path(output,evidence.path)
            if path in payloads and payloads[path] != artifact.raw:
                raise ValueError('CAPTURE_DDL_PATH_CONFLICT')
            payloads[path] = artifact.raw
        try:
            writers = int(os.environ.get('GENERATOR_CAPTURE_WRITERS', '4'))
        except ValueError:
            raise ValueError('CAPTURE_WRITERS_INVALID') from None
        if not 1 <= writers <= 4: raise ValueError('CAPTURE_WRITERS_INVALID')
        def write_batch(batch):
            for path,raw in batch:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(raw)
        items = list(payloads.items())
        batches = (items[index:index+16] for index in range(0,len(items),16))
        executor = ThreadPoolExecutor(max_workers=writers,thread_name_prefix='capture-write')
        try:
            for _ in executor.map(write_batch,batches): pass
        finally:
            executor.shutdown(wait=True,cancel_futures=True)
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
    started=perf_counter()
    observation=collect(target,credentials,profile,progress=progress,source=source)
    timings={'capture_seconds':perf_counter()-started}
    started=perf_counter()
    save_observation(observation,capture)
    timings['save_observation_seconds']=perf_counter()-started
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
        written=offline_plan(source,observation.snapshot,profile,bundle,name=target.name,secret_values=passwords,timings=timings)
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
    (capture/'performance.json').write_bytes(canonical_bytes(timings)+b'\n')
    return result
