"""Closed snapshot contracts, safe blob reads and atomic new source bundles.

Semantic digests are recomputed from actual facts on import rather than
trusting a caller-supplied cached digest. Identity/evidence hashes are checked.
"""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from ..config.loader import read_json, validate_document
from .evidence import Evidence
from .identity import Identifier, ObjectIdentity
from .serialization import digest, thaw
from .snapshot import Coverage, KnownValue, SchemaSnapshot, SnapshotObject


def _coverage(value):
    return Coverage(value['inventory'],value['ddl'],value['dictionary'],tuple(value['diagnostics']))


def _known(value):
    return KnownValue(value['state'],value['value'],tuple(value['evidence_ids']))


def safe_path(root: Path, relative: str):
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '\\' in relative or ':' in relative or any(p in {'','.', '..'} for p in relative.split('/')):
        raise ValueError('SNAPSHOT_PATH_UNSAFE')
    path = root.joinpath(*parts.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('SNAPSHOT_PATH_UNSAFE')
    return path


def load_snapshot(path: Path, *, require_ddl=False):
    path = Path(path)
    document = read_json(path)
    validate_document(document,'snapshot.schema.json')
    evidence = tuple(Evidence(**item) for item in document['evidence'])
    registry = {item.id:item for item in evidence}
    if len(registry)!=len(evidence):
        raise ValueError('SNAPSHOT_DUPLICATE_EVIDENCE')
    if require_ddl and document.get('source_origin'):
        for ev in evidence:
            if ev.path:
                blob=safe_path(path.parent,ev.path)
                if not blob.is_file():raise ValueError('SNAPSHOT_EVIDENCE_MISSING')
                if hashlib.sha256(blob.read_bytes()).hexdigest()!=ev.sha256:raise ValueError('SNAPSHOT_EVIDENCE_INTEGRITY_MISMATCH')
    objects = []
    for item in document['objects']:
        data = item['identity']
        identity = ObjectIdentity(data['profile_id'],Identifier(data['owner'],data['owner'],True),
                                  data['object_type'],Identifier(data['name'],data['name'],data['quoted']),data['parent_key'])
        if identity.key!=item['object_key']:
            raise ValueError('SNAPSHOT_IDENTITY_MISMATCH')
        if identity.profile_id!=document['profile_id'] or identity.owner.effective_name not in document['schemas']:
            raise ValueError('SNAPSHOT_OBJECT_OUTSIDE_SCOPE')
        if any(key not in registry for key in item['evidence_ids']):
            raise ValueError('SNAPSHOT_EVIDENCE_UNRESOLVED')
        props = {key:_known(value) for key,value in item['properties'].items()}
        if any(key not in registry for value in props.values() for key in value.evidence_ids):
            raise ValueError('SNAPSHOT_PROPERTY_EVIDENCE_UNRESOLVED')
        raw = None
        if item['ddl_path']:
            blob_path = safe_path(path.parent,item['ddl_path'])
            if blob_path.is_file():
                payload = blob_path.read_bytes()
                candidates = [registry[key] for key in item['evidence_ids'] if registry[key].path==item['ddl_path']]
                reference = candidates[0] if candidates else None
                full_hash = hashlib.sha256(payload).hexdigest()
                if reference and reference.sha256 and full_hash!=reference.sha256:
                    raise ValueError('SNAPSHOT_DDL_INTEGRITY_MISMATCH')
                if full_hash==item['ddl_sha256']:
                    raw = payload
                elif reference and reference.start_byte is not None and reference.end_byte is not None:
                    candidate = payload[reference.start_byte:reference.end_byte]
                    if hashlib.sha256(candidate).hexdigest()==item['ddl_sha256']:
                        raw = candidate
                if raw is None and (document.get('source_origin') or identity.object_type not in {'COMMENT','GRANT'}):
                    raise ValueError('SNAPSHOT_DDL_INTEGRITY_MISMATCH')
            elif require_ddl and document['side']=='SOURCE':
                raise ValueError('SNAPSHOT_DDL_MISSING')
        objects.append(SnapshotObject(identity,props,item['ddl_path'],item['ddl_sha256'],
                                      _coverage(item['coverage']),tuple(item['evidence_ids']),raw))
    return SchemaSnapshot(document['schema_version'],document['synthetic'],document['side'],document['profile_id'],
                          tuple(document['schemas']),document['source_commit'],document['target_id'],tuple(objects),
                          _coverage(document['coverage']),{key:_known(value) for key,value in document['capabilities'].items()},
                          evidence,document['observed_consistency'],document.get('source_origin'))


def write_source_snapshot(snapshot,inputs,output: Path):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    repository_path = getattr(inputs.revision.repository,'path',None)
    if repository_path and output.is_relative_to(Path(repository_path).resolve()):
        raise ValueError('SOURCE_OUTPUT_OVERLAP')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.source-staging-',dir=output.parent)).resolve()
    assert temporary.parent==output.parent and temporary.name.startswith('.source-staging-')
    try:
        for artifact in inputs.artifacts:
            target = safe_path(temporary,artifact.path)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(artifact.raw)
        document = snapshot.to_dict()
        validate_document(document,'snapshot.schema.json')
        (temporary/'source-snapshot.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (temporary/'source-input.json').write_text(json.dumps({'source_commit':inputs.revision.commit,
                                                              'input_digest':inputs.input_digest,
                                                              'files':[{'path':a.path,'sha256':a.sha256} for a in inputs.artifacts]},indent=2)+'\n',encoding='utf-8')
        if inputs.profile is not None:
            (temporary/'source-profile.json').write_text(json.dumps(thaw(inputs.profile),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.rename(temporary,output)
    finally:
        if temporary.exists():
            assert temporary.resolve().parent==output.parent and temporary.name.startswith('.source-staging-')
            shutil.rmtree(temporary)
    return output/'source-snapshot.json'
