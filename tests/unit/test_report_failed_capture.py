"""Schema Compare hedef okuması başarısızken bilinen kaynak bilgisini korur.

Sentetik snapshot ve yerel rapor dosyaları kullanır. Oracle ve mail bağlantısı açmaz.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from copy import deepcopy
import json

import pytest

from oracle_db_migration_generator.config.models import Endpoint, SchemaMapping, TargetConfig
from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.factories import profile, source


def failed_capture(count=1):
    from oracle_db_migration_generator.reporting.context import build_report_context
    selected = profile()
    desired = source('CREATE TABLE APP.T (ID NUMBER);', selected)
    targets = [TargetConfig('TEST-'+str(i), 'PROD', True,
        Endpoint('example.invalid', 1521, service_name='TEST'), 'THIN',
        (SchemaMapping('APP', 'APP', 'unused'),)) for i in range(count)]
    run = dict(run_id='failed-capture', source_commit='a'*40, build_number=9,
        status='FAILED', started_at='2026-11-09T05:00:00Z', finished_at='2026-11-09T05:39:27Z',
        targets=[dict(id=t.id, status='INCONSISTENT', difference_count=None,
            plan_id=None, plan_path=None, error_code='CHANGED_DURING_CAPTURE') for t in targets])
    context = build_report_context(desired, selected, targets)
    display = dict(run_id=run['run_id'], source_commit=run['source_commit'],
        source_environment='UAT', target_environments={t.id: 'PROD' for t in targets})
    return run, context, display


def test_failed_capture_keeps_real_source_counts_and_names_without_claiming_differences():
    run, context, display = failed_capture()
    view = build_run_view(run, {}, report_context=context, display_context=display, proposal_ids={})
    assert view['source_schemas'] == ['APP']
    assert view['targets'][0]['name'] == 'APP - PROD'
    assert view['targets'][0]['schemas'] == ['APP']
    assert view['scan_scope']['source_total'] == 1
    assert view['scan_scope']['rows'] == [{'label': 'Tablo', 'count': 1}]
    metrics = {row['label']: row['value'] for row in view['metrics']}
    assert metrics['Taranan Nesne'] == '1'
    assert metrics['Bulunan Fark'] == 'Karşılaştırılamadı'
    assert metrics['DDL Dosyası Eksik'] == 'Hesaplanmadı'
    html = render_email(view, preview=True).decode()
    assert '<title>Schema Compare</title>' in html
    assert 'Schema Compare Raporu' not in html
    assert 'APP - UAT' in html and 'APP - PROD' in html
    assert 'okuma sırasında değişti' in html
    assert 'Bilinmiyor' not in html and 'Hedef adı doğrulanamadı' not in html
    assert 'SQL üretildi, uygulanmadı' not in html
    assert 'Bu çalışmada DDL üretilmedi.' in html
    assert view['confirmed_differences'] is None
    assert view['targets'][0]['plan_path'] is None


def test_failed_multiple_targets_count_the_same_source_only_once():
    run, context, display = failed_capture(2)
    view = build_run_view(run, {}, report_context=context, display_context=display, proposal_ids={})
    assert view['scan_scope']['source_total'] == 1
    assert len(view['targets']) == 2
    assert all(t['source_object_count'] == 1 for t in view['targets'])


@pytest.mark.parametrize('mutation', ['commit', 'target', 'negative', 'duplicate'])
def test_failed_report_rejects_stale_or_invalid_source_context(mutation):
    run, context, display = failed_capture()
    changed = deepcopy(context)
    if mutation == 'commit': changed['source_commit'] = 'b'*40
    if mutation == 'target': changed['targets'][0]['id'] = 'OTHER-PROJECT'
    if mutation == 'negative': changed['targets'][0]['source']['by_schema']['APP']['TABLE'] = -1
    if mutation == 'duplicate': changed['targets'].append(deepcopy(changed['targets'][0]))
    with pytest.raises(ValueError, match='REPORT_CONTEXT'):
        build_run_view(run, {}, report_context=changed, display_context=display, proposal_ids={})


def test_jenkins_notification_loads_same_run_context_and_keeps_one_link(tmp_path, monkeypatch):
    from tools.jenkins_notification import write_notification
    run, context, _ = failed_capture()
    (tmp_path/'report-context.json').write_text(json.dumps(context), encoding='utf-8')
    monkeypatch.setenv('GENERATOR_REPORT_SOURCE_ENVIRONMENT', 'UAT')
    monkeypatch.setenv('GENERATOR_REPORT_TARGET_ENVIRONMENT', 'PROD')
    job = 'http://jenkins.example.invalid/job/generator/'
    path = write_notification(tmp_path, run, job+'9/', job)
    html = path.read_text(encoding='utf-8')
    assert 'APP - UAT' in html and 'APP - PROD' in html
    assert 'Bilinmiyor' not in html
    assert html.count('<a ') == 1
    assert job+'9/artifact/output/runs/build-9/index.html' in html
    context['source_commit'] = 'b'*40
    (tmp_path/'report-context.json').write_text(json.dumps(context), encoding='utf-8')
    with pytest.raises(ValueError, match='REPORT_CONTEXT'):
        write_notification(tmp_path, run, job+'9/', job)


def test_valid_plan_metrics_and_inventory_do_not_change_when_context_is_added():
    from dataclasses import replace
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.model.source_scope import source_for_schemas
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    from oracle_db_migration_generator.reporting.inventory import build_scan_summary
    from tests.factories import actual
    run, context, _ = failed_capture()
    selected = profile()
    desired = source_for_schemas(source('CREATE TABLE APP.T (ID NUMBER);', selected), selected, ('APP',))
    observed = replace(actual(selected_profile=selected), target_id='TEST-0')
    plan = plan_target(compare_snapshots(desired, observed, selected.policy),
        PlanningContext(desired, observed, selected, 'PROD')).to_dict()
    assert context['targets'][0]['source_digest'] == plan['source']['ddl_digest']
    run['status'] = 'COMPLETE'
    run['targets'][0].update(status=plan['status'], difference_count=1,
        plan_id=plan['plan_id'], plan_path='targets/TEST-0/plan.json', error_code=None)
    summaries = {'TEST-0': build_scan_summary(desired, observed, selected.policy, plan)}
    kwargs = dict(scan_summaries=summaries, proposal_ids={})
    original = build_run_view(run, {'TEST-0': plan}, **kwargs)
    updated = build_run_view(run, {'TEST-0': plan}, report_context=context, **kwargs)
    assert updated['metrics'] == original['metrics']
    assert updated['scan_scope'] == original['scan_scope']
    assert updated['ddl_types'] == original['ddl_types']
    invalid = deepcopy(context)
    invalid['targets'][0]['source_digest'] = 'b'*64
    with pytest.raises(ValueError, match='REPORT_CONTEXT'):
        build_run_view(run, {'TEST-0': plan}, report_context=invalid, **kwargs)
    invalid = deepcopy(context)
    invalid['targets'][0]['source']['by_schema']['APP']['TABLE'] = 42
    with pytest.raises(ValueError, match='REPORT_CONTEXT_SOURCE_CONFLICT'):
        build_run_view(run, {'TEST-0': plan}, report_context=invalid, **kwargs)
