from ..model.difference import Difference, DifferenceSet
from ..model.serialization import digest, thaw
from ..model.snapshot import Coverage, KnownValue
from ..model.validity import report_only_invalid_ddl
from .projection_adapter import canonical_fields, structured_changes, align_anonymous_constraints
from .scope import scoped_objects


def _absence(snapshot,obj=None,*,object_type=None,object_identity=None,verified_types=(),verified_context_types=(),
             verified_comment_names=None):
    ids = obj.evidence_ids if obj else tuple(ev.id for ev in snapshot.evidence if ev.kind=='ABSENCE_SCOPE')
    # Source scripts can ALTER an earlier CREATE: local absence also requires
    # closed context coverage when the global source inventory is incomplete.
    complete = (obj.coverage.inventory==obj.coverage.ddl=='COMPLETE' if obj is not None
                else snapshot.completeness.inventory=='COMPLETE' or object_type in verified_types)
    if obj is not None and snapshot.side=='SOURCE' and snapshot.completeness.inventory!='COMPLETE':
        complete = complete and obj.identity.object_type in verified_context_types
        if complete:
            ids=tuple(sorted(set((*ids,*snapshot.capabilities['source_inventory_proof'].evidence_ids))))
    if obj is None and snapshot.completeness.inventory!='COMPLETE' and object_type in verified_types:
        ids = snapshot.capabilities['source_inventory_proof'].evidence_ids
    if (obj is None and snapshot.side=='SOURCE' and object_type=='COMMENT'
            and object_identity is not None and verified_comment_names is not None):
        complete=(object_identity.owner.effective_name,object_identity.name.effective_name) not in verified_comment_names
        ids=snapshot.capabilities['source_inventory_proof'].evidence_ids
    return KnownValue('ABSENT' if complete and ids else 'UNKNOWN',None,ids)


def compare_snapshots(desired,actual,policy):
    if desired.side!='SOURCE' or actual.side!='TARGET':
        raise ValueError('SNAPSHOT_DIRECTION_MISMATCH')
    if desired.profile_id!=actual.profile_id or not set(actual.schemas).issubset(desired.schemas):
        raise ValueError('SNAPSHOT_PROFILE_OR_SCHEMA_MISMATCH')
    source = {obj.object_key:obj for obj in scoped_objects(desired,policy) if obj.identity.owner.effective_name in actual.schemas}
    target = {obj.object_key:obj for obj in scoped_objects(actual,policy)}
    from ..parsing.inventory import verified_inventory_types,verified_comment_identity_names
    source_inventory_types = verified_inventory_types(desired)
    source_context_types = verified_inventory_types(desired,context=True)
    source_comment_names = verified_comment_identity_names(desired)
    differences, diagnostics = [], []
    def add(key,path,before,after,kind):
        ids = tuple(sorted(set(before.evidence_ids+after.evidence_ids)))
        differences.append(Difference('diff-'+digest([key,path,kind,thaw(before),thaw(after)]),key,path,before,after,kind,ids))
    for key in sorted(source.keys() | target.keys()):
        new, old = source.get(key),target.get(key)
        if old is None or new is None:
            present = new or old
            before = KnownValue('KNOWN',True,old.evidence_ids) if old else _absence(actual)
            after = KnownValue('KNOWN',True,new.evidence_ids) if new else _absence(desired,
                object_type=present.identity.object_type,object_identity=present.identity,
                verified_types=source_inventory_types,verified_comment_names=source_comment_names)
            for snapshot,value in ((actual,before),(desired,after)):
                if value.state=='ABSENT' and present.identity.object_type in {'COMMENT','GRANT'}:
                    cap = snapshot.capabilities.get('coverage.'+present.identity.object_type)
                    if (snapshot.side=='TARGET' or snapshot.source_origin) and (cap is None or cap.state!='KNOWN' or cap.value!='COMPLETE'):
                        if snapshot is actual:
                            before = KnownValue('UNKNOWN',None,value.evidence_ids)
                        else:
                            after = KnownValue('UNKNOWN',None,value.evidence_ids)
            kind = 'UNKNOWN' if 'UNKNOWN' in {before.state,after.state} else 'MISSING' if old is None else 'EXTRA'
            add(key,'/presence',before,after,kind)
            continue
        old_fields = canonical_fields(old,actual,policy)
        new_fields = canonical_fields(new,desired,policy)
        if new.identity.object_type=='TABLE':
            old_fields=align_anonymous_constraints(old_fields,new_fields)
        changed_before = len(differences)
        for path in sorted(old_fields.keys() | new_fields.keys()):
            before = old_fields.get(path) or _absence(actual,old)
            after = new_fields.get(path) or _absence(desired,new,verified_context_types=source_context_types)
            # Omitted character collation needs evidence. A verified change
            # to NUMBER/DATE/etc has no collation and is a real type change,
            # not an unknown source character setting.
            source_type = new_fields.get(path.rsplit('/',1)[0]+'/data_type')
            collatable = (source_type is None or source_type.state!='KNOWN' or
                          source_type.value in {'CHAR','VARCHAR2','NCHAR','NVARCHAR2','CLOB','NCLOB','LONG'})
            if path.endswith('/collation') and collatable and before.state=='KNOWN' and before.value is not None and after.state=='KNOWN' and after.value is None:
                after = KnownValue('UNKNOWN',None,after.evidence_ids)
            if before.state=='UNKNOWN' or after.state=='UNKNOWN':
                kind = 'UNKNOWN'
            elif before.state==after.state and thaw(before.value)==thaw(after.value):
                continue
            elif before.state=='ABSENT':
                kind = 'MISSING'
            elif after.state=='ABSENT':
                kind = 'EXTRA'
            else:
                kind = 'CHANGED'
            if path.endswith('/position') or path=='/sequence/start_with':
                kind = 'INFORMATIONAL' if kind!='UNKNOWN' else kind
            add(key,path,before,after,kind)
        # The Analyzer remains the detailed routine/body comparator. Token
        # equality first prevents presentation-only facts becoming migration.
        if new.identity.object_type in {'PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','VIEW','TRIGGER'}:
            before = old_fields.get('/definition')
            after = new_fields.get('/definition')
            if before and after and before.state==after.state=='KNOWN' and before.value!=after.value:
                structured = structured_changes(old,new)
                if structured and not structured.diagnostics:
                    for fact in structured.facts:
                        if fact.taxonomy_id=='common.object.editionable':
                            continue
                        path = '/structured/'+fact.taxonomy_id+'/'+ '/'.join(fact.component_path)
                        left = KnownValue('KNOWN',fact.before.value,fact.before.evidence_ids)
                        right = KnownValue('KNOWN',fact.after.value,fact.after.evidence_ids)
                        add(key,path,left,right,'CHANGED')
    partial_target_objects=[obj for obj in actual.objects if obj.coverage.ddl!='COMPLETE']
    target_ddl_complete=(actual.completeness.ddl=='COMPLETE' or
                         actual.completeness.ddl=='PARTIAL' and bool(partial_target_objects)
                         and not actual.completeness.diagnostics
                         and all(obj.object_key not in source and report_only_invalid_ddl(obj)
                                 for obj in partial_target_objects))
    for side,snapshot in (('SOURCE',desired),('TARGET',actual)):
        coverage = snapshot.completeness
        if coverage.inventory!='COMPLETE':
            diagnostics.append(side+'_INVENTORY_'+coverage.inventory)
        if coverage.ddl!='COMPLETE' and not (side=='TARGET' and target_ddl_complete):
            diagnostics.append(side+'_DDL_'+coverage.ddl)
        if (snapshot.side=='TARGET' or snapshot.source_origin) and coverage.dictionary!='COMPLETE':
            diagnostics.append(side+'_DICTIONARY_'+coverage.dictionary)
    scope = Coverage('COMPLETE' if desired.completeness.inventory==actual.completeness.inventory=='COMPLETE' else 'PARTIAL',
                     'COMPLETE' if desired.completeness.ddl=='COMPLETE' and target_ddl_complete else 'PARTIAL',
                     'PARTIAL' if desired.source_origin and desired.completeness.dictionary!='COMPLETE' else actual.completeness.dictionary,tuple(sorted(diagnostics)))
    return DifferenceSet(desired.semantic_digest,actual.semantic_digest,tuple(differences),scope,tuple(sorted(diagnostics)))
