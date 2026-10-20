"""Explicit JSON transport for the controlled vendor dataclasses; no pickle."""
from dataclasses import fields, is_dataclass

from .._vendor.analyzer_core.oracle.dynamic_sql import DynamicSqlProfile
from .._vendor.analyzer_core.oracle.package import Parameter, Routine
from .._vendor.analyzer_core.oracle.projections import Projection

TYPES = {item.__name__: item for item in (Projection, Parameter, Routine, DynamicSqlProfile)}


def encode(value):
    if is_dataclass(value):
        return {'$type': type(value).__name__, 'fields': {f.name: encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, tuple):
        return {'$tuple': [encode(item) for item in value]}
    if isinstance(value, list):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


def decode(value):
    if isinstance(value, list):
        return [decode(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {'$tuple'}:
            return tuple(decode(item) for item in value['$tuple'])
        if set(value) == {'$type', 'fields'}:
            return TYPES[value['$type']](**{key: decode(item) for key, item in value['fields'].items()})
        return {key: decode(item) for key, item in value.items()}
    return value
