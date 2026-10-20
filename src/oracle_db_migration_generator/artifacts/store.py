"""Local immutable plan store. No network, Git commands or database connection."""
import hashlib
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from ..config.loader import read_json, validate_document
from ..model.serialization import canonical_bytes
from ..model.snapshot_io import safe_path
from .bundle import _scan, verify_bundle
from .layout import component, markdown

MARKER = '.artifact-store.json'


def _namespace(path):
    if path in {'README.md','catalog.json'}: return
    safe_component=r'[A-Za-z0-9_-]{1,80}'
    allowed=(re.fullmatch(r'plans/'+safe_component+'/'+safe_component+r'/[a-f0-9]{64}/.+',path)
             or re.fullmatch(r'runs/\d{4}/\d{2}/\d{2}/build-[A-Za-z0-9-]+/(README\.md|run\.json)',path)
             or re.fullmatch(r'latest/'+safe_component+'/'+safe_component+r'\.json',path))
    if not allowed or any(p.startswith('.') for p in path.split('/')): raise ValueError('STORE_NAMESPACE_UNSAFE')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_files(root):
    root = Path(root).resolve()
    marker = root/MARKER
    if marker.is_symlink(): raise ValueError('STORE_NOT_OWNED')
    if not marker.exists():
        if any(p.name != '.git' for p in root.iterdir()):
            raise ValueError('STORE_NOT_OWNED')
        return {}
    data = read_json(marker)
    if set(data) != {'schema_version', 'files'} or data['schema_version'] != 'artifact-store/1.0' or not isinstance(data['files'], dict):
        raise ValueError('STORE_NOT_OWNED')
    for path, expected in data['files'].items():
        _namespace(path)
        if not isinstance(expected,str) or not re.fullmatch('[a-f0-9]{64}',expected): raise ValueError('STORE_NOT_OWNED')
        target = safe_path(root, path)
        if any(p.is_symlink() for p in (target,*target.parents) if p.is_relative_to(root)) or not target.is_file() or sha(target.read_bytes()) != expected:
            raise ValueError('INTEGRITY_CONFLICT')
    return data['files']


def _atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.artifact-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def write_owned(root, payload, *, secret_values=()):
    """Caller holds store lock. Validate everything before writing; rollback owned bytes."""
    root = Path(root).resolve()
    old = owned_files(root)
    _scan(payload.values(), secret_values)
    for path in payload:
        _namespace(path)
        target = safe_path(root, path)
        if target.exists() and path not in old:
            raise ValueError('STORE_UNOWNED_PATH')
        if any(p.is_symlink() for p in (target,*target.parents) if p.is_relative_to(root)): raise ValueError('STORE_UNSAFE_PATH')
    changes = {path: raw for path, raw in payload.items() if old.get(path) != sha(raw)}
    previous = {path: safe_path(root, path).read_bytes() if path in old else None for path in changes}
    new_dirs={p for path in changes for p in safe_path(root,path).parents if p!=root and p.is_relative_to(root) and not p.exists()}
    hashes = {**old, **{path: sha(raw) for path, raw in payload.items()}}
    done = []
    try:
        for path, raw in changes.items():
            _atomic(safe_path(root, path), raw); done.append(path)
        _atomic(root/MARKER, canonical_bytes({'schema_version': 'artifact-store/1.0', 'files': hashes}) + b'\n')
    except BaseException:
        for path in reversed(done):
            target = safe_path(root, path)
            if previous[path] is None: target.unlink()
            else: _atomic(target, previous[path])
        for directory in sorted(new_dirs,key=lambda p:len(p.parts),reverse=True):
            if directory.is_dir() and not any(directory.iterdir()): directory.rmdir()
        raise
    return hashes


class StoreLock:
    def __init__(self, root): self.path = Path(root).resolve().with_name(Path(root).name + '.artifact-lock')
    def __enter__(self):
        try: self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError: raise ValueError('STORE_BUSY') from None
        return self
    def __exit__(self, *args):
        os.close(self.fd); self.path.unlink()


def archive_run(run_root, store, *, build_number=None, secret_values=()):
    run_root, store = Path(run_root).resolve(), Path(store).resolve()
    if run_root == store or run_root.is_relative_to(store) or store.is_relative_to(run_root):
        raise ValueError('STORE_OVERLAPS_RUN')
    run = read_json(run_root/'run.json'); validate_document(run, 'run.schema.json')
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,64}', run['run_id']): raise ValueError('RUN_ID_UNSAFE')
    if build_number is not None and (type(build_number) is not int or build_number < 0): raise ValueError('BUILD_NUMBER_INVALID')
    try: date = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00')).strftime('%Y/%m/%d')
    except ValueError: raise ValueError('RUN_DATE_INVALID') from None
    if len({t['id'] for t in run['targets']}) != len(run['targets']): raise ValueError('RUN_DUPLICATE_TARGET')
    store.mkdir(parents=True, exist_ok=True)
    with StoreLock(store):
        old = owned_files(store)
        catalog = read_json(store/'catalog.json') if 'catalog.json' in old else {'schema_version':'catalog/1.0','runs':[], 'plans':[]}
        validate_document(catalog, 'catalog.schema.json')
        payload = {}; new = reused = 0
        run_path = f"runs/{date}/build-{build_number if build_number is not None else 'local'}-{run['run_id']}"
        if any(item['run_id']==run['run_id'] for item in catalog['runs']): raise ValueError('RUN_ALREADY_ARCHIVED')
        archived = {**run, 'build_number':build_number, 'artifact_git_sha':None, 'targets':[]}
        lines = ['# Oracle Migration çalışma kaydı', '', f"Run: `{run['run_id']}` · Build: {build_number if build_number is not None else 'Yerel'}", '',
                 f"Kaynak SHA: `{run['source_commit']}`", '', 'Üretildi · Veritabanına uygulanmadı. Source ve target salt okunur.', '', '[Çalışma JSON](run.json)', '', '## Hedefler', '']
        for result in run['targets']:
            item = dict(result)
            if item['plan_path']:
                bundle = safe_path(run_root, item['plan_path']).parent
                verify_bundle(bundle); plan = read_json(bundle/'plan.json')
                known = plan['scope']['inventory']==plan['scope']['ddl']==plan['scope']['dictionary']=='COMPLETE' and not any(d['kind']=='UNKNOWN' for d in plan['differences'])
                expected = plan['counts']['observed_differences'] if known else None
                if (item['id']!=plan['target']['id'] or item['plan_id']!=plan['plan_id'] or item['status']!=plan['status'] or item['difference_count']!=expected or run['source_commit']!=plan['source']['commit_sha']):
                    raise ValueError('RUN_RESULT_PLAN_MISMATCH')
                profile = plan['source']['profile_id']
                folder = f"plans/{component(profile)}/{component(item['id'])}/{plan['plan_id']}"
                files = {p.relative_to(bundle).as_posix():p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
                existing = {p[len(folder)+1:]:h for p,h in old.items() if p.startswith(folder+'/')}
                if existing:
                    if existing != {p:sha(raw) for p,raw in files.items()}: raise ValueError('INTEGRITY_CONFLICT')
                    reused += 1
                else:
                    new += 1
                    payload.update({folder+'/'+p:raw for p,raw in files.items()})
                    catalog['plans'].append({'plan_id':plan['plan_id'],'path':folder,'profile_id':profile,'target_id':item['id']})
                item['plan_path'] = folder+'/plan.json'
                relative = os.path.relpath(store/folder, store/run_path).replace('\\','/')
                links = [f'[Plan]({relative}/README.md)', f'[plan.json]({relative}/plan.json)', f'[Manifest]({relative}/bundle-manifest.json)']
                aggregate = 'migration.sql' if plan['status']=='READY' else 'partial-ready.sql'
                if aggregate in files: links.append(f'[Genel DDL]({relative}/{aggregate})')
                lines.append(f"- {markdown(item['id'])} · {item['status']} · " + ' · '.join(links))
                payload[f"latest/{component(profile)}/{component(item['id'])}.json"] = canonical_bytes({'run_path':run_path,'plan_path':folder,'plan_id':plan['plan_id']})+b'\n'
            else:
                if item['status'] not in {'ERROR','INCONSISTENT'} or item['plan_id'] is not None or item['difference_count'] is not None:
                    raise ValueError('RUN_ERROR_MUST_BE_UNKNOWN')
                lines.append(f"- {markdown(item['id'])} · {item['status']} / UNKNOWN · {markdown(item['error_code'] or 'UNKNOWN')}")
            archived['targets'].append(item)
        validate_document(archived, 'run.schema.json')
        payload[run_path+'/run.json'] = canonical_bytes(archived)+b'\n'
        payload[run_path+'/README.md'] = ('\n'.join(lines)+'\n').encode('utf-8')
        catalog['runs'].append({'run_id':run['run_id'],'path':run_path,'status':run['status'],'source_commit':run['source_commit']})
        validate_document(catalog, 'catalog.schema.json')
        payload['catalog.json'] = canonical_bytes(catalog)+b'\n'
        payload['README.md'] = ('# Oracle Migration Artifact Kataloğu\n\nÜretildi · Veritabanına uygulanmadı.\n\n'
            + '\n'.join(f"- [{markdown(r['run_id'])}]({r['path']}/README.md) · {r['status']}" for r in reversed(catalog['runs']))
            + '\n\n[Hafif katalog](catalog.json)\n').encode('utf-8')
        write_owned(store, payload, secret_values=secret_values)
        return {'status':'ARCHIVED','run_path':run_path,'new_plans':new,'reused_plans':reused}
