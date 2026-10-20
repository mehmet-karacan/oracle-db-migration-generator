from ..model.plan import Condition, Operation, SqlIntent
from ..model.serialization import digest
import hashlib


def operation(context,obj,changes,kind,decision,reason_code,reason_tr,*,statement=None,statement_kind='SQL',
              phase=30,tag='',risk=None,references=(),feature_scope='OBJECT',extra_evidence_ids=(),affected_columns=()):
    changes = tuple(changes)
    if not changes:
        raise ValueError('OPERATION_REQUIRES_DIFFERENCE')
    operation_id = 'op-'+digest([obj.object_key,kind,tag,reason_code])
    ids = tuple(sorted({key for diff in changes for key in diff.evidence_ids} | set(obj.evidence_ids) | {context.policy_evidence.id} | set(extra_evidence_ids)))
    decision_risk = risk or ('LOW' if decision=='READY' else 'HIGH' if decision=='REVIEW_REQUIRED' else 'UNKNOWN')
    intent = SqlIntent(statement,statement_kind,phase,tuple(references),feature_scope,hashlib.sha256(statement).hexdigest(),tuple(affected_columns)) if statement is not None and decision in {'READY','REVIEW_REQUIRED'} else None
    pre = Condition('condition-'+digest([operation_id,'pre']), 'POLICY' if decision=='INFORMATIONAL' else 'METADATA',
                    'SATISFIED' if decision in {'READY','INFORMATIONAL'} else 'NOT_EVALUATED',reason_code,ids)
    post = (Condition('condition-'+digest([operation_id,'post']),'POSTCHECK','NOT_EVALUATED',
                      'TARGET_VALIDITY_AND_SCHEMA_POSTCHECK_REQUIRED',ids,'checks/postcheck.sql'),) if intent else ()
    return Operation(operation_id,obj.identity,kind,changes[0].before,changes[0].after,decision,decision_risk,
                     'V1.'+reason_code,(reason_code,),reason_tr,tuple(diff.difference_id for diff in changes),
                     ids,preconditions=(pre,),postconditions=post,intent=intent)
