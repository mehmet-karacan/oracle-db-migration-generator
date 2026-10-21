from copy import deepcopy
from html.parser import HTMLParser
import re

import pytest

from oracle_db_migration_generator.reporting.render import render_email, render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


class TimingSummary(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.depth = 0
        self.attributes = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'timing-summary' in attrs.get('class', '').split() or self.depth:
            self.attributes.append((tag, attrs))
            if tag not in {'br', 'img', 'meta', 'link'}:
                self.depth += 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, text):
        if self.depth:
            self.text.append(text)


def timing_view(*, refresh=True):
    run, plans = inputs()
    run.update(started_at='2026-10-21T07:00:00Z', finished_at='2026-10-21T07:01:06Z')
    timing = {'started_at': '2026-10-21T05:00:00Z', 'finished_at': '2026-10-21T06:15:09Z'}
    return build_run_view(run, plans, comparison_timing=timing if refresh else None)


def rendered(view, profile):
    return (render_email(view) if profile == 'email' else render_run_reports(view)['index.html']).decode()


@pytest.mark.parametrize('profile', ['email', 'web'])
def test_summary_groups_original_comparison_time_and_secondary_refresh(profile):
    view = timing_view()
    before = deepcopy(view)
    html = rendered(view, profile)
    summary = TimingSummary(html)
    text = ' '.join(summary.text)
    assert 'Karşılaştırma süresi' in text
    assert '75 dk 9 sn' in text
    assert 'Başlangıç (TSİ): 21.10.2026 08:00:00' in text
    assert 'Bitiş (TSİ): 21.10.2026 09:15:09' in text
    assert 'Rapor yenileme süresi: 1 dk 6 sn' in text
    assert text.index('75 dk 9 sn') < text.index('1 dk 6 sn')
    primary = [attrs for _, attrs in summary.attributes if 'timing-value' in attrs.get('class', '').split()]
    assert len(primary) == 1
    assert html.index('timing-summary') < html.index('class="metric"')
    assert view == before


@pytest.mark.parametrize('profile', ['email', 'web'])
@pytest.mark.parametrize('started,finished', [
    (None, None), ('invalid', 'invalid'),
    ('2026-10-21T07:01:00Z', '2026-10-21T07:00:00Z'),
])
def test_unmeasured_original_duration_never_becomes_the_refresh_duration(profile, started, finished):
    run, plans = inputs()
    run.update(started_at='2026-10-21T07:00:00Z', finished_at='2026-10-21T07:01:06Z')
    view = build_run_view(run, plans, comparison_timing={'started_at': started, 'finished_at': finished})
    summary = TimingSummary(rendered(view, profile))
    text = ' '.join(summary.text)
    assert 'Ölçülemedi' in text
    assert 'Rapor yenileme süresi: 1 dk 6 sn' in text


@pytest.mark.parametrize('profile', ['email', 'web'])
def test_fresh_comparison_has_no_empty_refresh_row(profile):
    html = rendered(timing_view(refresh=False), profile)
    text = ' '.join(TimingSummary(html).text)
    assert '1 dk 6 sn' in text and 'Karşılaştırma süresi' in text
    assert 'Rapor yenileme süresi' not in html and 'timing-refresh' not in text
    assert 'None' not in text


@pytest.mark.parametrize('profile', ['email', 'web'])
def test_timing_labels_are_escaped_and_can_wrap_without_losing_content(profile):
    view = timing_view()
    label = '<script>alert("x")</script>&' + 'Ç' * 200
    view.update(comparison_duration_label=label, report_duration_label=label,
                comparison_started_label=label, comparison_finished_label=label)
    html = rendered(view, profile)
    summary = TimingSummary(html)
    assert ' '.join(summary.text).count(label) == 4
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert len(html.encode()) <= 200 * 1024
    if profile == 'email':
        assert summary.attributes[0][0] == 'table'
        assert summary.attributes[0][1]['role'] == 'presentation'
        assert 'table-layout:fixed' in summary.attributes[0][1]['style']
        cells = [attrs for tag, attrs in summary.attributes if tag == 'td']
        assert len(cells) == 2
        assert all('overflow-wrap:anywhere' in cell['style'] for cell in cells)
        assert all('word-break:break-word' in cell['style'] for cell in cells)
        assert '.timing-cell{display:block!important;width:100%!important' in html
        mobile_cell = re.search(r'\.timing-cell\{([^}]+)\}', html).group(1)
        assert 'box-sizing:border-box!important' in mobile_cell
        assert '<!--[if mso]><table role="presentation" width="820"' in html
        assert 'src="cid:innova-logo" width="156" height="30"' in html
        assert re.findall(r'<th width="(\d+%)"', html) == ['60%', '12%', '12%', '16%']
        assert html.count('class="metric"') == 5
    else:
        css = render_run_reports(view)['assets/report.css'].decode()
        assert '.timing-summary' in css and '.timing-value' in css
        assert '.timing-summary{grid-template-columns:1fr}' in css
        assert 'min-width:0' in css and 'overflow-wrap:anywhere' in css
