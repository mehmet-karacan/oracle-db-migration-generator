"""Closed allowlist: no caller-provided SQL, business data, NEXTVAL or DDL."""

READ_ONLY_TRANSACTION = 'SET TRANSACTION READ ONLY'
REFERENCE_OBJECT = 'SELECT object_type, status FROM all_objects WHERE owner = :owner AND object_name = :name ORDER BY object_type'
REFERENCE_SYNONYM = '''SELECT
    table_owner,
    table_name,
    db_link
FROM
    all_synonyms
WHERE
    owner = :owner
    AND synonym_name = :name'''
SESSION_CALENDAR = '''SELECT
    parameter,
    value
FROM
    nls_session_parameters
WHERE
    parameter = 'NLS_CALENDAR' '''
IDENTITY = "SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') FROM dual"
COLLATION_PARAMETERS = """SELECT name,
    CASE WHEN name = 'max_string_size' AND SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT'
         THEN 'STANDARD' ELSE value END AS value
    FROM v$parameter WHERE name IN ('compatible', 'max_string_size') ORDER BY name"""
INVENTORY = '''SELECT object_type, object_name, status,
    TO_CHAR(last_ddl_time, 'YYYY-MM-DD"T"HH24:MI:SS')
    FROM user_objects ORDER BY object_type, object_name'''
SAMPLE_DDL = 'SELECT DBMS_METADATA.GET_DDL(:ddl_type, :name, :owner) FROM dual'

DICTIONARY_PROBES = {
    'objects': 'SELECT object_name, object_type, status FROM all_objects WHERE owner = :owner AND ROWNUM <= 1',
    'columns': 'SELECT table_name, column_name, data_type, data_length, data_precision, data_scale, nullable, data_default FROM all_tab_columns WHERE owner = :owner AND ROWNUM <= 1',
    'constraints': 'SELECT constraint_name, constraint_type, table_name, r_owner, r_constraint_name, delete_rule, status, deferrable, deferred, validated FROM all_constraints WHERE owner = :owner AND ROWNUM <= 1',
    'constraint_columns': 'SELECT constraint_name, table_name, column_name, position FROM all_cons_columns WHERE owner = :owner AND ROWNUM <= 1',
    'indexes': 'SELECT index_name, index_type, table_owner, table_name, uniqueness, status FROM all_indexes WHERE owner = :owner AND ROWNUM <= 1',
    'index_columns': 'SELECT index_name, table_name, column_name, column_position, descend FROM all_ind_columns WHERE index_owner = :owner AND ROWNUM <= 1',
    'index_expressions': 'SELECT index_name, column_expression, column_position FROM all_ind_expressions WHERE index_owner = :owner AND ROWNUM <= 1',
    'sequences': 'SELECT sequence_name, min_value, max_value, increment_by, cycle_flag, order_flag, cache_size FROM all_sequences WHERE sequence_owner = :owner AND ROWNUM <= 1',
    'table_comments': 'SELECT table_name, comments FROM all_tab_comments WHERE owner = :owner AND ROWNUM <= 1',
    'column_comments': 'SELECT table_name, column_name, comments FROM all_col_comments WHERE owner = :owner AND ROWNUM <= 1',
    'synonyms': 'SELECT synonym_name, table_owner, table_name, db_link FROM all_synonyms WHERE owner = :owner AND ROWNUM <= 1',
    'grants': 'SELECT grantee, table_name, privilege, grantable FROM all_tab_privs WHERE table_schema = :owner AND ROWNUM <= 1',
    'dependencies': 'SELECT name, type, referenced_owner, referenced_name, referenced_type FROM all_dependencies WHERE owner = :owner AND ROWNUM <= 1',
    'errors': 'SELECT name, type, line, position, text FROM all_errors WHERE owner = :owner AND ROWNUM <= 1',
}

DDL_TYPES = {
    'TABLE': 'TABLE', 'VIEW': 'VIEW', 'INDEX': 'INDEX', 'SEQUENCE': 'SEQUENCE',
    'PACKAGE': 'PACKAGE_SPEC', 'PACKAGE BODY': 'PACKAGE_BODY', 'TYPE': 'TYPE_SPEC',
    'TYPE BODY': 'TYPE_BODY', 'FUNCTION': 'FUNCTION', 'PROCEDURE': 'PROCEDURE',
    'TRIGGER': 'TRIGGER', 'SYNONYM': 'SYNONYM', 'MATERIALIZED VIEW': 'MATERIALIZED_VIEW',
}

# Full capture uses the same fixed-query boundary as preflight. Field names
# are explicit so an older Oracle release cannot silently lose semantics.
CAPTURE_INVENTORY = '''SELECT object_type, object_name, status,
    TO_CHAR(last_ddl_time, 'YYYY-MM-DD"T"HH24:MI:SS')
    FROM all_objects WHERE owner = :owner ORDER BY object_type, object_name'''

CAPTURE_QUERIES = {
    'columns': (('table_name','column_name','data_type','data_type_owner','data_length','char_length','char_used',
                 'data_precision','data_scale','nullable','data_default','column_id','hidden_column','virtual_column',
                 'identity_column','default_on_null','user_generated','collation'),
        'SELECT table_name, column_name, data_type, data_type_owner, data_length, char_length, char_used, data_precision, data_scale, nullable, data_default, column_id, hidden_column, virtual_column, identity_column, default_on_null, user_generated, collation FROM all_tab_cols WHERE owner = :owner ORDER BY table_name, internal_column_id'),
    'tables': (('table_name','partitioned','iot_type','temporary','cluster_name','nested'),
        'SELECT table_name, partitioned, iot_type, temporary, cluster_name, nested FROM all_tables WHERE owner = :owner ORDER BY table_name'),
    'constraints': (('table_name','constraint_name','constraint_type','r_owner','r_constraint_name','delete_rule','status','deferrable','deferred','validated','rely','index_owner','index_name','search_condition'),
        'SELECT table_name, constraint_name, constraint_type, r_owner, r_constraint_name, delete_rule, status, deferrable, deferred, validated, rely, index_owner, index_name, search_condition FROM all_constraints WHERE owner = :owner ORDER BY table_name, constraint_name'),
    'constraint_columns': (('table_name','constraint_name','column_name','position'),
        'SELECT table_name, constraint_name, column_name, position FROM all_cons_columns WHERE owner = :owner ORDER BY constraint_name, position'),
    'indexes': (('index_name','index_type','table_owner','table_name','uniqueness','status','visibility','partitioned','generated'),
        'SELECT index_name, index_type, table_owner, table_name, uniqueness, status, visibility, partitioned, generated FROM all_indexes WHERE owner = :owner ORDER BY index_name'),
    'index_columns': (('index_name','table_name','column_name','column_position','descend'),
        'SELECT index_name, table_name, column_name, column_position, descend FROM all_ind_columns WHERE index_owner = :owner ORDER BY index_name, column_position'),
    'index_expressions': (('index_name','column_expression','column_position'),
        'SELECT index_name, column_expression, column_position FROM all_ind_expressions WHERE index_owner = :owner ORDER BY index_name, column_position'),
    'index_partitioning': (('index_name','partition_count','subpartitioning_type','interval'),
        '''SELECT
    index_name, partition_count, subpartitioning_type, interval
FROM all_part_indexes
WHERE owner = :owner
ORDER BY index_name'''),
    'index_partition_counts': (('index_name','partition_count'),
        '''SELECT
    index_name, COUNT(*) AS partition_count
FROM all_ind_partitions
WHERE index_owner = :owner
GROUP BY index_name
ORDER BY index_name'''),
    'index_partitions': (('index_name','partition_name','composite','subpartition_count','status'),
        '''SELECT
    index_name, partition_name, composite, subpartition_count, status
FROM all_ind_partitions
WHERE index_owner = :owner
ORDER BY index_name, partition_position'''),
    'index_subpartitions': (('index_name','partition_name','subpartition_name','status'),
        '''SELECT
    index_name, partition_name, subpartition_name, status
FROM all_ind_subpartitions
WHERE index_owner = :owner
ORDER BY index_name, partition_position, subpartition_position'''),
    'partition_keys': (('name','object_type','column_name','column_position'),
        'SELECT name, object_type, column_name, column_position FROM all_part_key_columns WHERE owner = :owner ORDER BY name, column_position'),
    'sequences': (('sequence_name','min_value','max_value','increment_by','cycle_flag','order_flag','cache_size','last_number'),
        'SELECT sequence_name, min_value, max_value, increment_by, cycle_flag, order_flag, cache_size, last_number FROM all_sequences WHERE sequence_owner = :owner ORDER BY sequence_name'),
    'table_comments': (('table_name','comments'),
        'SELECT table_name, comments FROM all_tab_comments WHERE owner = :owner AND comments IS NOT NULL ORDER BY table_name'),
    'column_comments': (('table_name','column_name','comments'),
        'SELECT table_name, column_name, comments FROM all_col_comments WHERE owner = :owner AND comments IS NOT NULL ORDER BY table_name, column_name'),
    'grants': (('table_name','grantee','privilege','grantable','object_type'),
        'SELECT table_name, grantee, privilege, grantable, type FROM all_tab_privs WHERE table_schema = :owner ORDER BY table_name, grantee, privilege'),
    'column_grants': (('table_name','column_name','grantee','privilege','grantable'),
        'SELECT table_name, column_name, grantee, privilege, grantable FROM all_col_privs WHERE table_schema = :owner ORDER BY table_name, column_name, grantee, privilege'),
    'dependencies': (('name','type','referenced_owner','referenced_name','referenced_type'),
        'SELECT name, type, referenced_owner, referenced_name, referenced_type FROM all_dependencies WHERE owner = :owner ORDER BY name, type, referenced_owner, referenced_type, referenced_name'),
    'errors': (('name','type','line','position','text'),
        'SELECT name, type, line, position, text FROM all_errors WHERE owner = :owner ORDER BY name, type, sequence'),
    'synonyms': (('synonym_name','table_owner','table_name','db_link'),
        'SELECT synonym_name, table_owner, table_name, db_link FROM all_synonyms WHERE owner = :owner ORDER BY synonym_name'),
    'external_tables': (('table_name',),
        'SELECT table_name FROM all_external_tables WHERE owner = :owner ORDER BY table_name'),
    'materialized_view_logs': (('master','log_table'),
        'SELECT master, log_table FROM all_mview_logs WHERE log_owner = :owner ORDER BY master'),
    'grantees': (('username',), 'SELECT username FROM all_users ORDER BY username'),
    'nls': (('parameter','value'), "SELECT parameter, value FROM nls_database_parameters WHERE parameter IN ('NLS_CHARACTERSET', 'NLS_NCHAR_CHARACTERSET') ORDER BY parameter"),
}
DEPENDENT_DDL = 'SELECT DBMS_METADATA.GET_DEPENDENT_DDL(:ddl_type, :name, :owner) FROM dual'
