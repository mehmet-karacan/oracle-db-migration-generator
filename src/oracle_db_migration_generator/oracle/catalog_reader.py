"""Explicit catalogue access through an already authorized read-only session.

No identity changes or privilege grants are performed. The cursor accepts only
the original metadata SQL constants and maps them to fixed catalogue queries.
"""
from types import MappingProxyType

from . import queries


CATALOG_ROLES = '''SELECT
    role
FROM
    session_roles
WHERE
    role = 'SELECT_CATALOG_ROLE' '''

CATALOG_OWNER_PROBE = '''SELECT
    username
FROM
    dba_users
WHERE
    username = :owner'''

CATALOG_INVENTORY_PROBE = '''SELECT
    object_name
FROM
    dba_objects
WHERE
    owner = :owner
    AND ROWNUM <= 1'''

CATALOG_INVENTORY = '''SELECT
    object_type,
    object_name,
    status,
    TO_CHAR(last_ddl_time, 'YYYY-MM-DD"T"HH24:MI:SS')
FROM
    dba_objects
WHERE
    owner = :owner
ORDER BY
    object_type, object_name'''

CATALOG_REFERENCE_OBJECT = '''SELECT
    object_type,
    status
FROM
    dba_objects
WHERE
    owner = :owner
    AND object_name = :name
ORDER BY
    object_type'''

CATALOG_REFERENCE_SYNONYM = '''SELECT
    table_owner,
    table_name,
    db_link
FROM
    dba_synonyms
WHERE
    owner = :owner
    AND synonym_name = :name'''

_CAPTURE_SQL = {
    'columns': '''SELECT
    table_name, column_name, data_type, data_type_owner, data_length,
    char_length, char_used, data_precision, data_scale, nullable,
    data_default, column_id, hidden_column, virtual_column, identity_column,
    default_on_null, user_generated, collation
FROM
    dba_tab_cols
WHERE
    owner = :owner
ORDER BY
    table_name, internal_column_id''',
    'tables': '''SELECT
    table_name, partitioned, iot_type, temporary, cluster_name, nested
FROM
    dba_tables
WHERE
    owner = :owner
ORDER BY
    table_name''',
    'constraints': '''SELECT
    table_name, constraint_name, constraint_type, r_owner, r_constraint_name,
    delete_rule, status, deferrable, deferred, validated, rely, index_owner,
    index_name, search_condition
FROM
    dba_constraints
WHERE
    owner = :owner
ORDER BY
    table_name, constraint_name''',
    'constraint_columns': '''SELECT
    table_name, constraint_name, column_name, position
FROM
    dba_cons_columns
WHERE
    owner = :owner
ORDER BY
    constraint_name, position''',
    'indexes': '''SELECT
    index_name, index_type, table_owner, table_name, uniqueness,
    status, visibility, partitioned, generated
FROM
    dba_indexes
WHERE
    owner = :owner
ORDER BY
    index_name''',
    'index_columns': '''SELECT
    index_name, table_name, column_name, column_position, descend
FROM
    dba_ind_columns
WHERE
    index_owner = :owner
ORDER BY
    index_name, column_position''',
    'index_expressions': '''SELECT
    index_name, column_expression, column_position
FROM
    dba_ind_expressions
WHERE
    index_owner = :owner
ORDER BY
    index_name, column_position''',
    'index_partitioning': '''SELECT
    index_name, partition_count, subpartitioning_type, interval
FROM dba_part_indexes
WHERE owner = :owner
ORDER BY index_name''',
    'index_partition_counts': '''SELECT
    index_name, COUNT(*) AS partition_count
FROM dba_ind_partitions
WHERE index_owner = :owner
GROUP BY index_name
ORDER BY index_name''',
    'index_partitions': '''SELECT
    index_name, partition_name, composite, subpartition_count, status
FROM dba_ind_partitions
WHERE index_owner = :owner
ORDER BY index_name, partition_position''',
    'index_subpartitions': '''SELECT
    index_name, partition_name, subpartition_name, status
FROM dba_ind_subpartitions
WHERE index_owner = :owner
ORDER BY index_name, partition_position, subpartition_position''',
    'partition_keys': '''SELECT
    name, object_type, column_name, column_position
FROM
    dba_part_key_columns
WHERE
    owner = :owner
ORDER BY
    name, column_position''',
    'sequences': '''SELECT
    sequence_name, min_value, max_value, increment_by, cycle_flag,
    order_flag, cache_size, last_number
FROM
    dba_sequences
WHERE
    sequence_owner = :owner
ORDER BY
    sequence_name''',
    'table_comments': '''SELECT
    table_name, comments
FROM
    dba_tab_comments
WHERE
    owner = :owner
    AND comments IS NOT NULL
ORDER BY
    table_name''',
    'column_comments': '''SELECT
    table_name, column_name, comments
FROM
    dba_col_comments
WHERE
    owner = :owner
    AND comments IS NOT NULL
ORDER BY
    table_name, column_name''',
    'grants': '''SELECT
    table_name, grantee, privilege, grantable, type
FROM
    dba_tab_privs
WHERE
    owner = :owner
ORDER BY
    table_name, grantee, privilege''',
    'column_grants': '''SELECT
    table_name, column_name, grantee, privilege, grantable
FROM
    dba_col_privs
WHERE
    owner = :owner
ORDER BY
    table_name, column_name, grantee, privilege''',
    'dependencies': '''SELECT
    name, type, referenced_owner, referenced_name, referenced_type
FROM
    dba_dependencies
WHERE
    owner = :owner
ORDER BY
    name, type, referenced_owner, referenced_type, referenced_name''',
    'errors': '''SELECT
    name, type, line, position, text
FROM
    dba_errors
WHERE
    owner = :owner
ORDER BY
    name, type, sequence''',
    'synonyms': '''SELECT
    synonym_name, table_owner, table_name, db_link
FROM
    dba_synonyms
WHERE
    owner = :owner
ORDER BY
    synonym_name''',
    'external_tables': '''SELECT
    table_name
FROM
    dba_external_tables
WHERE
    owner = :owner
ORDER BY
    table_name''',
    'materialized_view_logs': '''SELECT
    master, log_table
FROM
    dba_mview_logs
WHERE
    log_owner = :owner
ORDER BY
    master''',
    'grantees': queries.CAPTURE_QUERIES['grantees'][1],
    'nls': queries.CAPTURE_QUERIES['nls'][1],
}

CATALOG_QUERIES = MappingProxyType({
    name: (queries.CAPTURE_QUERIES[name][0], statement)
    for name, statement in _CAPTURE_SQL.items()
})

CATALOG_DICTIONARY_PROBES = MappingProxyType({
    'objects': '''SELECT
    object_name, object_type, status
FROM
    dba_objects
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'columns': '''SELECT
    table_name, column_name, data_type, data_length, data_precision,
    data_scale, nullable, data_default
FROM
    dba_tab_columns
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'constraints': '''SELECT
    constraint_name, constraint_type, table_name, r_owner, r_constraint_name,
    delete_rule, status, deferrable, deferred, validated
FROM
    dba_constraints
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'constraint_columns': '''SELECT
    constraint_name, table_name, column_name, position
FROM
    dba_cons_columns
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'indexes': '''SELECT
    index_name, index_type, table_owner, table_name, uniqueness, status
FROM
    dba_indexes
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'index_columns': '''SELECT
    index_name, table_name, column_name, column_position, descend
FROM
    dba_ind_columns
WHERE
    index_owner = :owner AND ROWNUM <= 1''',
    'index_expressions': '''SELECT
    index_name, column_expression, column_position
FROM
    dba_ind_expressions
WHERE
    index_owner = :owner AND ROWNUM <= 1''',
    'sequences': '''SELECT
    sequence_name, min_value, max_value, increment_by, cycle_flag, order_flag, cache_size
FROM
    dba_sequences
WHERE
    sequence_owner = :owner AND ROWNUM <= 1''',
    'table_comments': '''SELECT
    table_name, comments
FROM
    dba_tab_comments
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'column_comments': '''SELECT
    table_name, column_name, comments
FROM
    dba_col_comments
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'synonyms': '''SELECT
    synonym_name, table_owner, table_name, db_link
FROM
    dba_synonyms
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'grants': '''SELECT
    grantee, table_name, privilege, grantable
FROM
    dba_tab_privs
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'dependencies': '''SELECT
    name, type, referenced_owner, referenced_name, referenced_type
FROM
    dba_dependencies
WHERE
    owner = :owner AND ROWNUM <= 1''',
    'errors': '''SELECT
    name, type, line, position, text
FROM
    dba_errors
WHERE
    owner = :owner AND ROWNUM <= 1''',
})

_STATEMENTS = MappingProxyType({
    queries.CAPTURE_INVENTORY: CATALOG_INVENTORY,
    queries.REFERENCE_OBJECT: CATALOG_REFERENCE_OBJECT,
    queries.REFERENCE_SYNONYM: CATALOG_REFERENCE_SYNONYM,
    **{queries.CAPTURE_QUERIES[name][1]: statement for name, statement in _CAPTURE_SQL.items()},
    **{queries.DICTIONARY_PROBES[name]: statement for name, statement in CATALOG_DICTIONARY_PROBES.items()},
    **{statement: statement for statement in (
        queries.IDENTITY, queries.SESSION_CALENDAR, queries.READ_ONLY_TRANSACTION,
        queries.SAMPLE_DDL, queries.DEPENDENT_DDL, queries.COLLATION_PARAMETERS,
    )},
})


def authorize_catalog_reader(cursor, expected_reader: str, owner: str) -> dict:
    """Verify explicit reader/role/catalog access after SET TRANSACTION READ ONLY.

    An empty inventory is valid only after the owner's existence is proven.
    All observations use fixed dictionary queries and unchanged owner binds.
    """
    if any(not isinstance(value, str) or not value or any(ord(char) < 32 for char in value)
           for value in (expected_reader, owner)):
        raise ValueError('CATALOG_READER_SCOPE_INVALID')
    try:
        cursor.execute(queries.IDENTITY)
        identity = cursor.fetchone()
    except Exception:
        raise ValueError('CATALOG_READER_IDENTITY_UNAVAILABLE') from None
    if identity != (expected_reader,):
        raise ValueError('CATALOG_READER_SESSION_MISMATCH')
    try:
        cursor.execute(CATALOG_ROLES)
        roles = cursor.fetchall()
    except Exception:
        raise ValueError('CATALOG_READER_ROLE_UNAVAILABLE') from None
    if not isinstance(roles, (tuple, list)) or ('SELECT_CATALOG_ROLE',) not in roles:
        raise ValueError('CATALOG_READER_ROLE_REQUIRED')
    try:
        cursor.execute(CATALOG_OWNER_PROBE, {'owner': owner})
        owners = cursor.fetchall()
    except Exception:
        raise ValueError('CATALOG_READER_OWNER_UNAVAILABLE') from None
    if not isinstance(owners, (tuple, list)) or len(owners) != 1 or owners[0] != (owner,):
        raise ValueError('CATALOG_READER_OWNER_UNVERIFIED')
    try:
        cursor.execute(CATALOG_INVENTORY_PROBE, {'owner': owner})
        rows = cursor.fetchall()
        if not isinstance(rows, (tuple, list)) or any(not isinstance(row, tuple) or len(row) != 1 for row in rows):
            raise ValueError('CATALOG_INVENTORY_RESULT_INVALID')
    except Exception:
        raise ValueError('CATALOG_READER_INVENTORY_UNAVAILABLE') from None
    return {'reader': expected_reader, 'owner': owner, 'required_role': 'SELECT_CATALOG_ROLE',
            'query_scope': 'DBA_METADATA', 'catalog_access': 'VERIFIED', 'owner_exists': 'VERIFIED'}


class CatalogCursor:
    """Cursor facade with exact SQL lookup and unchanged caller bind values."""

    __slots__ = ('_cursor',)
    query_scope = 'DBA_METADATA'

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, statement, *args, **kwargs):
        mapped = _STATEMENTS.get(statement) if isinstance(statement, str) else None
        if mapped is None:
            raise ValueError('CATALOG_QUERY_NOT_ALLOWED')
        self._cursor.execute(mapped, *args, **kwargs)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        return self._cursor.close()
