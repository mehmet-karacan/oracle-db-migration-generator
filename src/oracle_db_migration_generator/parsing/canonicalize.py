"""Token canonicalization keeps literal contents, quoted case and hints."""
import json
import re

from antlr4 import InputStream

from .._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer

CANONICALIZER_VERSION = 'oracle-tokens/1.0'
RESERVED = frozenset('ACCESS ADD ALL ALTER AND ANY AS ASC AUDIT BETWEEN BY CHAR CHECK CLUSTER COLUMN COMMENT COMPRESS CONNECT CREATE CURRENT DATE DECIMAL DEFAULT DELETE DESC DISTINCT DROP ELSE EXCLUSIVE EXISTS FILE FLOAT FOR FROM GRANT GROUP HAVING IDENTIFIED IMMEDIATE IN INCREMENT INDEX INITIAL INSERT INTEGER INTERSECT INTO IS LEVEL LIKE LOCK LONG MAXEXTENTS MINUS MLSLABEL MODE MODIFY NOAUDIT NOCOMPRESS NOT NOWAIT NULL NUMBER OF OFFLINE ON ONLINE OPTION OR ORDER PCTFREE PRIOR PRIVILEGES PUBLIC RAW RENAME RESOURCE REVOKE ROW ROWID ROWNUM ROWS SELECT SESSION SET SHARE SIZE SMALLINT START SUCCESSFUL SYNONYM SYSDATE SYSTIMESTAMP CURRENT_DATE CURRENT_TIMESTAMP TABLE THEN TO TRIGGER UID UNION UNIQUE UPDATE USER VALIDATE VALUES VARCHAR VARCHAR2 VIEW WHENEVER WHERE WITH'.split())


def canonical_sql(text: str) -> str:
    text = text.lstrip('\ufeff')
    text = re.sub(r'(?m)^\s*/\s*$', '', text)
    lexer = PlSqlLexer(InputStream(text))
    lexer.removeErrorListeners()
    result = []
    while True:
        token = lexer.nextToken()
        if token.type == -1:
            break
        value = token.text
        if token.channel != 0:
            if value.startswith(('/*+', '--+')):
                result.append(['hint', value])
            continue
        if value.startswith('"') and value.endswith('"'):
            name = value[1:-1].replace('""', '"')
            result.append(['quoted' if name in RESERVED else 'code', name])
        elif "'" in value:
            # Preserve national literals and their exact spelling/content.
            result.append(['literal', value])
        else:
            result.append(['code', value.upper()])
    if result[:3] == [['code', 'CREATE'], ['code', 'OR'], ['code', 'REPLACE']]:
        del result[1:3]
    while result and result[-1] == ['code', ';']:
        result.pop()
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))
