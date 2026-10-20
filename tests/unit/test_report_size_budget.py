from copy import deepcopy
import re

from oracle_db_migration_generator.reporting.render import render_reports
from tests.unit.test_bundle import make_plan


def document(count=1):
    result=make_plan('CREATE TABLE APP.T(ID NUMBER);').to_dict()
    base=result['operations'][0]
    result['operations']=[{**deepcopy(base),'id':f'op-size-{i:04d}','sql':None} for i in range(count)]
    return result


def html_pages(result):
    return {name:raw.decode() for name,raw in result.items() if name.endswith('.html')}


def test_unicode_rows_paginate_by_bytes_without_losing_or_repeating_operations():
    plan=document(125)
    for op in plan['operations']:
        op['reason_tr']='İşlem açıklaması <script>alert(1)</script> ' * 350
    before=deepcopy(plan)
    pages=html_pages(render_reports(plan,{}))
    changes={name:html for name,html in pages.items() if name.startswith('changes/')}
    assert len(changes)>2
    seen=[]
    for html in changes.values():
        assert len(html.encode())<=200*1024
        ids=re.findall(r'<p class="wrap">(op-size-\d+)</p>',html)
        assert 1<=len(ids)<=100
        seen.extend(ids)
        assert '<script>' not in html and '&lt;script&gt;' in html
        assert len(re.findall(r'href="../changes/page-',html))<=9
    assert sorted(seen)==[op['id'] for op in plan['operations']]
    assert len(pages['index.html'].encode())<=200*1024
    assert plan==before


def test_single_huge_operation_and_warning_previews_keep_complete_json_link():
    plan=document();op=plan['operations'][0]
    op['reason_tr']='ş<script>x</script>'*30000
    op['depends_on']=[f'dependency-{i}' for i in range(100)]
    op['evidence_ids']=[f'evidence-{i}' for i in range(100)]
    op['reason_codes']=[f'REASON_{i}' for i in range(100)]
    plan['warnings']=['LONG: '+('ü<script>w</script>'*20000) for _ in range(25)]
    before=deepcopy(plan)
    for html in html_pages(render_reports(plan,{})).values():
        assert len(html.encode())<=200*1024
        assert '<script>' not in html and '&lt;script&gt;' in html
        assert '92 ek bağımlılık' in html and '92 ek kanıt' in html and '92 ek neden kodu' in html
        assert '5 ek uyarının' in html
        assert 'karakter' in html and 'plan.json' in html
    assert plan==before


def test_small_reports_keep_complete_fields_and_first_five_summary():
    plan=document(6)
    for op in plan['operations']:
        op.update(reason_tr='Eksiksiz açıklama',depends_on=['dep-a','dep-b'],evidence_ids=['ev-a','ev-b'],reason_codes=['CODE_A','CODE_B'])
    pages=html_pages(render_reports(plan,{}))
    assert len(re.findall(r'<article>',pages['index.html']))==5
    assert len(re.findall(r'<article>',pages['changes/page-0001.html']))==6
    assert 'dep-a, dep-b' in pages['index.html'] and 'ev-a, ev-b' in pages['index.html']
    assert 'CODE_A · CODE_B' in pages['index.html'] and 'Eksiksiz açıklama' in pages['index.html']
    assert not re.search(r'\d+ ek bağımlılık',pages['index.html'])


def test_single_operation_that_fits_budget_is_not_truncated():
    plan=document();plan['operations'][0]['reason_tr']='A'*195000+'UNCHANGED_END'
    pages=html_pages(render_reports(plan,{}))
    assert all('UNCHANGED_END' in html and 'ek karakter' not in html for html in pages.values())


def test_empty_plan_with_large_warnings_still_has_bounded_pages():
    plan=document(0);plan['warnings']=['WARNING: '+('ş'*300000)]
    pages=html_pages(render_reports(plan,{}))
    assert len(pages)==2
    assert all(len(html.encode())<=200*1024 and '299.753 ek karakter' in html for html in pages.values())
