"""Verified completed source checkpoints; live metadata is never cached here.

A PARTIAL checkpoint stays PARTIAL, as with the explicit prepared-source resume.
Only identical pinned Git bytes, profile, preparation code and Python can reuse it.
The bounded parser response cache keeps its separate no-timeout-response policy.
"""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from ..config.loader import load_source_profile
from ..model.serialization import canonical_bytes, digest
from ..model.snapshot_io import load_snapshot, safe_path, write_source_snapshot
from ..parsing.fingerprint import parser_artifact_sha256
from ..parsing.response_cache import _guard_parents, _plain

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
    def __init__(self, root, inputs,*,runtime_fingerprint=None,max_entries=None,max_bytes=None):
        self.root = Path(os.path.abspath(root))
        self.inputs = inputs
        self.max_entries=max_entries
        self.max_bytes=max_bytes
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
        expected = {a.path for a in self.inputs.artifacts} | {
            'source-snapshot.json', 'source-input.json', 'source-profile.json'}
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
        if any(safe_path(root, a.path).read_bytes() != a.raw for a in self.inputs.artifacts):
            return None
        snapshot = load_snapshot(root/'source-snapshot.json', require_ddl=True)
        return snapshot if self._bound(snapshot) and snapshot.semantic_digest == document['semantic_digest'] else None

    def load(self):
        if not self.valid_input: return None
        try:
            if not self._allowed_root(): return None
            return self._load_at(self.path)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return None

    def store(self, snapshot):
        if not self._bound(snapshot): return False
        try:
            if not self._allowed_root(): return False
            _guard_parents(self.root)
            self.root.mkdir(parents=True, exist_ok=True); _plain(self.root, directory=True)
            if self.path.exists():
                previous = self.load()
                return previous is not None and canonical_bytes(previous.to_dict()) == canonical_bytes(snapshot.to_dict())
            entries = list(self.root.iterdir())
            if (len(entries) >= (self.max_entries or MAX_CACHE_ENTRIES) or any(not re.fullmatch('[0-9a-f]{64}', p.name)
                                                       or p.is_symlink() for p in entries)):
                return False
            used = sum(_plain(p).st_size for entry in entries for p in entry.rglob('*') if p.is_file())
            with tempfile.TemporaryDirectory(prefix='.prepared-staging-', dir=self.root) as temporary:
                staged = Path(temporary)/'payload'
                write_source_snapshot(snapshot, self.inputs, staged)
                files = {p.relative_to(staged).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in staged.rglob('*') if p.is_file()}
                manifest = {'schema_version': 'prepared-source-cache/1.0', 'binding': self.binding,
                            'files': files, 'semantic_digest': snapshot.semantic_digest}
                (staged/'prepared-cache.json').write_bytes(canonical_bytes(manifest)+b'\n')
                size = sum(p.stat().st_size for p in staged.rglob('*') if p.is_file())
                if used+size > (self.max_bytes or MAX_CACHE_BYTES) or self._load_at(staged) is None:
                    return False
                os.rename(staged, self.path)
            return True
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return False
