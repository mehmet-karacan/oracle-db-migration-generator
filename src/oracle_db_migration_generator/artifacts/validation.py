from copy import deepcopy

from ..config.loader import validate_document
from ..model.serialization import digest


def validate_plan(document):
    validate_document(document,'plan.schema.json')
    core=deepcopy(document); expected=core.pop('plan_id');core.pop('validation')
    for op in core['operations']: op['sql']=None
    if digest(core)!=expected: raise ValueError('PLAN_ID_MISMATCH')
    evidence={item['id'] for item in document['evidence']}
    if len(evidence)!=len(document['evidence']): raise ValueError('PLAN_DUPLICATE_EVIDENCE')
    changes={item['id'] for item in document['differences']}
    operations={op['id'] for op in document['operations']}
    if len(changes)!=len(document['differences']) or len(operations)!=len(document['operations']):
        raise ValueError('PLAN_DUPLICATE_ID')
    seen=set();covered=set()
    for diff in document['differences']:
        ids=set(diff['evidence_ids']) | set(diff['before']['evidence_ids']) | set(diff['after']['evidence_ids'])
        if not ids<=evidence: raise ValueError('PLAN_EVIDENCE_UNRESOLVED')
    for op in document['operations']:
        if not set(op['change_ids'])<=changes or not op['change_ids']: raise ValueError('PLAN_CHANGE_UNRESOLVED')
        covered.update(op['change_ids'])
        if not set(op['evidence_ids'])<=evidence: raise ValueError('PLAN_EVIDENCE_UNRESOLVED')
        # Blocked cycles may retain their edges as diagnostic evidence. Executable
        # operations must have all prerequisites earlier and executable.
        if not set(op['depends_on'])<=operations: raise ValueError('PLAN_DEPENDENCY_UNRESOLVED')
        if op['decision']=='READY' and not set(op['depends_on'])<=seen: raise ValueError('PLAN_DEPENDENCY_ORDER_INVALID')
        for condition in op['preconditions']+op['postconditions']:
            if not set(condition['evidence_ids'])<=evidence: raise ValueError('PLAN_CONDITION_EVIDENCE_UNRESOLVED')
        if op['decision'] in {'BLOCKED','INFORMATIONAL'} and op['sql'] is not None: raise ValueError('PLAN_NONEXECUTABLE_SQL')
        if op['decision']=='READY' and op['sql'] is None: raise ValueError('PLAN_READY_SQL_MISSING')
        if op['decision']=='READY': seen.add(op['id'])
    if covered!=changes: raise ValueError('PLAN_DIFFERENCE_UNACCOUNTED')
    actual={'observed_differences':len(changes),'ready_operations':0,'review_operations':0,'blocked_operations':0,'informational_changes':0}
    keys={'READY':'ready_operations','REVIEW_REQUIRED':'review_operations','BLOCKED':'blocked_operations','INFORMATIONAL':'informational_changes'}
    for op in document['operations']: actual[keys[op['decision']]]+=1
    if actual!=document['counts']: raise ValueError('PLAN_COUNTS_MISMATCH')
    return document
