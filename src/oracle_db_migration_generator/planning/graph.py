"""Resolve prerequisites and propagate failures before deterministic ordering."""
from dataclasses import replace
from heapq import heappop, heappush

from ..model.plan import DependencyReference
from ..model.validity import report_only_invalid_ddl


def _key(identity):
    return (identity.owner.effective_name,identity.object_type,identity.name.effective_name)


def _block(op,code,details):
    return replace(op,decision='BLOCKED',risk='UNKNOWN',intent=None,sql=None,
                   reason_codes=tuple(sorted(set((*op.reason_codes,code)))),
                   reason_tr='; '.join(sorted(set(details)))+'.',postconditions=())


def _unique_parent(obj,columns):
    from .table_ddl import source_projection
    from .._vendor.analyzer_core.oracle.table import constraint_properties
    from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,identifier
    projection=source_projection(obj)
    if projection is None or not columns: return False
    for definition in projection.properties.get('constraints',{}).values():
        details=constraint_properties(definition)
        if details['kind'] not in {'PRIMARY KEY','UNIQUE'} or details.get('enabled')=='DISABLE' or details.get('validation')=='NOVALIDATE': continue
        try:
            names=tuple(identifier(token)[0] for token in code_tokens(details['columns']) if token.text!=',')
            if names==columns: return True
        except (ValueError,TypeError): pass
    if len(columns)==1:
        detail=projection.properties.get('columns',{}).get(columns[0])
        words=[token.upper for token in code_tokens(detail.get('definition','')) or ()] if detail else ()
        if 'DISABLE' not in words and 'NOVALIDATE' not in words and ('UNIQUE' in words or any(words[i:i+2]==['PRIMARY','KEY'] for i in range(len(words)-1))):
            return True
    return False


def _existing_relation_shape(ref,desired,actual,context):
    if (ref.role not in {'QUERY_RELATION','SOURCE_DEPENDENCY'} or desired is None or actual is None
            or desired.identity.object_type!=actual.identity.object_type or actual.identity.object_type!='TABLE'
            or actual.coverage.ddl!='COMPLETE' or desired.coverage.ddl!='COMPLETE'):
        return False
    for obj in (desired,actual):
        proof=obj.properties.get('projection')
        if proof is None or proof.state!='KNOWN':return False
    from .table_rules import column_fields
    wanted=column_fields(desired,context.source,context.profile.policy)
    observed=column_fields(actual,context.target,context.profile.policy)
    return bool(wanted) and all(name in observed and fields['data_type'].state==observed[name]['data_type'].state=='KNOWN'
                               and fields['data_type'].value==observed[name]['data_type'].value for name,fields in wanted.items())


def _existing_sequence_shape(ref,desired,actual,context):
    if (ref.object_type!='SEQUENCE' or ref.role not in {'SOURCE_DEPENDENCY','SEQUENCE_DEFAULT'}
            or desired is None or actual is None or ref.columns):return False
    for obj in (desired,actual):
        proof=obj.properties.get('projection')
        if obj.coverage.ddl!='COMPLETE' or not proof or proof.state!='KNOWN':return False
    from ..compare.projection_adapter import canonical_fields
    wanted=canonical_fields(desired,context.source,context.profile.policy)
    observed=canonical_fields(actual,context.target,context.profile.policy)
    def known(fields,key):
        value=fields.get('/sequence/'+key)
        if not value or value.state!='KNOWN':raise ValueError('SEQUENCE_SHAPE_UNKNOWN')
        return value.value
    try:
        for key in ('increment_by','order','scale','shard','extend','session','keep'):
            if known(wanted,key)!=known(observed,key):return False
        if known(wanted,'cycle')!=known(observed,'cycle') or known(observed,'cycle')!='NOCYCLE':return False
        return (int(known(wanted,'min_value'))<=int(known(observed,'min_value'))
                and int(known(wanted,'max_value'))>=int(known(observed,'max_value')))
    except (ValueError,TypeError):return False


def bind_and_order(operations,context):
    by_object = {}
    for op in operations:
        by_object.setdefault(_key(op.identity),[]).append(op)
    result = {}
    for op in operations:
        if not op.intent:
            result[op.operation_id]=op
            continue
        obj = context.source_objects.get(op.identity.key)
        refs = list(op.intent.references)
        # A source exporter dependency inventory is explicit evidence. A parser
        # must not invent successful external resolution from name spelling.
        if obj:
            from ..parsing.dependencies import references
            refs.extend(ref for ref in references(obj) if not (op.intent.feature_scope=='TABLE_BASE' and ref.object_type=='TABLE'))
        prerequisites,blocked = set(),False
        extra_evidence=set();namespace_conflict=False;issues=[]
        def issue(ref,description):
            columns=' ('+', '.join(ref.columns)+')' if ref.columns else ''
            issues.append(f'{ref.owner}.{ref.name}{columns} [{ref.object_type}]: {description}')
        if op.identity.object_type=='TABLE' and op.kind!='CREATE':
            prerequisites.update(other.operation_id for other in by_object.get(_key(op.identity),()) if other.kind=='CREATE')
        for ref in refs:
            kinds=(('TABLE','VIEW','MATERIALIZED_VIEW','SYNONYM') if ref.object_type=='RELATION' else
                   ('PROCEDURE','FUNCTION','PACKAGE_SPEC') if ref.object_type=='CALLABLE' else
                   ('TABLE','VIEW','SEQUENCE','PROCEDURE','FUNCTION','PACKAGE_SPEC','TYPE_SPEC','SYNONYM') if ref.object_type=='SYNONYM_OBJECT' else (ref.object_type,))
            desired = next((found for kind in kinds if (found:=context.lookup(ref.owner,kind,ref.name)) is not None),None)
            actual = next((found for kind in kinds if (found:=context.lookup(ref.owner,kind,ref.name,desired=False)) is not None),None)
            if desired and desired.object_key==op.identity.key and ref.role not in {'FK_PARENT','SYNONYM_TARGET'}: continue
            resolution=context.target.capabilities.get('resolved_references')
            private_synonym=bool(desired is None and actual is not None and actual.identity.object_type=='SYNONYM')
            if desired is None and (actual is None or private_synonym) and resolution and resolution.state=='KNOWN':
                records=[row for row in resolution.value if row.get('requested_owner')==ref.owner
                         and row.get('requested_name')==ref.name and row.get('unqualified') is ref.unqualified]
                extra_evidence.update(resolution.evidence_ids)
                if (not ref.columns and ref.role not in {'FK_PARENT','BACKING_INDEX','USER_DEFINED_TYPE'}
                        and len(records)==1 and records[0].get('state')=='KNOWN'
                        and any(item.get('object_type') in kinds and item.get('status') in {'VALID','INVALID'}
                                for item in records[0].get('objects',()))):continue
            if private_synonym:
                issue(ref,'hedefteki özel synonym mevcut, gösterdiği nesne çözümlenemedi')
                blocked=True;continue
            candidates = tuple(other for kind in kinds for other in by_object.get((ref.owner,kind,ref.name),()))
            # A changed spec/parent must not be bypassed through its old target
            # definition while a dependent body is reported ready.
            verified_existing_parent=(actual is not None and actual.coverage.ddl=='COMPLETE'
                                      and actual.identity.object_type=='TABLE'
                                      and ref.role in {'SIDECAR_PARENT','INDEX_TABLE'}
                                      or _existing_relation_shape(ref,desired,actual,context)
                                      or _existing_sequence_shape(ref,desired,actual,context))
            if verified_existing_parent and actual is not None:extra_evidence.update(actual.evidence_ids)
            if not verified_existing_parent and any(other.decision in {'BLOCKED','REVIEW_REQUIRED'} for other in candidates):
                held=sorted({other.kind+' / '+other.decision for other in candidates if other.decision in {'BLOCKED','REVIEW_REQUIRED'}})
                issue(ref,'bağımlı nesnenin gerekli işlemi hazır değil: '+', '.join(held))
                blocked=True
            if ref.owner not in context.target.schemas:
                # ALL_OBJECTS proves existence/status only. FK keys and named
                # column/index associations need structural dictionary proof,
                # independently of VALID/INVALID reporting.
                if ref.columns or ref.role in {'FK_PARENT','BACKING_INDEX'}:
                    issue(ref,'başka şemadaki nesnenin kolon/anahtar yapısı dictionary kanıtıyla doğrulanamadı')
                    blocked=True;continue
                external=context.target.capabilities.get('reference_objects')
                if external and external.state=='KNOWN' and any(item['owner']==ref.owner and item['name']==ref.name
                      and item['object_type'] in kinds and item['status'] in {'VALID','INVALID'} for item in external.value):
                    continue
                issue(ref,'hedefteki görünürlüğü veya nesne durumu doğrulanamadı')
                blocked=True;continue
            if actual is not None and (actual.coverage.ddl=='COMPLETE' or
                                       report_only_invalid_ddl(actual) and not ref.columns
                                       and ref.role not in {'FK_PARENT','BACKING_INDEX','USER_DEFINED_TYPE'}):
                prerequisites.update(other.operation_id for other in candidates if other.operation_id!=op.operation_id
                                     and other.decision=='READY' and (ref.role!='FK_PARENT' or other.kind=='CREATE'
                                         or other.kind=='ADD_CONSTRAINT' and other.intent and other.intent.phase==40)
                                     and not verified_existing_parent)
                status=actual.properties.get('object_status')
                if status and (status.state!='KNOWN' or status.value not in {'VALID','INVALID'}):
                    issue(ref,'hedef nesne durumu VALID/INVALID olarak doğrulanamadı');blocked=True
                if ref.role=='FK_PARENT' and not _unique_parent(actual,ref.columns):
                    issue(ref,'hedefte bu kolonlar için etkin ve doğrulanmış PRIMARY KEY/UNIQUE bulunamadı');blocked=True
                if ref.columns:
                    from .table_rules import column_fields
                    cols = column_fields(actual,context.target,context.profile.policy)
                    missing=set(ref.columns)-set(cols)
                    adds=[other for other in candidates if other.kind=='ADD_COLUMN' and other.decision=='READY' and other.intent
                          and missing.intersection(other.intent.affected_columns)]
                    supplied={name for other in adds for name in other.intent.affected_columns}
                    if missing and (ref.role not in {'SIDECAR_PARENT','INDEX_TABLE'} or not missing<=supplied):
                        explanation=('ADD_COLUMN hazır olsa da bu bağımlılık için mevcut hedefte kolon yapısı doğrulanmalı'
                                     if missing<=supplied else 'hazır ADD_COLUMN işlemiyle sağlanamayan kolonlar: '+', '.join(sorted(missing-supplied)))
                        issue(ref,'hedefte eksik kolonlar: '+', '.join(sorted(missing))+'; '+explanation);blocked=True
                    else:prerequisites.update(other.operation_id for other in adds)
                continue
            creates = [other for other in candidates if other.kind=='CREATE' or ref.role=='BACKING_INDEX' and other.kind=='CREATE_INDEX']
            if not creates:
                issue(ref,'hedefte bulunamadı ve oluşturulmasını sağlayan kaynak işlemi yok' if actual is None else
                      'hedefte mevcut fakat DDL yapısı eksik; doğrulanmış oluşturma işlemi de yok')
                blocked=True
            if creates and ref.columns:
                from .table_rules import column_fields
                if desired is None or any(name not in column_fields(desired,context.source,context.profile.policy) for name in ref.columns):
                    issue(ref,'kaynak tanımı bu kolonları sağlamıyor');blocked=True
            if creates and ref.role=='FK_PARENT' and not _unique_parent(desired,ref.columns):
                issue(ref,'kaynakta bu kolonlar için etkin ve doğrulanmış PRIMARY KEY/UNIQUE bulunamadı');blocked=True
            prerequisites.update(other.operation_id for other in creates)
            if ref.role=='FK_PARENT':
                prerequisites.update(other.operation_id for other in candidates if other.kind=='ADD_CONSTRAINT' and other.intent and other.intent.phase==40)
        # Shared Oracle namespace collisions cannot be solved by CREATE order.
        if op.kind=='CREATE' and op.identity.object_type in {'TABLE','VIEW','SEQUENCE','PACKAGE_SPEC','PROCEDURE','FUNCTION','TYPE_SPEC','SYNONYM'}:
            conflicts=sorted({item.identity.object_type for item in context.target.objects
                   if _key(item.identity)[::2]==_key(op.identity)[::2] and item.identity.object_type!=op.identity.object_type
                   and item.identity.object_type in {'TABLE','VIEW','SEQUENCE','PACKAGE_SPEC','PROCEDURE','FUNCTION','TYPE_SPEC','SYNONYM'}})
            if conflicts:
                issues.append(f'{op.identity.owner.effective_name}.{op.identity.name.effective_name}: hedefte '+
                              ', '.join(conflicts)+f' mevcut; kaynak {op.identity.object_type} oluşturulması aynı Oracle ad alanında çakışıyor')
                blocked=True;namespace_conflict=True
        if extra_evidence:
            ids=tuple(sorted(set(op.evidence_ids)|extra_evidence))
            op=replace(op,evidence_ids=ids,preconditions=tuple(replace(c,evidence_ids=ids) for c in op.preconditions))
        result[op.operation_id] = _block(op,'TARGET_NAMESPACE_CONFLICT' if namespace_conflict else 'DEPENDENCY_UNVERIFIED',issues) if blocked else replace(op,dependencies=tuple(sorted(prerequisites)))
    # Failure propagation and topological sort. Cycles stay blocked, never FORCE.
    changed=True
    while changed:
        changed=False
        for key,op in list(result.items()):
            if op.intent and any(result[dep].decision!='READY' for dep in op.dependencies):
                held=[result[dep] for dep in op.dependencies if result[dep].decision!='READY']
                details=[f'{dep.identity.owner.effective_name}.{dep.identity.name.effective_name} [{dep.identity.object_type}]: '+
                         f'gerekli {dep.kind} işlemi {dep.decision}' for dep in held]
                result[key]=_block(op,'PREREQUISITE_NOT_READY',details);changed=True
    return _topological_order(result)


def _topological_order(operations):
    """Select the same minimum ready operation without rescanning the graph."""
    pending=dict(operations);ordered=[];remaining={};dependents={};ready=[]
    for key,op in pending.items():
        dependencies=set(op.dependencies)
        remaining[key]=len(dependencies)
        for dependency in dependencies:
            dependents.setdefault(dependency,[]).append(key)
        if not dependencies:
            heappush(ready,(op.intent.phase if op.intent else 999,_key(op.identity),key))
    while ready:
        _,_,key=heappop(ready)
        op=pending.pop(key);ordered.append(op)
        for dependent in dependents.get(key,()):
            remaining[dependent]-=1
            if remaining[dependent]==0:
                candidate=pending[dependent]
                heappush(ready,(candidate.intent.phase if candidate.intent else 999,
                                _key(candidate.identity),dependent))
    # The residual includes cycles and their downstream dependents, as before.
    for op in sorted(pending.values(),key=lambda item:item.operation_id):
        held=[pending[dep] for dep in op.dependencies if dep in pending]
        names=', '.join(sorted({f'{dep.identity.owner.effective_name}.{dep.identity.name.effective_name} [{dep.identity.object_type}]' for dep in held}))
        ordered.append(_block(op,'DEPENDENCY_CYCLE',['SQL sırası çözülemeyen gruptaki önkoşullar: '+names]))
    return tuple(ordered)
