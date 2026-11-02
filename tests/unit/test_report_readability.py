"""Oracle DB Migration Generator raporunun okunabilir metnini sınar.

Sentetik plan kullanılır. Veritabanına bağlanılmaz.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from dataclasses import replace
from html.parser import HTMLParser

from oracle_db_migration_generator.reporting.render import render_reports
from tests.unit.test_bundle import make_plan


def visible_text(raw):
    class Visible(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hidden=0
            self.parts=[]

        def handle_starttag(self,tag,attrs):
            if tag in {'details','style','pre'}:
                self.hidden+=1

        def handle_endtag(self,tag):
            if tag in {'details','style','pre'}:
                self.hidden-=1

        def handle_data(self,data):
            if not self.hidden:
                self.parts.append(data)

    parser=Visible()
    parser.feed(raw.decode('utf-8'))
    return ' '.join(parser.parts)


def test_report_keeps_summary_readable_and_warnings_collapsed():
    plan=make_plan('CREATE TABLE APP.T(C DATE);','CREATE TABLE APP.T(C NUMBER);')
    plan=replace(plan,warnings=(
        'TARGET_INVALID_OBJECT: APP.BROKEN [PROCEDURE] · PLS-00103',
        'PHYSICAL_STORAGE_PRESERVED: APP.T · Mevcut LOB ayarları korunacak.',
    ))
    html=render_reports(plan.to_dict(),{})['index.html']
    text=visible_text(html)
    assert 'Şema karşılaştırması' in text
    assert 'Kaynakta incelenen nesne' in text
    assert b'>Uyar' in html
    assert 'APP.BROKEN' not in text
    assert not any(character in text for character in ('→','—',';',':'))
    assert b'<details' in html
