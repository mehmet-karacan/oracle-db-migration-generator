from html.parser import HTMLParser

from tests.unit.test_bundle import make_plan
from oracle_db_migration_generator.artifacts.bundle import write_bundle
from oracle_db_migration_generator.runtime.aggregate import aggregate_run
from tools.jenkins_notification import write_notification


class Links(HTMLParser):
    def __init__(self,html):
        super().__init__();self.rows=[];self.current=None;self.feed(html)
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.current={'attrs':dict(attrs),'text':''}
    def handle_data(self,data):
        if self.current is not None:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:
            self.rows.append(self.current);self.current=None


def test_jenkins_general_sql_opens_in_view_and_downloads_use_native_file_page(tmp_path):
    root=tmp_path/'run';destination=root/'targets/DEMO-TEST'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),destination)
    sql=(destination/'migration.sql').read_bytes()
    job='https://jenkins.example.invalid/job/generator/';build=job+'46/'
    run=aggregate_run(root,build_number=46,build_url=build)
    write_notification(root,run,build,job)
    links=Links((root/'index.html').read_text(encoding='utf-8')).rows
    view=next(link for link in links if link['text']=='Genel DDL’i görüntüle')
    files=next(link for link in links if link['text']=='DDL dosyalarını indir')
    base=build+'artifact/output/runs/build-46/targets/DEMO-TEST/'
    assert view['attrs']['href']==base+'migration.sql/*view*/'
    assert files['attrs']['href']==base
    assert (destination/'migration.sql').read_bytes()==sql
    assert 'Oracle Şema Karşılaştırma' in (root/'index.html').read_text(encoding='utf-8')


def test_offline_report_keeps_portable_sql_download_link(tmp_path):
    root=tmp_path/'run'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),root/'targets/DEMO-TEST')
    aggregate_run(root)
    links=Links((root/'index.html').read_text(encoding='utf-8')).rows
    sql=next(link for link in links if link['attrs']['href']=='targets/DEMO-TEST/migration.sql')
    assert 'download' in sql['attrs']
    assert not any('/*view*/' in link['attrs']['href'] for link in links)
