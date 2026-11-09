"""Şema Karşılaştırma rapor ikonlarının dış kaynağa gerek duymadan görünmesini sınar.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
import base64
from html.parser import HTMLParser
import struct
from importlib.resources import files
import json
import xml.etree.ElementTree as ET

from oracle_db_migration_generator.reporting.render import render_email, render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


class Images(HTMLParser):
    """HTML'deki dekoratif ikonların gerçek görsel adreslerini toplar.

    Author: Mehmet KARACAN
    Date: 2026-11-07
    """
    def __init__(self, html):
        super().__init__()
        self.icons = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if tag == 'img' and 'data-report-icon' in values:
            self.icons.append(values)


def test_email_icons_are_embedded_and_web_icons_resolve_inside_the_report_bundle():
    run, plans = inputs()
    view = build_run_view(run, plans)
    bundle = render_run_reports(view)
    pages = [render_email(view), render_email(view, preview=True), bundle['index.html']]
    for raw in pages:
        icons = Images(raw.decode()).icons
        assert {'compare', 'code', 'time'} <= {i['data-report-icon'] for i in icons}
        for icon in icons:
            assert icon['alt'] == '' and icon['aria-hidden'] == 'true'
            assert icon['data-icon-set'] == 'lucide'
            if icon['src'].startswith('data:image/png;base64,'):
                image = base64.b64decode(icon['src'].partition(',')[2], validate=True)
            else:
                assert raw == bundle['index.html'] and icon['src'].startswith('assets/')
                image = bundle[icon['src']]
            assert image[:8] == b'\x89PNG\r\n\x1a\n'
            pixels = 48 if icon['data-report-icon'].startswith('object-') else 96
            assert struct.unpack('>II', image[16:24]) == (pixels, pixels)
        assert len(raw) <= 200 * 1024


def test_type_icons_keep_table_and_column_counts_visible():
    run, plans = inputs()
    html = render_email(build_run_view(run, plans), preview=True).decode()
    assert any(icon['data-report-icon'] == 'code' for icon in Images(html).icons)
    assert 'Toplam DDL İşlemi' in html and 'Tablo' in html


def test_metric_icons_use_the_named_measure_and_its_theme_tone():
    run, plans = inputs()
    view = build_run_view(run, plans)
    view['proposal_catalog_known'] = True
    icons = Images(render_email(view, preview=True).decode()).icons
    expected = {'compare': ('file-diff', 'warning'),
                'code': ('file-code-corner', 'output'), 'scan': ('scan-search', 'info'),
                'document': ('file-exclamation-point', 'negative'), 'time': ('clock', 'info')}
    for role, (name, tone) in expected.items():
        matches = [icon for icon in icons if icon['data-report-icon'] == role]
        assert matches
        assert all(icon['data-icon-name'] == name and icon['data-tone'] == tone for icon in matches)


def test_table_column_and_total_boxes_have_matching_icons():
    run, plans = inputs()
    view = build_run_view(run, plans)
    view['ddl_types']['rows'] = [{'label': 'Tablo', 'count': 30}, {'label': 'Kolon', 'count': 5}]
    view['scan_scope']['rows'] = [{'label': 'Tablo', 'count': 100}]
    icons = Images(render_email(view, preview=True).decode()).icons
    names = {icon['data-report-icon']: icon['data-icon-name'] for icon in icons}
    assert names['object-table'] == 'table'
    assert names['object-column'] == 'columns-3'
    assert names['inventory'] == 'boxes'


def test_type_icons_keep_their_colored_surface_and_contrast_in_dark_mode():
    from oracle_db_migration_generator.reporting.icons import report_type_icon
    assets = files('oracle_db_migration_generator.reporting').joinpath('assets')
    catalog = json.loads(assets.joinpath('report-icons.json').read_text(encoding='utf-8'))
    def luminance(color):
        channels = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        linear = [value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4 for value in channels]
        return sum(value*weight for value, weight in zip(linear, (.2126, .7152, .0722)))
    def contrast(first, second):
        light, dark = sorted((luminance(first), luminance(second)), reverse=True)
        return (light+.05)/(dark+.05)
    for role, record in catalog['icons'].items():
        if not role.startswith('object-'):
            continue
        svg = ET.fromstring(assets.joinpath(f'report-icon-{role}-semantic.svg').read_bytes())
        background = svg.find('{http://www.w3.org/2000/svg}rect')
        assert background is not None, role
        assert background.get('fill') == record['background']
        assert contrast(record['color'], record['background']) >= 4.5, role
        assert contrast(record['background'], '#101827') >= 7, role
    icon = Images(str(report_type_icon('Tablo'))).icons[0]
    png = base64.b64decode(icon['src'].partition(',')[2])
    assert png == assets.joinpath('report-icon-object-table-semantic.png').read_bytes()


def test_every_visible_icon_uses_a_colored_asset_including_time_and_traceability():
    run, plans = inputs()
    icons = Images(render_email(build_run_view(run, plans), preview=True).decode()).icons
    assets = files('oracle_db_migration_generator.reporting').joinpath('assets')
    catalog = json.loads(assets.joinpath('report-icons.json').read_text(encoding='utf-8'))
    for role, record in catalog['icons'].items():
        channels = [int(record['color'][i:i+2], 16) for i in (1, 3, 5)]
        assert max(channels) - min(channels) >= 40, role
        assert record['tone'] != 'neutral', role
    for icon in icons:
        role = icon['data-report-icon']
        assert icon['data-tone'] != 'neutral', role
        assert base64.b64decode(icon['src'].partition(',')[2]) == assets.joinpath(f'report-icon-{role}-semantic.png').read_bytes()
