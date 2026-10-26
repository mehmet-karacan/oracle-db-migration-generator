from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4


from ..artifacts.bundle import verify_bundle
from ..config.loader import read_json,validate_document
from ..model.serialization import canonical_bytes
from ..reporting.view import build_run_view
from ..reporting.render import render_run_reports
from ..artifacts.layout import markdown


def aggregate_run(root,*,source_commit=None,started_at=None,build_number=None,build_url=None,source_origin=None):
    root=Path(root).resolve();results=[];commits=set();synthetic=False;plans={}
    for path in sorted((root/'targets').glob('*')):
        if not path.is_dir(): continue
        if (path/'plan.json').is_file():
            verify_bundle(path);plan=read_json(path/'plan.json');commits.add(plan['source']['commit_sha'])
            synthetic=synthetic or plan['synthetic'];plans[plan['target']['id']]=plan
            result_path=path.parent/(path.name+'.result.json')
            expected={
                'id':plan['target']['id'],'status':plan['status'],'difference_count':plan['counts']['observed_differences'] if plan['scope']['inventory']==plan['scope']['ddl']==plan['scope']['dictionary']=='COMPLETE' else None,
                'plan_id':plan['plan_id'],'plan_path':'targets/'+path.name+'/plan.json','captured_at':None,'error_code':None,'publication':'NOT_REQUESTED'}
            if any(diff['kind']=='UNKNOWN' for diff in plan['differences']): expected['difference_count']=None
            result=read_json(result_path) if result_path.is_file() else expected
            if path.name!=plan['target']['id'] or any(result[key]!=expected[key] for key in ('id','status','difference_count','plan_id','plan_path','publication')):
                raise ValueError('RUN_RESULT_PLAN_MISMATCH')
            results.append(result)
        elif (path/'target-error.json').is_file():
            result=read_json(path/'target-error.json')
            if (result.get('id')!=path.name or result.get('status') not in {'ERROR','INCONSISTENT'}
                    or any(result.get(k) is not None for k in ('difference_count','plan_id','plan_path'))):
                raise ValueError('RUN_ERROR_MUST_BE_UNKNOWN')
            results.append(result)
    if not results: raise ValueError('RUN_HAS_NO_TARGET_RESULTS')
    if source_commit: commits.add(source_commit)
    origins=[plan['source'].get('origin') for plan in plans.values()]
    if origins and any(origin!=origins[0] for origin in origins):raise ValueError('RUN_SOURCE_ORIGIN_MISMATCH')
    if origins and origins[0]:
        if source_origin is not None and source_origin!=origins[0]:raise ValueError('RUN_SOURCE_ORIGIN_MISMATCH')
        source_origin=origins[0]
    if source_origin:
        if source_commit:raise ValueError('RUN_SOURCE_ORIGIN_MISMATCH')
        commits.add(None)
    if len(commits)!=1: raise ValueError('RUN_SOURCE_COMMIT_MISMATCH')
    now=datetime.now(timezone.utc).isoformat()
    partial=any(item['status'] in {'BLOCKED','REVIEW_REQUIRED','ERROR','INCONSISTENT','INCOMPLETE'} for item in results)
    failed=all(item['plan_id'] is None for item in results)
    code=20 if failed else 10 if partial else 0
    document={'schema_version':'run/1.0','synthetic':synthetic,'run_id':str(uuid4()),'started_at':started_at or now,'finished_at':now,
              'source_commit':commits.pop(),'status':'FAILED' if failed else 'PARTIAL' if partial else 'COMPLETE',
              'exit_code':code,'build_url':build_url,'targets':results}
    if build_number is not None: document['build_number']=build_number
    if source_origin:document['source_origin']=source_origin
    validate_document(document,'run.schema.json')
    (root/'run.json').write_bytes(canonical_bytes(document)+b'\n')
    lines=['# Oracle Migration çalışma kaydı', '', f"Run: `{document['run_id']}`", '', 'Üretildi · Veritabanına uygulanmadı.', '', '[Çalışma JSON](run.json) · [Web raporu](index.html)', '']
    for target in results:
        if target['plan_path']:
            folder=str(Path(target['plan_path']).parent).replace('\\','/')
            lines.append(f"- [{markdown(target['id'])}]({folder}/README.md) · {target['status']}")
        else: lines.append(f"- {markdown(target['id'])} · ERROR / UNKNOWN")
    (root/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    timing=read_json(root/'comparison-timing.json') if (root/'comparison-timing.json').is_file() else None
    if timing and timing.get('source_commit')!=document['source_commit']:raise ValueError('COMPARISON_TIMING_SOURCE_MISMATCH')
    from ..reporting.inventory import load_scan_summaries
    view=build_run_view(document,plans,comparison_timing=timing,
                        scan_summaries=load_scan_summaries(root,document,plans))
    for path,raw in render_run_reports(view).items():
        destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    return document
