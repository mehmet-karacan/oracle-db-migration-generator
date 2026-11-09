"""Şema Karşılaştırma ayrıntı sayımlarını ve statik SQL görüntülemesini sınar.

Sentetik arşiv kullanılır. Oracle, Jenkins veya mail bağlantısı açılmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
from copy import deepcopy
from html.parser import HTMLParser
import json
import re
import pytest

from oracle_db_migration_generator.reporting.render import render_reports, render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_bundle import make_plan
from tests.unit.test_report_views import inputs


class PreText(HTMLParser):
    def __init__(self, raw):
        super().__init__(); self.text=[]; self.inside=False; self.feed(raw)
    def handle_starttag(self, tag, attrs):
        if tag=='pre': self.inside=True
    def handle_endtag(self, tag):
        if tag=='pre': self.inside=False
    def handle_data(self, text):
        if self.inside: self.text.append(text)


def test_run_target_counts_use_catalog_metrics_and_show_ddl_type_distribution():
    run,plans=inputs()
    plan=plans['TARGET-000']; base=deepcopy(plan['operations'][0])
    plan['operations'].extend([{**deepcopy(base),'id':'op-review','decision':'REVIEW_REQUIRED','sql':None},
                               {**deepcopy(base),'id':'op-missing','decision':'BLOCKED','sql':None}])
    plan['counts'].update(ready_operations=1,review_operations=1,blocked_operations=1)
    view=build_run_view(run,plans,proposal_ids={'TARGET-000':{'op-review'}})
    html=render_run_reports(view)['index.html'].decode()
    assert 'data-metric="generated"' in html and 'data-metric="missing"' in html
    assert 'Üretilemeyen DDL' not in html
    assert 'Üretilen DDL türleri' in html
    assert view['targets'][0]['generated_ddl_count']==2 and view['targets'][0]['missing_ddl_count']==1


def test_detail_restores_proposals_and_source_paths_when_refreshing_old_archive():
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    op=document['operations'][0]; op.update(decision='REVIEW_REQUIRED',sql=None)
    document['counts'].update(ready_operations=0,review_operations=1,blocked_operations=0)
    proposal='proposals/APP/TABLE/T/'+op['id']+'.sql'
    source='source-ddl/APP/TABLE/T/source.sql'
    payload={proposal:b'ALTER TABLE "APP"."T" ADD ("ID" NUMBER);\n',source:b'CREATE TABLE "APP"."T" ("ID" NUMBER);\n',
             'source-ddl/index.json':json.dumps({'plan_id':document['plan_id'],'objects':[
                 {'path':source,'operation_ids':[op['id']]}]}).encode()}
    before=deepcopy((document,payload))
    pages=render_reports(document,payload)
    html=pages['index.html'].decode()
    assert 'DDL Dosyası Eksik' in html and 'data-metric="missing"' in html
    assert 'Önerilen DDL' in html and 'Kaynak DDL' in html
    assert re.search(r'href="sql/[a-f0-9]+-0001.html"',html)
    assert any(name.startswith('sql/') for name in pages)
    assert (document,payload)==before


def test_sql_viewer_keeps_all_long_text_escaped_and_does_not_execute_sql():
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    path='objects/APP/TABLE/T/ddl.sql'
    document['operations'][0]['sql']={'path':path}
    sql=('-- <script> & "quoted"\r\n'+'ş'*1000+';\r\n')*160
    payload={path:sql.encode()}
    pages=render_reports(document,payload)
    viewers=sorted((name,raw) for name,raw in pages.items() if name.startswith('sql/'))
    assert len(viewers)>1
    assert ''.join(''.join(PreText(raw.decode()).text) for _,raw in viewers)==sql
    assert all(len(raw)<=200*1024 and b'<script>' not in raw for _,raw in viewers)
    assert all('DDL Görüntüleyici' in raw.decode() and 'SQL Dosyasını İndir' in raw.decode() for _,raw in viewers)
    assert payload[path]==sql.encode()


def test_object_directory_groups_operations_and_uses_script_free_filters():
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    second=deepcopy(document['operations'][0]); second['id']='op-another'
    document['operations'].append(second)
    html=render_reports(document,{})['changes/page-0001.html'].decode()
    assert html.count('class="object-entry"')==1
    assert 'Bu Sayfayı Filtrele' in html and 'Nesne Bul' in html
    assert 'type="radio"' in html and 'Ctrl+F' in html
    assert 'aria-current="page"' in html and '<script' not in html
    assert all(op['id'] in html for op in document['operations'])


def test_web_reports_have_consistent_context_and_dark_theme(monkeypatch):
    monkeypatch.setenv('GENERATOR_REPORT_SOURCE_ENVIRONMENT','UAT')
    monkeypatch.setenv('GENERATOR_REPORT_TARGET_ENVIRONMENT','PROD')
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    from tests.factories import source, actual, profile
    from oracle_db_migration_generator.reporting.inventory import build_scan_summary
    selected=profile()
    summary=build_scan_summary(source('CREATE TABLE APP.T(ID NUMBER);',selected),actual('',selected),selected.policy,document)
    pages=render_reports(document,{'scan-summary.json':json.dumps(summary).encode()})
    html=pages['index.html'].decode()
    assert 'APP - UAT' in html and 'APP - PROD' in html
    assert 'Karşılaştırma raporu</p>' not in html
    assert 'Üretilen DDL türleri' in html
    assert 'prefers-color-scheme:dark' in pages['assets/report.css'].decode()
    assert '.report-back{display:none}' not in pages['assets/report.css'].decode()


@pytest.mark.parametrize('path',['../outside.sql','https://elsewhere.invalid/a.sql','/absolute.sql','folder\\file.sql'])
def test_sql_viewer_rejects_paths_outside_the_current_bundle(path):
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    document['operations'][0]['sql']={'path':path}
    with pytest.raises(ValueError,match='REPORT_SQL_PATH_UNSAFE'):
        render_reports(document,{path:b'SELECT 1 FROM dual;'})


@pytest.mark.parametrize('field,value',[
    ('target_id','another-target'),
    ('source_commit','another-source'),
    ('run_href','../../another-run/index.html'),
])
def test_report_return_context_cannot_cross_target_or_source(field,value):
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    context={'target_id':document['target']['id'],
             'source_commit':document['source']['commit_sha'],'run_href':'../../index.html'}
    context[field]=value
    with pytest.raises(ValueError,match='REPORT_DISPLAY_CONTEXT_MISMATCH'):
        render_reports(document,{},report_context=context)


def test_report_return_context_keeps_the_current_run_link():
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    context={'target_id':document['target']['id'],
             'source_commit':document['source']['commit_sha'],'run_href':'../../index.html'}
    html=render_reports(document,{},report_context=context)['index.html'].decode()
    assert 'href="../../index.html"' in html and 'Çalışma Özetine Dön' in html


def test_ambient_jenkins_build_does_not_change_immutable_plan_pages(monkeypatch):
    document=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    monkeypatch.delenv('BUILD_URL',raising=False)
    monkeypatch.delenv('BUILD_NUMBER',raising=False)
    before=render_reports(document,{})
    monkeypatch.setenv('BUILD_URL','https://jenkins.example/job/generator/42/')
    monkeypatch.setenv('BUILD_NUMBER','42')
    after=render_reports(document,{})
    assert set(after)==set(before)
    assert [name for name in before if after[name]!=before[name]]==[]
    assert 'jenkins.example' not in after['index.html'].decode()
