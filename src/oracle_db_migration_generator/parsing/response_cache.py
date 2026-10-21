"""Optional exact-byte parser responses; fresh metadata capture is never reused."""
from contextlib import contextmanager
import base64
from dataclasses import fields
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import zlib
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from .codec import TYPES, decode
from .fingerprint import PARSER_VERSION, parser_artifact_sha256

MAX_ENTRY_BYTES = 1024 * 1024
MAX_DECODED_BYTES = 32 * 1024 * 1024
MAX_BUCKET_BYTES = 1024 * 1024
MAX_BUCKET_ENTRIES = 128
_ENTRY = re.compile(r'[0-9a-f]{64}\.json\Z')
_OBJECT_FIELDS = {'object_type', 'raw_schema', 'schema_quoted', 'raw_name', 'name_quoted',
                  'start_char', 'end_char', 'parse_ok', 'diagnostics', 'projection'}
_SIDECAR_KINDS = {'COMMENT', 'GRANT', 'ALTER_TABLE', 'ALTER_TRIGGER', 'ALTER_INDEX'}


def json_bytes(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('CACHE_DUPLICATE_KEY')
        result[key] = value
    return result


def _plain(path, *, directory=False):
    info = path.lstat()
    if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('CACHE_REPARSE_POINT')
    if directory and not stat.S_ISDIR(info.st_mode):
        raise ValueError('CACHE_NOT_DIRECTORY')
    if not directory and not stat.S_ISREG(info.st_mode):
        raise ValueError('CACHE_NOT_REGULAR')
    return info


def _guard_parents(path):
    for parent in (path, *path.parents):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if parent.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('CACHE_REPARSE_POINT')


def _wire(value):
    if value is None or type(value) in {str, bool, int, float}:
        return True
    if isinstance(value, list):
        return all(_wire(item) for item in value)
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        return False
    if set(value) == {'$tuple'}:
        return isinstance(value['$tuple'], list) and all(_wire(item) for item in value['$tuple'])
    if set(value) == {'$type', 'fields'}:
        kind = TYPES.get(value['$type']) if isinstance(value['$type'], str) else None
        return (kind is not None and isinstance(value['fields'], dict)
                and set(value['fields']) == {field.name for field in fields(kind)}
                and all(_wire(item) for item in value['fields'].values()))
    return all(_wire(item) for item in value.values())


@lru_cache(maxsize=len(TYPES))
def _annotations(kind):
    return get_type_hints(kind)


def _typed(value, annotation):
    """Validate decoded transport dataclasses without coercing any field."""
    if annotation in {Any, object}:
        if type(value) in TYPES.values():
            return _typed(value, type(value))
        if isinstance(value, dict):
            return all(type(key) is str and _typed(item, Any) for key, item in value.items())
        if isinstance(value, (tuple, list)):
            return all(_typed(item, Any) for item in value)
        return value is None or type(value) in {str, bool, int, float}
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in {UnionType, Union}:
        return any(_typed(value, item) for item in args)
    if origin is dict:
        return (type(value) is dict and all(_typed(key, args[0]) and _typed(item, args[1])
                                           for key, item in value.items()))
    if origin in {tuple, list}:
        if type(value) is not origin:
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_typed(item, args[0]) for item in value)
        return len(value) == len(args) and all(_typed(item, kind) for item, kind in zip(value, args))
    if annotation in TYPES.values():
        return type(value) is annotation and all(_typed(getattr(value, key), kind)
                                                for key, kind in _annotations(annotation).items())
    return type(value) is annotation


def _projection_shape(encoded, object_type, source_text):
    from .projections import normalize_projection
    try:
        projection = decode(encoded)
        if (not _typed(projection, TYPES['Projection']) or projection.object_type != object_type
                or projection.support != 'structural'):
            return False
        properties = projection.properties
        families = {'columns': dict[str, dict[str, str | None]],
                    'routines': tuple[TYPES['Routine'], ...],
                    'declarations': dict[str, tuple[str, ...]],
                    'constraints': dict[str, str], 'comments': dict[str, str], 'partitions': dict[str, str],
                    'table_properties': dict[str, str | None], 'index_properties': dict[str, str | None],
                    'query_clauses': dict[str, str | None]}
        if any(key in properties and not _typed(properties[key], kind) for key, kind in families.items()):
            return False
        # Check the same consumption boundary as parse_ddl. This also rejects
        # malformed Generator extension records before a cache hit can escape.
        normalized = normalize_projection(projection, source_text)
        return (_typed(normalized, TYPES['Projection']) and normalized.diagnostics == ()
                and all(key not in normalized.properties or _typed(normalized.properties[key], kind)
                        for key, kind in families.items()))
    except (AttributeError, KeyError, TypeError, ValueError, IndexError, RecursionError):
        return False


def verified_payload(payload, raw):
    if not isinstance(payload, dict) or set(payload) != {'objects', 'sidecars', 'diagnostics'}:
        return False
    if payload['diagnostics'] != [] or not isinstance(payload['objects'], list) or not isinstance(payload['sidecars'], list):
        return False
    text = raw.decode('utf-8')
    for obj in payload['objects']:
        if not isinstance(obj, dict) or set(obj) != _OBJECT_FIELDS:
            return False
        if obj['parse_ok'] is not True or obj['diagnostics'] != []:
            return False
        if (not isinstance(obj['object_type'], str) or not isinstance(obj['raw_name'], str)
                or obj['raw_schema'] is not None and not isinstance(obj['raw_schema'], str)
                or type(obj['schema_quoted']) is not bool or type(obj['name_quoted']) is not bool):
            return False
        if not (type(obj['start_char']) is int and type(obj['end_char']) is int
                and 0 <= obj['start_char'] < obj['end_char'] <= len(text)):
            return False
        projection = obj['projection']
        if (not isinstance(projection, dict) or set(projection) != {'$type', 'fields'}
                or projection['$type'] != 'Projection' or not _wire(projection)
                or projection['fields']['diagnostics'] != {'$tuple': []}
                or not _projection_shape(projection, obj['object_type'], text[obj['start_char']:obj['end_char']])):
            return False
    for item in payload['sidecars']:
        if not isinstance(item, dict) or set(item) != {'kind', 'text', 'start_char', 'end_char'}:
            return False
        if item['kind'] not in _SIDECAR_KINDS or not isinstance(item['text'], str):
            return False
        begin, end = item['start_char'], item['end_char']
        if not (type(begin) is int and type(end) is int and 0 <= begin < end <= len(text)
                and text[begin:end] == item['text']):
            return False
    return True


@contextmanager
def _lock(bucket):
    path = bucket/'.lock'
    _guard_parents(path)
    with path.open('a+b') as stream:
        _plain(path)
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class ParserResponseCache:
    def __init__(self, root, raw, owner, metadata):
        self.root = Path(os.path.abspath(root))
        self.raw = raw
        self.input = {'schema_version': 'parser-input/1.0', 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                      'raw_bytes': len(raw), 'default_schema': owner, 'metadata': bool(metadata),
                      'parser_artifact_sha256': parser_artifact_sha256(), 'parser_version': PARSER_VERSION}
        self.key = hashlib.sha256(json_bytes(self.input)).hexdigest()
        self.bucket = self.root/self.key[:2]
        self.path = self.bucket/(self.key+'.json')

    def load(self):
        try:
            _guard_parents(self.path)
            info = _plain(self.path)
            if info.st_size > MAX_ENTRY_BYTES:
                return None
            with self.path.open('rb') as stream:
                _guard_parents(self.path)
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                    return None
                data = stream.read(MAX_ENTRY_BYTES+1)
            if len(data) > MAX_ENTRY_BYTES:
                return None
            document = json.loads(data, object_pairs_hook=_unique)
            if not isinstance(document,dict):
                return None
            if document.get('schema_version')=='parser-response-cache/zlib-1.0':
                if set(document)!={'schema_version','compressed'} or not isinstance(document['compressed'],str):
                    return None
                packed=base64.b64decode(document['compressed'],validate=True)
                decoder=zlib.decompressobj()
                decoded=decoder.decompress(packed,MAX_DECODED_BYTES+1)
                if len(decoded)>MAX_DECODED_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                    return None
                document=json.loads(decoded,object_pairs_hook=_unique)
                if not isinstance(document,dict):
                    return None
            if (set(document) != {'schema_version', 'input', 'payload_sha256', 'payload'}
                    or document['schema_version'] != 'parser-response-cache/1.0'
                    or not isinstance(document['input'], dict) or set(document['input']) != set(self.input)
                    or any(type(document['input'][key]) is not type(value) or document['input'][key] != value
                           for key, value in self.input.items())
                    or hashlib.sha256(json_bytes(document['payload'])).hexdigest() != document['payload_sha256']
                    or not verified_payload(document['payload'], self.raw)):
                return None
            return document['payload']
        except (OSError, ValueError, TypeError, KeyError, RecursionError, zlib.error):
            return None

    def store(self, payload):
        temporary = None
        try:
            if not verified_payload(payload, self.raw):
                return
            document = {'schema_version': 'parser-response-cache/1.0', 'input': self.input,
                        'payload_sha256': hashlib.sha256(json_bytes(payload)).hexdigest(), 'payload': payload}
            data = json_bytes(document)
            if len(data)>MAX_DECODED_BYTES:
                return
            if len(data)>MAX_ENTRY_BYTES:
                data=json_bytes({'schema_version':'parser-response-cache/zlib-1.0',
                                 'compressed':base64.b64encode(zlib.compress(data)).decode('ascii')})
            if len(data) > min(MAX_ENTRY_BYTES, MAX_BUCKET_BYTES):
                return
            _guard_parents(self.bucket)
            self.bucket.mkdir(parents=True, exist_ok=True)
            _guard_parents(self.bucket); _plain(self.bucket, directory=True)
            with _lock(self.bucket):
                entries = []
                for path in self.bucket.iterdir():
                    if _ENTRY.fullmatch(path.name):
                        info = _plain(path)
                        if path != self.path:
                            entries.append((info.st_mtime_ns, path.name, path, info.st_size))
                    elif path.name != '.lock':
                        # Unknown files are never deleted or followed.
                        return
                entries.sort()
                total = sum(item[3] for item in entries)
                while entries and (len(entries) >= MAX_BUCKET_ENTRIES or total+len(data) > MAX_BUCKET_BYTES):
                    _, _, path, size = entries.pop(0)
                    path.unlink(); total -= size
                _guard_parents(self.path)
                if self.path.exists():
                    _plain(self.path)
                with tempfile.NamedTemporaryFile(dir=self.bucket, prefix='.tmp-', delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary, self.path)
                temporary = None
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except OSError:
                    pass


def configured_cache(raw, owner, metadata):
    root = os.environ.get('GENERATOR_PARSER_CACHE_DIR')
    if not root:
        return None
    try:
        return ParserResponseCache(root, raw, owner, metadata)
    except (OSError, ValueError, TypeError):
        return None
