"""Per-process execution budgets; CLI defaults remain byte-for-byte compatible."""
from contextvars import ContextVar
from contextlib import contextmanager

_settings=ContextVar('generator_runtime_settings',default={})


def current_settings():return _settings.get()


@contextmanager
def runtime_settings(settings):
    token=_settings.set(dict(settings))
    try:yield
    finally:_settings.reset(token)
