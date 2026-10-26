"""A fresh Oracle desired-state capture; never impersonates a Git revision."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from ..model.serialization import canonical_bytes,digest,thaw
from ..model.atomic import rename_new_directory
from ..model.snapshot import KnownValue
from ..model.snapshot_io import safe_path,load_snapshot
from ..oracle.collector import TargetObservation,collect_target
from ..oracle.connection import connect_read_only


def from_observation(observation,*,connection_id):
    if observation.snapshot is None:
        return TargetObservation(None,{**observation.receipt,'source_kind':'ORACLE','source_connection_id':connection_id})
    snapshot=observation.snapshot
    origin={'kind':'ORACLE','connection_id':connection_id,'snapshot_id':digest({
        'connection_id':connection_id,'semantic_digest':snapshot.semantic_digest,
        'ddl':[[obj.object_key,obj.ddl_sha256] for obj in snapshot.objects]})}
    ids={ev.id:'ev-'+digest(['oracle-source',connection_id,origin['snapshot_id'],ev.id]) for ev in snapshot.evidence}
    def remap(value):
        if isinstance(value,str):return ids.get(value,value)
        if isinstance(value,list):return [remap(v) for v in value]
        if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
        return value
    def known(value):return KnownValue(value.state,remap(thaw(value.value)),tuple(ids[k] for k in value.evidence_ids))
    evidence=tuple(replace(ev,id=ids[ev.id],side='SOURCE',
        path='source-evidence/'+ev.sha256+'.sql' if ev.path and ev.sha256 else ev.path,
        kind='SOURCE_METADATA' if ev.kind=='TARGET_METADATA' else ev.kind) for ev in snapshot.evidence)
    objects=tuple(replace(obj,properties={k:known(v) for k,v in obj.properties.items()},
        evidence_ids=tuple(ids[k] for k in obj.evidence_ids),ddl_path='source-ddl/'+obj.ddl_sha256+'.sql' if obj.ddl_path else None)
        for obj in snapshot.objects)
    source=replace(snapshot,side='SOURCE',target_id=None,source_commit=None,source_origin=origin,evidence=evidence,
        objects=objects,capabilities={k:known(v) for k,v in snapshot.capabilities.items()})
    return TargetObservation(source,{**observation.receipt,'source_kind':'ORACLE','source_origin':origin,
                                     'execution_status':'NOT_EXECUTED','read_only':True},observation.artifacts)


def save_source(observation,output):
    """Atomically retain raw desired-state bytes and their capture evidence for replay."""
    if observation.snapshot is None:raise ValueError('SOURCE_SNAPSHOT_REQUIRED')
    source=observation.snapshot;output=Path(output).resolve()
    if output.exists():raise ValueError('OUTPUT_ALREADY_EXISTS')
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.oracle-source-',dir=output.parent))
    blobs={hashlib.sha256(obj.raw_ddl).hexdigest():obj.raw_ddl for obj in source.objects if obj.raw_ddl is not None}
    blobs.update({hashlib.sha256(a.raw).hexdigest():a.raw for a in observation.artifacts})
    try:
        paths={obj.ddl_path:obj.ddl_sha256 for obj in source.objects if obj.ddl_path}
        paths.update({ev.path:ev.sha256 for ev in source.evidence if ev.path})
        for relative,sha in paths.items():
            if sha not in blobs:raise ValueError('SOURCE_EVIDENCE_BLOB_MISSING')
            path=safe_path(staging,relative);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blobs[sha])
        (staging/'source-snapshot.json').write_bytes(canonical_bytes(source.to_dict())+b'\n')
        (staging/'capture-receipt.json').write_bytes(canonical_bytes(observation.receipt)+b'\n')
        load_snapshot(staging/'source-snapshot.json',require_ddl=True)
        rename_new_directory(staging,output)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return output/'source-snapshot.json'


def collect_source(config,credentials,profile,*,connect=connect_read_only,progress=None):
    # Namespace capture evidence separately even if source and target use one connection.
    captured=collect_target(replace(config,id='source-'+config.id),credentials,profile,connect=connect,progress=progress)
    observation=from_observation(captured,connection_id=config.id)
    from ..oracle.routine_metadata import complete_routine_observation
    return complete_routine_observation(observation,config,credentials,connect=connect)


def source_descriptor(snapshot):
    result={'profile_id':snapshot.profile_id,'commit_sha':snapshot.source_commit,'ddl_digest':snapshot.semantic_digest}
    if snapshot.source_origin is not None:result['origin']=dict(snapshot.source_origin)
    return result
