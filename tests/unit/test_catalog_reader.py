import pytest

from oracle_db_migration_generator.oracle import queries


class RecordingCursor:
    def __init__(self, responses=(), *, fail_at=None):
        self.responses = iter(responses)
        self.calls = []
        self.fail_at = fail_at
        self.closed = False
        self.description = [('COLUMN',)]

    def execute(self, statement, *args, **kwargs):
        self.calls.append((statement, args, kwargs))
        if len(self.calls) == self.fail_at:
            raise RuntimeError('database-error secret-password private-service')
        return self

    def fetchone(self):
        return next(self.responses)

    def fetchall(self):
        return next(self.responses)

    def close(self):
        self.closed = True


def implementation():
    from oracle_db_migration_generator.oracle import catalog_reader
    return catalog_reader


@pytest.mark.parametrize('inventory', [[], [('SOME_TABLE',)]])
def test_authorization_checks_exact_identity_role_and_owner_catalog_access(inventory):
    module = implementation()
    cursor = RecordingCursor([('INNOVA_ODI',), [('SELECT_CATALOG_ROLE',)], [('TTBP',)], inventory])
    proof = module.authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')
    assert proof == {'reader': 'INNOVA_ODI', 'owner': 'TTBP', 'required_role': 'SELECT_CATALOG_ROLE',
                     'query_scope': 'DBA_METADATA', 'catalog_access': 'VERIFIED', 'owner_exists': 'VERIFIED'}
    assert cursor.calls[0] == (queries.IDENTITY, (), {})
    assert 'session_roles' in cursor.calls[1][0] and "'SELECT_CATALOG_ROLE'" in cursor.calls[1][0]
    assert cursor.calls[1][1:] == ((), {})
    assert cursor.calls[2][0] == module.CATALOG_OWNER_PROBE
    assert 'dba_users' in cursor.calls[2][0] and 'username = :owner' in cursor.calls[2][0]
    assert cursor.calls[2][1:] == (({'owner': 'TTBP'},), {})
    assert 'dba_objects' in cursor.calls[3][0] and 'owner = :owner' in cursor.calls[3][0]
    assert cursor.calls[3][1:] == (({'owner': 'TTBP'},), {})
    assert len(cursor.calls) == 4


def test_authorization_rejects_reader_mismatch_before_catalog_queries():
    cursor = RecordingCursor([('TTBP',)])
    with pytest.raises(ValueError, match='^CATALOG_READER_SESSION_MISMATCH$'):
        implementation().authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')
    assert len(cursor.calls) == 1


@pytest.mark.parametrize('roles', [[], [('DBA',)], [('select_catalog_role',)], [('SELECT ANY DICTIONARY',)]])
def test_authorization_requires_enabled_select_catalog_role(roles):
    cursor = RecordingCursor([('INNOVA_ODI',), roles])
    with pytest.raises(ValueError, match='^CATALOG_READER_ROLE_REQUIRED$'):
        implementation().authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')
    assert len(cursor.calls) == 2


@pytest.mark.parametrize(('fail_at', 'code'), [(1, 'CATALOG_READER_IDENTITY_UNAVAILABLE'),
                                            (2, 'CATALOG_READER_ROLE_UNAVAILABLE'),
                                            (3, 'CATALOG_READER_OWNER_UNAVAILABLE'),
                                            (4, 'CATALOG_READER_INVENTORY_UNAVAILABLE')])
def test_authorization_query_denial_is_closed_and_does_not_expose_database_error(fail_at, code):
    cursor = RecordingCursor([('INNOVA_ODI',), [('SELECT_CATALOG_ROLE',)], [('TTBP',)], []], fail_at=fail_at)
    with pytest.raises(ValueError) as result:
        implementation().authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')
    assert str(result.value) == code
    assert 'secret-password' not in str(result.value)
    assert result.value.__suppress_context__
    assert len(cursor.calls) == fail_at


def test_explicit_sys_reader_is_not_assumed_or_implicitly_substituted():
    cursor = RecordingCursor([('SYS',), [('SELECT_CATALOG_ROLE',)], [('TTBP',)], []])
    assert implementation().authorize_catalog_reader(cursor, 'SYS', 'TTBP')['reader'] == 'SYS'
    mismatch = RecordingCursor([('SYS',)])
    with pytest.raises(ValueError, match='CATALOG_READER_SESSION_MISMATCH'):
        implementation().authorize_catalog_reader(mismatch, 'INNOVA_ODI', 'TTBP')


@pytest.mark.parametrize(('reader', 'owner'), [('', 'TTBP'), ('INNOVA_ODI', ''), (None, 'TTBP'),
                                             ('INNOVA_ODI', None), ('INNOVA_ODI\x00', 'TTBP')])
def test_invalid_scope_values_are_rejected_before_any_query(reader, owner):
    cursor = RecordingCursor()
    with pytest.raises(ValueError, match='^CATALOG_READER_SCOPE_INVALID$'):
        implementation().authorize_catalog_reader(cursor, reader, owner)
    assert cursor.calls == []


def test_inventory_and_reference_queries_use_closed_dba_views_and_keep_binds():
    module = implementation()
    raw = RecordingCursor()
    cursor = module.CatalogCursor(raw)
    binds = {'owner': 'TTBP', 'name': 'T'}
    cases = [
        (queries.CAPTURE_INVENTORY, 'FROM dba_objects WHERE owner = :owner'),
        (queries.REFERENCE_OBJECT, 'FROM dba_objects WHERE owner = :owner'),
        (queries.REFERENCE_SYNONYM, 'dba_synonyms'),
    ]
    for statement, expected in cases:
        assert cursor.execute(statement, binds) is cursor
        mapped, args, kwargs = raw.calls[-1]
        assert expected in ' '.join(mapped.split())
        assert args == (binds,) and args[0] is binds and kwargs == {}
    assert cursor.query_scope == 'DBA_METADATA'


@pytest.mark.parametrize(('group', 'view'), [
    ('columns', 'dba_tab_cols'), ('tables', 'dba_tables'), ('constraints', 'dba_constraints'),
    ('constraint_columns', 'dba_cons_columns'), ('indexes', 'dba_indexes'),
    ('index_columns', 'dba_ind_columns'), ('index_expressions', 'dba_ind_expressions'),
    ('partition_keys', 'dba_part_key_columns'), ('sequences', 'dba_sequences'),
    ('table_comments', 'dba_tab_comments'), ('column_comments', 'dba_col_comments'),
    ('grants', 'dba_tab_privs'), ('column_grants', 'dba_col_privs'),
    ('dependencies', 'dba_dependencies'), ('errors', 'dba_errors'), ('synonyms', 'dba_synonyms'),
    ('external_tables', 'dba_external_tables'), ('materialized_view_logs', 'dba_mview_logs'),
])
def test_each_capture_group_has_explicit_dba_mapping(group, view):
    raw = RecordingCursor()
    module = implementation()
    cursor = module.CatalogCursor(raw)
    columns, statement = queries.CAPTURE_QUERIES[group]
    binds = {'owner': 'TTBP'}
    cursor.execute(statement, binds)
    mapped = raw.calls[-1][0]
    assert 'FROM ' + view + ' WHERE ' in ' '.join(mapped.split())
    assert raw.calls[-1][1:] == ((binds,), {})
    assert module.CATALOG_QUERIES[group] == (columns, mapped)
    if group in {'grants', 'column_grants'}:
        assert 'WHERE owner = :owner' in ' '.join(mapped.split()) and 'table_schema' not in mapped


@pytest.mark.parametrize('statement', [queries.IDENTITY, queries.SESSION_CALENDAR,
    queries.READ_ONLY_TRANSACTION, queries.SAMPLE_DDL, queries.DEPENDENT_DDL,
    queries.COLLATION_PARAMETERS, queries.CAPTURE_QUERIES['grantees'][1], queries.CAPTURE_QUERIES['nls'][1]])
def test_required_session_and_metadata_statements_pass_exactly(statement):
    raw = RecordingCursor()
    cursor = implementation().CatalogCursor(raw)
    binds = {'owner': 'TTBP', 'name': 'T', 'ddl_type': 'TABLE'}
    cursor.execute(statement, binds, batcherrors=False)
    assert raw.calls == [(statement, (binds,), {'batcherrors': False})]


@pytest.mark.parametrize('statement', [
    'SELECT * FROM TTBP.BUSINESS_TABLE', 'SELECT * FROM dba_users',
    'BEGIN SYS.DBMS_SESSION.SET_IDENTIFIER(:identity); END;',
    'ALTER TRIGGER SYS.BLOCK_TOOLS_TTBP DISABLE',
    'SELECT DBMS_METADATA.GET_DDL(:ddl_type, :name, :owner) FROM dual; DROP TABLE TTBP.T',
    queries.CAPTURE_INVENTORY + ' ', queries.CAPTURE_INVENTORY + '\n-- same query',
    queries.CAPTURE_INVENTORY.replace(':owner', "'TTBP'"),
    queries.INVENTORY, None, ['SELECT 1 FROM dual'],
])
def test_unknown_modified_business_and_privilege_statements_never_reach_cursor(statement):
    raw = RecordingCursor()
    cursor = implementation().CatalogCursor(raw)
    with pytest.raises(ValueError, match='^CATALOG_QUERY_NOT_ALLOWED$'):
        cursor.execute(statement, {'owner': 'TTBP'})
    assert raw.calls == []


def test_fetch_description_and_close_delegate_without_exposing_sql_escape_hatch():
    raw = RecordingCursor([('X',), [('Y',)]])
    cursor = implementation().CatalogCursor(raw)
    assert cursor.fetchone() == ('X',)
    assert cursor.fetchall() == [('Y',)]
    assert cursor.description is raw.description
    assert not hasattr(cursor, 'executemany') and not hasattr(cursor, 'callproc')
    cursor.close()
    assert raw.closed


def test_mapped_database_errors_preserve_type_for_existing_safe_error_code_handling():
    raw = RecordingCursor(fail_at=1)
    with pytest.raises(RuntimeError):
        implementation().CatalogCursor(raw).execute(queries.CAPTURE_INVENTORY, {'owner': 'TTBP'})
    assert len(raw.calls) == 1


@pytest.mark.parametrize(('group', 'view'), [
    ('objects', 'dba_objects'), ('columns', 'dba_tab_columns'), ('constraints', 'dba_constraints'),
    ('constraint_columns', 'dba_cons_columns'), ('indexes', 'dba_indexes'),
    ('index_columns', 'dba_ind_columns'), ('index_expressions', 'dba_ind_expressions'),
    ('sequences', 'dba_sequences'), ('table_comments', 'dba_tab_comments'),
    ('column_comments', 'dba_col_comments'), ('synonyms', 'dba_synonyms'),
    ('grants', 'dba_tab_privs'), ('dependencies', 'dba_dependencies'), ('errors', 'dba_errors'),
])
def test_preflight_probe_constants_map_to_exact_dba_queries(group, view):
    raw = RecordingCursor()
    module = implementation()
    binds = {'owner': 'TTBP'}
    module.CatalogCursor(raw).execute(queries.DICTIONARY_PROBES[group], binds)
    mapped = ' '.join(raw.calls[-1][0].split())
    original = ' '.join(queries.DICTIONARY_PROBES[group].split())
    assert 'FROM ' + view + ' WHERE ' in mapped
    assert 'ROWNUM <= 1' in mapped
    assert mapped.split(' FROM ', 1)[0] == original.split(' FROM ', 1)[0]
    assert raw.calls[-1][1:] == ((binds,), {}) and raw.calls[-1][1][0] is binds
    if group == 'grants':
        assert 'WHERE owner = :owner' in mapped and 'table_schema' not in mapped


def test_catalog_mappings_preserve_original_column_order_and_selection():
    module = implementation()
    for group, (_, statement) in queries.CAPTURE_QUERIES.items():
        original = ' '.join(statement.split()).split(' FROM ', 1)[0]
        mapped = ' '.join(module.CATALOG_QUERIES[group][1].split()).split(' FROM ', 1)[0]
        assert original == mapped


@pytest.mark.parametrize('inventory', [None, [('A', 'unexpected_column')], ['A']])
def test_catalog_authorization_rejects_malformed_probe_results(inventory):
    cursor = RecordingCursor([('INNOVA_ODI',), [('SELECT_CATALOG_ROLE',)], [('TTBP',)], inventory])
    with pytest.raises(ValueError, match='^CATALOG_READER_INVENTORY_UNAVAILABLE$'):
        implementation().authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')


@pytest.mark.parametrize('owners', [[], [('OTHER',)], [('ttbp',)], [('TTBP',), ('TTBP',)],
                                   [('TTBP', 'unexpected')], ['TTBP'], None, ('TTBP',)])
def test_catalog_owner_must_exist_with_exactly_one_matching_username_before_inventory(owners):
    cursor = RecordingCursor([('INNOVA_ODI',), [('SELECT_CATALOG_ROLE',)], owners, []])
    with pytest.raises(ValueError, match='^CATALOG_READER_OWNER_UNVERIFIED$'):
        implementation().authorize_catalog_reader(cursor, 'INNOVA_ODI', 'TTBP')
    assert len(cursor.calls) == 3
    assert 'dba_users' in cursor.calls[-1][0]
    assert all('dba_objects' not in statement for statement, _, _ in cursor.calls)
