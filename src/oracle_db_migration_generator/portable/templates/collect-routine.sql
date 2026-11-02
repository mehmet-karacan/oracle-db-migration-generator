-- Şema Karşılaştırma için seçili derleme metadata kaydını salt okunur toplar.
-- Author: Mehmet KARACAN
-- Date: 2026-11-01
SET DEFINE OFF
SET AUTOCOMMIT OFF
SET ECHO OFF
SET FEEDBACK OFF
SET VERIFY OFF
SET HEADING OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMSPOOL ON
SET SERVEROUTPUT ON SIZE UNLIMITED FORMAT TRUNCATED
VARIABLE odmg_exit_code NUMBER
SPOOL routine.odmg.jsonl
DECLARE
    v_message PLS_INTEGER := 0;
    v_bytes PLS_INTEGER := 0;
    v_started TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    v_user VARCHAR2(128);
    v_version VARCHAR2(128);
    v_compatibility VARCHAR2(128);
    v_record JSON_OBJECT_T;

    FUNCTION encoded(p_text CLOB) RETURN JSON_ELEMENT_T IS
        v_object JSON_OBJECT_T := JSON_OBJECT_T();
        v_chunks JSON_ARRAY_T := JSON_ARRAY_T();
        v_piece VARCHAR2(32767);
        v_offset PLS_INTEGER := 1;
    BEGIN
        IF p_text IS NULL THEN RETURN NULL; END IF;
        IF DBMS_LOB.GETLENGTH(p_text) > 2097152 THEN
            RAISE_APPLICATION_ERROR(-20002,'ROUTINE_VALUE_LIMIT');
        END IF;
        WHILE v_offset <= DBMS_LOB.GETLENGTH(p_text) LOOP
            v_piece := DBMS_LOB.SUBSTR(p_text,4000,v_offset);
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
        IF DBMS_LOB.GETLENGTH(v_text) > 8388608 THEN
            RAISE_APPLICATION_ERROR(-20003,'ROUTINE_MESSAGE_LIMIT');
        END IF;
        v_message := v_message + 1;
        WHILE v_offset <= DBMS_LOB.GETLENGTH(v_text) LOOP
            v_piece := DBMS_LOB.SUBSTR(v_text,4000,v_offset);
            v_raw := UTL_I18N.STRING_TO_RAW(v_piece,'AL32UTF8');
            SELECT RAWTOHEX(STANDARD_HASH(v_raw,'SHA256')) INTO v_hash FROM dual;
            v_line := '{"record":"chunk","message":'||TO_CHAR(v_message,'FM9999999990')||
                ',"part":'||TO_CHAR(v_part,'FM9999999990')||',"sha256":"'||v_hash||'","data":"'||
                REPLACE(REPLACE(UTL_RAW.CAST_TO_VARCHAR2(UTL_ENCODE.BASE64_ENCODE(v_raw)),CHR(13),''),CHR(10),'')||'"}';
            IF v_bytes + LENGTHB(v_line) > 67108864 THEN
                RAISE_APPLICATION_ERROR(-20004,'ROUTINE_OUTPUT_LIMIT');
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

    PROCEDURE capture_query(p_index PLS_INTEGER,p_sql VARCHAR2,p_owner VARCHAR2 DEFAULT NULL,
        p_name VARCHAR2 DEFAULT NULL,p_kind VARCHAR2 DEFAULT NULL,p_ddl_type VARCHAR2 DEFAULT NULL) IS
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
        v_rows JSON_ARRAY_T := JSON_ARRAY_T();
        v_row JSON_ARRAY_T;
        v_record JSON_OBJECT_T;
        v_error INTEGER;
    BEGIN
        IF (CAST(SYSTIMESTAMP AS DATE)-CAST(v_started AS DATE))*86400 > 7200 THEN
            RAISE_APPLICATION_ERROR(-20005,'ROUTINE_TIME_LIMIT');
        END IF;
        v_cursor := DBMS_SQL.OPEN_CURSOR;
        DBMS_SQL.PARSE(v_cursor,p_sql,DBMS_SQL.NATIVE);
        IF INSTR(p_sql,':owner')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':owner',p_owner); END IF;
        IF INSTR(p_sql,':name')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':name',p_name); END IF;
        IF INSTR(p_sql,':kind')>0 THEN DBMS_SQL.BIND_VARIABLE(v_cursor,':kind',p_kind); END IF;
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
                    IF v_clob IS NULL THEN v_row.APPEND_NULL;
                    ELSE v_row.APPEND(encoded(v_clob)); END IF;
                ELSIF v_desc(c).col_type=8 THEN
                    DBMS_LOB.CREATETEMPORARY(v_clob,TRUE);v_offset:=0;
                    LOOP
                        DBMS_SQL.COLUMN_VALUE_LONG(v_cursor,c,8000,v_offset,v_long,v_got);
                        EXIT WHEN v_got=0;
                        DBMS_LOB.WRITEAPPEND(v_clob,LENGTH(v_long),v_long);v_offset:=v_offset+v_got;
                        IF DBMS_LOB.GETLENGTH(v_clob)>2097152 THEN RAISE_APPLICATION_ERROR(-20002,'ROUTINE_VALUE_LIMIT'); END IF;
                    END LOOP;
                    IF DBMS_LOB.GETLENGTH(v_clob)=0 THEN v_row.APPEND_NULL;
                    ELSE v_row.APPEND(encoded(v_clob)); END IF;
                    DBMS_LOB.FREETEMPORARY(v_clob);
                ELSE
                    DBMS_SQL.COLUMN_VALUE(v_cursor,c,v_text);
                    IF v_text IS NULL THEN v_row.APPEND_NULL;
                    ELSE v_row.APPEND(encoded(TO_CLOB(v_text))); END IF;
                END IF;
            END LOOP;
            v_rows.APPEND(v_row);
            IF v_rows.GET_SIZE>50000 THEN RAISE_APPLICATION_ERROR(-20006,'ROUTINE_ROW_LIMIT'); END IF;
        END LOOP;
        DBMS_SQL.CLOSE_CURSOR(v_cursor);
        v_record := JSON_OBJECT_T();v_record.PUT('kind','query');v_record.PUT('index',p_index);
        v_record.PUT('state','KNOWN');v_record.PUT('rows',v_rows);emit(v_record);
    EXCEPTION WHEN OTHERS THEN
        v_error:=SQLCODE;
        IF v_cursor IS NOT NULL AND DBMS_SQL.IS_OPEN(v_cursor) THEN DBMS_SQL.CLOSE_CURSOR(v_cursor); END IF;
        IF v_error BETWEEN -20006 AND -20002 THEN RAISE; END IF;
        v_record := JSON_OBJECT_T();v_record.PUT('kind','query');v_record.PUT('index',p_index);
        v_record.PUT('state','UNKNOWN');v_record.PUT('rows',JSON_ARRAY_T());
        v_record.PUT('error_code','ORA-'||TO_CHAR(ABS(v_error),'FM00000'));emit(v_record);
    END;

BEGIN
    :odmg_exit_code := 20;
    DBMS_OUTPUT.ENABLE(NULL);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'DEFAULT',TRUE);
    SET TRANSACTION READ ONLY;
    SELECT SYS_CONTEXT('USERENV','SESSION_USER') INTO v_user FROM dual;
    IF v_user <> @@ROOT_OWNER@@ THEN RAISE_APPLICATION_ERROR(-20007,'ROUTINE_OWNER_MISMATCH'); END IF;
    SELECT version_full INTO v_version
    FROM product_component_version
    WHERE product LIKE 'Oracle Database%' AND ROWNUM = 1;
    v_record := JSON_OBJECT_T();v_record.PUT('kind','header');
    v_record.PUT('schema_version','routine-capture/1.0');
    v_record.PUT('request_sha256','@@REQUEST_SHA@@');
    v_record.PUT('session_user',v_user);v_record.PUT('database_version',v_version);
    v_record.PUT('captured_at',TO_CHAR(SYS_EXTRACT_UTC(SYSTIMESTAMP),'YYYY-MM-DD"T"HH24:MI:SS.FF3"Z"'));
    emit(v_record);
@@QUERY_CALLS@@
    v_record := JSON_OBJECT_T();v_record.PUT('kind','footer');
    v_record.PUT('queries',@@QUERY_COUNT@@);v_record.PUT('messages',v_message+1);emit(v_record);
    :odmg_exit_code := 0;
    ROLLBACK;
EXCEPTION WHEN OTHERS THEN
    :odmg_exit_code := 20;
    ROLLBACK;
    DBMS_OUTPUT.PUT_LINE('{"record":"capture_error","code":"ORA-'||TO_CHAR(ABS(SQLCODE),'FM00000')||'"}');
END;
/
SPOOL OFF
EXIT :odmg_exit_code ROLLBACK
