import hashlib
import json
import re
from pathlib import Path

import pytest

from oracle_db_migration_generator.artifacts.bundle import write_bundle, verify_bundle
from tests.unit.test_bundle import make_plan


def test_nested_object_sql_readme_review_and_exact_include_order(tmp_path):
    plan = make_plan('CREATE TABLE APP.T(ID NUMBER NOT NULL); CREATE TABLE APP.NEW_T(ID NUMBER);',
                     'CREATE TABLE APP.T(ID NUMBER);')
    write_bundle(plan, tmp_path/'bundle')
    root = tmp_path/'bundle'
    document = json.loads((root/'plan.json').read_bytes())
    sql_ops = [op for op in document['operations'] if op['sql']]
    assert sql_ops and all(re.fullmatch(r'objects/APP/TABLE/NEW_T/op-[a-f0-9]{64}\.sql', op['sql']['path']) for op in sql_ops)
    assert (root/'objects/APP/TABLE/NEW_T/README.md').is_file()
    assert list((root/'review').glob('*.json'))
    includes = [line[2:] for line in (root/'partial-ready.sql').read_text().splitlines() if line.startswith('@@')]
    assert includes == [op['sql']['path'] for op in sql_ops]
    assert 'Nesne' in (root/'README.md').read_text(encoding='utf-8')
    assert verify_bundle(root)['status'] == 'VERIFIED'


def test_path_components_cannot_escape_or_collide_on_windows():
    from oracle_db_migration_generator.artifacts.layout import component
    values = ['../x', 'CON', 'a/b', 'A', 'a', 'x'*300, 'nul.txt', '<script>', 'a#b']
    paths = [component(value) for value in values]
    assert len({path.casefold() for path in paths}) == len(paths)
    assert all(re.fullmatch('[A-Za-z0-9_-]{1,80}', path) for path in paths)


def test_aggregate_rejects_unmanifested_order_even_with_valid_manifest(tmp_path):
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'), tmp_path/'bundle')
    root = tmp_path/'bundle'
    raw = (root/'migration.sql').read_bytes().replace(b'@@objects/', b'--@@objects/')
    (root/'migration.sql').write_bytes(raw)
    manifest = json.loads((root/'bundle-manifest.json').read_bytes())
    row = next(item for item in manifest['files'] if item['path']=='migration.sql')
    row.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    (root/'bundle-manifest.json').write_bytes(canonical_bytes(manifest))
    with pytest.raises(ValueError, match='BUNDLE_AGGREGATE_MISMATCH'):
        verify_bundle(root)


def run_fixture(root):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    write_bundle(make_plan('CREATE TABLE APP.T(ID NUMBER);'), root/'targets/DEMO-TEST')
    return aggregate_run(root)


def test_two_runs_deduplicate_plan_and_preserve_error(tmp_path):
    from oracle_db_migration_generator.artifacts.store import archive_run
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    root=tmp_path/'run'
    first=run_fixture(root)
    error=root/'targets/FAILED';error.mkdir()
    error.joinpath('target-error.json').write_text(json.dumps(dict(id='FAILED',status='ERROR',difference_count=None,
        plan_id=None,plan_path=None,captured_at=None,error_code='ORA-01031',publication='NOT_REQUESTED')))
    first=aggregate_run(root)
    a=archive_run(root,tmp_path/'store',build_number=1)
    second=aggregate_run(root)
    b=archive_run(root,tmp_path/'store',build_number=2)
    assert first['run_id']!=second['run_id'] and a['run_path']!=b['run_path']
    assert a['new_plans']==1 and b['new_plans']==0 and b['reused_plans']==1
    assert len(list((tmp_path/'store/plans').rglob('plan.json')))==1
    run=json.loads((tmp_path/'store'/b['run_path']/'run.json').read_bytes())
    assert run['targets'][1]['status']=='ERROR' and run['targets'][1]['difference_count'] is None
    assert run['artifact_git_sha'] is None
    for doc in (tmp_path/'store').rglob('README.md'):
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            assert (doc.parent/link).resolve().is_file(), (doc, link)


def test_store_rejects_unowned_files_and_modified_plan(tmp_path):
    from oracle_db_migration_generator.artifacts.store import archive_run
    run_fixture(tmp_path/'run')
    store=tmp_path/'user';store.mkdir();(store/'README.md').write_text('user document')
    with pytest.raises(ValueError,match='STORE_NOT_OWNED'):
        archive_run(tmp_path/'run', store)
    assert (store/'README.md').read_text()=='user document'
    archive_run(tmp_path/'run',tmp_path/'store')
    plan=next((tmp_path/'store/plans').rglob('plan.json'));plan.write_text('{}')
    with pytest.raises(ValueError,match='INTEGRITY_CONFLICT'):
        archive_run(tmp_path/'run',tmp_path/'store')


def test_failed_store_write_rolls_back_and_can_retry(tmp_path,monkeypatch):
    from oracle_db_migration_generator.artifacts import store
    run_fixture(tmp_path/'run')
    original=store._atomic;calls=0
    def fail_once(path,raw):
        nonlocal calls
        calls+=1
        if calls==3: raise OSError('synthetic failure')
        return original(path,raw)
    monkeypatch.setattr(store,'_atomic',fail_once)
    with pytest.raises(OSError): store.archive_run(tmp_path/'run',tmp_path/'store')
    assert not list((tmp_path/'store').rglob('*'))
    assert store.archive_run(tmp_path/'run',tmp_path/'store')['status']=='ARCHIVED'


def test_plan_identity_includes_safety_inputs_but_not_run_time():
    from dataclasses import replace
    base=make_plan('CREATE TABLE APP.T(ID NUMBER);')
    variants=[replace(base,source={**base.source,'commit_sha':'b'*40}),
              replace(base,target_snapshot_digest='c'*64),replace(base,rule_version='other'),
              replace(base,generator_version='other'),
              replace(base,input_fingerprint={**base.input_fingerprint,'parser_artifact_sha256':'d'*64}),
              replace(base,input_fingerprint={**base.input_fingerprint,'profile_sha256':'e'*64})]
    assert all(p.plan_id!=base.plan_id for p in variants)
    assert replace(base,validation={'time':'unrelated'}).plan_id==base.plan_id
