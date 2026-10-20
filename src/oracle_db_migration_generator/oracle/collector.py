"""Full target metadata capture through a closed SELECT allowlist."""
import hashlib
import re
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from ..model.evidence import Evidence
from ..model.identity import Identifier, ObjectIdentity
from ..model.serialization import digest, thaw
from ..model.snapshot import Coverage, KnownValue, SchemaSnapshot, SnapshotObject
from ..parsing.adapter import parse_ddl
from ..parsing.canonicalize import canonical_sql
from ..parsing.statements import quote_identifier
from ..source.models import SourceArtifact
from ..source.sidecars import merge_sidecars
from .capabilities import describe_capabilities, collation_capabilities
from .connection import connect_read_only
from .enrichment import enrich_object
from .ddl_model import project_target_object
from .preflight import safe_error_code
from .queries import CAPTURE_INVENTORY, CAPTURE_QUERIES, COLLATION_PARAMETERS, DDL_TYPES, DEPENDENT_DDL, IDENTITY, READ_ONLY_TRANSACTION, SAMPLE_DDL


class CaptureError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TargetObservation:
    snapshot: SchemaSnapshot | None
    receipt: dict


def get_dependent_ddl(cursor, ddl_type, name, owner, *, inventory_complete, expected_count=None):
    if ddl_type not in {'COMMENT', 'OBJECT_GRANT'}:
        raise CaptureError('DEPENDENT_DDL_TYPE_NOT_ALLOWED')
    try:
        cursor.execute(DEPENDENT_DDL, {'ddl_type':ddl_type,'name':name,'owner':owner})
        row = cursor.fetchone()
    except Exception as error:
        if safe_error_code(error) == 'ORA-31608' and inventory_complete and expected_count == 0:
            return None
        raise
    if not row or row[0] is None:
        raise CaptureError('DEPENDENT_DDL_UNEXPECTED_EMPTY')
    return row[0].read() if hasattr(row[0],'read') else str(row[0])


def _read_groups(cursor, owner):
    groups, failures = {}, {}
    for group, (columns, query) in CAPTURE_QUERIES.items():
        try:
            cursor.execute(query, {'owner':owner} if ':owner' in query else None)
            records = []
            for values in cursor.fetchall():
                if len(values) != len(columns):
                    raise CaptureError('DICTIONARY_ROW_SHAPE_MISMATCH')
                row = {key:(value.read() if hasattr(value,'read') else value) for key,value in zip(columns,values)}
                if group == 'errors':
                    row['text'] = ','.join(re.findall(r'(?:ORA|PLS)-\d+', str(row['text'])))
                records.append(row)
            groups[group] = records
        except Exception as error:
            groups[group] = None
            failures[group] = safe_error_code(error)
    return groups, failures


def _sidecar_artifacts(groups, owner, *, excluded=None):
    excluded=excluded if excluded is not None else []
    def skip(group,row):
        code=None
        if row['table_name'].startswith('BIN$'):
            code='INTERNAL_RECYCLEBIN_OBJECT'
        elif group in {'grants','column_grants'} and (row.get('object_type')=='USER' or row.get('privilege')=='INHERIT PRIVILEGES'):
            code='USER_SECURITY_GRANT_OUT_OF_SCOPE'
        if code:
            excluded.append({'owner':owner,'group':group,'object_name':row['table_name'],'reason_code':code})
        return code is not None
    statements = {'COMMENT':[], 'GRANT':[]}
    for row in groups.get('table_comments') or []:
        if skip('table_comments',row): continue
        target = quote_identifier(owner)+'.'+quote_identifier(row['table_name'])
        statements['COMMENT'].append(f"COMMENT ON TABLE {target} IS '"+row['comments'].replace("'","''")+"';")
    for row in groups.get('column_comments') or []:
        if skip('column_comments',row): continue
        target = '.'.join(quote_identifier(value) for value in (owner,row['table_name'],row['column_name']))
        statements['COMMENT'].append(f"COMMENT ON COLUMN {target} IS '"+row['comments'].replace("'","''")+"';")
    for group in ('grants','column_grants'):
        for row in groups.get(group) or []:
            if skip(group,row): continue
            target = quote_identifier(owner)+'.'+quote_identifier(row['table_name'])
            privilege = row['privilege']
            if group == 'column_grants':
                privilege += ' ('+quote_identifier(row['column_name'])+')'
            statement = f'GRANT {privilege} ON {target} TO {quote_identifier(row["grantee"])}'
            statements['GRANT'].append(statement + (' WITH GRANT OPTION;' if row['grantable']=='YES' else ';'))
    artifacts = []
    for kind, rows in statements.items():
        if rows:
            raw = ('\n'.join(rows)+'\n').encode()
            artifacts.append(SourceArtifact('target-metadata/'+kind.lower()+'.sql',owner,kind,kind,raw,hashlib.sha256(raw).hexdigest()))
    return tuple(artifacts)


def _capture_schema(target, mapping, credentials, profile, connect, deadline, progress, source=None):
    owner = Identifier.parse(mapping.target_schema).effective_name
    connection = cursor = None
    try:
        connection = connect(target, credentials(mapping.credential_id))
        cursor = connection.cursor()
        cursor.execute(READ_ONLY_TRANSACTION)
        reader_proof=None
        if mapping.metadata_reader is not None:
            from .catalog_reader import authorize_catalog_reader,CatalogCursor
            try:
                reader_proof=authorize_catalog_reader(cursor,Identifier.parse(mapping.metadata_reader).effective_name,owner)
            except ValueError as error:
                code=str(error)
                raise CaptureError(code if re.fullmatch(r'CATALOG_[A-Z_]+',code) else 'CATALOG_AUTHORIZATION_FAILED') from None
            cursor=CatalogCursor(cursor)
        else:
            cursor.execute(IDENTITY)
            if cursor.fetchone() != (owner,):
                raise CaptureError('SESSION_OWNER_MISMATCH')
        cursor.execute(CAPTURE_INVENTORY, {'owner':owner})
        before = cursor.fetchall()
        groups, failures = _read_groups(cursor,owner)
        objects, evidence = [], []
        scope_id = 'ev-'+digest([target.id,owner,'inventory',before])
        evidence.append(Evidence(scope_id,'ABSENCE_SCOPE','TARGET',None,digest(before),None,None,
                                 'dba_objects' if reader_proof else 'all_objects',
                                 'Yetkisi doğrulanmış katalogdan şema envanteri.' if reader_proof else 'Kendi oturum kullanıcısının tam nesne envanteri.'))
        group_evidence = {}
        for group, rows in groups.items():
            ev_id = 'ev-'+digest([target.id,owner,group,rows,failures.get(group)])
            group_evidence[group] = ev_id
            evidence.append(Evidence(ev_id,'TARGET_METADATA','TARGET',None,digest(rows) if rows is not None else None,
                                     None,None,'dictionary.'+group,'Dictionary alan grubu: '+group+'.'))
        capabilities = describe_capabilities(connection.version,groups['nls'],group_evidence['nls'])
        if reader_proof:
            reader_id='ev-'+digest([target.id,owner,'catalog-reader',reader_proof])
            evidence.append(Evidence(reader_id,'TARGET_METADATA','TARGET',None,digest(reader_proof),None,None,
                'session_roles.dba_objects','Mevcut katalog okuma yetkisi ve açık metadata okuyucusu doğrulandı.'))
            capabilities['metadata_access']=KnownValue('KNOWN',reader_proof,(reader_id,))
        parameter_rows=None;capability_errors={}
        try:
            cursor.execute(COLLATION_PARAMETERS)
            parameter_rows=[{'name':name,'value':value} for name,value in cursor.fetchall()]
        except Exception as error:
            capability_errors['collation_parameters']=safe_error_code(error)
        parameter_id='ev-'+digest([target.id,owner,'collation_parameters',parameter_rows,capability_errors])
        evidence.append(Evidence(parameter_id,'TARGET_METADATA','TARGET',None,
                                 digest(parameter_rows) if parameter_rows is not None else None,
                                 None,None,'v$parameter.collation','COLLATE desteği için salt okunur initialization parameter gözlemi.'))
        capabilities.update(collation_capabilities(parameter_rows,parameter_id))
        from .reference_metadata import read_reference_metadata
        resolution,resolution_evidence=read_reference_metadata(cursor,source,owner,
            target_id=target.id,deadline=deadline)
        capabilities.update(resolution);evidence.append(resolution_evidence)
        if source is not None:
            from ..parsing.dependencies import references
            from .queries import REFERENCE_OBJECT
            requested=sorted({(ref.owner,ref.name) for obj in source.objects for ref in references(obj) if ref.owner!=owner})
            external=[];external_failed=False
            for reference_owner,reference_name in requested:
                try:
                    cursor.execute(REFERENCE_OBJECT,{'owner':reference_owner,'name':reference_name})
                    external.extend({'owner':reference_owner,'name':reference_name,
                                     'object_type':{'PACKAGE':'PACKAGE_SPEC','TYPE':'TYPE_SPEC'}.get(kind,kind.replace(' ','_')),
                                     'status':status} for kind,status in cursor.fetchall())
                except Exception:
                    external_failed=True
            ref_id='ev-'+digest([target.id,owner,'references',requested,external,external_failed])
            evidence.append(Evidence(ref_id,'TARGET_METADATA','TARGET',None,digest(external),None,None,'all_objects.references','İstenen harici bağımlılıkların görünürlük ve durum metadata kaydı.'))
            capabilities['reference_objects']=KnownValue('UNKNOWN' if external_failed else 'KNOWN',None if external_failed else external,(ref_id,))
        capabilities['grantees'] = KnownValue('KNOWN' if groups['grantees'] is not None else 'UNKNOWN',
                                              [r['username'] for r in groups['grantees']]+['PUBLIC'] if groups['grantees'] is not None else None,
                                              (group_evidence['grantees'],))
        for kind, needed in [('COMMENT',('table_comments','column_comments')),('GRANT',('grants','column_grants'))]:
            complete = all(groups[name] is not None for name in needed)
            capabilities['coverage.'+kind] = KnownValue('KNOWN','COMPLETE' if complete else 'PARTIAL',
                                                        tuple(group_evidence[name] for name in needed))
        type_map = {key:('PACKAGE_SPEC' if key=='PACKAGE' else 'TYPE_SPEC' if key=='TYPE' else key.replace(' ','_')) for key in DDL_TYPES}
        managed = [row for row in before if row[0] in type_map and type_map[row[0]] in profile.object_types
                   and not re.match(r'^(?:BIN\$|ISEQ\$\$_|SYS_IL\d|SYS_IOT_OVER_)',row[1])]
        # MView storage tables belong to the view/log rather than independent heap tables.
        mviews = {row[1] for row in before if row[0]=='MATERIALIZED VIEW'}
        log_tables = {row['log_table'] for row in groups['materialized_view_logs'] or []}
        managed = [row for row in managed if not (row[0]=='TABLE' and row[1] in mviews | log_tables)]
        for index, (oracle_kind,name,status,stamp) in enumerate(managed):
            if time.monotonic() > deadline:
                raise CaptureError('TARGET_CAPTURE_TIMEOUT')
            if progress:
                progress(index,len(managed))
            identity = ObjectIdentity(profile.id,Identifier(owner,owner,True),type_map[oracle_kind],Identifier(name,name,True))
            path = 'target-ddl/'+identity.key+'.sql'
            ev_id = 'ev-'+digest([target.id,owner,oracle_kind,name,stamp])
            reasons, raw, projection = [], None, None
            try:
                cursor.execute(SAMPLE_DDL,{'ddl_type':DDL_TYPES[oracle_kind],'name':name,'owner':owner})
                row = cursor.fetchone()
                if not row or row[0] is None:
                    raise CaptureError('GET_DDL_RETURNED_EMPTY')
                text = row[0].read() if hasattr(row[0],'read') else str(row[0])
                if not text.strip(): raise CaptureError('GET_DDL_RETURNED_EMPTY')
                raw = text.encode('utf-8')
            except Exception as error:
                reasons.append(safe_error_code(error))
            raw_hash = hashlib.sha256(raw).hexdigest() if raw else None
            evidence.append(Evidence(ev_id,'TARGET_METADATA','TARGET',path if raw else None,raw_hash,
                                     1 if raw else None,len(raw.decode().splitlines()) if raw else None,
                                     'dbms_metadata.get_ddl','Hedef DDL ve envanter kaydı.',0 if raw else None,len(raw) if raw else None))
            properties = {'projection':KnownValue('UNKNOWN',None,(ev_id,)),
                          'definition':KnownValue('UNKNOWN',None,(ev_id,)),
                          'object_status':KnownValue('KNOWN',status,(scope_id,))}
            item = SnapshotObject(identity,properties,path if raw else None,raw_hash,
                                  Coverage('COMPLETE','PARTIAL' if reasons else 'COMPLETE',
                                           'PARTIAL' if failures else 'COMPLETE',tuple(sorted(set(reasons)))),(ev_id,),raw,projection)
            if raw and not reasons:
                item,context_evidence=project_target_object(item)
                evidence.extend(context_evidence)
            objects.append(enrich_object(item,groups,group_evidence))
        # A new transaction is essential: the final inventory must not reuse
        # the initial read-only transaction's older consistent read point.
        connection.rollback()
        cursor.execute(READ_ONLY_TRANSACTION)
        cursor.execute(CAPTURE_INVENTORY,{'owner':owner})
        after = cursor.fetchall()
        if before != after:
            raise CaptureError('CHANGED_DURING_CAPTURE')
        partial = any(obj.coverage.ddl!='COMPLETE' for obj in objects)
        snapshot = SchemaSnapshot('snapshot/1.0',False,'TARGET',profile.id,(mapping.source_schema,),None,target.id,
                                  tuple(sorted(objects,key=lambda obj:obj.object_key)),
                                  Coverage('COMPLETE','PARTIAL' if partial else 'COMPLETE',
                                           'PARTIAL' if failures else 'COMPLETE',tuple('DICTIONARY_UNAVAILABLE:'+name for name in sorted(failures))),
                                  capabilities,tuple(evidence),'OBSERVED_STABLE')
        excluded=[]
        artifacts=_sidecar_artifacts(groups,owner,excluded=excluded)
        if excluded:
            capabilities=dict(snapshot.capabilities)
            capabilities['excluded_sidecars']=KnownValue('KNOWN',excluded,
                tuple(sorted({group_evidence[item['group']] for item in excluded})))
            snapshot=replace(snapshot,capabilities=capabilities)
        snapshot = merge_sidecars(snapshot,artifacts)
        snapshot = replace(snapshot,evidence=tuple(replace(ev,kind='TARGET_METADATA',query_id='dictionary.sidecars')
                                                   if ev.kind=='SOURCE_SPAN' else ev for ev in snapshot.evidence),
                           objects=tuple(replace(obj,ddl_path='target-sidecars/'+obj.object_key+'.sql')
                                         if obj.identity.object_type in {'COMMENT','GRANT'} else obj for obj in snapshot.objects))
        return snapshot, {'schema':mapping.source_schema,'status':'CAPTURED','dictionary_errors':failures,'capability_errors':capability_errors,
                          'object_count':len(snapshot.objects),'inventory_count':len(before)}
    finally:
        # Close all handles, including after permission errors or retry.
        cleanup_failed = False
        for action in (cursor.close if cursor else None,connection.rollback if connection else None,
                       connection.close if connection else None):
            if action:
                try:
                    action()
                except Exception:
                    cleanup_failed = True
        if cleanup_failed:
            raise CaptureError('TARGET_CAPTURE_CLEANUP_FAILED')


def collect_target(config, credentials, profile, *, connect=connect_read_only, progress=None, timeout_seconds=None, source=None):
    started = datetime.now(timezone.utc).isoformat()
    deadline = time.monotonic()+(config.capture_timeout_seconds if timeout_seconds is None else timeout_seconds)
    snapshots, receipts, failed = [], [], False
    for mapping in config.schema_mappings:
        for attempt in range(2):
            try:
                snapshot, receipt = _capture_schema(config,mapping,credentials,profile,connect,deadline,progress,source)
                snapshots.append(snapshot); receipts.append(receipt)
                break
            except Exception as error:
                changed = isinstance(error,CaptureError) and str(error)=='CHANGED_DURING_CAPTURE'
                if changed and attempt==0:
                    continue
                code = str(error) if isinstance(error,CaptureError) else safe_error_code(error)
                receipts.append({'schema':mapping.source_schema,'status':'INCONSISTENT' if changed else 'ERROR','error_code':code})
                failed = True
                break
    snapshot = None
    if not failed and snapshots:
        first = snapshots[0]
        capabilities = dict(first.capabilities)
        # Version/charset values must agree across isolated schema credentials.
        for other in snapshots[1:]:
            for key,value in capabilities.items():
                if key in other.capabilities and (value.state,value.value)!=(other.capabilities[key].state,other.capabilities[key].value):
                    capabilities[key] = KnownValue('UNKNOWN',None,tuple(sorted(set(value.evidence_ids+other.capabilities[key].evidence_ids))))
        snapshot = replace(first,schemas=tuple(schema for item in snapshots for schema in item.schemas),
                           objects=tuple(obj for item in snapshots for obj in item.objects),
                           evidence=tuple(ev for item in snapshots for ev in item.evidence),capabilities=capabilities,
                           completeness=Coverage('COMPLETE', 'PARTIAL' if any(item.completeness.ddl!='COMPLETE' for item in snapshots) else 'COMPLETE',
                                                 'PARTIAL' if any(item.completeness.dictionary!='COMPLETE' for item in snapshots) else 'COMPLETE',
                                                 tuple(sorted({code for item in snapshots for code in item.completeness.diagnostics}))))
    status = 'INCONSISTENT' if any(r['status']=='INCONSISTENT' for r in receipts) else 'ERROR' if failed else 'CAPTURED'
    receipt = {'target_id':config.id,'status':status,'started_at':started,
               'finished_at':datetime.now(timezone.utc).isoformat(),'schemas':receipts,
               'difference_count':None,'execution_status':'NOT_EXECUTED','read_only':True}
    return TargetObservation(snapshot,receipt)
