"""Interpret by_object v1 or flat; do not execute repository metadata."""
import hashlib
import json
from pathlib import PurePosixPath

from .models import GitEntry, SourceArtifact, SourceError

TYPE_DIRS = {
    'tables':'TABLE', 'indexes':'INDEX', 'sequences':'SEQUENCE', 'views':'VIEW',
    'packages':'PACKAGE_SPEC', 'procedures':'PROCEDURE', 'functions':'FUNCTION',
    'triggers':'TRIGGER', 'types':'TYPE_SPEC', 'synonyms':'SYNONYM',
    'materialized_views':'MATERIALIZED_VIEW', 'materialized_view_logs':'MATERIALIZED_VIEW_LOG',
}
FLAT_DIRS = {key.replace('_', ''): value for key, value in TYPE_DIRS.items()}
FLAT_DIRS.update(comments='COMMENT', grants='GRANT')
SIDECARS = {'comments.sql':'COMMENT', 'grants.sql':'GRANT',
            'dependencies.json':'DEPENDENCIES', '_manifest.json':'MANIFEST'}


def relevant_path(path: str) -> bool:
    return path.lower().endswith('.sql') or PurePosixPath(path).name in SIDECARS


def collect_layout(entries: tuple[GitEntry, ...], profile) -> tuple[SourceArtifact, ...]:
    artifacts = []
    for root in profile.schema_roots:
        prefix = root.path + '/'
        scoped = [entry for entry in entries if entry.path.startswith(prefix)]
        if not scoped:
            raise SourceError('SOURCE_SCOPE_MISSING')
        for entry in sorted(scoped, key=lambda item: item.path):
            path = PurePosixPath(entry.path)
            if path.is_absolute() or any(part in {'.', '..'} for part in path.parts) or '\\' in entry.path:
                raise SourceError('UNSAFE_SOURCE_PATH')
            if entry.mode not in {'100644', '100755'} or entry.kind != 'blob':
                raise SourceError('UNSAFE_GIT_ENTRY')
            if not relevant_path(entry.path):
                continue
            if entry.raw is None:
                raise SourceError('SOURCE_BLOB_MISSING')
            if b'\x00' in entry.raw or entry.raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise SourceError('SOURCE_NOT_SQL_OR_METADATA')
            relative = entry.path[len(prefix):].split('/')
            kind = SIDECARS.get(path.name, 'DDL')
            hint = None
            if kind == 'MANIFEST':
                try:
                    manifest = json.loads(entry.raw.decode('utf-8-sig'))
                except (UnicodeError, json.JSONDecodeError):
                    raise SourceError('SOURCE_MANIFEST_INVALID') from None
                if (manifest.get('schema') != root.source_schema or manifest.get('layout') != profile.layout
                        or manifest.get('layout_version') != profile.layout_version):
                    raise SourceError('SOURCE_MANIFEST_MISMATCH')
            if kind in {'DDL', 'COMMENT', 'GRANT'}:
                if profile.layout == 'by_object':
                    if relative[0] not in TYPE_DIRS:
                        raise SourceError('SOURCE_LAYOUT_MISMATCH')
                    hint = TYPE_DIRS[relative[0]]
                    for segment in relative[1:-1]:
                        if segment in {'indexes', 'triggers', 'synonyms'}:
                            hint = TYPE_DIRS[segment]
                    if path.name == 'body.sql' and hint in {'PACKAGE_SPEC', 'TYPE_SPEC'}:
                        hint = hint.replace('_SPEC', '_BODY')
                else:
                    hint = FLAT_DIRS.get(relative[0].lower())
                    if hint is None:
                        raise SourceError('SOURCE_LAYOUT_MISMATCH')
                    if hint in {'COMMENT', 'GRANT'}:
                        kind = hint
                if kind != 'DDL':
                    hint = kind
            artifacts.append(SourceArtifact(entry.path, root.source_schema, kind, hint, entry.raw,
                                            hashlib.sha256(entry.raw).hexdigest()))
    if not artifacts:
        raise SourceError('SOURCE_SCOPE_EMPTY')
    return tuple(sorted(artifacts, key=lambda item: item.path))
