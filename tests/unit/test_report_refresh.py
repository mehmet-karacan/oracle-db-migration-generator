import json
from pathlib import Path

import pytest

from tests.factories import source,actual,profile
from oracle_db_migration_generator.model.serialization import canonical_bytes
from oracle_db_migration_generator.runtime.worker import offline_plan


def saved_inputs(tmp_path):
    sql='CREATE TABLE APP.T(ID NUMBER); CREATE VIEW APP.V AS SELECT ID FROM APP.MISSING;'
    desired=source(sql);target=actual()
    root=tmp_path/'source';(root/'app').mkdir(parents=True)
    (root/'app/fixture.sql').write_text(sql,encoding='utf-8')
    source_path=root/'source-snapshot.json';source_path.write_bytes(canonical_bytes(desired.to_dict()))
    target_path=tmp_path/'target-snapshot.json';target_path.write_bytes(canonical_bytes(target.to_dict()))
    previous=tmp_path/'previous';offline_plan(desired,target,profile(),previous,name='Saved target')
    return previous,source_path,target_path


def test_refresh_uses_verified_snapshots_without_oracle_and_preserves_sql(tmp_path,monkeypatch):
    from tools.jenkins_report_refresh import refresh_plan
    previous,source_path,target_path=saved_inputs(tmp_path)
    before={p.relative_to(previous).as_posix():p.read_bytes() for p in previous.rglob('*') if p.is_file()}
    def forbidden(*a,**kw):raise AssertionError('Oracle connection forbidden')
    monkeypatch.setattr('oracledb.connect',forbidden)
    result=refresh_plan(previous,source_path,target_path,profile(),tmp_path/'new')
    assert result['sql_bodies_verified']==1 and result['database_connections']==0
    current=json.loads((tmp_path/'new/plan.json').read_bytes())
    assert current['counts']['ready_operations']==1 and current['counts']['blocked_operations']==1
    assert 'APP.MISSING' in next(op for op in current['operations'] if op['decision']=='BLOCKED')['reason_tr']
    assert before=={p.relative_to(previous).as_posix():p.read_bytes() for p in previous.rglob('*') if p.is_file()}


def test_refresh_rejects_a_different_source_snapshot_before_output(tmp_path):
    from tools.jenkins_report_refresh import refresh_plan
    previous,source_path,target_path=saved_inputs(tmp_path)
    document=json.loads(source_path.read_bytes());document['source_commit']='b'*40
    source_path.write_bytes(canonical_bytes(document))
    with pytest.raises(ValueError,match='REFRESH_INPUT_MISMATCH'):
        refresh_plan(previous,source_path,target_path,profile(),tmp_path/'new')
    assert not (tmp_path/'new').exists()
