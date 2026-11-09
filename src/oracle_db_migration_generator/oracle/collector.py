"""Schema Compare hedef metadata ve DDL tanımlarını salt okunur toplar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
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
from ..parsing.client import parallel_parser_map
from ..parsing.canonicalize import canonical_sql
from ..parsing.statements import quote_identifier
from ..source.models import SourceArtifact
from ..source.sidecars import merge_sidecars
from .capabilities import describe_capabilities, collation_capabilities
from .connection import connect_read_only
from .enrichment import enrich_object, index_metadata_groups
from .ddl_model import project_target_object
from .preflight import safe_error_code
from .inventory_consistency import inventory_check
from .ddl_reads import ddl_records, reader_count, active_read_seconds, DDLReadError
from .queries import CAPTURE_INVENTORY, CAPTURE_QUERIES, COLLATION_PARAMETERS, DDL_TYPES, DEPENDENT_DDL, IDENTITY, READ_ONLY_TRANSACTION, SAMPLE_DDL


class CaptureError(ValueError):
    """Toplama nedenini ve varsa sınırlı envanter farkını taşır.

    Author: Mehmet KARACAN
    Date: 2026-11-09
    """
    def __init__(self, code, *, inventory=None):
        super().__init__(code)
        self.inventory = inventory


@dataclass(frozen=True, slots=True)
class TargetObservation:
    snapshot: SchemaSnapshot | None
    receipt: dict
    artifacts: tuple = ()


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
    capture_started = time.monotonic()
    timings = {key:0.0 for key in ('dictionary_group_reads', 'reference_metadata', 'ddl_reads',
                                  'grammar_projection', 'dictionary_enrichment', 'sidecar_merge', 'total')}
    try:
        credential = credentials(mapping.credential_id)
        connection = connect(target, credential)
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
        phase_started = time.monotonic()
        groups, failures = _read_groups(cursor,owner)
        timings['dictionary_group_reads'] += time.monotonic()-phase_started
        phase_started = time.monotonic()
        row_index = index_metadata_groups(groups)
        timings['dictionary_enrichment'] += time.monotonic()-phase_started
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
        phase_started = time.monotonic()
        from ..parsing.dependencies import references
        reference_started=time.monotonic()
        source_references=tuple(ref for obj in source.objects for ref in references(obj)) if source else ()
        timings['source_reference_analysis']=time.monotonic()-reference_started
        resolution,resolution_evidence=read_reference_metadata(cursor,source,owner,
            target_id=target.id,deadline=deadline,source_references=source_references)
        capabilities.update(resolution);evidence.append(resolution_evidence)
        if source is not None:
            from .queries import REFERENCE_OBJECT
            requested=sorted({(ref.owner,ref.name) for ref in source_references if ref.owner!=owner})
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
        timings['reference_metadata'] += time.monotonic()-phase_started
        timings['reference_queries']=timings['reference_metadata']-timings['source_reference_analysis']
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
        workers = reader_count(builtin_connector=connect is connect_read_only)
        read_intervals, slow_reads = [], []
        def ddl_items(records):
            for index, raw, reasons, read_started, read_finished in records:
                oracle_kind,name,status,stamp = managed[index]
                if time.monotonic() > deadline:
                    raise CaptureError('TARGET_CAPTURE_TIMEOUT')
                identity = ObjectIdentity(profile.id,Identifier(owner,owner,True),type_map[oracle_kind],Identifier(name,name,True))
                path = 'target-ddl/'+identity.key+'.sql'
                ev_id = 'ev-'+digest([target.id,owner,oracle_kind,name,stamp])
                projection = None
                elapsed = read_finished-read_started
                timings['ddl_reads'] += elapsed
                read_intervals.append((read_started, read_finished))
                slow_reads.append({'object_type':type_map[oracle_kind], 'name':name, 'seconds':elapsed,
                                   'bytes':len(raw) if raw else 0, 'errors':reasons})
                raw_hash = hashlib.sha256(raw).hexdigest() if raw else None
                ddl_evidence=Evidence(ev_id,'TARGET_METADATA','TARGET',path if raw else None,raw_hash,
                                         1 if raw else None,len(raw.decode().splitlines()) if raw else None,
                                         'dbms_metadata.get_ddl','Hedef DDL ve envanter kaydı.',0 if raw else None,len(raw) if raw else None)
                properties = {'projection':KnownValue('UNKNOWN',None,(ev_id,)),
                              'definition':KnownValue('UNKNOWN',None,(ev_id,)),
                              'object_status':KnownValue('KNOWN',status,(scope_id,))}
                item = SnapshotObject(identity,properties,path if raw else None,raw_hash,
                                      Coverage('COMPLETE','PARTIAL' if reasons else 'COMPLETE',
                                               'PARTIAL' if failures else 'COMPLETE',tuple(sorted(set(reasons)))),(ev_id,),raw,projection)
                yield index,item,ddl_evidence,bool(raw and not reasons)
        source_packages = {item.object_key: item for item in source.objects
                           if item.identity.object_type in {'PACKAGE_SPEC', 'PACKAGE_BODY'}} if source else {}
        package_statistics = {'raw_sha_match': 0, 'content_sha_match': 0}
        def project_item(record):
            index,item,ddl_evidence,needs_projection=record
            started=time.monotonic()
            candidate = source_packages.get(item.object_key)
            statistics = {}
            item,context_evidence=(project_target_object(item, source=candidate, statistics=statistics) if candidate is not None
                                  else project_target_object(item)) if needs_projection else (item,())
            elapsed=time.monotonic()-started if needs_projection else 0.0
            return index,item,ddl_evidence,context_evidence,elapsed,statistics
        completed = {}
        projection_started=time.monotonic()
        try:
            with ddl_records(managed, cursor, target=target, mapping=mapping, credential=credential,
                             connect=connect, owner=owner, deadline=deadline, workers=workers) as records:
                with parallel_parser_map(project_item,ddl_items(records),ordered=False) as projected:
                    for record in projected:
                        completed[record[0]] = record[1:]
                        if progress: progress(len(completed),len(managed))
        except DDLReadError as error:
            raise CaptureError(str(error)) from None
        timings['ddl_projection_pipeline_wall']=time.monotonic()-projection_started
        timings['ddl_read_active_wall'] = active_read_seconds(read_intervals)
        slow_projections=[]
        for index in range(len(managed)):
            item,ddl_evidence,context_evidence,elapsed,statistics = completed.pop(index)
            for key, value in statistics.items():
                package_statistics[key] += value
            evidence.append(ddl_evidence)
            evidence.extend(context_evidence)
            timings['grammar_projection'] += elapsed
            if elapsed:
                slow_projections.append({'object_type':item.identity.object_type,
                    'name':item.identity.name.effective_name,'seconds':elapsed,'bytes':len(item.raw_ddl or b''),
                    'diagnostics':item.coverage.diagnostics})
            phase_started = time.monotonic()
            objects.append(enrich_object(item,groups,group_evidence,row_index=row_index))
            timings['dictionary_enrichment'] += time.monotonic()-phase_started
        # A new transaction is essential: the final inventory must not reuse
        # the initial read-only transaction's older consistent read point.
        connection.rollback()
        cursor.execute(READ_ONLY_TRANSACTION)
        cursor.execute(CAPTURE_INVENTORY,{'owner':owner})
        after = cursor.fetchall()
        consistency = inventory_check(before, after)
        if not consistency['same_rows']:
            raise CaptureError('CHANGED_DURING_CAPTURE', inventory=consistency)
        partial = any(obj.coverage.ddl!='COMPLETE' for obj in objects)
        snapshot = SchemaSnapshot('snapshot/1.0',False,'TARGET',profile.id,(mapping.source_schema,),None,target.id,
                                  tuple(sorted(objects,key=lambda obj:obj.object_key)),
                                  Coverage('COMPLETE','PARTIAL' if partial else 'COMPLETE',
                                           'PARTIAL' if failures else 'COMPLETE',tuple('DICTIONARY_UNAVAILABLE:'+name for name in sorted(failures))),
                                  capabilities,tuple(evidence),'OBSERVED_STABLE')
        phase_started = time.monotonic()
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
        timings['sidecar_merge'] += time.monotonic()-phase_started
        return snapshot, {'schema':mapping.source_schema,'status':'CAPTURED','dictionary_errors':failures,'capability_errors':capability_errors,
                          'object_count':len(snapshot.objects),'inventory_count':len(before),'phase_timings_seconds':timings,
                          'inventory_check':consistency,
                          'package_sha_reuse':package_statistics,
                          'ddl_reader_workers':min(workers,len(managed)),
                          'slowest_ddl_reads':sorted(slow_reads,key=lambda item:(-item['seconds'],item['object_type'],item['name']))[:10],
                          'slowest_grammar_projections':sorted(slow_projections,key=lambda item:(-item['seconds'],item['object_type'],item['name']))[:10],
                          'ddl_read_timing_basis':'SUM_OF_WORKER_DURATIONS',
                          'grammar_projection_timing_basis':'SUM_OF_WORKER_DURATIONS'}, artifacts
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
        timings['total'] = time.monotonic()-capture_started
        if cleanup_failed:
            raise CaptureError('TARGET_CAPTURE_CLEANUP_FAILED')


def collect_target(config, credentials, profile, *, connect=connect_read_only, progress=None, timeout_seconds=None, source=None):
    started = datetime.now(timezone.utc).isoformat()
    deadline = time.monotonic()+(config.capture_timeout_seconds if timeout_seconds is None else timeout_seconds)
    snapshots, receipts, artifacts, failed = [], [], [], False
    for mapping in config.schema_mappings:
        changes = []
        for attempt in range(2):
            try:
                snapshot, receipt, blobs = _capture_schema(config,mapping,credentials,profile,connect,deadline,progress,source)
                receipt['capture_attempts'] = attempt+1
                if changes: receipt['previous_inventory_changes'] = changes
                snapshots.append(snapshot); receipts.append(receipt)
                artifacts.extend(blobs)
                break
            except Exception as error:
                changed = isinstance(error,CaptureError) and str(error)=='CHANGED_DURING_CAPTURE'
                if changed and error.inventory is not None:
                    changes.append({'attempt':attempt+1,'inventory_check':error.inventory})
                if changed and attempt==0:
                    continue
                code = str(error) if isinstance(error,(CaptureError,DDLReadError)) else safe_error_code(error)
                failure = {'schema':mapping.source_schema,'status':'INCONSISTENT' if changed else 'ERROR','error_code':code,
                           'capture_attempts':attempt+1}
                if changes:
                    failure['inventory_check'] = changes[-1]['inventory_check']
                    failure['inventory_changes'] = changes
                receipts.append(failure)
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
    observation=TargetObservation(snapshot,receipt,tuple(artifacts))
    if source is not None and snapshot is not None:
        from .routine_metadata import complete_routine_observation
        observation=complete_routine_observation(observation,config,credentials,source=source,
                                                  connect=connect,deadline=deadline)
    return observation
