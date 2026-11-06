import json
from copy import deepcopy
from dataclasses import replace
import pytest

from tests.factories import actual, profile, source
from oracle_db_migration_generator.runtime.worker import offline_plan
from oracle_db_migration_generator.runtime.aggregate import aggregate_run
from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view


SQL = 'CREATE TABLE APP.T(ID NUMBER); CREATE VIEW APP.V AS SELECT ID FROM APP.T;'


def bundle(tmp_path, *, partial=False):
    selected = profile(); desired = source(SQL, selected); target = actual(SQL, selected)
    if partial:
        desired = replace(desired, completeness=replace(desired.completeness, inventory='PARTIAL'))
    root = tmp_path/'run'; destination = root/'targets'/target.target_id
    offline_plan(desired, target, selected, destination)
    return root, destination


def test_unchanged_objects_are_counted_in_web_and_mail(tmp_path):
    root, destination = bundle(tmp_path)
    run = aggregate_run(root)
    plan = json.loads((destination/'plan.json').read_bytes())
    assert plan['operations'] == []
    summary = json.loads((destination/'scan-summary.json').read_bytes())
    assert summary['source']['by_schema'] == {'APP': {'TABLE': 1, 'VIEW': 1}}
    assert summary['target']['by_schema'] == {'APP': {'TABLE': 1, 'VIEW': 1}}
    view = build_run_view(run, {plan['target']['id']: plan}, scan_summaries={plan['target']['id']: summary})
    assert view['scan_scope']['source_total'] == 2
    assert view['scan_scope']['rows'] == [
        {'label': 'Tablo', 'count': 1}, {'label': 'Görünüm', 'count': 1}]
    for html in [(root/'index.html').read_text(encoding='utf-8'),
                 (destination/'index.html').read_text(encoding='utf-8'), render_email(view).decode()]:
        assert 'Tarama Kapsamı' in html and 'Toplam taranan nesne' in html
        assert 'Tablo' in html and 'Görünüm' in html
        scope = html.split('<section aria-label="Tarama Kapsamı">', 1)[1].split('</section>', 1)[0]
        assert 'Hedefler' not in scope and 'kaynak nesneleri' in scope
        if 'Kaynak ve İzlenebilirlik' in html:
            assert html.index('Tarama Kapsamı') < html.index('Kaynak ve İzlenebilirlik')


def test_shared_source_is_counted_once_across_targets(tmp_path):
    root, destination = bundle(tmp_path); run = aggregate_run(root)
    plan = json.loads((destination/'plan.json').read_bytes())
    summary = json.loads((destination/'scan-summary.json').read_bytes())
    second = deepcopy(plan); second['target']['id'] = 'SECOND'
    second_summary = deepcopy(summary); second_summary['target_id'] = 'SECOND'
    result = deepcopy(run['targets'][0]); result.update(id='SECOND', plan_path='targets/SECOND/plan.json')
    run['targets'].append(result)
    view = build_run_view(run, {plan['target']['id']: plan, 'SECOND': second},
                          scan_summaries={plan['target']['id']: summary, 'SECOND': second_summary})
    assert view['scan_scope']['source_total'] == 2
    assert view['scan_scope']['rows'] == [{'label': 'Tablo', 'count': 1}, {'label': 'Görünüm', 'count': 1}]


def test_old_archive_and_failed_target_do_not_become_zero_inventory():
    from tests.unit.test_report_views import inputs
    run, plans = inputs()
    view = build_run_view(run, plans)
    assert view['scan_scope']['source_total'] is None
    html = render_email(view).decode()
    assert 'Tarama kapsamı bilgisi kaydedilmedi' in html
    assert 'Bilinmiyor' in html


def test_partial_inventory_is_explicit(tmp_path):
    root, destination = bundle(tmp_path, partial=True); run = aggregate_run(root)
    html = (root/'index.html').read_text(encoding='utf-8')
    assert 'Envanter eksik, sayılar gözlenen alt sınırdır' in html


def test_target_inventory_does_not_change_source_counters_or_completeness(tmp_path):
    root, destination = bundle(tmp_path); run = aggregate_run(root)
    plan = json.loads((destination/'plan.json').read_bytes())
    summary = json.loads((destination/'scan-summary.json').read_bytes())
    summary['target'].update(inventory='UNAVAILABLE', by_schema={'APP': {}})
    view = build_run_view(run, {plan['target']['id']: plan}, scan_summaries={plan['target']['id']: summary})
    assert view['scan_scope']['source_total'] == 2
    assert view['scan_scope']['rows'] == [{'label': 'Tablo', 'count': 1}, {'label': 'Görünüm', 'count': 1}]
    assert 'Envanter eksik' not in view['scan_scope']['note']


def test_empty_target_is_zero_and_scope_policy_excludes_technical_objects(tmp_path):
    selected = profile()
    selected = replace(selected, policy=replace(selected.policy, exclude_system_generated=True,
                                               excluded_object_types=('GRANT',)))
    desired = source('CREATE TABLE APP.T(ID NUMBER); CREATE TABLE APP."BIN$TEST"(ID NUMBER); '
                     'COMMENT ON TABLE APP.T IS \'test\'; GRANT SELECT ON APP.T TO PUBLIC;', selected)
    target = actual('', selected); destination = tmp_path/'target'
    offline_plan(desired, target, selected, destination)
    summary = json.loads((destination/'scan-summary.json').read_bytes())
    assert summary['source']['by_schema'] == {'APP': {'COMMENT': 1, 'TABLE': 1}}
    assert summary['source']['excluded'] == 2
    assert summary['target']['by_schema'] == {'APP': {}}
    plan = json.loads((destination/'plan.json').read_bytes())
    from oracle_db_migration_generator.reporting.inventory import scan_scope_view
    view = scan_scope_view({target.target_id:plan}, {target.target_id:summary}, [target.target_id])
    assert view['source_total'] == 1
    assert view['rows'] == [{'label': 'Tablo', 'count': 1}]
    html = (destination/'index.html').read_text(encoding='utf-8')
    assert 'Açıklama' in html and 'Bilinmiyor' not in html


def test_scan_summary_survives_presentation_refresh_without_changing_sql(tmp_path):
    from tools.jenkins_report_presentation import refresh_bundle
    from oracle_db_migration_generator.artifacts.bundle import verify_bundle
    selected = profile(); destination = tmp_path/'previous'
    offline_plan(source(SQL, selected), actual('', selected), selected, destination)
    output = tmp_path/'refreshed'
    refresh_bundle(destination, output)
    assert verify_bundle(output)['status'] == 'VERIFIED'
    for path in destination.rglob('*'):
        if path.is_file() and (path.suffix == '.sql' or path.name in {'plan.json', 'scan-summary.json'}):
            assert path.read_bytes() == (output/path.relative_to(destination)).read_bytes()
    assert 'Tarama Kapsamı' in (output/'index.html').read_text(encoding='utf-8')


def test_jenkins_mail_uses_the_archived_inventory(tmp_path):
    from tools.jenkins_notification import write_notification
    root, destination = bundle(tmp_path); run = aggregate_run(root, build_number=42)
    url = 'https://jenkins.example.invalid/job/generator/'
    html = write_notification(root, run, url+'42/', url).read_text(encoding='utf-8')
    assert 'Tarama Kapsamı' in html and 'Görünüm' in html
    assert 'Tarama kapsamı bilgisi kaydedilmedi' not in html


def test_summary_cannot_be_attached_to_another_plan(tmp_path):
    from oracle_db_migration_generator.reporting.inventory import validate_scan_summary
    root, destination = bundle(tmp_path)
    plan = json.loads((destination/'plan.json').read_bytes())
    summary = json.loads((destination/'scan-summary.json').read_bytes())
    summary['plan_id'] = 'f'*64
    with pytest.raises(ValueError, match='SCAN_SUMMARY_PLAN_MISMATCH'):
        validate_scan_summary(summary, plan)
