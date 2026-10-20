"""Build to a sibling staging directory, validate, then atomically publish locally."""
import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from ..config.loader import read_json, validate_document
from ..emission.sql import aggregate_sql, render_statement
from ..model.serialization import canonical_bytes, thaw
from ..model.snapshot_io import safe_path
from ..reporting.render import render_reports
from .validation import validate_plan
from .layout import object_sql_path, navigation


def _scan(payloads,secret_values):
    patterns=(rb'(?i)\b(?:password|passwd|api_key|access_token)\s*[:=]\s*[\"\']?[^\s\"\',;]{6,}',
              rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'(?i)https?://[^\s/:]+:[^\s/@]+@')
    for raw in payloads:
        if any(secret and len(secret)>=4 and secret.encode() in raw for secret in secret_values) or any(re.search(pattern,raw) for pattern in patterns):
            raise ValueError('SENSITIVE_CONTENT_DETECTED')


def write_bundle(plan,output,*,secret_values=()):
    output=Path(output).resolve()
    if output.exists(): raise ValueError('OUTPUT_ALREADY_EXISTS')
    payload={};ops=[];plan_id=plan.plan_id
    for op in plan.operations:
        if op.decision=='READY':
            raw=render_statement(op,plan_id);path=object_sql_path(op)
            payload[path]=raw
            op=replace(op,sql={'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'statement_kind':op.intent.statement_kind})
        ops.append(op)
    checks=b'-- Read-only postchecks for a separately authorized execution environment.\nSELECT owner, object_name, object_type, status FROM all_objects WHERE status = \'INVALID\';\nSELECT owner, name, type, line, position, text FROM all_errors ORDER BY owner, name, sequence;\n'
    payload['checks/postcheck.sql']=checks
    validation={'level':'OFFLINE_VALIDATED','execution_status':'NOT_EXECUTED',
                'checks':['CLOSED_JSON_SCHEMA','EVIDENCE_AND_CHANGE_REFERENCES','DEPENDENCY_ORDER','EMITTED_SQL_GRAMMAR_AND_IDENTITY','PAYLOAD_SHA256'],
                'limitations_tr':['Oracle üzerinde syntax/compile veya iş verisi doğrulaması yapılmadı.',
                                  'Eksik metadata, inceleme ve bloklar plan kapsamındadır; partial-ready.sql tam migration değildir.']}
    document=plan.with_operations(ops,validation=validation).to_dict()
    validate_plan(document)
    ready=[op.sql['path'] for op in ops if op.sql]
    if ready:
        payload['migration.sql' if plan.status=='READY' else 'partial-ready.sql']=aggregate_sql(ready,plan_id,partial=plan.status!='READY',source_commit=document['source']['commit_sha'],target_id=document['target']['id'])
    payload['plan.json']=canonical_bytes(document)+b'\n'
    payload['evidence.json']=canonical_bytes({'plan_id':plan_id,'evidence':thaw(plan.evidence)})+b'\n'
    payload['README.md']=(f'# Oracle DB Migration Generator\n\nPlan: `{plan_id}`\n\nDurum: {plan.status}. '
                          'Git source desired → Oracle target actual.\n\nVeritabanına uygulanmadı. Source ve target salt okunur. '
                          'Dosyaları çalıştırmadan önce plan.json içindeki kapsam, reason_codes ve bağımlılıkları inceleyin. '
                          'partial-ready.sql yalnız hazır alt kümedir; tam bir migration veya çalıştırma onayı değildir. '
                          'BLOCKED/REVIEW işlemleri aggregate SQL içine alınmaz.\n\n'
                          'Doğrulama: offline grammar, kimlik, kanıt bağlantıları ve hash; canlı Oracle compile/iş verisi testi yapılmadı.\n').encode()
    payload.update(navigation(document))
    payload.update(render_reports(document,payload))
    _scan(payload.values(),secret_values)
    manifest={'schema_version':'bundle-manifest/1.0','synthetic':plan.synthetic,'plan_id':plan_id,
              'target_id':document['target']['id'],'execution_status':'NOT_EXECUTED',
              'files':[{'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                        'media_type':mimetypes.guess_type(path)[0] or 'application/octet-stream'} for path,raw in sorted(payload.items())]}
    validate_document(manifest,'bundle-manifest.schema.json')
    payload['bundle-manifest.json']=canonical_bytes(manifest)+b'\n'
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.bundle-staging-',dir=output.parent)).resolve()
    assert temporary.parent==output.parent and temporary.name.startswith('.bundle-staging-')
    try:
        for path,raw in payload.items():
            target=safe_path(temporary,path);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        verify_bundle(temporary)
        # rename on Windows refuses replacing an existing destination.
        os.rename(temporary,output)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
    return {'status':'WRITTEN','plan_id':plan_id,'decision':plan.status,'counts':plan.counts,
            'comparison_complete':plan.scope.inventory==plan.scope.ddl==plan.scope.dictionary=='COMPLETE'
                and not any(diff.kind=='UNKNOWN' for diff in plan.differences)}


def verify_bundle(root):
    root=Path(root).resolve();manifest=read_json(root/'bundle-manifest.json')
    validate_document(manifest,'bundle-manifest.schema.json')
    paths=[item['path'] for item in manifest['files']]
    if len(set(paths))!=len(paths): raise ValueError('BUNDLE_DUPLICATE_PATH')
    for item in manifest['files']:
        path=safe_path(root,item['path'])
        if path.is_symlink() or not path.is_file(): raise ValueError('BUNDLE_FILE_MISSING_OR_UNSAFE')
        raw=path.read_bytes()
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']: raise ValueError('BUNDLE_INTEGRITY_MISMATCH')
    observed={path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file() or path.is_symlink()}
    if observed!=set(paths)|{'bundle-manifest.json'}: raise ValueError('BUNDLE_UNEXPECTED_FILES')
    document=validate_plan(read_json(root/'plan.json'))
    if document['plan_id']!=manifest['plan_id'] or document['target']['id']!=manifest['target_id']: raise ValueError('BUNDLE_PLAN_MISMATCH')
    for op in document['operations']:
        if op['sql']:
            raw=safe_path(root,op['sql']['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=op['sql']['sha256']: raise ValueError('BUNDLE_SQL_INTEGRITY_MISMATCH')
        for condition in op['postconditions']:
            if condition['check_path'] and not safe_path(root,condition['check_path']).is_file(): raise ValueError('BUNDLE_POSTCHECK_MISSING')
    if document['status']!='READY' and (root/'migration.sql').exists(): raise ValueError('BUNDLE_UNSAFE_AGGREGATE')
    ready=[op['sql']['path'] for op in document['operations'] if op['sql']]
    name='migration.sql' if document['status']=='READY' else 'partial-ready.sql'
    aggregates={p for p in ('migration.sql','partial-ready.sql') if (root/p).exists()}
    if aggregates != ({name} if ready else set()): raise ValueError('BUNDLE_UNSAFE_AGGREGATE')
    if ready and (root/name).read_bytes()!=aggregate_sql(ready,document['plan_id'],partial=document['status']!='READY',source_commit=document['source']['commit_sha'],target_id=document['target']['id']):
        raise ValueError('BUNDLE_AGGREGATE_MISMATCH')
    return {'status':'VERIFIED','plan_id':manifest['plan_id'],'files':len(paths),'execution_status':'NOT_EXECUTED'}
