"""Closed JSON contracts and semantic checks; errors never echo input values."""
import json
from importlib.resources import files
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator

from ..model.identity import Identifier
from .credentials import credential_prefix
from .models import Endpoint, Policy, SchemaMapping, SchemaRoot, SourceProfile, TargetConfig


class ConfigError(ValueError):
    exit_code = 30


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_keys)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ConfigError("CONFIG_UNREADABLE_OR_INVALID_JSON") from None
    if not isinstance(document, dict):
        raise ConfigError("CONFIG_EXPECTED_OBJECT")
    return document


def validate_document(document: dict, schema_name: str) -> None:
    schema = json.loads(files('oracle_db_migration_generator').joinpath('schemas', schema_name).read_text(encoding='utf-8'))
    if next(Draft202012Validator(schema).iter_errors(document), None) is not None:
        raise ConfigError("CONFIG_SCHEMA_INVALID")


def _owner(raw: str) -> str:
    try:
        return Identifier.parse(raw).effective_name
    except ValueError:
        raise ConfigError("INVALID_SCHEMA_IDENTIFIER") from None


def load_source_profile(path: Path) -> SourceProfile:
    data = read_json(path)
    validate_document(data, "source-profile.schema.json")
    roots = tuple(SchemaRoot(**root) for root in data['schema_roots'])
    owners = [_owner(root.source_schema) for root in roots]
    if len(set(owners)) != len(owners):
        raise ConfigError("DUPLICATE_SOURCE_SCHEMA")
    for index, root in enumerate(roots):
        parts = root.path.split('/')
        if any(part in ('', '.', '..') for part in parts):
            raise ConfigError("INVALID_SOURCE_ROOT")
        for other in roots[:index]:
            left, right = PurePosixPath(root.path), PurePosixPath(other.path)
            if left == right or left in right.parents or right in left.parents:
                raise ConfigError("OVERLAPPING_SOURCE_ROOTS")
    if len(set(data['object_types'])) != len(data['object_types']):
        raise ConfigError("DUPLICATE_OBJECT_TYPE")
    policy = dict(data['policy'])
    policy['grant_allowlist'] = tuple(policy['grant_allowlist'])
    return SourceProfile(data['schema_version'], data['id'], data['layout'], data['layout_version'], roots,
                         tuple(data['object_types']), data['source_length_semantics'], Policy(**policy))


def load_targets(path: Path, selected: tuple[str, ...]) -> tuple[TargetConfig, ...]:
    data = read_json(path)
    validate_document(data, "targets.schema.json")
    targets = []
    ids = set()
    credential_keys = {}
    for item in data['targets']:
        if item['id'] in ids:
            raise ConfigError("DUPLICATE_TARGET_ID")
        ids.add(item['id'])
        source_owners, target_owners = set(), set()
        for mapping in item['schema_mappings']:
            credential_id = mapping['credential_id']
            key = credential_prefix(credential_id)
            if key in credential_keys and credential_keys[key] != credential_id:
                raise ConfigError("CREDENTIAL_ENV_KEY_COLLISION")
            credential_keys[key] = credential_id
            source, target = _owner(mapping['source_schema']), _owner(mapping['target_schema'])
            if source != target:
                raise ConfigError("SCHEMA_REMAP_NOT_SUPPORTED")
            if source in source_owners or target in target_owners:
                raise ConfigError("DUPLICATE_SCHEMA_MAPPING")
            source_owners.add(source)
            target_owners.add(target)
        endpoint = item['endpoint']
        host = endpoint['host']
        if host != host.strip() or any(c.isspace() or c in '/@\\:' for c in host):
            raise ConfigError("INVALID_ENDPOINT_HOST")
        targets.append(TargetConfig(item['id'], item['name'], item['enabled'], Endpoint(**endpoint),
                                    item['driver_mode'], tuple(SchemaMapping(**m) for m in item['schema_mappings'])))
    if not selected or len(set(selected)) != len(selected) or ('ALL' in selected and selected != ('ALL',)):
        raise ConfigError("INVALID_TARGET_SELECTION")
    enabled = {t.id: t for t in targets if t.enabled}
    if selected == ('ALL',):
        result = tuple(enabled.values())
    else:
        if any(key not in enabled for key in selected):
            raise ConfigError("UNKNOWN_OR_DISABLED_TARGET")
        result = tuple(enabled[key] for key in selected)
    if not result:
        raise ConfigError("NO_ENABLED_TARGETS")
    return result
