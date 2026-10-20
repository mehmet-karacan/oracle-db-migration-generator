"""Re-interpret an immutable metadata capture offline, without Oracle I/O."""
from dataclasses import replace

from ..model.evidence import Evidence
from ..model.serialization import digest,thaw
from ..model.snapshot import KnownValue
from ..source.sidecars import merge_sidecars
from .collector import _sidecar_artifacts
from .ddl_model import project_target_object

GROUPS=('table_comments','column_comments','grants','column_grants')


def _groups(snapshot,owner):
    rows={group:{} for group in GROUPS}
    for obj in snapshot.objects:
        if obj.identity.owner.effective_name!=owner: continue
        for group in GROUPS:
            value=obj.properties.get('dictionary.'+group)
            if value and value.state=='KNOWN':
                for row in value.value:
                    record=thaw(row);rows[group][digest(record)]=record
        # Preserve sidecars whose parent was excluded from the original object
        # inventory, so the exclusion policy has an auditable input too.
        if obj.identity.object_type=='GRANT' and obj.identity.parent_key is None:
            def known(key):
                value=obj.properties.get(key)
                return value.value if value and value.state=='KNOWN' else None
            row={'table_name':known('target'),'grantee':known('grantee'),'privilege':known('privilege'),
                 'grantable':'YES' if known('grantable') else 'NO'}
            if all(row[key] is not None for key in ('table_name','grantee','privilege')):
                rows['grants'][digest(row)]=row
    return {group:[entries[key] for key in sorted(entries)] for group,entries in rows.items()}


def reparse_target(snapshot,*,progress=None):
    if snapshot.side!='TARGET': raise ValueError('TARGET_SNAPSHOT_REQUIRED')
    objects=[];evidence=list(snapshot.evidence)
    candidates=[obj for obj in snapshot.objects if obj.identity.object_type not in {'COMMENT','GRANT'}]
    for index,obj in enumerate(candidates):
        if progress: progress(index,len(candidates))
        updated,context_evidence=project_target_object(obj)
        objects.append(updated)
        evidence.extend(context_evidence)
    # Capture consistency and dictionary facts remain those of the original
    # observation. Re-parsing does not imply a fresh or new Oracle snapshot.
    ev_id='ev-'+digest(['reparsed-target',snapshot.semantic_digest])
    evidence.append(Evidence(ev_id,'POLICY','POLICY',None,snapshot.semantic_digest,None,None,None,
                             'Kaydedilmiş hedef metadata snapshot yeniden yorumlandı; Oracle bağlantısı açılmadı.'))
    capabilities=dict(snapshot.capabilities)
    capabilities['reparsed_from_snapshot']=KnownValue('KNOWN',snapshot.semantic_digest,(ev_id,))
    capabilities.pop('sidecar_diagnostics',None)
    diagnostics=tuple(code for code in snapshot.completeness.diagnostics if code!='SOURCE_SIDECAR_UNRESOLVED')
    result=replace(snapshot,objects=tuple(objects),evidence=tuple(evidence),capabilities=capabilities,
                   completeness=replace(snapshot.completeness,ddl='PARTIAL' if any(obj.coverage.ddl!='COMPLETE' for obj in objects) else 'COMPLETE',diagnostics=diagnostics))
    excluded=[]
    for owner in snapshot.schemas:
        artifacts=_sidecar_artifacts(_groups(snapshot,owner),owner,excluded=excluded)
        result=merge_sidecars(result,artifacts)
    # Register explicit out-of-scope records without converting them into
    # fictitious missing TABLE/VIEW parents.
    if excluded:
        caps=dict(result.capabilities);caps['excluded_sidecars']=KnownValue('KNOWN',excluded,(ev_id,))
        result=replace(result,capabilities=caps)
    excluded_names={(item['owner'],item['object_name']) for item in excluded}
    keys={obj.object_key for obj in result.objects}
    retained=[]
    for obj in snapshot.objects:
        if obj.identity.object_type not in {'COMMENT','GRANT'} or obj.object_key in keys: continue
        target=obj.properties.get('target')
        if target and target.state=='KNOWN' and (obj.identity.owner.effective_name,target.value) in excluded_names: continue
        # Absence of reconstructable dictionary rows is not proof that the
        # original sidecar ceased to exist. Preserve unknown/legacy records.
        retained.append(obj)
    if retained:
        result=replace(result,objects=result.objects+tuple(retained))
    result=replace(result,completeness=replace(result.completeness,
        ddl='PARTIAL' if any(obj.coverage.ddl!='COMPLETE' for obj in result.objects) or result.completeness.diagnostics else 'COMPLETE'))
    registry={}
    for item in result.evidence:
        if item.kind=='SOURCE_SPAN' and item.side=='TARGET':
            item=replace(item,kind='TARGET_METADATA',query_id='dictionary.sidecars')
        if item.id in registry and registry[item.id]!=item: raise ValueError('EVIDENCE_ID_CONFLICT')
        registry[item.id]=item
    return replace(result,evidence=tuple(registry[key] for key in sorted(registry)),
                   objects=tuple(replace(obj,ddl_path='target-sidecars/'+obj.object_key+'.sql')
                       if obj.identity.object_type in {'COMMENT','GRANT'} else obj for obj in result.objects))
