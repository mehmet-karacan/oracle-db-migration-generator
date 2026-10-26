from copy import deepcopy
import json

from oracle_db_migration_generator.reporting.view import build_run_view
from oracle_db_migration_generator.reporting.render import render_email, render_run_reports
from tests.unit.test_report_views import inputs


def test_partial_comparison_shows_confirmed_differences_separately_from_unknown_records():
    run, plans = inputs(); plan = plans['TARGET-000']
    run['targets'][0]['difference_count'] = None
    plan['differences'] = [{'kind':kind} for kind in ('CHANGED','UNKNOWN','INFORMATIONAL','UNKNOWN')]
    before = deepcopy((run, plans))
    view = build_run_view(run, plans)
    assert view['metrics'][1]['value'] == '2'
    assert view['confirmed_differences'] == 2 and view['unverified_differences'] == 2
    assert view['targets'][0]['confirmed_difference_count'] == 2
    for raw in (render_email(view), render_run_reports(view)['index.html']):
        html = raw.decode()
        assert 'Bulunan fark' in html and '2 kayıt, bilgisi eksik olduğu için karşılaştırılamadı.' in html
        assert 'Bilinmiyor fark' not in html and 'fark sayısı bilinmiyor' not in html
    assert (run, plans) == before


def test_no_target_result_does_not_invent_zero_differences():
    run, _ = inputs(); run['targets'][0].update(status='ERROR',difference_count=None)
    view = build_run_view(run, {})
    assert view['metrics'][1]['value'] == 'Sonuç alınamadı'
    assert view['confirmed_differences'] is None


def test_comparison_duration_remains_primary_after_a_short_presentation_refresh():
    run, plans = inputs(); run.update(started_at='2026-10-21T07:00:00Z',finished_at='2026-10-21T07:01:05Z')
    timing={'schema_version':'comparison-timing/1.0','build_number':29,
            'started_at':'2026-10-21T05:00:00.603+00:00','finished_at':'2026-10-21T06:15:09.472414+00:00'}
    view = build_run_view(run, plans, comparison_timing=timing)
    assert view['comparison_duration_label'] == '75 dk 9 sn'
    assert view['report_duration_label'] == '1 dk 5 sn'
    assert view['comparison_finished_label'] == '21.10.2026 09:15:09'
    for raw in (render_email(view), render_run_reports(view)['index.html']):
        html=raw.decode()
        assert 'Karşılaştırma süresi' in html and '75 dk 9 sn' in html
        assert 'Rapor yenileme süresi' not in html and '1 dk 5 sn' not in html
        assert html.index('75 dk 9 sn') < html.index('class="metric"')


def test_invalid_comparison_timing_is_not_replaced_with_the_refresh_duration():
    run, plans=inputs();run.update(started_at='2026-10-21T07:00:00Z',finished_at='2026-10-21T07:01:05Z')
    view=build_run_view(run, plans, comparison_timing={'started_at':'invalid','finished_at':'invalid'})
    assert view['comparison_duration_label'] == 'Ölçülemedi'
    assert view['report_duration_label'] == '1 dk 5 sn'


def test_jenkins_mail_reads_original_comparison_timing_from_archive(tmp_path):
    from tools.jenkins_notification import write_notification
    run, plans=inputs();url='https://jenkins.example.invalid/job/generator/'
    run.update(build_number=31,started_at='2026-10-21T07:00:00Z',finished_at='2026-10-21T07:01:05Z')
    for target in run['targets']:
        path=tmp_path/target['plan_path'];path.parent.mkdir(parents=True)
        path.write_text(json.dumps(plans[target['id']]),encoding='utf-8')
    (tmp_path/'comparison-timing.json').write_text(json.dumps({'schema_version':'comparison-timing/1.0',
        'build_number':29,'source_commit':run['source_commit'],'started_at':'2026-10-21T05:00:00Z',
        'finished_at':'2026-10-21T06:15:09Z'}),encoding='utf-8')
    html=write_notification(tmp_path,run,url+'31/',url).read_text(encoding='utf-8')
    assert 'Karşılaştırma süresi: 75 dk 9 sn' in html
    assert 'Rapor yenileme süresi' not in html and '1 dk 5 sn' not in html
