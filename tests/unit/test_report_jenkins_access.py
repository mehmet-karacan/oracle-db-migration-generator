"""Schema Compare raporlarının aynı Jenkins çalışmasının SQL arşivine bağlanmasını sınar.

Testler örnek dosya arşivleri kullanır, gerçek Jenkins veya Oracle çağrısı yapmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
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
    assert 'Schema Compare' in (root/'index.html').read_text(encoding='utf-8')


def test_email_has_one_report_and_ddl_link_to_the_same_build(tmp_path):
    root=tmp_path/'run'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),root/'targets/DEMO-TEST')
    job='https://jenkins.example.invalid/job/generator/'
    build=job+'46/'
    run=aggregate_run(root,build_number=46,build_url=build)
    mail=write_notification(root,run,build,job)
    links=Links(mail.read_text(encoding='utf-8')).rows
    assert len(links)==1
    assert links[0]['text'].strip()=='Raporu ve DDL Dosyalarını Aç'
    assert links[0]['attrs']['href']==build+'artifact/output/runs/build-46/index.html'


def test_local_email_without_jenkins_archive_does_not_invent_an_sql_url():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    from tests.unit.test_report_views import inputs
    run,plans=inputs()
    links=Links(render_email(build_run_view(run,plans),preview=True).decode()).rows
    assert not any(link['text'].strip()=='Genel DDL' for link in links)


def test_email_uses_one_report_link_for_multiple_targets():
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    from tests.unit.test_report_views import inputs
    run,plans=inputs(6)
    view=build_run_view(run,plans)
    for target in view['targets']:
        target['aggregate_view_path']='https://jenkins.example.invalid/job/generator/46/artifact/output/runs/build-46/targets/'+target['id']+'/migration.sql/*view*/'
    view['link']='https://jenkins.example.invalid/job/generator/46/artifact/output/runs/build-46/index.html'
    links=Links(render_email(view,preview=True).decode()).rows
    assert len(links)==1
    assert links[0]['attrs']['href']==view['link']
    assert links[0]['text'].strip()=='Raporu ve DDL Dosyalarını Aç'


def test_offline_report_keeps_portable_sql_download_link(tmp_path):
    root=tmp_path/'run'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),root/'targets/DEMO-TEST')
    aggregate_run(root)
    links=Links((root/'index.html').read_text(encoding='utf-8')).rows
    sql=next(link for link in links if link['attrs']['href']=='targets/DEMO-TEST/migration.sql')
    assert 'download' in sql['attrs']
    assert not any('/*view*/' in link['attrs']['href'] for link in links)


def test_jenkins_configured_environment_names_match_approved_mail(tmp_path, monkeypatch):
    from tests.factories import source, actual, profile
    from oracle_db_migration_generator.reporting.inventory import build_scan_summary
    root=tmp_path/'run'
    sql='CREATE TABLE APP.T(ID NUMBER);'
    selected=profile()
    desired=source(sql,selected)
    target=actual('',selected)
    plan=make_plan(sql)
    summary=build_scan_summary(desired,target,selected.policy,plan)
    write_bundle(plan,root/'targets/DEMO-TEST',scan_summary=summary)
    job='https://jenkins.example.invalid/job/generator/'
    build=job+'46/'
    run=aggregate_run(root,build_number=46,build_url=build)
    before=(root/'targets/DEMO-TEST/migration.sql').read_bytes()
    monkeypatch.setenv('GENERATOR_REPORT_SOURCE_ENVIRONMENT','UAT')
    monkeypatch.setenv('GENERATOR_REPORT_TARGET_ENVIRONMENT','PROD')
    mail=write_notification(root,run,build,job)
    html=mail.read_text(encoding='utf-8')
    assert '<strong>APP - UAT</strong>' in html
    assert '<strong>APP - PROD</strong>' in html
    assert (root/'targets/DEMO-TEST/migration.sql').read_bytes()==before
    assert run['source_commit'] in html


def test_jenkins_rejects_half_configured_environment_names(tmp_path, monkeypatch):
    import pytest
    root=tmp_path/'run'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),root/'targets/DEMO-TEST')
    job='https://jenkins.example.invalid/job/generator/'
    run=aggregate_run(root,build_number=46,build_url=job+'46/')
    monkeypatch.setenv('GENERATOR_REPORT_SOURCE_ENVIRONMENT','UAT')
    monkeypatch.delenv('GENERATOR_REPORT_TARGET_ENVIRONMENT',raising=False)
    with pytest.raises(ValueError,match='REPORT_ENVIRONMENT_CONFIGURATION_INCOMPLETE'):
        write_notification(root,run,job+'46/',job)
