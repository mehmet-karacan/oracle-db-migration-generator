"""Readiness probe, deliberately distinct from a snapshot or comparison."""
import hashlib
import json
import re
from collections import Counter

from ..config.loader import ConfigError
from ..model.identity import Identifier
from .connection import connect_read_only
from .queries import DDL_TYPES, DICTIONARY_PROBES, IDENTITY, INVENTORY, CAPTURE_INVENTORY, READ_ONLY_TRANSACTION, SAMPLE_DDL


class ProbeError(ValueError):
    pass


def safe_error_code(error: Exception) -> str:
    # Never retain provider text: it may contain DSNs or secrets.
    match = re.search(r'\b(?:ORA|DPY|DPI)-\d{4,5}\b', str(error))
    if match:
        return match.group()
    if isinstance(error, (ProbeError, ConfigError)) and re.fullmatch(r'[A-Z][A-Z0-9_]{1,80}', str(error)):
        return str(error)
    if str(error) in {'CREDENTIALS_NOT_FOUND', 'INVALID_CREDENTIAL_FILE', 'DUPLICATE_CREDENTIAL_KEY',
                      'CREDENTIAL_FILE_UNREADABLE', 'ORACLE_DRIVER_MODE_MISMATCH'}:
        return str(error)
    return 'CONNECTION_OR_METADATA_ERROR'


def _probe_schema(target, mapping, credentials, connect):
    result = {'schema': mapping.source_schema, 'status': 'FAILED', 'inventory_count': None,
              'dictionary_access': {}, 'ddl_sample': 'NOT_RUN'}
    connection = cursor = None
    try:
        credential = credentials(mapping.credential_id)
        expected_owner = Identifier.parse(mapping.target_schema).effective_name
        connection = connect(target, credential)
        cursor = connection.cursor()
        cursor.execute(READ_ONLY_TRANSACTION)
        if mapping.metadata_reader is not None:
            from .catalog_reader import authorize_catalog_reader,CatalogCursor
            try:
                authorize_catalog_reader(cursor,Identifier.parse(mapping.metadata_reader).effective_name,expected_owner)
            except ValueError as error:
                code=str(error)
                raise ProbeError(code if re.fullmatch(r'CATALOG_[A-Z_]+',code) else 'CATALOG_AUTHORIZATION_FAILED') from None
            cursor=CatalogCursor(cursor)
            inventory,binds=CAPTURE_INVENTORY,{'owner':expected_owner}
        else:
            cursor.execute(IDENTITY)
            identity = cursor.fetchone()
            if identity is None or identity[0] != expected_owner:
                raise ProbeError('SESSION_OWNER_MISMATCH')
            inventory,binds=INVENTORY,None
        cursor.execute(inventory,binds)
        before = cursor.fetchall()
        for name, query in DICTIONARY_PROBES.items():
            cursor.execute(query, {'owner': expected_owner})
            cursor.fetchone()
            result['dictionary_access'][name] = 'ACCESSIBLE'
        sample = next((row for row in before if row[0] in DDL_TYPES), None)
        if sample is not None:
            cursor.execute(SAMPLE_DDL, {'ddl_type': DDL_TYPES[sample[0]], 'name': sample[1], 'owner': expected_owner})
            value = cursor.fetchone()
            if not value or value[0] is None:
                raise ProbeError('GET_DDL_RETURNED_EMPTY')
            ddl = value[0].read() if hasattr(value[0], 'read') else str(value[0])
            if not ddl.strip():
                raise ProbeError('GET_DDL_RETURNED_EMPTY')
            # Store only access evidence. Real DDL does not enter preflight output.
            result['ddl_sample'] = 'ACCESSIBLE_ONE_OBJECT'
        cursor.execute(inventory,binds)
        after = cursor.fetchall()
        if before != after:
            raise ProbeError('INVENTORY_CHANGED_DURING_PREFLIGHT')
        result.update(status='PASSED', inventory_count=len(before),
                      object_counts=dict(sorted(Counter(row[0] for row in before).items())),
                      inventory_digest=hashlib.sha256(json.dumps(before, separators=(',', ':')).encode()).hexdigest(),
                      oracle_version=connection.version,
                      observed_consistency='READ_ONLY_TRANSACTION_AND_INVENTORY_RECHECK')
    except Exception as error:
        result['error_code'] = safe_error_code(error)
    finally:
        # Attempt every cleanup even when another cleanup failed.
        for action in [cursor.close if cursor else None,
                       connection.rollback if connection else None,
                       connection.close if connection else None]:
            if action is None:
                continue
            try:
                action()
            except Exception:
                result.update(status='FAILED', error_code='CONNECTION_CLEANUP_FAILED')
    return result


def probe_target(config, credentials, *, connect=connect_read_only):
    schemas = [_probe_schema(config, mapping, credentials, connect) for mapping in config.schema_mappings]
    return {'target_id': config.id, 'status': 'PASSED' if all(s['status'] == 'PASSED' for s in schemas) else 'FAILED',
            'read_only': True, 'schemas': schemas, 'comparison_status': 'NOT_RUN',
            'difference_count': None, 'execution_status': 'NOT_EXECUTED',
            'limitations': ['READINESS_ONLY', 'GET_DDL_SAMPLED_NOT_FULL_EXTRACTION',
                            'DATABASE_ACCOUNT_PRIVILEGES_NOT_CERTIFIED']}
