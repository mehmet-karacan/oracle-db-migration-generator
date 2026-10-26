"""Project imported metadata with the existing Oracle parser and planner."""
from dataclasses import replace
import hashlib
import re

from ..model.evidence import Evidence
from ..model.identity import Identifier, ObjectIdentity
from ..model.serialization import digest,thaw
from ..model.snapshot import Coverage,KnownValue,SchemaSnapshot,SnapshotObject
from ..oracle.capabilities import describe_capabilities,collation_capabilities
from ..oracle.collector import TargetObservation,_sidecar_artifacts
from ..oracle.ddl_model import project_target_object
from ..oracle.enrichment import enrich_object,index_metadata_groups
from ..oracle.queries import CAPTURE_QUERIES,DDL_TYPES
from ..source.sidecars import merge_sidecars
from .selection import CaptureFilter


def _records(schema,name):
    query=schema.queries.get(name)
    return [dict(zip(query.columns,row)) for row in query.rows] if query and query.rows is not None else None


def observation_from_capture(capture,profile,*,target_id,schemas=None):
    requested=tuple(schemas or capture.schemas)
    if not set(requested).issubset(capture.schemas):raise ValueError('CAPTURE_SCHEMA_NOT_EXPORTED')
    evidence=[];objects=[];capabilities={};artifacts=[];diagnostics=[];complete=True
    for owner in requested:
        schema=capture.schemas[owner];complete &= schema.inventory_complete
        def ev(name,rows,*,kind='TARGET_METADATA',path=None,raw=None):
            key='ev-'+digest([capture.sha256,target_id,owner,name])
            evidence.append(Evidence(key,kind,'TARGET',path,hashlib.sha256(raw).hexdigest() if raw else digest(rows) if rows is not None else None,
                1 if raw else None,len(raw.decode().splitlines()) if raw else None,name,
                'Taşınabilir Oracle metadata kaydı. Canlı bağlantı açılmadan içe aktarıldı.',0 if raw else None,len(raw) if raw else None))
            return key
        scope_id=ev('portable.inventory',schema.queries['inventory_before'].rows,
            kind='ABSENCE_SCOPE' if schema.inventory_complete else 'TARGET_METADATA')
        groups={name:_records(schema,name) for name in CAPTURE_QUERIES}
        # Store only diagnostic codes from Oracle compiler error text.
        if groups['errors'] is not None:
            groups['errors']=[{**r,'text':','.join(re.findall(r'(?:ORA|PLS)-\d+',r['text'] or ''))} for r in groups['errors']]
        group_evidence={name:ev('dictionary.'+name,rows) for name,rows in groups.items()}
        failures=tuple('DICTIONARY_UNAVAILABLE:'+name for name,rows in groups.items() if rows is None)
        diagnostics.extend(failures)
        caps=describe_capabilities(capture.header['database_version'],groups['nls'],group_evidence['nls'])
        params=_records(schema,'collation_parameters');parameter_id=ev('collation_parameters',params)
        caps.update(collation_capabilities(params,parameter_id))
        calendar=_records(schema,'session_calendar');calendar_id=ev('session_calendar',calendar)
        value=calendar[0]['value'] if calendar and len(calendar)==1 and calendar[0]['parameter']=='NLS_CALENDAR' else None
        caps['nls_calendar']=KnownValue('KNOWN' if isinstance(value,str) and value else 'UNKNOWN',
            value if isinstance(value,str) and value else None,(calendar_id,))
        external=_records(schema,'dependency_objects');external_id=ev('dependency_objects',external)
        caps['reference_objects']=KnownValue('KNOWN' if external is not None else 'UNKNOWN',
            [{'owner':row['owner'],'name':row['object_name'],
              'object_type':{'PACKAGE':'PACKAGE_SPEC','TYPE':'TYPE_SPEC'}.get(row['object_type'],row['object_type'].replace(' ','_')),
              'status':row['status']} for row in external] if external is not None else None,(external_id,))
        caps['grantees']=KnownValue('KNOWN' if groups['grantees'] is not None else 'UNKNOWN',
            [r['username'] for r in groups['grantees']]+['PUBLIC'] if groups['grantees'] is not None else None,(group_evidence['grantees'],))
        for kind,names in (('COMMENT',('table_comments','column_comments')),('GRANT',('grants','column_grants'))):
            caps['coverage.'+kind]=KnownValue('KNOWN','COMPLETE' if all(groups[n] is not None for n in names) else 'PARTIAL',tuple(group_evidence[n] for n in names))
        if not capabilities:capabilities=caps
        else:
            for key,value in list(capabilities.items()):
                other=caps[key]
                if (value.state,value.value)!=(other.state,other.value):capabilities[key]=KnownValue('UNKNOWN',None,tuple(sorted(set(value.evidence_ids+other.evidence_ids))))
        row_index=index_metadata_groups(groups)
        mviews={r[1] for r in schema.queries['inventory_before'].rows if r[0]=='MATERIALIZED VIEW'}
        log_tables={r['log_table'] for r in groups['materialized_view_logs'] or []}
        local=[]
        for oracle_kind,name,status,stamp in schema.queries['inventory_before'].rows:
            kind=DDL_TYPES.get(oracle_kind)
            related=capture.selection.include_related and (kind,name) in schema.selected
            if (kind not in profile.object_types and not related) or oracle_kind=='TABLE' and name in mviews|log_tables:continue
            identity=ObjectIdentity(profile.id,Identifier(owner,owner,True),kind,Identifier(name,name,True))
            query=schema.queries.get('ddl:'+oracle_kind+':'+name);raw=None
            if query and query.rows is not None and len(query.rows)==1 and isinstance(query.rows[0][0],str) and query.rows[0][0].strip():raw=query.rows[0][0].encode('utf-8')
            reason=() if raw else (query.error_code if query and query.error_code else 'CAPTURE_DDL_NOT_EXPORTED',)
            path='target-ddl/'+identity.key+'.sql' if raw else None
            eid=ev('portable.ddl.'+identity.key,None,path=path,raw=raw)
            item=SnapshotObject(identity,{'projection':KnownValue('UNKNOWN',None,(eid,)),
                'definition':KnownValue('UNKNOWN',None,(eid,)),'object_status':KnownValue('KNOWN',status,(scope_id,))},
                path,hashlib.sha256(raw).hexdigest() if raw else None,
                Coverage('COMPLETE' if schema.inventory_complete else 'PARTIAL','COMPLETE' if raw else 'PARTIAL','PARTIAL' if failures else 'COMPLETE',reason),(eid,),raw)
            if raw:
                item,extra=project_target_object(item);evidence.extend(extra)
            parents=_records(schema,'trigger_parents') if kind=='TRIGGER' else None
            parent=next((r for r in parents or [] if r['trigger_name']==name),None)
            if parent:
                parent_id=ev('portable.trigger-parent.'+identity.key,parent)
                item=replace(item,properties={**item.properties,'portable.parent':KnownValue('KNOWN',{'owner':parent['table_owner'],'name':parent['table_name']},(parent_id,))})
            local.append(enrich_object(item,groups,group_evidence,row_index=row_index))
        snapshot=SchemaSnapshot('snapshot/1.0',False,'TARGET',profile.id,(owner,),None,target_id,tuple(local),
            Coverage('COMPLETE' if schema.inventory_complete else 'PARTIAL','PARTIAL' if any(o.coverage.ddl!='COMPLETE' for o in local) else 'COMPLETE',
                'PARTIAL' if failures else 'COMPLETE',failures),caps,tuple(evidence),'OBSERVED_STABLE')
        blobs=_sidecar_artifacts(groups,owner)
        snapshot=merge_sidecars(snapshot,blobs)
        snapshot=replace(snapshot,evidence=tuple(replace(e,kind='TARGET_METADATA',query_id='dictionary.sidecars') if e.kind=='SOURCE_SPAN' else e for e in snapshot.evidence),
            objects=tuple(replace(o,ddl_path='target-sidecars/'+o.object_key+'.sql') if o.identity.object_type in {'COMMENT','GRANT'} else o for o in snapshot.objects))
        objects.extend(snapshot.objects);evidence=list(snapshot.evidence);artifacts.extend(blobs)
    eid='ev-'+digest([capture.sha256,target_id,'portable-provenance'])
    evidence.append(Evidence(eid,'TARGET_METADATA','TARGET',None,capture.sha256,None,None,'portable.header','İçe aktarılan dosyanın SHA256 ve toplama kapsamı.'))
    capabilities['portable_capture']=KnownValue('KNOWN',{'sha256':capture.sha256,'captured_at':capture.header['captured_at'],
        'environment':capture.header['environment'],'filter':capture.selection.to_dict(),
        'schemas':{s:{'authority':capture.schemas[s].authority,'roots':[list(v) for v in capture.schemas[s].roots]} for s in requested}},(eid,))
    result=SchemaSnapshot('snapshot/1.0',False,'TARGET',profile.id,requested,None,target_id,tuple(sorted(objects,key=lambda o:o.object_key)),
        Coverage('COMPLETE' if complete else 'PARTIAL','PARTIAL' if any(o.coverage.ddl!='COMPLETE' for o in objects) else 'COMPLETE',
            'PARTIAL' if diagnostics else 'COMPLETE',tuple(sorted(set(diagnostics)))),capabilities,tuple(evidence),'OBSERVED_STABLE')
    return TargetObservation(result,{'target_id':target_id,'status':'CAPTURED','capture_kind':'PORTABLE',
        'captured_at':capture.header['captured_at'],'packet_sha256':capture.sha256,'read_only':True,'execution_status':'NOT_EXECUTED'},tuple(artifacts))


def _data_types(obj):
    value=obj.properties.get('dictionary.columns')
    result={re.sub(r'\([0-9, ]*\)','',str(row.get('data_type',''))).upper() for row in value.value} if value and value.state=='KNOWN' else set()
    if result:return result
    projection=obj.properties.get('projection')
    if projection and projection.state=='KNOWN':
        for col in projection.value.get('columns',{}).values():
            text=col.get('data_type','')
            if isinstance(text,str):result.add(re.sub(r'\([0-9, ]*\)','',text).strip().upper())
    return result


def scope_comparison(source,target,selection=None):
    """Use source datatype membership for both sides; retain target type changes."""
    if selection is None:
        saved=source.capabilities.get('portable_capture')
        selection=thaw(saved.value)['filter'] if saved and saved.state=='KNOWN' else None
    if selection is None:return source,target
    scope=CaptureFilter.from_dict(selection) if isinstance(selection,dict) else selection
    owners=set(scope.schemas or source.schemas)
    def root(obj,*,dtype=True):
        identity=obj.identity;name=identity.name.effective_name
        return (identity.owner.effective_name in owners and identity.object_type in scope.object_types
            and (not scope.object_names or name in scope.object_names)
            and (not scope.exclude_system_generated or not re.match(r'^(BIN\$|ISEQ\$\$_|SYS_IL\d|SYS_IOT_OVER_)',name))
            and (not dtype or not scope.data_types or bool(set(scope.data_types)&_data_types(obj))))
    roots={o.object_key for o in source.objects if root(o)}
    def apply(snapshot):
        selected={o.object_key for o in snapshot.objects if (o.object_key in roots if scope.data_types else root(o,dtype=False))}
        names={(o.identity.owner.effective_name,o.identity.name.effective_name) for o in snapshot.objects if o.object_key in selected and o.identity.object_type in {'TABLE','VIEW','MATERIALIZED_VIEW'}}
        if scope.include_related:
            for o in snapshot.objects:
                if o.identity.parent_key in selected:selected.add(o.object_key);continue
                if o.identity.object_type not in {'INDEX','TRIGGER'}:continue
                parent=o.properties.get('portable.parent')
                if parent and parent.state=='KNOWN' and (parent.value['owner'],parent.value['name']) in names:selected.add(o.object_key)
                metadata=o.properties.get('dictionary.indexes')
                if metadata and metadata.state=='KNOWN' and any((r.get('table_owner'),r.get('table_name')) in names for r in metadata.value):selected.add(o.object_key)
                projection=o.properties.get('projection')
                if projection and projection.state=='KNOWN':
                    table=projection.value.get('target') or projection.value.get('table')
                    if isinstance(table,str):
                        from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
                        from ..parsing.statements import qualified_parts
                        try:
                            parts=qualified_parts(code_tokens(table))
                            parent=tuple(parts) if len(parts)==2 else (o.identity.owner.effective_name,parts[0]) if len(parts)==1 else None
                        except (ValueError,IndexError):parent=None
                        if parent is None and o.identity.object_type=='TRIGGER' and o.raw_ddl:
                            # Some existing trigger projections omit a quoted target.
                            # Read the validated header tokens, preserving quoted dots.
                            tokens=code_tokens(o.raw_ddl.decode('utf-8'))
                            on=next((i for i,t in enumerate(tokens) if t.text.upper()=='ON'),None)
                            if on is not None:
                                start=on+1;end=start+3 if len(tokens)>start+1 and tokens[start+1].text=='.' else start+1
                                try:
                                    parts=qualified_parts(tokens[start:end])
                                    parent=tuple(parts) if len(parts)==2 else (o.identity.owner.effective_name,parts[0])
                                except (ValueError,IndexError):parent=None
                        if parent in names:selected.add(o.object_key)
        objects=tuple(o for o in snapshot.objects if o.object_key in selected)
        coverage=replace(snapshot.completeness,ddl='PARTIAL' if any(o.coverage.ddl!='COMPLETE' for o in objects) else 'COMPLETE')
        return replace(snapshot,schemas=tuple(s for s in snapshot.schemas if s in owners),objects=objects,completeness=coverage)
    return apply(source),apply(target)
