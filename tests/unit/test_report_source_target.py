"""Şema Karşılaştırma HTML alan farklarını kayıtlı sentetik planlarla sınar.

Oracle ve Jenkins bağlantısı açılmaz. Kaynak ve hedef yönü, eksik bilgi,
nesne ayrımı ve uzun metnin eksiksiz gösterimi kontrol edilir.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from copy import deepcopy
from html.parser import HTMLParser
import json
import re
import pytest

from oracle_db_migration_generator.reporting.render import render_reports
from tests.unit.test_bundle import make_plan


class ComparisonRows(HTMLParser):
    def __init__(self,raw):
        super().__init__()
        self.rows=[]
        self.row=None
        self.side=None
        self.feed(raw)

    def handle_starttag(self,tag,attrs):
        attributes=dict(attrs)
        if tag=='tr' and 'data-change-id' in attributes:
            self.row={'id':attributes['data-change-id'],'source':'','target':''}
            self.rows.append(self.row)
        if tag=='pre' and self.row is not None:
            self.side=attributes.get('data-side')

    def handle_endtag(self,tag):
        if tag=='pre':self.side=None
        if tag=='tr':self.row=None

    def handle_data(self,text):
        if self.side in {'source','target'} and self.row is not None:
            self.row[self.side]+=text


def sample():
    plan=make_plan('CREATE TABLE APP.T(C VARCHAR2(80 CHAR));',
                   'CREATE TABLE APP.T(C VARCHAR2(20 BYTE));').to_dict()
    row=deepcopy(plan['differences'][0])
    row.update(id='diff-length',property_path='/columns/C/length',kind='CHANGED',
               before={'state':'KNOWN','value':20},after={'state':'KNOWN','value':80})
    plan['differences']=[row]
    for op in plan['operations']:op['change_ids']=[row['id']]
    return plan


def comparison_pages(pages):
    return {name:raw.decode() for name,raw in pages.items()
            if name.startswith('comparison/') and not name.startswith('comparison/index-')}


def test_html_shows_source_after_and_target_before_under_the_same_field():
    plan=sample()
    pages=render_reports(plan,{})
    html=''.join(comparison_pages(pages).values())
    assert 'Kaynak ve Hedef Karşılaştırması' in html
    assert 'Kolon C' in html and 'Uzunluk' in html and 'Özellikleri Farklı' in html
    rows=ComparisonRows(html).rows
    assert rows==[{'id':'diff-length','source':'80','target':'20'}]
    assert 'Kaynak ve Hedefi Karşılaştır' in pages['index.html'].decode()
    assert 'data-change-id="diff-length"' in pages['changes/page-0001.html'].decode()


def test_html_keeps_unknown_absent_null_empty_and_false_distinct():
    plan=sample()
    values=[('unknown','UNKNOWN',None,'Bilgi Doğrulanamadı'),
            ('absent','ABSENT',None,'Alan Bulunmuyor'),
            ('null','KNOWN',None,'NULL'),('empty','KNOWN','','Boş Metin'),
            ('false','KNOWN',False,'Hayır'),
            ('na','NOT_APPLICABLE',None,'Uygulanamaz')]
    base=plan['differences'][0]
    plan['differences']=[{**deepcopy(base),'id':key,'property_path':'/columns/C/'+key,
        'after':{'state':state,'value':value}} for key,state,value,_ in values]
    plan['operations'][0]['change_ids']=[row['id'] for row in plan['differences']]
    rows=ComparisonRows(''.join(comparison_pages(render_reports(plan,{})).values())).rows
    assert {row['id']:row['source'] for row in rows}=={key:label for key,_,_,label in values}


def test_shared_operations_do_not_repeat_differences_and_orphan_rows_remain_reachable():
    plan=sample()
    op=deepcopy(plan['operations'][0]);op['id']='another-operation'
    plan['operations'].append(op)
    extra=deepcopy(plan['differences'][0]);extra.update(id='orphan',object_key='f'*64)
    plan['differences'].append(extra)
    before=deepcopy(plan)
    pages=render_reports(plan,{})
    rows=[row for html in comparison_pages(pages).values() for row in ComparisonRows(html).rows]
    assert sorted(row['id'] for row in rows)==['diff-length','orphan']
    assert 'comparison/index-0001.html' in pages
    assert 'Tüm Kaynak ve Hedef Farkları' in pages['index.html'].decode()
    assert plan==before


def test_same_named_objects_in_different_schemas_never_share_values():
    from oracle_db_migration_generator.model.identity import Identifier,ObjectIdentity
    plan=sample();obj=plan['operations'][0]['object']
    other=deepcopy(plan['operations'][0]);other['id']='other-schema'
    other['object']['owner']='OTHER'
    key=ObjectIdentity(obj['profile_id'],Identifier.parse('OTHER'),obj['object_type'],
                       Identifier.parse(obj['name']),obj.get('parent_key')).key
    row=deepcopy(plan['differences'][0]);row.update(id='diff-other',object_key=key,
                        after={'state':'KNOWN','value':999})
    other['change_ids']=[row['id']]
    plan['operations'].append(other);plan['differences'].append(row)
    pages=comparison_pages(render_reports(plan,{}))
    app=next(html for html in pages.values() if 'APP.T' in html)
    other=next(html for html in pages.values() if 'OTHER.T' in html)
    assert 'diff-length' in app and 'diff-other' not in app
    assert 'diff-other' in other and 'diff-length' not in other


def test_long_values_are_escaped_bounded_complete_and_inputs_unchanged():
    plan=sample();row=plan['differences'][0]
    text='ş<script>&"\n'*6000
    row['property_path']='/definition'
    row['after']={'state':'KNOWN','value':text}
    before=deepcopy(plan)
    pages=render_reports(plan,{})
    comparisons=comparison_pages(pages)
    assert len(comparisons)>1
    rows=[row for _,html in sorted(comparisons.items()) for row in ComparisonRows(html).rows]
    assert ''.join(row['source'] for row in rows)==text
    assert all(len(raw)<=200*1024 for name,raw in pages.items() if name.endswith('.html'))
    assert all('<script>' not in html and '<script ' not in html for html in comparisons.values())
    assert plan==before


def test_sql_token_metadata_is_readable_without_changing_the_plan():
    plan=sample();row=plan['differences'][0]
    row['property_path']='/columns/C/default'
    row['after']={'state':'KNOWN','value':json.dumps([['code','COALESCE'],['code','('],
        ['quoted','a"b'],['code',','],['literal',"'X'"],['code',')']])}
    rows=ComparisonRows(''.join(comparison_pages(render_reports(plan,{})).values())).rows
    assert rows[0]['source']=='COALESCE ("a""b", \'X\')'


def test_comment_that_looks_like_sql_tokens_remains_literal_text():
    plan=sample();row=plan['differences'][0]
    text='[["code","EXPECTED_LITERAL_TEXT"]]'
    row['property_path']='/text';row['after']={'state':'KNOWN','value':text}
    rows=ComparisonRows(''.join(comparison_pages(render_reports(plan,{})).values())).rows
    assert rows[0]['source']==text


def test_values_beginning_with_a_newline_have_a_child_element_inside_pre():
    plan=sample();row=plan['differences'][0]
    row['property_path']='/text';row['after']={'state':'KNOWN','value':'\nFirst Line'}
    html=''.join(comparison_pages(render_reports(plan,{})).values())
    assert '<pre data-side="source"><code>\nFirst Line</code></pre>' in html


def test_comparison_returns_to_the_page_containing_its_object_operations():
    plan=sample();base=plan['operations'][0]
    plan['operations']=[]
    for number in range(101):
        op=deepcopy(base);op['id']=f'op-{number:03d}'
        op['object']['name']=f'T{number:03d}'
        plan['operations'].append(op)
    pages=render_reports(plan,{})
    html=next(html for html in comparison_pages(pages).values() if 'APP.T100' in html)
    operation_page=next(name for name,raw in pages.items()
                        if name.startswith('changes/') and b'op-100</p>' in raw)
    assert re.search(r'href="../'+re.escape(operation_page)+r'#object-[a-f0-9]+"',html)


def test_constraint_sql_properties_are_decoded_from_real_canonical_differences():
    plan=make_plan('CREATE TABLE APP.T(C NUMBER, CONSTRAINT CK CHECK(C>0) ENABLE);',
                   'CREATE TABLE APP.T(C NUMBER, CONSTRAINT CK CHECK(C>0) DISABLE);').to_dict()
    change=next(row for row in plan['differences'] if row['property_path']=='/constraints/CK/enabled')
    rows=ComparisonRows(''.join(comparison_pages(render_reports(plan,{})).values())).rows
    row=next(row for row in rows if row['id']==change['id'])
    assert row['source']=='ENABLE' and row['target']=='DISABLE'


def test_index_column_list_decodes_each_tokenized_entry():
    plan=sample();row=plan['differences'][0]
    row['property_path']='/index/keys'
    row['after']={'state':'KNOWN','value':[json.dumps([['quoted','Code'],['code','DESC']]),
        json.dumps([['code','LENGTH'],['code','('],['code','C'],['code',')']])]}
    rows=ComparisonRows(''.join(comparison_pages(render_reports(plan,{})).values())).rows
    assert json.loads(rows[0]['source'])==['"Code" DESC','LENGTH (C)']


@pytest.mark.parametrize('key',['../../outside','/absolute','invalid-key'])
def test_comparison_rejects_noncanonical_keys_before_creating_paths(key):
    plan=sample();plan['differences'][0]['object_key']=key
    with pytest.raises(ValueError,match='REPORT_COMPARISON_KEY_INVALID'):
        render_reports(plan,{})
