from copy import deepcopy
from dataclasses import replace
import json
import re

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle,verify_bundle
from oracle_db_migration_generator.artifacts.layout import object_folder
from oracle_db_migration_generator.config.loader import ConfigError,validate_document
from oracle_db_migration_generator.reporting.render import render_email,render_reports,render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_bundle import make_plan


def commented_plan():
    return make_plan("CREATE TABLE APP.ORDERS(ID NUMBER); COMMENT ON TABLE APP.ORDERS IS 'Orders'; COMMENT ON COLUMN APP.ORDERS.ID IS 'Key'; GRANT SELECT ON APP.ORDERS TO READER;")


def run_view(plan):
    document=plan.to_dict();document['target'].update(name='PROD',schemas=['TTBP'])
    target=document['target']['id']
    run={'run_id':'labels','source_commit':'a'*40,'finished_at':'2026-10-20T12:00:00Z','status':'PARTIAL',
         'targets':[{'id':target,'status':document['status'],'difference_count':4,'plan_id':document['plan_id'],
                     'plan_path':f'targets/{target}/plan.json','error_code':None}]}
    return build_run_view(run,{target:document})


def test_sidecar_display_fact_uses_parent_without_changing_identity_or_sql(tmp_path):
    plan=commented_plan()
    sidecars=[op for op in plan.operations if op.identity.object_type in {'COMMENT','GRANT'}]
    assert len(sidecars)==3
    assert sorted(op.to_dict()['object'].get('display_name','') for op in sidecars)==['ORDERS','ORDERS','ORDERS.ID']
    for op in sidecars:
        assert op.identity.name.effective_name.startswith('S_')
        assert op.to_dict()['object']['name']==op.identity.name.effective_name
        without=replace(op,display_name=None)
        assert without.operation_id==op.operation_id and object_folder(without.to_dict()['object'])==object_folder(op.to_dict()['object'])
        assert without.intent==op.intent and without.decision==op.decision
    output=tmp_path/'bundle';write_bundle(plan,output);assert verify_bundle(output)['status']=='VERIFIED'
    stored=json.loads((output/'plan.json').read_bytes())
    assert any(op['object'].get('display_name')=='ORDERS.ID' for op in stored['operations'])
    markdown='\n'.join(p.read_text(encoding='utf-8') for p in output.rglob('README.md'))
    assert 'APP.ORDERS.ID' in markdown
    assert not any(('APP.'+op.identity.name.effective_name) in markdown for op in sidecars)


def test_all_human_reports_use_parent_labels_and_production_target_name():
    plan=commented_plan();view=run_view(plan);before=deepcopy(view)
    assert view['important_objects'][0]['target_label']=='PROD (TTBP)'
    pages={**render_reports(plan.to_dict(),{}),**{'run/'+k:v for k,v in render_run_reports(view).items()}}
    pages['mail.html']=render_email(view)
    for name,raw in pages.items():
        if not name.endswith('.html'):continue
        html=raw.decode()
        if 'changes/' in name or name in {'index.html','run/index.html','mail.html'}:
            assert 'APP.ORDERS.ID' in html
        assert not any(('APP.'+op.identity.name.effective_name) in html for op in plan.operations if op.identity.object_type in {'COMMENT','GRANT'})
    assert re.search(r'<strong[^>]*>PROD</strong>',pages['run/index.html'].decode())
    assert 'TTBP' in pages['run/index.html'].decode()
    assert view==before


def test_legacy_unresolved_comment_has_clear_label_and_evidence_link():
    document=commented_plan().to_dict()
    document['operations']=[op for op in document['operations'] if op['object']['object_type']=='COMMENT'][:1]
    document['operations'][0]['object'].pop('display_name',None)
    html=render_reports(document,{})['index.html'].decode()
    assert 'Açıklama (bağlı nesne doğrulanamadı)' in html
    assert 'href="plan.json"' in html
    assert ('APP.'+document['operations'][0]['object']['name']) not in html


def test_optional_display_name_contract_remains_closed_and_accepts_legacy_plans():
    document=commented_plan().to_dict()
    for op in document['operations']:
        if op['object']['object_type']=='COMMENT':op['object']['display_name']='ORDERS.ID'
    validate_document(document,'plan.schema.json')
    legacy=deepcopy(document)
    for op in legacy['operations']:op['object'].pop('display_name',None)
    validate_document(legacy,'plan.schema.json')
    document['operations'][0]['object']['unexpected_display']=True
    with pytest.raises(ConfigError):validate_document(document,'plan.schema.json')


def test_quoted_sidecar_parent_label_is_escaped_in_html_and_markdown(tmp_path):
    plan=make_plan('CREATE TABLE APP."Order<script>" ("Key<script>" NUMBER); COMMENT ON COLUMN APP."Order<script>"."Key<script>" IS \'Key\';')
    comment=next(op for op in plan.operations if op.identity.object_type=='COMMENT')
    assert comment.to_dict()['object']['display_name']=='Order<script>.Key<script>'
    output=tmp_path/'quoted';write_bundle(plan,output)
    html=(output/'index.html').read_text(encoding='utf-8')
    assert 'APP.Order&lt;script&gt;.Key&lt;script&gt;' in html and '<script>' not in html
    markdown=(output/'README.md').read_text(encoding='utf-8')
    assert 'APP.Order&#60;script&#62;.Key&#60;script&#62;' in markdown


def test_unknown_parent_fact_does_not_create_a_display_name():
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.model.snapshot import KnownValue
    from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
    from tests.factories import source,actual,profile
    selected=profile();desired=source("CREATE TABLE APP.T(ID NUMBER); COMMENT ON TABLE APP.T IS 'Text';")
    comment=next(obj for obj in desired.objects if obj.identity.object_type=='COMMENT')
    unknown=replace(comment,properties={**comment.properties,'target':KnownValue('UNKNOWN',None,comment.evidence_ids)})
    desired=replace(desired,objects=tuple(unknown if obj is comment else obj for obj in desired.objects))
    target=actual()
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'PROD'))
    comment_op=next(op for op in plan.operations if op.identity.object_type=='COMMENT')
    assert 'display_name' not in comment_op.to_dict()['object']
    assert 'Açıklama (bağlı nesne doğrulanamadı)' in render_reports(plan.to_dict(),{})['index.html'].decode()


def test_error_target_without_plan_does_not_expose_id_as_a_business_name():
    from html.parser import HTMLParser
    class VisibleText(HTMLParser):
        def __init__(self):super().__init__();self.parts=[]
        def handle_data(self,value):self.parts.append(value)
    run={'run_id':'error-label','source_commit':'a'*40,'finished_at':'2026-10-20T12:00:00Z','status':'FAILED',
         'targets':[{'id':'LOCAL-TTBP','status':'ERROR','difference_count':None,'plan_id':None,
                     'plan_path':None,'error_code':'ORA-01031'}]}
    view=build_run_view(run,{})
    assert view['targets'][0]['id']=='LOCAL-TTBP' and view['targets'][0]['schemas']==[]
    reports=[render_email(view),render_run_reports(view)['index.html']]
    for raw in reports:
        text=VisibleText();text.feed(raw.decode());visible=' '.join(text.parts)
        assert 'Hedef adı doğrulanamadı' in visible
        assert 'LOCAL-' not in visible and 'TTBP' not in visible and 'PROD' not in visible
        assert 'Karşılaştırma yapılamadı' in visible and 'fark sonucu üretilemedi' in visible
        assert 'ORA-01031' not in visible and 'UNKNOWN' not in visible
