"""Schema Compare epostasının okunabilir tema ve etiket sözleşmesini sınar.

Örnek raporlar kullanır, Oracle veya posta sunucusuna bağlanmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
from html.parser import HTMLParser
import base64
from importlib.resources import files
import re

from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


class EmailElements(HTMLParser):
    """Görünür metinleri ve eposta hücrelerinin sabit boşluklarını toplar.

    Author: Mehmet KARACAN
    Date: 2026-11-07
    """
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def email(count=1):
    run, plans = inputs(count)
    view = build_run_view(run, plans)
    view['source_schemas'] = ['APP']
    return render_email(view, preview=True).decode()


def test_comparison_description_names_both_schema_roles_naturally():
    assert 'kaynak şeması ile' in email()
    assert 'hedef şemasının karşılaştırma sonuçları' in email()
    assert 'hedef şemalarının karşılaştırma sonuçları' in email(2)


def test_duration_has_a_physical_icon_gutter_without_relying_on_image_margin():
    tags = EmailElements(email()).tags
    gutters = [attrs for tag, attrs in tags if tag == 'td' and attrs.get('class') == 'timing-icon']
    assert len(gutters) == 1
    assert int(gutters[0]['width']) >= 28
    assert 'class="timing-summary"' in email()


def test_email_has_explicit_dark_colors_and_outlook_overrides():
    html = email()
    assert 'name="color-scheme" content="light dark"' in html
    assert 'name="supported-color-schemes" content="light dark"' in html
    assert '@media (prefers-color-scheme:dark)' in html
    assert '[data-ogsc] .mail-shell' in html
    assert 'class="brand-surface"' in html
    assert 'class="mail-muted"' in html
    # Açıklamalar silinerek kontrast sorunu gizlenmez.
    assert 'Kaynak ve İzlenebilirlik' in html
    assert 'Hazırlanan SQL veritabanına uygulanmadı.' in html


def test_mobile_details_stack_without_tiny_table_text_or_three_column_metrics():
    html = email()
    styles = ''.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S))
    assert '.detail-cell{display:block!important;width:100%!important' in styles
    assert '.metric{display:inline-block' not in styles
    assert '.metric-final' not in styles
    assert '.metric:last-child' not in styles
    assert 'font-size:10px' not in styles
    assert 'class="detail-cell"' in html


def test_helper_text_has_readable_contrast_on_both_actual_panel_colors():
    html = email()
    def luminance(color):
        channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    def contrast(first, second):
        high, low = sorted((luminance(first), luminance(second)), reverse=True)
        return (high + .05) / (low + .05)
    muted = re.search(r'\.mail-shell \.mail-muted[^{}]+\{color:(#[0-9A-F]{6})', html)[1]
    panel = re.search(r'\.mail-shell \.mail-panel[^{}]+\{background-color:(#[0-9A-F]{6})', html)[1]
    shell = re.search(r'\.mail-shell\{background-color:(#[0-9A-F]{6})', html)[1]
    assert contrast(muted, panel) >= 4.5
    assert contrast(muted, shell) >= 4.5
    cells = EmailElements(html).tags
    label = next(attrs for tag, attrs in cells if attrs.get('class') == 'scope-name')
    light_muted = re.search(r'color:(#[0-9A-F]{6})', label['style'])[1]
    light_panel = next(attrs['bgcolor'] for tag, attrs in cells if attrs.get('class') == 'scope-panel mail-panel')
    assert contrast(light_muted, light_panel) >= 4.5


def test_section_headings_have_a_physical_icon_gutter_in_every_mail_section():
    tags = EmailElements(email(2)).tags
    gutters = [attrs for tag, attrs in tags if tag == 'td' and attrs.get('class') == 'heading-icon']
    assert len(gutters) == 5
    assert all(int(attrs['width']) >= 32 for attrs in gutters)


def test_summary_grid_keeps_two_complete_columns_without_media_css():
    tags = EmailElements(email()).tags
    metrics = [attrs for tag, attrs in tags if tag == 'td' and 'metric' in attrs.get('class', '').split()]
    assert len(metrics) == 4
    assert all(attrs.get('width') == '50%' for attrs in metrics)
    assert 'Hedef Ortam' not in email()
    assert 'metric-context' not in email()
    assert sum(tag == 'tr' and attrs.get('class') == 'metric-row' for tag, attrs in tags) == 2
    labels = [attrs for tag, attrs in tags if tag == 'td' and attrs.get('class') == 'metric-label' and attrs.get('height')]
    assert len(labels) == 4
    assert all(int(attrs['height']) >= 36 for attrs in labels)


def test_email_logo_is_the_exact_original_corporate_file():
    import hashlib
    tags = EmailElements(email()).tags
    logo = next(attrs for tag, attrs in tags if tag == 'img' and attrs.get('alt') == 'İnnova')
    raw = base64.b64decode(logo['src'].partition(',')[2])
    original = files('oracle_db_migration_generator.reporting').joinpath('assets/innova-logo.png').read_bytes()
    assert raw == original
    assert hashlib.sha256(raw).hexdigest() == 'a2c9bf53db4c693d39ea8b746a6dd8a5866e592084976d04b8fbac6ab3539ad1'
    assert not any(effect in logo.get('style', '') for effect in ('filter', 'opacity', 'transform'))


def test_email_has_one_professional_visible_report_title():
    html = email()
    headings = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    assert headings == ['Schema Compare']
    assert '<title>Schema Compare</title>' in html


def test_header_uses_corporate_messaging_and_a_description_without_schema_cards():
    html = email(2)
    assert 'class="header-context"' not in html
    assert 'Daha akıllı' in html and 'Daha güçlü yarınlara' in html
    assert 'İnsan için teknoloji.' in html and 'Daha iyi bir gelecek.' in html
    assert 'class="comparison-description"' in html
    assert html.index('<h1') < html.index('class="comparison-description"') < html.index('class="timing-summary"')
    assert html.count('kaynak şeması ile') == 1
