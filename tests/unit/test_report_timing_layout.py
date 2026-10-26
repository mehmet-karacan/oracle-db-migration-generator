from copy import deepcopy
import re

import pytest

from oracle_db_migration_generator.reporting.render import render_email, render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


def timing_view(*, refresh=True):
    run, plans = inputs()
    run.update(started_at='2026-10-21T07:00:00Z', finished_at='2026-10-21T07:01:06Z')
    timing = {'started_at': '2026-10-21T05:00:00Z', 'finished_at': '2026-10-21T06:15:09Z'}
    return build_run_view(run, plans, comparison_timing=timing if refresh else None)


def rendered(view, profile):
    return (render_email(view) if profile == 'email' else render_run_reports(view)['index.html']).decode()


@pytest.mark.parametrize('profile', ['email', 'web'])
def test_original_duration_is_visible_before_summary_metrics_without_refresh_clocks(profile):
    view = timing_view()
    before = deepcopy(view)
    html = rendered(view, profile)
    assert 'Karşılaştırma süresi: 75 dk 9 sn' in html
    assert html.count('Karşılaştırma süresi:') == 1
    assert html.index('Karşılaştırma süresi:') < html.index('class="metric"')
    assert html.index('Karşılaştırma süresi:') < html.index('Tarama Kapsamı')
    assert 'Başlangıç' not in html and 'Bitiş' not in html and 'TSİ' not in html
    assert 'Rapor yenileme süresi' not in html and '1 dk 6 sn' not in html
    assert view == before


@pytest.mark.parametrize('profile', ['email', 'web'])
@pytest.mark.parametrize('started,finished', [(None,None),('invalid','invalid'),
    ('2026-10-21T07:01:00Z','2026-10-21T07:00:00Z')])
def test_unknown_original_duration_does_not_show_refresh_time_as_comparison(profile,started,finished):
    run,plans=inputs()
    run.update(started_at='2026-10-21T07:00:00Z',finished_at='2026-10-21T07:01:06Z')
    view=build_run_view(run,plans,comparison_timing={'started_at':started,'finished_at':finished})
    html=rendered(view,profile)
    assert 'Karşılaştırma süresi: Ölçülemedi' in html
    assert '1 dk 6 sn' not in html


@pytest.mark.parametrize('profile', ['email', 'web'])
def test_duration_note_escapes_content_and_keeps_readable_small_text(profile):
    view=timing_view()
    label='<script>alert("x")</script>&'+'Ç'*200
    view['comparison_duration_label']=label
    html=rendered(view,profile)
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert len(html.encode())<=200*1024
    if profile=='email':
        assert 'class="timing-summary"' in html and 'font-size:14px' in html
        assert re.findall(r'<th width="(\d+%)"',html)==['60%','12%','12%','16%']
        assert html.count('class="metric"')==5
    else:
        css=render_run_reports(view)['assets/report.css'].decode()
        assert '.timing-summary{' in css and 'overflow-wrap:anywhere' in css
