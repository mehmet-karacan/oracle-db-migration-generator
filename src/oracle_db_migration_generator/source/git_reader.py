"""Raw Git blob reads pinned to one commit; no checkout, hooks, LFS or writes."""
import re
import subprocess
from dataclasses import replace
from pathlib import Path

from ..model.serialization import digest
from .layout import collect_layout, relevant_path
from .models import GitEntry, RepositoryReader, SourceError, SourceInput, SourceRevision

MAX_BLOB_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 128 * 1024 * 1024


class GitRepository:
    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        self._read('rev-parse', '--git-dir')

    def _read(self, *args: str, input_bytes=None) -> bytes:
        try:
            result = subprocess.run(['git', '--no-replace-objects', '--no-optional-locks',
                                     '-C', str(self.path), *args], input=input_bytes,
                                    capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            raise SourceError('SOURCE_GIT_READ_UNAVAILABLE') from None
        if result.returncode:
            raise SourceError('SOURCE_GIT_READ_FAILED')
        return result.stdout

    def resolve_commit(self, ref: str) -> str:
        if not ref or ref.startswith('-') or any(c in ref for c in '\x00\r\n'):
            raise SourceError('SOURCE_REF_INVALID')
        commit = self._read('rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode('ascii').strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
            raise SourceError('SOURCE_COMMIT_INVALID')
        return commit

    def entries(self, commit: str) -> tuple[GitEntry, ...]:
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
            raise SourceError('SOURCE_COMMIT_INVALID')
        result = []
        for row in self._read('ls-tree', '-r', '-z', commit).split(b'\x00'):
            if not row:
                continue
            metadata, raw_path = row.split(b'\t', 1)
            mode, kind, object_id = metadata.decode('ascii').split()
            try:
                path = raw_path.decode('utf-8')
            except UnicodeError:
                raise SourceError('SOURCE_PATH_ENCODING_UNRESOLVED') from None
            result.append(GitEntry(path, mode, kind, object_id))
        return tuple(result)

    def read_blobs(self, object_ids: tuple[str, ...]) -> dict[str, bytes]:
        ids = tuple(dict.fromkeys(object_ids))
        if any(not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', oid) for oid in ids):
            raise SourceError('SOURCE_BLOB_ID_INVALID')
        sizes = self._read('cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)',
                           input_bytes=''.join(oid + '\n' for oid in ids).encode())
        rows = sizes.decode('ascii').splitlines()
        if len(rows) != len(ids):
            raise SourceError('SOURCE_BLOB_METADATA_INVALID')
        total = 0
        for oid, row in zip(ids, rows):
            parts = row.split()
            if len(parts) != 3 or parts[0] != oid or parts[1] != 'blob':
                raise SourceError('SOURCE_BLOB_METADATA_INVALID')
            size = int(parts[2])
            if size > MAX_BLOB_BYTES:
                raise SourceError('SOURCE_BLOB_TOO_LARGE')
            total += size
        if total > MAX_SOURCE_BYTES:
            raise SourceError('SOURCE_INPUT_TOO_LARGE')
        payload = self._read('cat-file', '--batch', input_bytes=''.join(oid + '\n' for oid in ids).encode())
        offset, result = 0, {}
        for oid in ids:
            end = payload.index(b'\n', offset)
            parts = payload[offset:end].decode('ascii').split()
            if len(parts) != 3 or parts[0] != oid or parts[1] != 'blob':
                raise SourceError('SOURCE_BLOB_PAYLOAD_INVALID')
            size = int(parts[2])
            offset = end + 1
            result[oid] = payload[offset:offset + size]
            offset += size + 1
            if len(result[oid]) != size or payload[offset - 1:offset] != b'\n':
                raise SourceError('SOURCE_BLOB_PAYLOAD_INVALID')
        if offset != len(payload):
            raise SourceError('SOURCE_BLOB_PAYLOAD_INVALID')
        return result


def resolve_source(repo: RepositoryReader, ref: str) -> SourceRevision:
    return SourceRevision(repo.resolve_commit(ref), repo)


def read_source(revision: SourceRevision, profile) -> SourceInput:
    scoped = tuple(entry for entry in revision.repository.entries(revision.commit)
                   if any(entry.path.startswith(root.path + '/') for root in profile.schema_roots))
    if any(entry.mode not in {'100644', '100755'} or entry.kind != 'blob' for entry in scoped):
        raise SourceError('UNSAFE_GIT_ENTRY')
    blobs = revision.repository.read_blobs(tuple(entry.object_id for entry in scoped if relevant_path(entry.path)))
    entries = tuple(replace(entry, raw=blobs.get(entry.object_id)) for entry in scoped)
    artifacts = collect_layout(entries, profile)
    fingerprint = digest({'commit': revision.commit, 'profile': profile,
                          'files': [[item.path, item.kind, item.sha256] for item in artifacts]})
    return SourceInput(revision, artifacts, fingerprint, profile)
