"""Şema Karşılaştırma logosunun ayrı açık zeminde ve değişmeden gösterilmesini sınar.

Örnek rapor kullanır, gerçek mail göndermez veya Outlook'a bağlanmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
import base64
from html.parser import HTMLParser
from importlib.resources import files
import struct
import zlib

from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


class LogoSurface(HTMLParser):
    """Logo görselini, zemin hücresini ve Outlook koşullu işaretlemesini toplar.

    Author: Mehmet KARACAN
    Date: 2026-11-07
    """
    def __init__(self, html):
        super().__init__()
        self.surfaces = []
        self.logos = []
        self.comments = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'td' and attrs.get('class') == 'brand-surface':
            self.surfaces.append(attrs)
        if tag == 'img' and attrs.get('alt') == 'İnnova':
            self.logos.append(attrs)

    def handle_comment(self, comment):
        self.comments.append(comment)


def rendered():
    run, plans = inputs()
    return render_email(build_run_view(run, plans), preview=True).decode()


def test_logo_background_is_a_separate_embedded_light_tile():
    parsed = LogoSurface(rendered())
    assert len(parsed.surfaces) == len(parsed.logos) == 1
    surface = parsed.surfaces[0]
    assert surface.get('background', '').startswith('data:image/png;base64,')
    tile = base64.b64decode(surface['background'].partition(',')[2], validate=True)
    assert tile == files('oracle_db_migration_generator.reporting').joinpath('assets/brand-surface-light.png').read_bytes()
    assert len(tile) < 256
    assert struct.unpack('>II', tile[16:24]) == (1, 1)
    assert tile[24:26] == bytes((8, 2))
    offset, content = 8, []
    while offset < len(tile):
        length = int.from_bytes(tile[offset:offset+4], 'big')
        if tile[offset+4:offset+8] == b'IDAT':
            content.append(tile[offset+8:offset+8+length])
        offset += length + 12
    assert zlib.decompress(b''.join(content)) == bytes((0, 245, 245, 245))
    original = files('oracle_db_migration_generator.reporting').joinpath('assets/innova-logo.png').read_bytes()
    assert base64.b64decode(parsed.logos[0]['src'].partition(',')[2]) == original
    assert tile != original


def test_logo_surface_has_modern_and_classic_outlook_fallbacks():
    parsed = LogoSurface(rendered())
    surface = parsed.surfaces[0]
    assert 'background-image:url(' in surface['style']
    assert 'linear-gradient(#F5F5F5,#F5F5F5)' in surface['style']
    comments = '\n'.join(parsed.comments)
    assert '<v:rect' in comments and '<v:fill type="tile"' in comments
    assert 'width:132pt;height:34.5pt' in comments
    assert surface['background'] in comments
    assert '<v:textbox' in comments and '</v:textbox>' in comments
