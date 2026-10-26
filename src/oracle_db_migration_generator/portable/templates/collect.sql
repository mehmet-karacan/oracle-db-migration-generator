-- Oracle 19c+, SQL*Plus 19c+ / SQLcl common command subset.
-- Only fixed metadata SELECTs and DBMS_METADATA reads. No object SQL is executed.
SET DEFINE OFF
SET AUTOCOMMIT OFF
SET ECHO OFF
SET FEEDBACK OFF
SET VERIFY OFF
SET HEADING OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMSPOOL ON
SET TAB OFF
SET SERVEROUTPUT ON SIZE UNLIMITED FORMAT TRUNCATED
SPOOL capture.odmg.jsonl
DECLARE
@@STRING_PARAMS@@
    TYPE t_query IS RECORD(name VARCHAR2(80), columns_json VARCHAR2(4000), statement VARCHAR2(32767), catalog_statement VARCHAR2(32767));
    TYPE t_queries IS TABLE OF t_query INDEX BY PLS_INTEGER;
    TYPE t_strings IS TABLE OF VARCHAR2(32767) INDEX BY VARCHAR2(512);
    TYPE t_flags IS TABLE OF BOOLEAN INDEX BY VARCHAR2(512);
    v_queries t_queries;
    v_ddl_types t_strings;
    v_tables t_flags;
    v_dtype_tables t_flags;
    v_selected t_flags;
    v_parents t_strings;
    v_inventory JSON_ARRAY_T;
    v_after JSON_ARRAY_T;
    v_owner VARCHAR2(128);
    v_user VARCHAR2(128);
    v_mode VARCHAR2(16);
    v_schema_list VARCHAR2(32767);
    v_message PLS_INTEGER := 0;
    v_bytes PLS_INTEGER := 0;
    v_errors PLS_INTEGER := 0;
    v_selected_count PLS_INTEGER := 0;
    v_started TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    v_scope JSON_OBJECT_T;
    v_header JSON_OBJECT_T;

    PROCEDURE budget IS
    BEGIN
        IF (CAST(SYSTIMESTAMP AS DATE) - CAST(v_started AS DATE))*86400 > :p_timeout_seconds THEN
            RAISE_APPLICATION_ERROR(-20001,'CAPTURE_TIME_BUDGET');
        END IF;
    END;

    FUNCTION encoded(p_text CLOB) RETURN JSON_ELEMENT_T IS
        v_object JSON_OBJECT_T := JSON_OBJECT_T();
        v_chunks JSON_ARRAY_T := JSON_ARRAY_T();
        v_piece VARCHAR2(32767);
        v_offset PLS_INTEGER := 1;
        v_total PLS_INTEGER := 0;
    BEGIN
        IF p_text IS NULL THEN RETURN NULL; END IF;
        IF DBMS_LOB.GETLENGTH(p_text) > 2097152 THEN
            RAISE_APPLICATION_ERROR(-20002,'CAPTURE_VALUE_LIMIT');
        END IF;
        WHILE v_offset <= DBMS_LOB.GETLENGTH(p_text) LOOP
            v_piece := DBMS_LOB.SUBSTR(p_text,4000,v_offset);
            v_total := v_total + UTL_RAW.LENGTH(UTL_I18N.STRING_TO_RAW(v_piece,'AL32UTF8'));
            IF v_total>2097152 THEN RAISE_APPLICATION_ERROR(-20002,'CAPTURE_VALUE_LIMIT'); END IF;
            v_chunks.APPEND(REPLACE(REPLACE(UTL_RAW.CAST_TO_VARCHAR2(
                UTL_ENCODE.BASE64_ENCODE(UTL_I18N.STRING_TO_RAW(v_piece,'AL32UTF8'))),CHR(13),''),CHR(10),''));
            v_offset := v_offset + LENGTH(v_piece);
        END LOOP;
        v_object.PUT('encoding','base64-utf8');
        v_object.PUT('chunks',v_chunks);
        RETURN v_object;
    END;

    PROCEDURE emit(p_value JSON_OBJECT_T) IS
        v_text CLOB := p_value.TO_CLOB();
        v_piece VARCHAR2(32767);
        v_raw RAW(32767);
        v_hash VARCHAR2(64);
        v_line VARCHAR2(32767);
        v_offset PLS_INTEGER := 1;
        v_part PLS_INTEGER := 0;
    BEGIN
        v_message := v_message + 1;
        WHILE v_offset <= DBMS_LOB.GETLENGTH(v_text) LOOP
            v_piece := DBMS_LOB.SUBSTR(v_text,4000,v_offset);
            v_raw := UTL_I18N.STRING_TO_RAW(v_piece,'AL32UTF8');
            SELECT RAWTOHEX(STANDARD_HASH(v_raw,'SHA256')) INTO v_hash FROM dual;
            v_line := '{"record":"chunk","message":'||TO_CHAR(v_message,'FM9999999990')||
                ',"part":'||TO_CHAR(v_part,'FM9999999990')||',"sha256":"'||v_hash||'","data":"'||
                REPLACE(REPLACE(UTL_RAW.CAST_TO_VARCHAR2(UTL_ENCODE.BASE64_ENCODE(v_raw)),CHR(13),''),CHR(10),'')||'"}';
            IF v_bytes + LENGTHB(v_line) > 67108864 THEN
                RAISE_APPLICATION_ERROR(-20003,'CAPTURE_OUTPUT_LIMIT');
            END IF;
            DBMS_OUTPUT.PUT_LINE(v_line);
            v_bytes := v_bytes + LENGTHB(v_line);
            v_part := v_part + 1;
            v_offset := v_offset + LENGTH(v_piece);
        END LOOP;
        DBMS_OUTPUT.PUT_LINE('{"record":"end_message","message":'||TO_CHAR(v_message,'FM9999999990')||
            ',"parts":'||TO_CHAR(v_part,'FM9999999990')||'}');
        DBMS_LOB.FREETEMPORARY(v_text);
    END;

    PROCEDURE add_query(p_name VARCHAR2,p_columns VARCHAR2,p_statement VARCHAR2,p_catalog_statement VARCHAR2 DEFAULT NULL) IS
        n PLS_INTEGER := v_queries.COUNT+1;
    BEGIN
        v_queries(n).name := p_name;
        v_queries(n).columns_json := p_columns;
        v_queries(n).statement := p_statement;
        v_queries(n).catalog_statement := NVL(p_catalog_statement,p_statement);
    END;

    FUNCTION statement_for(p_text VARCHAR2) RETURN VARCHAR2 IS
    BEGIN
        IF v_mode='CATALOG' THEN
            RETURN REPLACE(REPLACE(p_text,'all_','dba_'),'ALL_','DBA_');
        END IF;
        RETURN p_text;
    END;

    FUNCTION csv_has(p_values VARCHAR2,p_value VARCHAR2) RETURN BOOLEAN IS
    BEGIN
        RETURN p_values IS NULL OR INSTR(','||p_values||',',','||p_value||',')>0;
    END;

    FUNCTION text_at(p_row JSON_ARRAY_T,p_index PLS_INTEGER) RETURN VARCHAR2 IS
        v_element JSON_ELEMENT_T;
        v_encoded JSON_OBJECT_T;
        v_chunks JSON_ARRAY_T;
    BEGIN
        v_element := p_row.GET(p_index);
        IF v_element IS NULL OR v_element.IS_NULL THEN RETURN NULL; END IF;
        v_encoded := TREAT(v_element AS JSON_OBJECT_T);
        v_chunks := v_encoded.GET_ARRAY('chunks');
        IF v_chunks.GET_SIZE=0 THEN RETURN NULL; END IF;
        RETURN UTL_I18N.RAW_TO_CHAR(UTL_ENCODE.BASE64_DECODE(UTL_RAW.CAST_TO_RAW(v_chunks.GET_STRING(0))),'AL32UTF8');
    END;

    PROCEDURE query_rows(p_name VARCHAR2,p_columns VARCHAR2,p_sql VARCHAR2,
        p_result OUT JSON_ARRAY_T,p_object_name VARCHAR2 DEFAULT NULL,p_ddl_type VARCHAR2 DEFAULT NULL) IS
        v_cursor INTEGER := NULL;
        v_ignored INTEGER;
        v_count INTEGER;
        v_desc DBMS_SQL.DESC_TAB2;
        v_number NUMBER;
        v_text VARCHAR2(32767);
        v_clob CLOB;
        v_long VARCHAR2(32767);
        v_got INTEGER;
        v_offset INTEGER;
        v_row JSON_ARRAY_T;
        v_record JSON_OBJECT_T;
        v_error INTEGER;
        v_rows PLS_INTEGER := 0;
    BEGIN
        budget;
        p_result := JSON_ARRAY_T();
        v_record := JSON_OBJECT_T();
        v_record.PUT('kind','query_start'); v_record.PUT('schema',v_owner);
        v_record.PUT('query',p_name); v_record.PUT('columns',JSON_ARRAY_T(p_columns)); emit(v_record);
        v_cursor := DBMS_SQL.OPEN_CURSOR;
        DBMS_SQL.PARSE(v_cursor,p_sql,DBMS_SQL.NATIVE);
        IF INSTR(p_sql,':owner')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':owner',v_owner); END IF;
        IF INSTR(p_sql,':name')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':name',p_object_name); END IF;
        IF INSTR(p_sql,':ddl_type')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':ddl_type',p_ddl_type); END IF;
        DBMS_SQL.DESCRIBE_COLUMNS2(v_cursor,v_count,v_desc);
        FOR c IN 1..v_count LOOP
            IF v_desc(c).col_type=2 THEN DBMS_SQL.DEFINE_COLUMN(v_cursor,c,v_number);
            ELSIF v_desc(c).col_type=112 THEN DBMS_SQL.DEFINE_COLUMN(v_cursor,c,v_clob);
            ELSIF v_desc(c).col_type=8 THEN DBMS_SQL.DEFINE_COLUMN_LONG(v_cursor,c);
            ELSE DBMS_SQL.DEFINE_COLUMN(v_cursor,c,v_text,32767);
            END IF;
        END LOOP;
        v_ignored := DBMS_SQL.EXECUTE(v_cursor);
        WHILE DBMS_SQL.FETCH_ROWS(v_cursor)>0 LOOP
            budget;
            v_row := JSON_ARRAY_T();
            FOR c IN 1..v_count LOOP
                IF v_desc(c).col_type=2 THEN
                    DBMS_SQL.COLUMN_VALUE(v_cursor,c,v_number);
                    IF v_number IS NULL THEN v_row.APPEND_NULL;
                    ELSE
                        v_record := JSON_OBJECT_T();
                        v_record.PUT('number',TO_CHAR(v_number,'TM9','NLS_NUMERIC_CHARACTERS=''.,'''));
                        v_row.APPEND(v_record);
                    END IF;
                ELSIF v_desc(c).col_type=112 THEN
                    DBMS_SQL.COLUMN_VALUE(v_cursor,c,v_clob);
                    IF v_clob IS NULL THEN v_row.APPEND_NULL; ELSE v_row.APPEND(encoded(v_clob)); END IF;
                ELSIF v_desc(c).col_type=8 THEN
                    DBMS_LOB.CREATETEMPORARY(v_clob,TRUE); v_offset:=0;
                    LOOP
                        DBMS_SQL.COLUMN_VALUE_LONG(v_cursor,c,8000,v_offset,v_long,v_got);
                        EXIT WHEN v_got=0;
                        DBMS_LOB.WRITEAPPEND(v_clob,LENGTH(v_long),v_long); v_offset:=v_offset+v_got;
                        IF DBMS_LOB.GETLENGTH(v_clob)>2097152 THEN RAISE_APPLICATION_ERROR(-20002,'CAPTURE_VALUE_LIMIT'); END IF;
                    END LOOP;
                    IF DBMS_LOB.GETLENGTH(v_clob)=0 THEN v_row.APPEND_NULL; ELSE v_row.APPEND(encoded(v_clob)); END IF;
                    DBMS_LOB.FREETEMPORARY(v_clob);
                ELSE
                    DBMS_SQL.COLUMN_VALUE(v_cursor,c,v_text);
                    IF v_text IS NULL THEN v_row.APPEND_NULL; ELSE v_row.APPEND(encoded(TO_CLOB(v_text))); END IF;
                END IF;
            END LOOP;
            v_record := JSON_OBJECT_T(); v_record.PUT('kind','row'); v_record.PUT('schema',v_owner);
            v_record.PUT('query',p_name); v_record.PUT('index',v_rows); v_record.PUT('values',v_row); emit(v_record);
            IF p_name IN ('inventory_before','inventory_after','owner_probe','catalog_roles') THEN p_result.APPEND(v_row); END IF;
            IF p_name='columns' AND csv_has(:p_data_types,REGEXP_REPLACE(UPPER(text_at(v_row,2)),'\([0-9, ]*\)','')) THEN
                v_dtype_tables(text_at(v_row,0)):=TRUE;
            ELSIF p_name='indexes' THEN
                v_parents('INDEX'||CHR(31)||text_at(v_row,0)):=text_at(v_row,3);
            ELSIF p_name='trigger_parents' THEN
                v_parents('TRIGGER'||CHR(31)||text_at(v_row,0)):=text_at(v_row,2);
            END IF;
            v_rows := v_rows+1;
            IF v_rows>200000 THEN RAISE_APPLICATION_ERROR(-20004,'CAPTURE_ROW_LIMIT'); END IF;
        END LOOP;
        DBMS_SQL.CLOSE_CURSOR(v_cursor);
        v_record := JSON_OBJECT_T(); v_record.PUT('kind','query_end'); v_record.PUT('schema',v_owner);
        v_record.PUT('query',p_name); v_record.PUT('rows',v_rows); v_record.PUT('status','COMPLETE'); emit(v_record);
    EXCEPTION WHEN OTHERS THEN
        v_error:=SQLCODE;
        IF v_cursor IS NOT NULL AND DBMS_SQL.IS_OPEN(v_cursor) THEN DBMS_SQL.CLOSE_CURSOR(v_cursor); END IF;
        IF v_error BETWEEN -20004 AND -20001 THEN RAISE; END IF;
        v_errors:=v_errors+1;
        p_result:=NULL;
        v_record:=JSON_OBJECT_T(); v_record.PUT('kind','query_end'); v_record.PUT('schema',v_owner);
        v_record.PUT('query',p_name); v_record.PUT('rows',v_rows); v_record.PUT('status','ERROR');
        v_record.PUT('error_code','ORA-'||TO_CHAR(ABS(v_error),'FM00000')); emit(v_record);
    END;

    FUNCTION root_matches(p_kind VARCHAR2,p_name VARCHAR2) RETURN BOOLEAN IS
        v_kind VARCHAR2(64);
    BEGIN
        IF NOT v_ddl_types.EXISTS(p_kind) THEN RETURN FALSE; END IF;
        v_kind:=v_ddl_types(p_kind);
        IF NOT csv_has(:p_object_types,v_kind) OR NOT csv_has(:p_object_names,p_name) THEN RETURN FALSE; END IF;
        IF :p_exclude_system_generated=1 AND REGEXP_LIKE(p_name,'^(BIN\$|ISEQ\$\$_|SYS_IL[0-9]|SYS_IOT_OVER_)') THEN RETURN FALSE; END IF;
        IF :p_filter_side='SOURCE' AND :p_data_types IS NOT NULL AND NOT v_dtype_tables.EXISTS(p_name) THEN RETURN FALSE; END IF;
        RETURN TRUE;
    END;

    PROCEDURE capture_schema IS
        v_dummy JSON_ARRAY_T;
        v_row JSON_ARRAY_T;
        v_kind VARCHAR2(64);
        v_name VARCHAR2(128);
        v_key VARCHAR2(512);
        v_record JSON_OBJECT_T;
        v_roots JSON_ARRAY_T := JSON_ARRAY_T();
        v_chosen JSON_ARRAY_T := JSON_ARRAY_T();
        v_count NUMBER;
        v_owner_exists NUMBER;
    BEGIN
        v_tables.DELETE; v_dtype_tables.DELETE; v_selected.DELETE; v_parents.DELETE;
        v_mode:='VISIBLE';
        IF v_owner=v_user AND :p_reader_mode IN ('AUTO','OWN') THEN v_mode:='OWN';
        ELSIF :p_reader_mode IN ('AUTO','CATALOG') THEN
            BEGIN
                query_rows('catalog_roles','["role"]','SELECT role FROM session_roles WHERE role=''SELECT_CATALOG_ROLE''',v_dummy);
                IF v_dummy IS NOT NULL AND v_dummy.GET_SIZE>0 THEN
                    query_rows('owner_probe','["username"]','SELECT username FROM dba_users WHERE username = :owner',v_dummy);
                    IF v_dummy IS NOT NULL AND v_dummy.GET_SIZE=1 THEN v_mode:='CATALOG'; END IF;
                END IF;
            EXCEPTION WHEN OTHERS THEN v_mode:='VISIBLE'; END;
        END IF;
        IF :p_reader_mode='OWN' AND v_owner<>v_user THEN RAISE_APPLICATION_ERROR(-20005,'CAPTURE_OWNER_MISMATCH'); END IF;
        IF :p_reader_mode='CATALOG' AND v_mode<>'CATALOG' THEN RAISE_APPLICATION_ERROR(-20006,'CAPTURE_CATALOG_UNVERIFIED'); END IF;
        v_record:=JSON_OBJECT_T(); v_record.PUT('kind','schema_start'); v_record.PUT('schema',v_owner);
        v_record.PUT('authority',v_mode); emit(v_record);
        query_rows('inventory_before','["object_type","object_name","status","last_ddl_time"]',
            statement_for(@@INVENTORY_QUERY@@),v_inventory);
        IF v_inventory IS NULL THEN RAISE_APPLICATION_ERROR(-20007,'CAPTURE_INVENTORY_UNAVAILABLE'); END IF;
        FOR q IN 1..v_queries.COUNT LOOP
            query_rows(v_queries(q).name,v_queries(q).columns_json,CASE WHEN v_mode='CATALOG' THEN v_queries(q).catalog_statement ELSE v_queries(q).statement END,v_dummy);
        END LOOP;
        FOR i IN 0..v_inventory.GET_SIZE-1 LOOP
            v_row:=TREAT(v_inventory.GET(i) AS JSON_ARRAY_T);v_kind:=text_at(v_row,0);v_name:=text_at(v_row,1);
            IF root_matches(v_kind,v_name) THEN
                v_key:=v_kind||CHR(31)||v_name;v_selected(v_key):=TRUE;
                v_record:=JSON_OBJECT_T();v_record.PUT('object_type',v_ddl_types(v_kind));v_record.PUT('name',v_name);v_roots.APPEND(v_record);
                IF v_kind IN ('TABLE','VIEW','MATERIALIZED VIEW') THEN v_tables(v_name):=TRUE; END IF;
            END IF;
        END LOOP;
        IF :p_include_related=1 THEN
            FOR i IN 0..v_inventory.GET_SIZE-1 LOOP
                v_row:=TREAT(v_inventory.GET(i) AS JSON_ARRAY_T);v_kind:=text_at(v_row,0);v_name:=text_at(v_row,1);v_key:=v_kind||CHR(31)||v_name;
                IF v_parents.EXISTS(v_key) AND v_tables.EXISTS(v_parents(v_key)) THEN v_selected(v_key):=TRUE; END IF;
            END LOOP;
        END IF;
        FOR i IN 0..v_inventory.GET_SIZE-1 LOOP
            v_row:=TREAT(v_inventory.GET(i) AS JSON_ARRAY_T);v_kind:=text_at(v_row,0);v_name:=text_at(v_row,1);v_key:=v_kind||CHR(31)||v_name;
            IF v_selected.EXISTS(v_key) THEN
                v_selected_count:=v_selected_count+1;
                IF v_selected_count>:p_max_objects THEN RAISE_APPLICATION_ERROR(-20008,'CAPTURE_OBJECT_LIMIT'); END IF;
                v_record:=JSON_OBJECT_T();v_record.PUT('object_type',v_ddl_types(v_kind));v_record.PUT('name',v_name);v_chosen.APPEND(v_record);
                query_rows('ddl:'||v_kind||':'||v_name,'["ddl"]',
                    'SELECT DBMS_METADATA.GET_DDL(:ddl_type, :name, :owner) FROM dual',v_dummy,v_name,v_ddl_types(v_kind));
            END IF;
        END LOOP;
        v_record:=JSON_OBJECT_T();v_record.PUT('kind','selection');v_record.PUT('schema',v_owner);
        v_record.PUT('roots',v_roots);v_record.PUT('objects',v_chosen);emit(v_record);
        ROLLBACK;
        SET TRANSACTION READ ONLY;
        query_rows('inventory_after','["object_type","object_name","status","last_ddl_time"]',
            statement_for(@@INVENTORY_QUERY@@),v_after);
        IF v_after IS NULL OR DBMS_LOB.COMPARE(v_inventory.TO_CLOB(),v_after.TO_CLOB())<>0 THEN
            RAISE_APPLICATION_ERROR(-20011,'CAPTURE_INVENTORY_CHANGED');
        END IF;
        v_record:=JSON_OBJECT_T();v_record.PUT('kind','schema_end');v_record.PUT('schema',v_owner);
        v_record.PUT('authority',v_mode);v_record.PUT('inventory_complete',v_mode IN ('OWN','CATALOG'));
        v_record.PUT('stable',TRUE);emit(v_record);
        ROLLBACK;
        SET TRANSACTION READ ONLY;
    END;
BEGIN
    :odmg_exit_code:=20;
    -- SQLcl may enable a one-megabyte buffer despite its UNLIMITED command.
    -- Our explicit packet/value/row budgets remain enforced below.
    DBMS_OUTPUT.ENABLE(NULL);
    -- Client sessions may change transforms, including export/data SQL.
    -- Match a fresh Oracle engine session instead of inheriting SQLcl settings.
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'DEFAULT',TRUE);
    SET TRANSACTION READ ONLY;
    SELECT SYS_CONTEXT('USERENV','SESSION_USER') INTO v_user FROM dual;
    IF DBMS_DB_VERSION.VERSION<19 THEN RAISE_APPLICATION_ERROR(-20009,'CAPTURE_ORACLE_VERSION_UNSUPPORTED'); END IF;
    IF :p_timeout_seconds NOT BETWEEN 30 AND 7200 OR :p_max_objects NOT BETWEEN 1 AND 100000 THEN
        RAISE_APPLICATION_ERROR(-20010,'CAPTURE_PARAMETERS_INVALID');
    END IF;
@@DDL_TYPES@@
@@QUERY_BLOCKS@@
    add_query('session_calendar','["parameter","value"]','SELECT parameter, value FROM nls_session_parameters WHERE parameter = ''NLS_CALENDAR''');
    add_query('trigger_parents','["trigger_name","table_owner","table_name"]','SELECT trigger_name, table_owner, table_name FROM all_triggers WHERE owner = :owner ORDER BY trigger_name','SELECT trigger_name, table_owner, table_name FROM dba_triggers WHERE owner = :owner ORDER BY trigger_name');
    v_header:=JSON_OBJECT_T();v_header.PUT('kind','header');v_header.PUT('schema_version','portable-capture/1.0');
    v_header.PUT('collector_version','1.0');v_header.PUT('query_contract','@@QUERY_CONTRACT@@');
    v_header.PUT('session_user',v_user);v_header.PUT('database_version',TO_CHAR(DBMS_DB_VERSION.VERSION)||'.'||TO_CHAR(DBMS_DB_VERSION.RELEASE));
    v_header.PUT('captured_at',TO_CHAR(SYS_EXTRACT_UTC(SYSTIMESTAMP),'YYYY-MM-DD"T"HH24:MI:SS.FF3"Z"'));
    v_header.PUT('environment',:p_environment);
    v_scope:=JSON_OBJECT_T();v_scope.PUT('schemas',:p_schemas);v_scope.PUT('object_types',:p_object_types);
    v_scope.PUT('object_names',:p_object_names);v_scope.PUT('data_types',:p_data_types);
    v_scope.PUT('filter_side',:p_filter_side);
    v_scope.PUT('include_related',:p_include_related=1);v_scope.PUT('exclude_system_generated',:p_exclude_system_generated=1);
    v_header.PUT('selection',v_scope);emit(v_header);
    v_schema_list:=NVL(:p_schemas,v_user);
    FOR i IN 1..REGEXP_COUNT(v_schema_list,',')+1 LOOP
        v_owner:=REGEXP_SUBSTR(v_schema_list,'[^,]+',1,i);
        capture_schema;
    END LOOP;
    v_header:=JSON_OBJECT_T();v_header.PUT('kind','footer');v_header.PUT('status',CASE WHEN v_errors>0 THEN 'PARTIAL' ELSE 'COMPLETE' END);
    v_header.PUT('messages',v_message+1);v_header.PUT('objects',v_selected_count);v_header.PUT('errors',v_errors);emit(v_header);
    :odmg_exit_code:=CASE WHEN v_errors>0 THEN 10 ELSE 0 END;
    ROLLBACK;
EXCEPTION WHEN OTHERS THEN
    :odmg_exit_code:=20;
    ROLLBACK;
    -- Missing footer makes an interrupted or failed capture non-importable.
    DBMS_OUTPUT.PUT_LINE('{"record":"capture_error","code":"ORA-'||TO_CHAR(ABS(SQLCODE),'FM00000')||'"}');
END;
/
SPOOL OFF
SET TERMOUT ON
