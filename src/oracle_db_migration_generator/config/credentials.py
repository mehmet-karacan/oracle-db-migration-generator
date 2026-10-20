"""Resolve secrets at the I/O boundary; no environment mutation or logging."""
import os
import re
from dataclasses import dataclass
from pathlib import Path


def credential_prefix(credential_id: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', credential_id).upper()


@dataclass(frozen=True, slots=True, repr=False)
class Credentials:
    username: str
    password: str

    def __repr__(self):
        return 'Credentials(<redacted>)'


class EnvCredentialResolver:
    def __init__(self, path: Path | None = None, environ=None):
        values = {}
        if path is not None:
            try:
                for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
                    if not line.strip() or line.lstrip().startswith('#'):
                        continue
                    key, separator, value = line.partition('=')
                    if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key.strip()):
                        raise ValueError('INVALID_CREDENTIAL_FILE')
                    if key.strip() in values:
                        raise ValueError('DUPLICATE_CREDENTIAL_KEY')
                    values[key.strip()] = value
            except (OSError, UnicodeError):
                raise ValueError('CREDENTIAL_FILE_UNREADABLE') from None
        values.update(dict(os.environ if environ is None else environ))
        self._values = values

    def __call__(self, credential_id: str) -> Credentials:
        prefix = credential_prefix(credential_id)
        user, password = self._values.get(prefix + '_USER'), self._values.get(prefix + '_PASSWORD')
        if not user or not password:
            raise ValueError('CREDENTIALS_NOT_FOUND')
        return Credentials(user, password)

    def __repr__(self):
        return 'EnvCredentialResolver(<redacted>)'
