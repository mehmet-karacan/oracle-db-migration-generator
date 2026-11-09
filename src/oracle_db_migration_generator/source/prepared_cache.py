"""Şema Karşılaştırma aynı Git içeriğinin doğrulanmış kaynak sonucunu saklar.

Kapasite dolduğunda yalnız hash'leri doğrulanmış en eski kayıt yenilenir.
Kullanılan kayıt korunur. Kaynak deposundaki dosyalar değiştirilmez.

A PARTIAL checkpoint stays PARTIAL, as with the explicit prepared-source resume.
Only identical pinned Git bytes, profile, preparation code and Python can reuse it.
The bounded parser response cache keeps its separate no-timeout-response policy.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

from ..config.loader import load_source_profile
from ..model.serialization import canonical_bytes, digest
from ..model.snapshot_io import load_snapshot, safe_path, write_source_snapshot, source_storage_paths
from ..parsing.fingerprint import parser_artifact_sha256
from ..parsing.response_cache import _guard_parents, _plain, _lock

MAX_CACHE_ENTRIES = 4
MAX_CACHE_BYTES = 1024 * 1024 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024


@lru_cache(maxsize=1)
def preparation_artifact_sha256():
    package = Path(__file__).resolve().parents[1]
    paths = [package/'cli.py']
    for directory in ('source', 'model', 'config'):
        paths.extend((package/directory).glob('*.py'))
    manifest = [[path.relative_to(package).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()]
                for path in sorted(paths, key=lambda path: path.relative_to(package).as_posix())]
    return digest([parser_artifact_sha256(), list(sys.version_info[:3]), manifest])


class PreparedSourceCache:
    """Git byte değerleri ve hazırlama sürümü aynıysa kayıtlı sonucu geri verir.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, root, inputs,*,runtime_fingerprint=None,max_entries=None,max_bytes=None):
        self.root = Path(os.path.abspath(root))
        self.inputs = inputs
        self.max_entries=max_entries
        self.max_bytes=max_bytes
        self.last_load_reason='NOT_ATTEMPTED'
        self.last_store_reason='NOT_ATTEMPTED'
        self.evicted_entries=0
        files = [{'path': a.path, 'kind': a.kind, 'owner': a.source_schema,
                  'type_hint': a.object_type_hint, 'sha256': hashlib.sha256(a.raw).hexdigest(),
                  'bytes': len(a.raw)} for a in inputs.artifacts]
        self.binding = {'schema_version': 'prepared-source-input/1.0',
                        'source_commit': inputs.revision.commit, 'input_digest': inputs.input_digest,
                        'profile_sha256': digest(inputs.profile), 'files': files,
                        'preparation_sha256': preparation_artifact_sha256()}
        if runtime_fingerprint is not None:self.binding['runtime_fingerprint']=runtime_fingerprint
        expected = digest({'commit': inputs.revision.commit, 'profile': inputs.profile,
                           'files': [[a.path, a.kind, a.sha256] for a in inputs.artifacts]})
        self.valid_input = (inputs.profile is not None and expected == inputs.input_digest
                            and all(a.sha256 == row['sha256'] for a, row in zip(inputs.artifacts, files)))
        self.key = digest(self.binding)
        self.path = self.root/self.key

    def _allowed_root(self):
        repository = getattr(self.inputs.revision.repository, 'path', None)
        return repository is None or not self.root.resolve().is_relative_to(Path(repository).resolve())

    def _bound(self, snapshot):
        def known(key, expected):
            value = snapshot.capabilities.get(key)
            return value is not None and value.state == 'KNOWN' and value.value == expected
        return (self.valid_input and snapshot.side == 'SOURCE'
                and snapshot.source_commit == self.inputs.revision.commit
                and snapshot.profile_id == self.inputs.profile.id
                and snapshot.schemas == tuple(root.source_schema for root in self.inputs.profile.schema_roots)
                and known('source_input_digest', self.inputs.input_digest)
                and known('source_profile_sha256', self.binding['profile_sha256']))

    def _load_at(self, root):
        _guard_parents(root); _plain(root, directory=True)
        manifest_path = root/'prepared-cache.json'
        if _plain(manifest_path).st_size > MAX_MANIFEST_BYTES:
            return None
        document = json.loads(manifest_path.read_bytes())
        if (set(document) != {'schema_version', 'binding', 'files', 'semantic_digest'}
                or document['schema_version'] != 'prepared-source-cache/1.0'
                or document['binding'] != self.binding or not isinstance(document['files'], dict)):
            return None
        storage = source_storage_paths(self.inputs)
        expected = {storage.get(a.path, a.path) for a in self.inputs.artifacts} | {
            'source-snapshot.json', 'source-input.json', 'source-profile.json'}
        if storage:
            expected.add('source-storage.json')
            if json.loads((root/'source-storage.json').read_bytes()) != {'schema_version': 'source-storage/1.0', 'paths': storage}:
                return None
        if set(document['files']) != expected:
            return None
        actual = set()
        for path in root.rglob('*'):
            _guard_parents(path)
            if path.is_file(): actual.add(path.relative_to(root).as_posix())
        if actual != expected | {'prepared-cache.json'}:
            return None
        for name, sha in document['files'].items():
            path = safe_path(root, name); _guard_parents(path)
            if (_plain(path).st_size > MAX_CACHE_BYTES or not isinstance(sha, str)
                    or not re.fullmatch('[0-9a-f]{64}', sha)
                    or hashlib.sha256(path.read_bytes()).hexdigest() != sha):
                return None
        if load_source_profile(root/'source-profile.json') != self.inputs.profile:
            return None
        expected_manifest = {'source_commit': self.inputs.revision.commit,
                             'input_digest': self.inputs.input_digest,
                             'files': [{'path': a.path, 'sha256': a.sha256} for a in self.inputs.artifacts]}
        if json.loads((root/'source-input.json').read_bytes()) != expected_manifest:
            return None
        # Compare current Git bytes independently of the cache's own hash manifest.
        if any(safe_path(root, storage.get(a.path, a.path)).read_bytes() != a.raw for a in self.inputs.artifacts):
            return None
        snapshot = load_snapshot(root/'source-snapshot.json', require_ddl=True)
        return snapshot if self._bound(snapshot) and snapshot.semantic_digest == document['semantic_digest'] else None

    def load(self):
        self.last_load_reason='INPUT_MISMATCH'
        if not self.valid_input: return None
        try:
            self.last_load_reason='ROOT_NOT_ALLOWED'
            if not self._allowed_root(): return None
            self.last_load_reason='NOT_FOUND'
            if not self.path.exists():return None
            self.last_load_reason='INVALID_ENTRY'
            snapshot=self._load_at(self.path)
            if snapshot is not None:
                self.last_load_reason='HIT_VERIFIED'
                try:os.utime(self.path,None)
                except OSError:pass
            return snapshot
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            self.last_load_reason='INVALID_ENTRY'
            return None

    def _owned_entry_size(self, entry):
        """Yalnız kapalı manifesti ve bütün dosya hash'leri doğrulanan kaydı tanır."""
        if entry.parent!=self.root or not re.fullmatch('[0-9a-f]{64}',entry.name):
            raise ValueError('UNVERIFIED_EXISTING_ENTRY')
        _guard_parents(entry);_plain(entry,directory=True)
        manifest=entry/'prepared-cache.json'
        if _plain(manifest).st_size>MAX_MANIFEST_BYTES:raise ValueError('UNVERIFIED_EXISTING_ENTRY')
        doc=json.loads(manifest.read_bytes())
        if (set(doc)!={'schema_version','binding','files','semantic_digest'}
                or doc['schema_version']!='prepared-source-cache/1.0'
                or not isinstance(doc['binding'],dict) or digest(doc['binding'])!=entry.name
                or not isinstance(doc['files'],dict)
                or not {'source-snapshot.json','source-input.json','source-profile.json'}<=set(doc['files'])):
            raise ValueError('UNVERIFIED_EXISTING_ENTRY')
        actual=set();size=0
        for path in entry.rglob('*'):
            _guard_parents(path)
            if path.is_dir():_plain(path,directory=True);continue
            size+=_plain(path).st_size;actual.add(path.relative_to(entry).as_posix())
        if actual!=set(doc['files'])|{'prepared-cache.json'}:raise ValueError('UNVERIFIED_EXISTING_ENTRY')
        for name,expected in doc['files'].items():
            path=safe_path(entry,name);_guard_parents(path);_plain(path)
            if (not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected)
                    or hashlib.sha256(path.read_bytes()).hexdigest()!=expected):
                raise ValueError('UNVERIFIED_EXISTING_ENTRY')
        return size

    def store(self, snapshot):
        self.evicted_entries=0
        self.last_store_reason='SNAPSHOT_BINDING_MISMATCH'
        if not self._bound(snapshot): return False
        try:
            self.last_store_reason='ROOT_NOT_ALLOWED'
            if not self._allowed_root(): return False
            _guard_parents(self.root)
            self.root.mkdir(parents=True, exist_ok=True); _plain(self.root, directory=True)
            self.last_store_reason='CACHE_BUSY'
            with _lock(self.root):
                if self.path.exists():
                    previous=self.load()
                    same=previous is not None and canonical_bytes(previous.to_dict())==canonical_bytes(snapshot.to_dict())
                    self.last_store_reason='ALREADY_VERIFIED' if same else 'INVALID_EXISTING_ENTRY'
                    return same
                self.last_store_reason='UNVERIFIED_EXISTING_ENTRY'
                entries=[p for p in self.root.iterdir() if p.name!='.lock']
                sizes={entry:self._owned_entry_size(entry) for entry in entries}
                used=sum(sizes.values())
                # Yeni kayıt doğrulanmadan mevcut bir kayıt kaldırılmaz.
                self.last_store_reason='STAGED_VALIDATION_FAILED'
                with tempfile.TemporaryDirectory(prefix='.prepared-staging-', dir=self.root.parent) as temporary:
                    staged=Path(temporary)/'payload'
                    write_source_snapshot(snapshot,self.inputs,staged)
                    files={p.relative_to(staged).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in staged.rglob('*') if p.is_file()}
                    manifest={'schema_version':'prepared-source-cache/1.0','binding':self.binding,
                              'files':files,'semantic_digest':snapshot.semantic_digest}
                    (staged/'prepared-cache.json').write_bytes(canonical_bytes(manifest)+b'\n')
                    size=sum(p.stat().st_size for p in staged.rglob('*') if p.is_file())
                    if size>(self.max_bytes or MAX_CACHE_BYTES):
                        self.last_store_reason='ENTRY_TOO_LARGE';return False
                    if self._load_at(staged) is None:return False
                    ordered=sorted(entries,key=lambda p:(p.stat().st_mtime_ns,p.name))
                    while ordered and (len(ordered)>=(self.max_entries or MAX_CACHE_ENTRIES)
                                       or used+size>(self.max_bytes or MAX_CACHE_BYTES)):
                        victim=ordered.pop(0)
                        if victim.parent!=self.root:raise ValueError('CACHE_PATH_OUTSIDE_ROOT')
                        _guard_parents(victim);_plain(victim,directory=True)
                        shutil.rmtree(victim)
                        used-=sizes[victim];self.evicted_entries+=1
                    os.rename(staged,self.path)
            self.last_store_reason='STORED_VERIFIED'
            return True
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return False
