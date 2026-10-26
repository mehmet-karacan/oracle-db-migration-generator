"""Generate a credential-free SQL*Plus/SQLcl capture package offline."""
import json
import hashlib
from importlib.resources import files
from pathlib import Path
import shutil
import tempfile
from ..oracle.queries import CAPTURE_QUERIES,CAPTURE_INVENTORY,COLLATION_PARAMETERS,DDL_TYPES
from ..oracle.catalog_reader import _STATEMENTS
from .selection import CaptureFilter
from ..model.atomic import rename_new_directory

PORTABLE_INVENTORY=CAPTURE_INVENTORY.replace('WHERE owner = :owner','WHERE owner = :owner AND subobject_name IS NULL')
DEPENDENCY_OBJECTS='''SELECT
    o.owner, o.object_name, o.object_type, o.status
FROM all_objects o
WHERE o.subobject_name IS NULL
    AND o.owner <> :owner
    AND EXISTS (
        SELECT
            1
        FROM all_dependencies d
        WHERE d.owner = :owner
            AND d.referenced_owner = o.owner
            AND d.referenced_name = o.object_name
    )
ORDER BY o.owner, o.object_name, o.object_type'''


def query_contract():
    return hashlib.sha256(json.dumps({'inventory':PORTABLE_INVENTORY,'queries':CAPTURE_QUERIES,'collation':COLLATION_PARAMETERS,'ddl_types':DDL_TYPES},sort_keys=True).encode()).hexdigest()


def _literal(text):return "'"+text.replace("'","''")+"'"


def _hex_bind(key,value):
    if isinstance(value,(list,tuple)):value=','.join(value)
    if isinstance(value,bool):return f':p_{key} := '+('1' if value else '0')+';'
    if isinstance(value,int):return f':p_{key} := {value};'
    if not value:return f':p_{key} := NULL;'
    encoded=value.encode('utf-8').hex().upper()
    parts=[encoded[i:i+1800] for i in range(0,len(encoded),1800)]
    return f':p_{key} := UTL_I18N.RAW_TO_CHAR(HEXTORAW(\n'+(' ||\n'.join(_literal(p) for p in parts))+"\n), 'AL32UTF8');"


def _query_blocks():
    rows=[]
    for name,(columns,sql) in CAPTURE_QUERIES.items():
        rows.append('    add_query('+_literal(name)+','+_literal(json.dumps(columns,separators=(',',':')))+','+_literal(sql)+','+_literal(_STATEMENTS.get(sql,sql))+');')
    rows.append("    add_query('collation_parameters','[\"name\",\"value\"]',"+_literal(COLLATION_PARAMETERS)+');')
    rows.append("    add_query('dependency_objects','[\"owner\",\"object_name\",\"object_type\",\"status\"]',"+
        _literal(DEPENDENCY_OBJECTS)+','+_literal(DEPENDENCY_OBJECTS.replace('all_','dba_'))+');')
    return '\n'.join(rows)


def package_files(selection):
    scope=CaptureFilter.from_dict(selection) if isinstance(selection,dict) else selection
    if not set(scope.object_types)&set(DDL_TYPES.values()):raise ValueError('CAPTURE_ROOT_TYPES_REQUIRED')
    values=scope.to_dict();binds={key:getattr(scope,key) for key in values};root=files('oracle_db_migration_generator').joinpath('portable/templates')
    collector=root.joinpath('collect.sql').read_text(encoding='utf-8').replace('@@QUERY_BLOCKS@@',_query_blocks())
    kinds='\n'.join('    v_ddl_types('+_literal(oracle)+') := '+_literal(kind)+';' for oracle,kind in DDL_TYPES.items())
    collector=collector.replace('@@DDL_TYPES@@',kinds).replace('@@QUERY_CONTRACT@@',query_contract())
    collector=collector.replace('@@INVENTORY_QUERY@@',_literal(PORTABLE_INVENTORY))
    string_keys=[key for key,value in values.items() if not isinstance(value,(bool,int))]
    for key in string_keys:collector=collector.replace(':p_'+key,'v_p_'+key)
    collector=collector.replace('@@STRING_PARAMS@@','\n'.join('    v_p_'+key+' VARCHAR2(32767) := :p_'+key+';' for key in string_keys))
    request='SET DEFINE OFF\nSET SQLBLANKLINES ON\nSET ECHO OFF\nWHENEVER OSERROR EXIT FAILURE ROLLBACK\nWHENEVER SQLERROR EXIT FAILURE ROLLBACK\n'
    for key,value in values.items():request+='VARIABLE p_'+key+(' NUMBER\n' if isinstance(value,(bool,int)) else ' CLOB\n')
    request+='VARIABLE odmg_exit_code NUMBER\nBEGIN\n'+'\n'.join('    '+_hex_bind(k,v) for k,v in binds.items())+'\nEND;\n/\n@collect.sql\nEXIT :odmg_exit_code ROLLBACK\n'
    payload={'run_export.sql':request,'collect.sql':collector,'selection.json':json.dumps(values,ensure_ascii=False,indent=2)+'\n'}
    for name in ('New-Capture.ps1','README.md'):payload[name]=root.joinpath(name).read_text(encoding='utf-8')
    return payload


def prepare_capture(output,selection):
    output=Path(output).resolve()
    if output.exists():raise ValueError('CAPTURE_OUTPUT_ALREADY_EXISTS')
    payload=package_files(selection);output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.capture-',dir=output.parent))
    try:
        for name,text in payload.items():(staging/name).write_text(text,encoding='utf-8',newline='\n')
        rename_new_directory(staging,output)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return output
