import json

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle, verify_bundle
from tests.unit.test_bundle import make_plan


def test_legacy_presentation_can_add_verified_inventory_without_replanning(tmp_path,monkeypatch):
    from tests.factories import source,actual,profile
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    from tools.jenkins_report_presentation import archived_scan_summary,refresh_bundle
    sql='CREATE TABLE APP.T(ID NUMBER);'
    previous=tmp_path/'previous';write_bundle(make_plan(sql),previous)
    source_dir=tmp_path/'source';(source_dir/'app').mkdir(parents=True)
    (source_dir/'app/fixture.sql').write_text(sql,encoding='utf-8')
    source_path=source_dir/'source-snapshot.json';source_path.write_bytes(canonical_bytes(source(sql).to_dict()))
    target_path=tmp_path/'target-snapshot.json';target_path.write_bytes(canonical_bytes(actual().to_dict()))
    def forbidden(*a,**kw):raise AssertionError('No comparison or Oracle connection during presentation refresh')
    monkeypatch.setattr('oracledb.connect',forbidden)
    monkeypatch.setattr('oracle_db_migration_generator.compare.snapshots.compare_snapshots',forbidden)
    summary,proof=archived_scan_summary(previous,source_path,target_path,profile())
    output=tmp_path/'new';refresh_bundle(previous,output,scan_summary=summary)
    assert verify_bundle(output)['status']=='VERIFIED'
    assert json.loads((output/'scan-summary.json').read_bytes())['source']['by_schema']=={'APP':{'TABLE':1}}
    assert len(proof['inventory_source_snapshot_sha256'])==64
    assert (previous/'plan.json').read_bytes()==(output/'plan.json').read_bytes()
    for path in previous.rglob('*.sql'):
        assert path.read_bytes()==(output/path.relative_to(previous)).read_bytes()


def test_legacy_inventory_rejects_unrelated_snapshot(tmp_path):
    from tests.factories import source,actual,profile
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    from tools.jenkins_report_presentation import archived_scan_summary
    previous=tmp_path/'previous';write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'),previous)
    root=tmp_path/'source';(root/'app').mkdir(parents=True)
    sql='CREATE TABLE APP.OTHER(ID NUMBER);';(root/'app/fixture.sql').write_text(sql,encoding='utf-8')
    source_path=root/'source-snapshot.json';source_path.write_bytes(canonical_bytes(source(sql).to_dict()))
    target_path=tmp_path/'target-snapshot.json';target_path.write_bytes(canonical_bytes(actual().to_dict()))
    with pytest.raises(ValueError,match='PRESENTATION_INVENTORY_INPUT_MISMATCH'):
        archived_scan_summary(previous,source_path,target_path,profile())


def test_presentation_refresh_preserves_every_non_presentation_byte(tmp_path):
    from tools.jenkins_report_presentation import refresh_bundle
    previous = tmp_path/'previous'; output = tmp_path/'new'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'), previous)
    before = {p.relative_to(previous).as_posix():p.read_bytes() for p in previous.rglob('*') if p.is_file()}
    result = refresh_bundle(previous, output)
    assert result['sql_files_verified'] >= 2
    assert verify_bundle(output)['status'] == 'VERIFIED'
    for name, raw in before.items():
        if name != 'bundle-manifest.json' and not name.endswith('.html') and not name.startswith('assets/'):
            assert (output/name).read_bytes() == raw
        assert (previous/name).read_bytes() == raw
    assert 'DDL hazır' in (output/'index.html').read_text(encoding='utf-8')
    assert json.loads((output/'plan.json').read_bytes()) == json.loads(before['plan.json'])
    with pytest.raises(ValueError, match='OUTPUT_ALREADY_EXISTS'):
        refresh_bundle(previous, output)


def test_presentation_refresh_rejects_tampered_input_before_creating_output(tmp_path):
    from tools.jenkins_report_presentation import refresh_bundle
    previous = tmp_path/'previous'; output = tmp_path/'new'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'), previous)
    (previous/'migration.sql').write_bytes(b'-- tampered')
    with pytest.raises(ValueError): refresh_bundle(previous, output)
    assert not output.exists()


def test_presentation_refresh_does_not_publish_a_half_verified_bundle(tmp_path, monkeypatch):
    from tools import jenkins_report_presentation as refresh
    previous = tmp_path/'previous'; output = tmp_path/'new'
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'), previous)
    verify = refresh.verify_bundle
    def reject_new(path):
        if path.resolve() != previous.resolve(): raise ValueError('RENDERED_BUNDLE_REJECTED')
        return verify(path)
    monkeypatch.setattr(refresh, 'verify_bundle', reject_new)
    with pytest.raises(ValueError, match='RENDERED_BUNDLE_REJECTED'):
        refresh.refresh_bundle(previous, output)
    assert not output.exists() and not list(tmp_path.glob('.presentation-staging-*'))


def test_repeated_report_refresh_keeps_the_original_comparison_clock(tmp_path):
    from tools.jenkins_report_presentation import comparison_origin
    source='a'*40
    original=tmp_path/'build-29';original.mkdir()
    original.joinpath('run.json').write_text(json.dumps({'build_number':29,'source_commit':source,
        'started_at':'2026-10-21T05:00:00Z','finished_at':'2026-10-21T06:15:09Z'}))
    refresh=tmp_path/'build-30';refresh.mkdir()
    refresh.joinpath('run.json').write_text(json.dumps({'build_number':30,'source_commit':source,
        'started_at':'2026-10-21T07:00:00Z','finished_at':'2026-10-21T07:01:05Z'}))
    refresh.joinpath('presentation-refresh-receipt.json').write_text(json.dumps({'base_build':29}))
    timing=comparison_origin(refresh)
    assert timing['build_number']==29 and timing['finished_at']=='2026-10-21T06:15:09Z'
