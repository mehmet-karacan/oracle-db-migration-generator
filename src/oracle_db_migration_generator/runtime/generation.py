"""Schema Compare DDL dosyalarının tamamlanmasını uyarılardan ayrı hesaplar.

Çağıran arşiv bütünlüğünü doğrular. Bu özet SQL uygulama izni vermez.

Author: Mehmet KARACAN
Date: 2026-11-09
"""


def generation_summary(targets, plans, proposal_ids):
    """Doğrulanmış plan ve dosya kataloğundan üretim sonucunu çıkarır."""
    generated=missing=failed=unknown=incomplete=dependency=other=0
    for target in targets:
        plan=plans.get(target['id'])
        if plan is None or not target.get('plan_id'):
            failed+=1
            continue
        eligible={op['id'] for op in plan['operations'] if op['decision'] in {'BLOCKED','REVIEW_REQUIRED'}}
        proposed=set((proposal_ids or {}).get(target['id'],()))
        if not proposed<=eligible:
            raise ValueError('RUN_PROPOSAL_OPERATION_MISMATCH')
        generated+=sum(op['decision']=='READY' and bool(op['sql']) for op in plan['operations'])+len(proposed)
        missing+=len(eligible-proposed)+sum(op['decision']=='READY' and not op['sql'] for op in plan['operations'])
        unknown+=sum(diff['kind']=='UNKNOWN' for diff in plan['differences'])
        incomplete+=any(plan['scope'][key]!='COMPLETE' for key in ('inventory','ddl','dictionary'))
        for op in plan['operations']:
            codes=op.get('reason_codes',())
            if any('DEPENDENCY' in code for code in codes):
                dependency+=1
            elif op['decision'] in {'BLOCKED','REVIEW_REQUIRED'}:
                other+=1
    verified=proposal_ids is not None and bool(targets)
    status='FAILURE' if failed else 'NOT_VERIFIED' if not verified else 'UNSTABLE' if missing else 'SUCCESS'
    return {'status':status,'exit_code':0 if status=='SUCCESS' else 10 if status=='UNSTABLE' else 20,
            'generated_ddl':generated,'missing_ddl':missing,'failed_targets':failed,
            'metadata_unknown_records':unknown,'incomplete_metadata_targets':incomplete,
            'dependency_warning_operations':dependency,'other_warning_operations':other,
            'execution_status':'NOT_EXECUTED'}
