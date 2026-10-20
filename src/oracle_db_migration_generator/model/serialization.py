"""Deterministic JSON primitives shared by snapshots, plans and artifacts."""
import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass


def thaw(value):
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw(item) for item in value]
    if is_dataclass(value):
        return {field.name: thaw(getattr(value, field.name)) for field in fields(value)}
    return value


def canonical_bytes(value) -> bytes:
    return json.dumps(thaw(value), sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
