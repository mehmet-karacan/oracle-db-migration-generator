from copy import deepcopy
import re
import pytest

from tests.unit.test_bundle import make_plan


def inputs(count=1):
    plan=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    targets=[];plans={}
    for i in range(count):
        target=f'TARGET-{i:03d}'
        targets.append(dict(id=target,status='READY',difference_count=2353,plan_id=plan['plan_id'],plan_path=f'targets/{target}/plan.json',error_code=None))
        plans[target]=deepcopy(plan)
    return dict(run_id='run-test',source_commit='a'*40,finished_at='2026-10-20T12:00:00Z',status='COMPLETE',targets=targets),plans


def test_email_limits_unique_objects_and_preserves_unknown_counts():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    run,plans=inputs(101)
    run['targets'][-1].update(status='ERROR',difference_count=None,plan_id=None,plan_path=None,error_code='ORA-01031')
    del plans[run['targets'][-1]['id']]
    view=build_run_view(run,plans)
    assert len(view['critical_targets'])==5 and view['critical_targets'][0]['id']=='TARGET-100'
    assert len(view['important_objects'])==1 and len(view['important_objects'][0]['targets'])==100
    assert view['metrics'][0]['value']=='101' and view['metrics'][1]['value']=='235.300 + ?'
    html=render_email(view).decode()
    assert 'cid:innova-logo' in html and '<script' not in html and 'CREATE TABLE' not in html
    assert 'ERROR / UNKNOWN' in html and '2.353' in html
    assert 'artifact-browser.preview' not in html and 'href=' not in html
    assert len(html.encode())<200*1024


def test_email_zero_and_thousand_objects_escape_and_rank():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    run,plans=inputs(0)
    empty=render_email(build_run_view(run,plans)).decode()
    assert 'Hedef sonucu bulunmuyor' in empty
    run,plans=inputs()
    p=plans['TARGET-000'];base=p['operations'][0]
    p['operations']=[]
    for i in range(1001):
        op=deepcopy(base);op['id']=f'op-{i}';op['object']['name']=f'T{i}';op['decision']='BLOCKED' if i==1000 else 'READY'
        p['operations'].append(op)
    p['operations'][-1]['object']['name']='<script>'+('X'*200)
    view=build_run_view(run,plans)
    assert len(view['important_objects'])==5 and view['unique_objects']==1001
    assert view['important_objects'][0]['decision']=='BLOCKED'
    html=render_email(view,preview=True).decode()
    assert '&lt;script&gt;' in html and '<script>' not in html
    assert 'data:image/png;base64,' in html


def test_first_five_objects_keep_blocked_and_review_before_ready_and_information():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email,render_run_reports
    run,plans=inputs();plan=plans['TARGET-000'];base=plan['operations'][0]
    plan['operations']=[]
    for name,decision in [('A_INFO','INFORMATIONAL'),('Z_READY','READY'),('B_READY','READY'),
                          ('A_READY','READY'),('Z_REVIEW','REVIEW_REQUIRED'),('Z_BLOCK','BLOCKED'),('B_BLOCK','BLOCKED')]:
        op=deepcopy(base);op['id']='op-'+name;op['object']['name']=name;op['decision']=decision
        plan['operations'].append(op)
    view=build_run_view(run,plans)
    assert [row['object']['name'] for row in view['important_objects']]==['B_BLOCK','Z_BLOCK','Z_REVIEW','A_READY','B_READY']
    assert view['unique_objects']==7
    for html in [render_email(view).decode(),render_run_reports(view)['index.html'].decode()]:
        assert 'B_BLOCK' in html and 'Z_REVIEW' in html and 'B_READY' in html
        assert 'A_INFO' not in html and 'Z_READY' not in html
    assert 'en fazla 5 benzersiz nesne' in render_email(view).decode()


@pytest.mark.parametrize('started,finished,expected',[
    ('2026-10-20T09:00:00Z','2026-10-20T09:12:34Z','12 dk 34 sn'),
    ('2026-10-20T12:00:00+03:00','2026-10-20T09:12:34+00:00','12 dk 34 sn'),
    ('2026-10-20T09:00:00Z','2026-10-20T10:02:03Z','1 sa 2 dk 3 sn'),
    ('2026-10-20T09:00:00Z','2026-10-20T09:00:00Z','0 dk 0 sn'),
    (None,'2026-10-20T09:12:34Z','Bilinmiyor'),
    ('2026-10-20T09:00:00Z',None,'Bilinmiyor'),
    ('invalid','2026-10-20T09:12:34Z','Bilinmiyor'),
    ('2026-10-20T09:00:00Z','invalid','Bilinmiyor'),
    ('2026-10-20T09:12:34Z','2026-10-20T09:00:00Z','Bilinmiyor'),
    ('2026-10-20T09:00:00','2026-10-20T09:12:34Z','Bilinmiyor'),
])
def test_duration_is_visible_in_email_and_web_without_guessing(started,finished,expected):
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email,render_run_reports
    run,plans=inputs();run.update(started_at=started,finished_at=finished)
    if started is None:run.pop('started_at')
    view=build_run_view(run,plans)
    assert view['duration_label']==expected
    for html in [render_email(view).decode(),render_run_reports(view)['index.html'].decode()]:
        assert 'Çalışma süresi' in html and expected in html


def test_email_link_must_match_the_current_run_commit_and_retention_check():
    from oracle_db_migration_generator.artifacts.publisher import Publication
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    run,plans=inputs()
    url='https://github.com/acme/artifacts/blob/'+('b'*40)+'/runs/2026/10/20/build-42-run-test/README.md'
    pub=Publication('PUBLISHED',url,'b'*40)
    valid=render_email(build_run_view(run,plans,publication=pub,url_check=lambda u:True,allowed_link_hosts=('github.com',))).decode()
    assert url in valid
    expired=render_email(build_run_view(run,plans,publication=pub,url_check=lambda u:False,allowed_link_hosts=('github.com',))).decode()
    assert url not in expired and 'doğrulanmadı' in expired
    forged=Publication('PUBLISHED',url.replace('build-42-run-test','build-42-other'), 'b'*40)
    assert url.replace('build-42-run-test','build-42-other') not in render_email(build_run_view(run,plans,publication=forged,url_check=lambda u:True,allowed_link_hosts=('github.com',))).decode()


def test_fallback_is_bound_to_the_current_build_and_explicit_host():
    from oracle_db_migration_generator.reporting.links import ArchiveLink
    from oracle_db_migration_generator.reporting.view import build_run_view
    run,plans=inputs();run.update(build_number=142,build_url='https://jenkins.example/job/migration/142/')
    good=ArchiveLink(run['build_url']+'artifact/report/index.html')
    assert build_run_view(run,plans,fallback=good,url_check=lambda u:True,allowed_link_hosts=('jenkins.example',))['link']==good.url
    assert build_run_view(run,plans,fallback=good,url_check=lambda u:True)['link'] is None
    wrong=ArchiveLink(good.url.replace('/142/','/141/'))
    assert build_run_view(run,plans,fallback=wrong,url_check=lambda u:True,allowed_link_hosts=('jenkins.example',))['link'] is None


def test_web_paginates_101_targets_and_email_has_no_tablet_overflow_rule():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_run_reports,render_email
    run,plans=inputs(101)
    payload=render_run_reports(build_run_view(run,plans))
    assert all(name in payload for name in ('index.html','targets-0002.html','targets-0003.html'))
    assert payload['index.html'].count(b'class="target"')==50
    assert payload['targets-0003.html'].count(b'class="target"')==1
    assert all(len(raw)<=200*1024 for name,raw in payload.items() if name.endswith('.html'))
    assert b'margin:0 auto;width:100%;max-width:820px' in render_email(build_run_view(run,plans))
