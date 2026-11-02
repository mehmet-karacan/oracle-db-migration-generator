"""Şema Karşılaştırma için parolasız SQLcl toplama paketi hazırlar.

Paket hazırlığı Oracle bağlantısı açmaz ve kaynak dosyalara yazmaz.

Author: Mehmet KARACAN
Date: 2026-10-26
"""
import json
import hashlib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import shutil
import tempfile
from ..oracle.queries import CAPTURE_QUERIES,CAPTURE_INVENTORY,COLLATION_PARAMETERS,DDL_TYPES
from ..oracle.catalog_reader import _STATEMENTS
from .selection import CaptureFilter
from ..model.atomic import rename_new_directory
from ..planning.routine_proof import _metadata
from ..oracle.routine_metadata import UNIT_KINDS, QUERIES as ROUTINE_QUERIES
from ..model.serialization import digest

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


@dataclass(frozen=True)
class RoutineCaptureRequest:
    """Kaynak kanıtındaki birim ve bağımlılıkları hedef gözlemine bağlar.

    Author: Mehmet KARACAN
    Date: 2026-11-01
    """

    selected_units: tuple[tuple[str, str], ...]
    record_keys: tuple[tuple[str, str, str], ...]
    target_snapshot_digest: str
    root_owner: str
    include_compiler_runtime: bool

    @property
    def queries(self):
        rows = [('identity', None, 'identity')]
        units = {(self.root_owner, name, kind) for kind, name in self.selected_units}
        for key in self.record_keys:
            rows.append(('object', key, 'before'))
            if key in units:
                rows.extend((name, key, name) for name in ('dependencies', 'errors', 'settings'))
            if key[2] == 'SYNONYM':
                rows.extend((name, key, name) for name in ('synonym', 'local_shadow'))
            else:
                rows.extend((name, key, name) for name in ('columns', 'procedures', 'arguments', 'privileges'))
                if key[2] in UNIT_KINDS | {'TYPE', 'TABLE', 'VIEW', 'SEQUENCE', 'RESOLVED'}:
                    rows.append(('ddl_resolved' if key[2] == 'RESOLVED' else 'ddl', key, 'ddl'))
            rows.append(('object', key, 'after'))
            if key in units:
                rows.append(('dependencies', key, 'dependencies_after'))
        if self.include_compiler_runtime:
            rows.extend((name, None, name) for name in ('compiler_objects', 'compiler_source'))
        return tuple(rows)

    @property
    def sha256(self):
        return digest({'selected_units': self.selected_units, 'record_keys': self.record_keys,
                       'target_snapshot_digest': self.target_snapshot_digest,
                       'root_owner': self.root_owner,
                       'include_compiler_runtime': self.include_compiler_runtime,
                       'queries': self.queries})


def routine_capture_request(source, target):
    """Doğrulanmış kaynak derleyici kaydından kapalı hedef isteği çıkarır."""
    if source.side != 'SOURCE' or target.side != 'TARGET':
        raise ValueError('ROUTINE_CAPTURE_SIDES_INVALID')
    data, records, _ = _metadata(source)
    units = tuple(tuple(item) for item in data.get('selected_units', ()))
    if not units or len(units) > 64 or len(records) > 256:
        raise ValueError('ROUTINE_CAPTURE_SCOPE_INVALID')
    owners = set(source.schemas) & set(target.schemas)
    if len(owners) != 1 or source.profile_id != target.profile_id:
        raise ValueError('ROUTINE_CAPTURE_OWNER_INVALID')
    owner = next(iter(owners))
    if any(kind not in UNIT_KINDS or not isinstance(name, str) or not name
           or (owner, name, kind) not in records for kind, name in units):
        raise ValueError('ROUTINE_CAPTURE_SCOPE_INVALID')
    if any(len(key) != 3 or any(not isinstance(value, str) or not value
           or len(value.encode('utf-8')) > 128 or any(ord(ch) < 32 for ch in value)
           for value in key) for key in records):
        raise ValueError('ROUTINE_CAPTURE_SCOPE_INVALID')
    return RoutineCaptureRequest(units, tuple(sorted(records)), target.semantic_digest,
                                 owner, bool(data.get('compiler_runtime')))


RESOLVED_DDL = '''SELECT
    DBMS_METADATA.GET_DDL(
        CASE object_type WHEN 'PACKAGE' THEN 'PACKAGE_SPEC'
            WHEN 'TYPE' THEN 'TYPE_SPEC' ELSE object_type END,
        :name, :owner)
FROM all_objects
WHERE owner = :owner AND object_name = :name
    AND subobject_name IS NULL
    AND object_type IN ('TABLE','VIEW','PACKAGE','TYPE','SEQUENCE','PROCEDURE','FUNCTION')'''


def routine_capture_script(request):
    """Kapalı SELECT listesini SQLcl ve SQL*Plus için çalıştırma dosyasına yazar."""
    root = files('oracle_db_migration_generator').joinpath('portable/templates')
    script = root.joinpath('collect-routine.sql').read_text(encoding='utf-8')
    calls = []
    for index, (query, key, _field) in enumerate(request.queries):
        sql = RESOLVED_DDL if query == 'ddl_resolved' else ROUTINE_QUERIES[query]
        owner, name, kind = key if key is not None else (None, None, None)
        ddl_type = {'PACKAGE': 'PACKAGE_SPEC', 'PACKAGE BODY': 'PACKAGE_BODY',
                    'TYPE': 'TYPE_SPEC', 'TYPE BODY': 'TYPE_BODY'}.get(kind, kind)
        args = [str(index), _literal(sql), *(_literal(v) if v is not None else 'NULL'
                                           for v in (owner, name, kind, ddl_type))]
        calls.append('    capture_query(' + ','.join(args) + ');')
    return (script.replace('@@ROOT_OWNER@@', _literal(request.root_owner))
                  .replace('@@REQUEST_SHA@@', request.sha256)
                  .replace('@@QUERY_COUNT@@', str(len(request.queries)))
                  .replace('@@QUERY_CALLS@@', '\n'.join(calls)))


def prepare_routine_capture(output, source, target):
    """Kaynak kanıtına bağlı hedef SQLcl paketi oluşturur ve mevcut dizini korur."""
    request = routine_capture_request(source, target)
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('CAPTURE_OUTPUT_ALREADY_EXISTS')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.routine-capture-', dir=output.parent))
    try:
        (staging / 'run_routine.sql').write_text(routine_capture_script(request),
                                                  encoding='utf-8', newline='\n')
        description = {
            'schema_version': 'routine-request/1.0', 'sha256': request.sha256,
            'root_owner': request.root_owner, 'target_snapshot_digest': request.target_snapshot_digest,
            'selected_units': request.selected_units, 'record_keys': request.record_keys,
            'query_count': len(request.queries),
        }
        (staging / 'request.json').write_text(json.dumps(description, ensure_ascii=False,
                                                         indent=2) + '\n', encoding='utf-8', newline='\n')
        (staging / 'README.md').write_text(
            '# Şema Karşılaştırma derleyici kanıtı\n\n'
            'Author: Mehmet KARACAN\nDate: 2026-11-01\n\n'
            'Bu paket seçili program birimleri için salt okunur metadata toplar. '
            'Veri tabanında nesne çalıştırmaz veya değiştirmez.\n\n'
            'Mevcut SQLcl veya SQL*Plus oturumunda `@run_routine.sql` çalıştırın. '
            '`routine.odmg.jsonl` dosyasını aynı hedef snapshot ile içe aktarın. '
            'Ayrı ve temiz bir oturum kullanın, betik sonunda oturum kapanır.\n',
            encoding='utf-8', newline='\n')
        rename_new_directory(staging, output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output


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
