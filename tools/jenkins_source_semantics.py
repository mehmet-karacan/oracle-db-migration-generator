"""Read-only source column correspondence for omissions in immutable Git DDL."""
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import hashlib

from oracle_db_migration_generator.compare.projection_adapter import table_columns,restore_projection
from oracle_db_migration_generator.model.evidence import Evidence
from oracle_db_migration_generator.model.serialization import canonical_bytes,digest,thaw
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.oracle.connection import connect_read_only
from oracle_db_migration_generator.oracle.queries import CAPTURE_INVENTORY,CAPTURE_QUERIES,IDENTITY,READ_ONLY_TRANSACTION


def capture_source_metadata(target,credentials,*,owner='INNOVA_ODI',connect=connect_read_only):
    if owner not in {'INNOVA_ODI','TTBP'}:raise ValueError('SOURCE_METADATA_OWNER_NOT_ALLOWED')
    started=datetime.now(timezone.utc).isoformat();conn=cursor=None
    try:
        conn=connect(target,credentials);cursor=conn.cursor()
        cursor.execute(READ_ONLY_TRANSACTION);cursor.execute(IDENTITY)
        if cursor.fetchone()!=(owner,):raise ValueError('SOURCE_METADATA_OWNER_MISMATCH')
        cursor.execute(CAPTURE_INVENTORY,{'owner':owner});before=cursor.fetchall()
        names,query=CAPTURE_QUERIES['columns'];cursor.execute(query,{'owner':owner})
        columns=[dict(zip(names,[v.read() if hasattr(v,'read') else v for v in row])) for row in cursor.fetchall()]
        conn.rollback();cursor.execute(READ_ONLY_TRANSACTION)
        cursor.execute(CAPTURE_INVENTORY,{'owner':owner});after=cursor.fetchall()
        return {'status':'CAPTURED' if before==after else 'INCONSISTENT','owner':owner,
                'read_only':True,'ddl_executed':False,'business_data_read':False,
                'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),
                'inventory_before':before,'inventory_after':after,'columns':columns}
    finally:
        try:
            if cursor is not None:cursor.close()
        finally:
            if conn is not None:
                try:conn.rollback()
                finally:conn.close()


def reconcile_source(source,capture,root):
    if (capture.get('status')!='CAPTURED' or capture.get('read_only') is not True
        or capture.get('ddl_executed') is not False or capture.get('business_data_read') is not False
        or capture.get('owner') not in source.schemas
        or capture.get('inventory_before')!=capture.get('inventory_after')):
        raise ValueError('SOURCE_METADATA_UNTRUSTED')
    rows=defaultdict(list)
    for row in capture['columns']:
        if row.get('hidden_column')=='YES' and row.get('user_generated')=='NO':continue
        rows[row['table_name']].append(row)
    objects=[];accepted=[];rejected=[]
    for obj in source.objects:
        if obj.identity.object_type!='TABLE' or obj.identity.owner.effective_name!=capture['owner']:
            objects.append(obj);continue
        original=table_columns(obj,source)
        current=table_columns(replace(obj,properties={**obj.properties,
            'dictionary.columns':KnownValue('KNOWN',rows[obj.identity.name.effective_name],obj.evidence_ids)}),source)
        reason=None
        names=[row['column_name'] for row in rows[obj.identity.name.effective_name]]
        if not original or set(original)!=set(names) or len(names)!=len(set(names)) or obj.coverage.ddl!='COMPLETE':reason='SOURCE_COLUMN_SET_DRIFT'
        if not reason:
            for name,fields in original.items():
                for field,value in fields.items():
                    if field in {'length_semantics','collation'} and (value.state=='UNKNOWN' or value.value is None):continue
                    observed=current[name][field]
                    if value.state!='KNOWN' or observed.state!='KNOWN' or value.value!=observed.value:
                        reason='SOURCE_KNOWN_COLUMN_FACT_DRIFT';break
                if reason:break
        if reason:
            rejected.append({'object_key':obj.object_key,'reason_code':reason});objects.append(obj);continue
        projection=thaw(restore_projection(obj).properties);resolved={}
        for name,fields in original.items():
            detail=projection['columns'][name];changes={}
            if fields['length_semantics'].state=='UNKNOWN' and current[name]['length_semantics'].value in {'BYTE','CHAR'}:
                changes['length_semantics']=current[name]['length_semantics'].value
            if fields['collation'].value is None and isinstance(current[name]['collation'].value,str):
                changes['collation']=current[name]['collation'].value
            detail.update(changes)
            if changes:resolved[name]=changes
        accepted.append({'object_key':obj.object_key,'ddl_sha256':obj.ddl_sha256,'known_fields_sha256':digest(original),'resolved':resolved})
        objects.append(replace(obj,properties={**obj.properties,'projection':KnownValue('KNOWN',projection,obj.properties['projection'].evidence_ids)},projection=None))
    proof={'owner':capture['owner'],'source_commit':source.source_commit,'original_semantic_digest':source.semantic_digest,
           'matched_tables':len(accepted),'rejected_tables':rejected,'tables':accepted,
           'basis':'Git DDL unchanged; only omitted semantics filled after all known column facts match. Current metadata is not a historical SCN guarantee.'}
    from oracle_db_migration_generator.artifacts.layout import component
    evidence_path='metadata/source-column-semantics'+('.'+component(capture['owner']) if len(source.schemas)>1 else '')+'.json'
    raw=canonical_bytes(proof)+b'\n';path=root/evidence_path
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    ev=Evidence('ev-'+digest(['source-correspondence',source.source_commit,digest(proof)]),'SOURCE_SPAN','SOURCE',
                evidence_path,hashlib.sha256(raw).hexdigest(),1,1,
                'SOURCE_COLUMNS_KNOWN_FACTS_MATCH','Kaynak kolon metadata gözlemi Git tanımındaki bilinen alanlarla eşleşti; yalnız eksik etkin semantik tamamlandı.',0,len(raw))
    accepted_keys={item['object_key'] for item in accepted}
    objects=[replace(obj,properties={**obj.properties,'projection':KnownValue('KNOWN',thaw(obj.properties['projection'].value),
                obj.properties['projection'].evidence_ids+(ev.id,))},evidence_ids=obj.evidence_ids+(ev.id,)) if obj.object_key in accepted_keys else obj for obj in objects]
    return replace(source,objects=tuple(objects),evidence=source.evidence+(ev,)),proof
