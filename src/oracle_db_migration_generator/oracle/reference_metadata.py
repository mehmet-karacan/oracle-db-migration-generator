"""Metadata-only name resolution. No SQL from source text is executed."""
import time

from ..model.evidence import Evidence
from ..model.serialization import digest
from ..model.snapshot import KnownValue
from ..parsing.dependencies import references
from .queries import REFERENCE_OBJECT,REFERENCE_SYNONYM,SESSION_CALENDAR
from .preflight import safe_error_code

SHARED_NAMESPACE=frozenset({'TABLE','VIEW','MATERIALIZED_VIEW','SEQUENCE','PROCEDURE','FUNCTION','PACKAGE_SPEC','TYPE_SPEC','SYNONYM'})


def _kind(kind):
    return {'PACKAGE':'PACKAGE_SPEC','TYPE':'TYPE_SPEC'}.get(kind,kind.replace(' ','_'))


def read_reference_metadata(cursor,source,owner,existing=(),*,target_id,deadline=None):
    records=[];errors=[];cache={}
    def query(sql,binds):
        key=(sql,tuple(sorted(binds.items())))
        if key not in cache:
            if deadline is not None and time.monotonic()>=deadline:raise TimeoutError('METADATA_DEADLINE')
            cursor.execute(sql,binds);cache[key]=cursor.fetchall()
        return cache[key]
    def resolve(request_owner,name,unqualified):
        current_owner,current_name=request_owner,name;chain=[];visited=set()
        for _ in range(5):
            if (current_owner,current_name) in visited:raise ValueError('SYNONYM_CYCLE')
            visited.add((current_owner,current_name))
            rows=query(REFERENCE_OBJECT,{'owner':current_owner,'name':current_name})
            concrete=[{'owner':current_owner,'name':current_name,'object_type':_kind(kind),'status':status}
                      for kind,status in rows if _kind(kind) in SHARED_NAMESPACE-{'SYNONYM'}]
            if concrete:return concrete,chain
            synonyms=query(REFERENCE_SYNONYM,{'owner':current_owner,'name':current_name})
            if not concrete and not any(kind=='SYNONYM' for kind,status in rows) and not synonyms and not chain and unqualified:
                synonyms=query(REFERENCE_SYNONYM,{'owner':'PUBLIC','name':current_name})
                synonym_owner='PUBLIC'
            else:synonym_owner=current_owner
            if not synonyms:return [],chain
            if len(synonyms)!=1:raise ValueError('SYNONYM_AMBIGUOUS')
            next_owner,next_name,link=synonyms[0]
            if link:raise ValueError('SYNONYM_REMOTE_UNSUPPORTED')
            if not next_owner or not next_name:raise ValueError('SYNONYM_TARGET_UNKNOWN')
            chain.append({'owner':synonym_owner,'name':current_name,'target_owner':next_owner,'target_name':next_name})
            current_owner,current_name=next_owner,next_name
        raise ValueError('SYNONYM_CHAIN_LIMIT')
    known={(o.identity.owner.effective_name,o.identity.name.effective_name) for o in existing if o.identity.object_type in SHARED_NAMESPACE-{'SYNONYM'}}
    desired={(o.identity.owner.effective_name,o.identity.name.effective_name) for o in source.objects if o.identity.object_type in SHARED_NAMESPACE} if source else set()
    synonyms={(o.identity.owner.effective_name,o.identity.name.effective_name) for o in existing if o.identity.object_type=='SYNONYM'}
    requested=sorted({(r.owner,r.name,r.unqualified) for obj in source.objects for r in references(obj)
                      if r.owner!=owner or (r.owner,r.name) in synonyms or r.unqualified and (r.owner,r.name) not in known|desired}) if source else []
    for request_owner,name,unqualified in requested:
        record={'requested_owner':request_owner,'requested_name':name,'unqualified':unqualified,'state':'KNOWN','objects':[],'chain':[]}
        try:
            objects,chain=resolve(request_owner,name,unqualified)
            record.update(objects=objects,chain=chain,state='KNOWN' if objects else 'MISSING')
        except Exception as error:
            record['state']='UNKNOWN';errors.append(safe_error_code(error))
        records.append(record)
    calendar=None
    try:
        rows=query(SESSION_CALENDAR,{})
        if len(rows)==1 and rows[0][0]=='NLS_CALENDAR':calendar=rows[0][1]
    except Exception as error:errors.append(safe_error_code(error))
    ev_id='ev-'+digest([target_id,owner,'reference-resolution',records,calendar,errors])
    evidence=Evidence(ev_id,'TARGET_METADATA','TARGET',None,digest([records,calendar,errors]),None,None,
                      'all_objects.all_synonyms.nls_session_parameters','Salt okunur ad çözümleme ve NLS calendar gözlemi.')
    return {'resolved_references':KnownValue('KNOWN',records,(ev_id,)),
            'nls_calendar':KnownValue('KNOWN' if calendar is not None else 'UNKNOWN',calendar,(ev_id,))},evidence
