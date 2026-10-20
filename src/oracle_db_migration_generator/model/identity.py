import hashlib
import json
import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Identifier:
    effective_name: str
    raw_name: str = field(compare=False)
    quoted: bool = field(compare=False)

    @classmethod
    def parse(cls, raw: str):
        if re.fullmatch(r'"(?:[^"\x00-\x1f]|"")+"', raw):
            return cls(raw[1:-1].replace('""', '"'), raw, True)
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9_$#]*', raw):
            return cls(raw.upper(), raw, False)
        raise ValueError('INVALID_ORACLE_IDENTIFIER')


@dataclass(frozen=True, slots=True)
class ObjectIdentity:
    profile_id: str
    owner: Identifier
    object_type: str
    name: Identifier
    parent_key: str | None = None

    @property
    def key(self):
        raw = json.dumps([self.profile_id, self.owner.effective_name, self.object_type,
                          self.name.effective_name, self.parent_key], ensure_ascii=False, separators=(',', ':'))
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
