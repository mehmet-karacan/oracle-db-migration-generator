"""Bounded SELECT-only supplement for previously held compiled program units.

The caller owns a read-only transaction and private evidence storage. No text
read from a snapshot can become SQL. Every query is fixed and value-bound.
"""
import hashlib
import time
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone

from ..model.evidence import Evidence
from ..model.serialization import canonical_bytes, digest, thaw
from ..model.snapshot import KnownValue
from ..source.models import SourceArtifact
from ..model.identity import Identifier
from .preflight import safe_error_code

UNIT_KINDS=frozenset({'PROCEDURE','FUNCTION','PACKAGE','PACKAGE BODY','TRIGGER'})


def _base_snapshot(snapshot):
    # UI selection describes the same Oracle observation. It may be added
    # after a source capture and must not invalidate its catalog evidence.
    return replace(snapshot,capabilities={k:v for k,v in snapshot.capabilities.items()
                                           if k not in {'routine_metadata','comparison_filter'}})
QUERIES={
    'identity': "SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') FROM dual",
    'object': '''SELECT
    object_type, status, TO_CHAR(last_ddl_time, 'YYYY-MM-DD"T"HH24:MI:SS'), edition_name
FROM all_objects
WHERE owner = :owner AND object_name = :name AND subobject_name IS NULL
ORDER BY object_type''',
    'dependencies': '''SELECT
    name, type, referenced_owner, referenced_name, referenced_type, referenced_link_name, dependency_type
FROM all_dependencies
WHERE owner = :owner AND name = :name AND type = :kind
ORDER BY referenced_owner, referenced_name, referenced_type''',
    'errors': '''SELECT
    name, type, attribute, message_number
FROM all_errors
WHERE owner = :owner AND name = :name AND type = :kind
ORDER BY sequence''',
    'settings': '''SELECT
    type, plsql_optimize_level, plsql_code_type, plsql_debug, plsql_warnings,
    nls_length_semantics, plsql_ccflags, plscope_settings
FROM all_plsql_object_settings
WHERE owner = :owner AND name = :name AND type = :kind''',
    'procedures': '''SELECT
    procedure_name, subprogram_id, overload, object_type, authid, aggregate,
    pipelined, parallel, interface, deterministic, result_cache
FROM all_procedures
WHERE owner = :owner AND object_name = :name
ORDER BY subprogram_id, overload''',
    'arguments': '''SELECT
    package_name, object_name, overload, subprogram_id, argument_name, position,
    sequence, data_level, data_type, defaulted, in_out, data_length, data_precision,
    data_scale, character_set_name, type_owner, type_name, type_subname, type_link,
    pls_type, char_length, char_used
FROM all_arguments
WHERE owner = :owner AND (package_name = :name OR package_name IS NULL AND object_name = :name)
ORDER BY subprogram_id, overload, sequence''',
    'columns': '''SELECT
    column_name, data_type, data_type_owner, data_length, data_precision, data_scale,
    char_length, char_used, nullable, column_id, hidden_column, virtual_column,
    identity_column, default_on_null, collation
FROM all_tab_cols
WHERE owner = :owner AND table_name = :name
ORDER BY internal_column_id''',
    'synonym': '''SELECT
    table_owner, table_name, db_link
FROM all_synonyms
WHERE owner = :owner AND synonym_name = :name''',
    'local_shadow': '''SELECT
    object_type, status
FROM all_objects
WHERE owner = SYS_CONTEXT('USERENV','SESSION_USER') AND object_name = :name AND subobject_name IS NULL
ORDER BY object_type''',
    'privileges': '''SELECT
    grantee, privilege
FROM all_tab_privs
WHERE table_schema = :owner AND table_name = :name
    AND grantee IN (SYS_CONTEXT('USERENV','SESSION_USER'),'PUBLIC')
ORDER BY grantee, privilege''',
    'ddl': 'SELECT DBMS_METADATA.GET_DDL(:ddl_type, :name, :owner) FROM dual',
    'compiler_objects': '''SELECT
    object_type, status
FROM dba_objects
WHERE owner = 'SYS' AND object_name = 'SYS_STUB_FOR_PURITY_ANALYSIS' AND subobject_name IS NULL
ORDER BY object_type''',
    'compiler_source': '''SELECT
    type, line, text
FROM dba_source
WHERE owner = 'SYS' AND name = 'SYS_STUB_FOR_PURITY_ANALYSIS'
ORDER BY type, line''',
}


def snapshot_binding_digest(snapshot):
    """Bind compiler evidence to one side, connection observation and DDL set."""
    snapshot=_base_snapshot(snapshot)
    return digest({'semantic_digest':snapshot.semantic_digest,'side':snapshot.side,
                   'source_origin':thaw(snapshot.source_origin),'source_commit':snapshot.source_commit,
                   'target_id':snapshot.target_id,
                   'ddl':sorted((obj.object_key,obj.ddl_sha256) for obj in snapshot.objects)})


def snapshot_scope_state(snapshot):
    """Record the full capture so a later selection can prove it only removed objects."""
    base=_base_snapshot(snapshot)
    return {'base_snapshot_digest':base.semantic_digest,
            'base_snapshot_binding':snapshot_binding_digest(base),
            'schema_version':base.schema_version,'synthetic':base.synthetic,
            'side':base.side,'profile_id':base.profile_id,
            'source_origin':thaw(base.source_origin),'source_commit':base.source_commit,
            'target_id':base.target_id,'schemas':tuple(base.schemas),
            'capabilities_digest':digest(thaw(base.capabilities)),
            'completeness':thaw(base.completeness),
            'objects':tuple((obj.object_key,digest(obj.to_dict())) for obj in base.objects)}


def scoped_snapshot_matches(snapshot,document):
    """Accept only a byte-identical object subset of the bound full snapshot."""
    state=document.get('base_scope')
    if not isinstance(state,Mapping):return False
    base=_base_snapshot(snapshot)
    if (state.get('base_snapshot_digest')!=document.get('base_snapshot_digest')
            or state.get('base_snapshot_binding')!=document.get('base_snapshot_binding')
            or state.get('schema_version')!=base.schema_version or state.get('synthetic')!=base.synthetic
            or state.get('side')!=base.side or state.get('profile_id')!=base.profile_id
            or state.get('source_origin')!=thaw(base.source_origin)
            or state.get('source_commit')!=base.source_commit or state.get('target_id')!=base.target_id
            or state.get('capabilities_digest')!=digest(thaw(base.capabilities))):return False
    if not set(base.schemas)<=set(state.get('schemas',())):return False
    original=dict(state.get('objects',()))
    if len(original)!=len(state.get('objects',())):return False
    if any(original.get(obj.object_key)!=digest(obj.to_dict()) for obj in base.objects):return False
    coverage=state.get('completeness',{})
    if (base.completeness.inventory!=coverage.get('inventory')
            or base.completeness.dictionary!=coverage.get('dictionary')
            or tuple(base.completeness.diagnostics)!=tuple(coverage.get('diagnostics',()))
            or base.completeness.ddl!=('PARTIAL' if any(obj.coverage.ddl!='COMPLETE' for obj in base.objects)
                                       else 'COMPLETE')):return False
    return True


def read_routine_metadata(cursor,units,*,owner,oracle_version,dependency_rows=(),deadline=None):
    """Collect <=64 units and <=256 direct dependencies plus one-hop synonyms.

    Missing ALL_* visibility is not absence proof. In particular, a missing
    local object can only be planned through the separately complete snapshot.
    Compiler internals use two exact DBA queries, never generic catalog SQL.
    """
    units=tuple(units)
    if (not units or len(units)>64 or len(set(units))!=len(units)
            or any(kind not in UNIT_KINDS or not isinstance(name,str) or not name or len(name.encode())>128 for kind,name in units)
            or not isinstance(owner,str) or not owner or len(owner.encode())>128):
        raise ValueError('ROUTINE_METADATA_SCOPE_INVALID')
    calls=0
    def query(key,binds):
        nonlocal calls
        if deadline is not None and time.monotonic()>=deadline:raise TimeoutError('ROUTINE_METADATA_DEADLINE')
        calls+=1
        try:
            cursor.execute(QUERIES[key],binds);rows=[]
            for row in cursor.fetchall():
                if len(rows)>=50000:raise ValueError('ROUTINE_METADATA_ROW_LIMIT')
                values=[v.read() if hasattr(v,'read') else v for v in row]
                if any(isinstance(v,str) and len(v.encode())>4*1024*1024 for v in values):
                    raise ValueError('ROUTINE_METADATA_VALUE_LIMIT')
                rows.append(values)
            return {'state':'KNOWN','rows':rows}
        except Exception as error:
            return {'state':'UNKNOWN','error_code':safe_error_code(error)}
    def ddl(who,name,kind):
        result=query('ddl',{'owner':who,'name':name,'ddl_type':{'PACKAGE':'PACKAGE_SPEC','PACKAGE BODY':'PACKAGE_BODY','TYPE':'TYPE_SPEC'}.get(kind,kind)})
        rows=result.get('rows',())
        if result['state']=='KNOWN' and len(rows)==1 and len(rows[0])==1 and isinstance(rows[0][0],str) and rows[0][0]:
            return {'state':'KNOWN','sha256':hashlib.sha256(rows[0][0].encode()).hexdigest()}
        return {'state':'UNKNOWN','error_code':result.get('error_code','DDL_EMPTY')}
    identity=query('identity',{})
    records={};requested={(owner,name,kind) for kind,name in units};dependencies=list(dependency_rows)
    for kind,name in units:
        bind={'owner':owner,'name':name};unitbind={**bind,'kind':kind}
        record={'owner':owner,'name':name,'kind':kind,'before':query('object',bind)}
        for field in ('dependencies','errors','settings'):record[field]=query(field,unitbind)
        dependencies.extend(record['dependencies'].get('rows',()))
        records[(owner,name,kind)]=record
    if len(dependencies)>2048:raise ValueError('ROUTINE_METADATA_DEPENDENCY_LIMIT')
    for row in dependencies:
        if len(row)!=7 or any(not isinstance(value,str) or not value or len(value.encode())>128 for value in row[2:5]):
            raise ValueError('ROUTINE_METADATA_DEPENDENCY_INVALID')
        requested.add(tuple(row[2:5]))
    if len(requested)>256:raise ValueError('ROUTINE_METADATA_SCOPE_LIMIT')
    # One-hop synonym targets are metadata requests, never statements/includes.
    for who,name,kind in sorted(requested):
        if kind!='SYNONYM':continue
        bind={'owner':who,'name':name};record={'owner':who,'name':name,'kind':kind,'before':query('object',bind),'synonym':query('synonym',bind),
                                           'local_shadow':query('local_shadow',{'name':name})}
        records[(who,name,kind)]=record
        for target_owner,target_name,link in record['synonym'].get('rows',()):
            if not link and target_owner and target_name:
                records.setdefault((target_owner,target_name,'RESOLVED'),{'owner':target_owner,'name':target_name,'kind':'RESOLVED'})
    requested.update(records)
    for who,name,kind in sorted(requested):
        record=records.setdefault((who,name,kind),{'owner':who,'name':name,'kind':kind});bind={'owner':who,'name':name}
        if 'before' not in record:record['before']=query('object',bind)
        if kind=='SYNONYM':continue
        for field in ('columns','procedures','arguments','privileges'):record[field]=query(field,bind)
        concrete=[r[0] for r in record['before'].get('rows',()) if r[0] in {'TABLE','VIEW','PACKAGE','TYPE','PROCEDURE','FUNCTION','SEQUENCE'}]
        ddl_kind=kind if (who,name,kind) in {(owner,n,k) for k,n in units} else (kind if kind!='RESOLVED' else concrete[0] if len(concrete)==1 else None)
        if ddl_kind in UNIT_KINDS|{'TYPE','TABLE','VIEW','SEQUENCE'} and any(r[0]==ddl_kind for r in record['before'].get('rows',())):
            record['ddl']=ddl(who,name,ddl_kind)
            record['dependency_ddl']=dict(record['ddl'])
    compiler={}
    if any(tuple(row[2:5])==('SYS','SYS_STUB_FOR_PURITY_ANALYSIS','PACKAGE') for row in dependencies):
        objects=query('compiler_objects',{});raw=query('compiler_source',{})
        compiler={'objects':objects,'source_sha256':digest(raw) if raw['state']=='KNOWN' and raw['rows'] else None}
    # Re-read all stamps after the full observation, not just each individual SELECT.
    for key,record in sorted(records.items()):
        who,name,kind=key;record['after']=query('object',{'owner':who,'name':name})
        if (kind,name) in units and who==owner:
            record['dependencies_after']=query('dependencies',{'owner':who,'name':name,'kind':kind})
    return {'identity':identity,'oracle_version':oracle_version,'selected_units':units,
            'records':[records[key] for key in sorted(records)],
            'compiler_runtime':compiler,'query_count':calls,'execution_status':'NOT_EXECUTED'}


def attach_routine_metadata(snapshot,capture):
    """Bind a supplement to exactly one immutable base snapshot and its side.

    Return the new snapshot and private evidence bytes. The caller must save
    those bytes at the returned evidence path alongside the new snapshot.
    """
    if 'routine_metadata' in snapshot.capabilities:raise ValueError('ROUTINE_METADATA_ALREADY_ATTACHED')
    base=_base_snapshot(snapshot)
    document={**capture,'base_snapshot_digest':base.semantic_digest,
              'base_snapshot_binding':snapshot_binding_digest(snapshot),
              'base_scope':snapshot_scope_state(snapshot)}
    sha=digest(document);raw=canonical_bytes(document)
    evidence=Evidence('ev-'+digest([snapshot.side,sha]),'SOURCE_METADATA' if snapshot.side=='SOURCE' else 'TARGET_METADATA',snapshot.side,
                      'routine-metadata/'+sha+'.json',sha,None,None,'oracle.compiled-static/v1',
                      'Salt okunur derleme, bağımlılık, synonym, imza ve doğrudan erişim metadata gözlemi.')
    updated=replace(snapshot,capabilities={**snapshot.capabilities,'routine_metadata':KnownValue('KNOWN',document,(evidence.id,))},evidence=(*snapshot.evidence,evidence))
    return updated,evidence.path,raw


def candidate_compiled_units(snapshot):
    """Pick bounded valid source units that need a static dependency inventory."""
    from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
    from ..parsing.dependencies import has_dynamic_sql
    selected=[]
    for obj in snapshot.objects:
        kind=obj.identity.object_type
        if kind not in {'PROCEDURE','FUNCTION','PACKAGE_SPEC','PACKAGE_BODY'} or not obj.raw_ddl:
            continue
        status=obj.properties.get('object_status')
        declared=obj.properties.get('dependencies')
        if (not status or status.state!='KNOWN' or status.value!='VALID'
                or declared and declared.state=='KNOWN' or has_dynamic_sql(obj)):
            continue
        tokens=code_tokens(obj.raw_ddl.decode()) or ()
        words={token.upper for token in tokens}
        qualified_uses=sum(token.text=='.' for token in tokens)
        own_qualified=any(tokens[i].text=='.' and i>0 and i+1<len(tokens)
                          and tokens[i-1].text.strip('"').upper()==obj.identity.owner.effective_name.upper()
                          and tokens[i+1].text.strip('"').upper()==obj.identity.name.effective_name.upper()
                          for i in range(min(len(tokens),12)))
        if qualified_uses<=int(own_qualified) and not words & {'SELECT','INSERT','UPDATE','DELETE','MERGE','EXECUTE'}:
            continue
        selected.append(({'PACKAGE_SPEC':'PACKAGE','PACKAGE_BODY':'PACKAGE BODY'}.get(kind,kind),
                         obj.identity.name.effective_name))
    result=tuple(sorted(set(selected)))
    if len(result)>64:raise ValueError('ROUTINE_METADATA_SCOPE_LIMIT')
    return result


def complete_routine_observation(observation,config,credentials,*,source=None,connect=None,deadline=None):
    """Attach optional, private, read-only compiler evidence to one Oracle snapshot.

    Any unavailable evidence leaves the main capture intact. The planner then
    keeps affected units in REVIEW instead of assuming an empty inventory.
    """
    snapshot=observation.snapshot
    if snapshot is None:return observation
    def unavailable(code):
        return replace(observation,receipt={**observation.receipt,
                           'routine_metadata':{'status':'UNAVAILABLE','error_code':code}})
    if len(config.schema_mappings)!=1 or len(snapshot.schemas)!=1:
        return unavailable('ROUTINE_METADATA_SINGLE_SCHEMA_REQUIRED')
    mapping=config.schema_mappings[0]
    owner=Identifier.parse(mapping.target_schema).effective_name
    if snapshot.schemas!=(owner,):return unavailable('ROUTINE_METADATA_OWNER_MISMATCH')
    if source is None:
        if snapshot.side!='SOURCE' or not snapshot.source_origin or snapshot.source_origin.get('kind')!='ORACLE':
            return observation
        try:units=candidate_compiled_units(snapshot)
        except ValueError as error:return unavailable(str(error))
        dependencies=()
    else:
        if snapshot.side!='TARGET':return observation
        capability=source.capabilities.get('routine_metadata')
        if not capability or capability.state!='KNOWN':return observation
        data=capability.value
        units=tuple(tuple(item) for item in data.get('selected_units',()))
        if not units:return observation
        dependencies=tuple(row for record in data.get('records',())
                           if (record.get('kind'),record.get('name')) in units
                           for row in record.get('dependencies',{}).get('rows',()))
    if not units:return observation
    if connect is None:
        from .connection import connect_read_only
        connect=connect_read_only
    conn=cursor=None;completed=None;failure=None;cleanup_failed=False
    try:
        credential=credentials(mapping.credential_id)
        if Identifier.parse(credential.username).effective_name!=owner or mapping.metadata_reader:
            return unavailable('ROUTINE_METADATA_SESSION_OWNER_REQUIRED')
        conn=connect(config,credential);cursor=conn.cursor()
        from .queries import READ_ONLY_TRANSACTION
        cursor.execute(READ_ONLY_TRANSACTION)
        version=str(conn.version)
        recorded=snapshot.capabilities.get('oracle_version')
        if recorded and (recorded.state!='KNOWN' or recorded.value!=version):
            raise ValueError('ROUTINE_METADATA_VERSION_CHANGED')
        captured=read_routine_metadata(cursor,units,owner=owner,oracle_version=version,
                                        dependency_rows=dependencies,
                                        deadline=deadline or time.monotonic()+min(config.capture_timeout_seconds,300))
        if captured['identity'].get('state')!='KNOWN' or captured['identity'].get('rows')!=[[owner]]:
            raise ValueError('ROUTINE_METADATA_IDENTITY_MISMATCH')
        augmented,path,raw=attach_routine_metadata(snapshot,captured)
        artifact=SourceArtifact(path,owner,'ROUTINE_METADATA','ROUTINE_METADATA',raw,hashlib.sha256(raw).hexdigest())
        receipt={**observation.receipt,'finished_at':datetime.now(timezone.utc).isoformat(),
                 'routine_metadata':{'status':'CAPTURED','query_count':captured['query_count'],
                                     'unit_count':len(units),'execution_status':'NOT_EXECUTED'}}
        completed=replace(observation,snapshot=augmented,receipt=receipt,
                          artifacts=(*observation.artifacts,artifact))
    except Exception as error:
        failure=safe_error_code(error)
    finally:
        for action in (cursor.close if cursor else None,conn.rollback if conn else None,
                       conn.close if conn else None):
            if action:
                try:action()
                except Exception:cleanup_failed=True
    if cleanup_failed:return unavailable('ROUTINE_METADATA_CLEANUP_FAILED')
    if failure:return unavailable(failure)
    return completed
