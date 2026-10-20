"""Pure comparison scope; raw inventories remain available for safety checks.

The technical-name patterns adapt DDL Sync's oracle_client.py
_SYSTEM_GENERATED_PATTERNS/_is_system_generated (read-only reference).
Matching uses effective Oracle names, preserving quoted identifier case.
Exact 64-hex technical names also match quoted case variants by user policy.
"""
import re

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from ..model.identity import Identifier, ObjectIdentity
from ..parsing.statements import qualified_parts


_SYSTEM_GENERATED_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r'^BIN\$', r'^ISEQ\$\$_', r'^MLOG\$_', r'^I_MLOG\$_', r'^RUPD\$_',
    r'^SYS_IOT_OVER_', r'^SYS_IL\d', r'^SYS_FBA_HIST_', r'^SYS_TEMP_FBT',
    r'^C\$_', r'^I\$_', r'^E\$_', r'^JV?\$', r'^T\$',
))
_HASH_NAME_PATTERN = re.compile(r'^(?:S_)?[A-Fa-f0-9]{64}$', re.IGNORECASE)


def _technical(name, kind=None):
    return bool(_HASH_NAME_PATTERN.fullmatch(name)) or (kind != 'MATERIALIZED_VIEW_LOG'
            and any(pattern.match(name) for pattern in _SYSTEM_GENERATED_PATTERNS))


def _known(obj, key):
    value = obj.properties.get(key)
    return value.value if value is not None and value.state == 'KNOWN' else None


def _parents(obj):
    """Only ownership links, never ordinary dependency edges, imply exclusion."""
    if obj.identity.object_type in {'COMMENT', 'GRANT'}:
        owner, name = _known(obj, 'owner'), _known(obj, 'target')
        if isinstance(owner, str) and isinstance(name, str):
            return ((owner, name),)
    if obj.identity.object_type != 'INDEX':
        return ()
    rows = _known(obj, 'dictionary.indexes')
    if rows is not None:
        matches = {(row.get('table_owner'), row.get('table_name')) for row in rows
                   if row.get('index_name') == obj.identity.name.effective_name
                   and isinstance(row.get('table_owner'), str) and isinstance(row.get('table_name'), str)}
        # Ambiguous dictionary ownership cannot prove an exclusion. Dictionary
        # names already carry their effective case; do not fold them again.
        if len(matches) == 1:
            return tuple(matches)
        if matches:
            return ()
    projection = _known(obj, 'projection')
    if projection is None or obj.coverage.ddl != 'COMPLETE' or obj.coverage.diagnostics:
        return ()
    target = projection.get('target')
    if not isinstance(target, str):
        return ()
    try:
        parts = qualified_parts(code_tokens(target))
    except ValueError:
        return ()
    if len(parts) == 1:
        return ((obj.identity.owner.effective_name, parts[0]),)
    return (parts,) if len(parts) == 2 else ()


def _exclusions(snapshot, policy):
    objects = {obj.object_key: obj for obj in snapshot.objects}
    excluded = {}
    excluded_types = set(policy.excluded_object_types)
    for key, obj in objects.items():
        kind = obj.identity.object_type
        if kind in excluded_types:
            excluded[key] = ('EXCLUDED_OBJECT_TYPE', None)
        elif (policy.exclude_system_generated and kind not in {'COMMENT', 'GRANT'}
              and _technical(obj.identity.name.effective_name, kind)):
            excluded[key] = ('SYSTEM_GENERATED_OBJECT', None)
    # Child metadata must be removed with its excluded owner. Keep all other
    # objects, including business routines referencing technical objects.
    changed = True
    while changed:
        changed = False
        for key, obj in objects.items():
            if key in excluded or obj.identity.object_type not in {'INDEX', 'COMMENT', 'GRANT'}:
                continue
            parent = obj.identity.parent_key
            if parent not in excluded:
                parent = None
                for owner, name in _parents(obj):
                    matches = [candidate.object_key for candidate in objects.values()
                               if candidate.identity.owner.effective_name == owner
                               and candidate.identity.name.effective_name == name
                               and candidate.identity.object_type in {'TABLE', 'VIEW', 'MATERIALIZED_VIEW',
                                   'SEQUENCE', 'PACKAGE_SPEC', 'TYPE_SPEC', 'PROCEDURE', 'FUNCTION'}]
                    if len(matches) == 1 and matches[0] in excluded:
                        parent = matches[0]
                    elif policy.exclude_system_generated and _technical(name):
                        parent = ObjectIdentity(snapshot.profile_id, Identifier(owner, owner, True), 'TABLE',
                                                Identifier(name, name, True)).key
                    if parent:
                        break
            if parent:
                excluded[key] = ('EXCLUDED_PARENT_OBJECT', parent)
                changed = True
    return excluded


def scoped_objects(snapshot, policy):
    """Return comparison objects without modifying the captured snapshot."""
    excluded = _exclusions(snapshot, policy)
    return tuple(obj for obj in snapshot.objects if obj.object_key not in excluded)


def scope_exclusions(source, target, policy):
    """Return deterministic JSON-compatible scope receipts for both sides."""
    result = []
    for snapshot in (source, target):
        excluded = _exclusions(snapshot, policy)
        for obj in sorted(snapshot.objects, key=lambda item: item.object_key):
            if snapshot.side == 'SOURCE' and obj.identity.owner.effective_name not in target.schemas:
                continue
            if obj.object_key not in excluded:
                continue
            reason, parent = excluded[obj.object_key]
            result.append({'side': snapshot.side, 'object_key': obj.object_key,
                           'owner': obj.identity.owner.effective_name, 'name': obj.identity.name.effective_name,
                           'object_type': obj.identity.object_type, 'reason_code': reason,
                           'parent_object_key': parent})
    return tuple(result)
