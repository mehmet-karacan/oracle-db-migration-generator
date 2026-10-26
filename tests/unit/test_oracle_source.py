from dataclasses import replace
import json
from pathlib import Path

import pytest

from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.config.loader import validate_document
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from test_collector import FakeConnection,FakeCursor,inputs


def test_oracle_source_uses_capture_identity_and_source_evidence(tmp_path):
    from oracle_db_migration_generator.source.oracle_reader import collect_source
    config,profile=inputs()
    result=collect_source(config,lambda _:Credentials('APP','synthetic'),profile,
                          connect=lambda *_:FakeConnection())
    source=result.snapshot
    assert source.side=='SOURCE' and source.source_commit is None and source.target_id is None
    assert source.source_origin['kind']=='ORACLE'
    assert len(source.source_origin['snapshot_id'])==64
    assert all(ev.side=='SOURCE' for ev in source.evidence)
    assert all(ev.kind!='TARGET_METADATA' for ev in source.evidence)
    assert result.receipt['read_only'] and result.receipt['execution_status']=='NOT_EXECUTED'
    document=source.to_dict();validate_document(document,'snapshot.schema.json')
    path=tmp_path/'source.json';path.write_text(json.dumps(document),encoding='utf-8')
    restored=load_snapshot(path)
    assert restored.source_origin==source.source_origin
    assert restored.semantic_digest==source.semantic_digest


def test_inconsistent_oracle_source_cannot_produce_a_source_snapshot():
    from oracle_db_migration_generator.source.oracle_reader import collect_source
    config,profile=inputs()
    result=collect_source(config,lambda _:Credentials('APP','synthetic'),profile,
                          connect=lambda *_:FakeConnection(changing=True))
    assert result.snapshot is None and result.receipt['status']=='INCONSISTENT'


def test_oracle_source_produces_actual_ddl_without_forging_commit(tmp_path):
    from oracle_db_migration_generator.source.oracle_reader import from_observation
    from oracle_db_migration_generator.oracle.collector import TargetObservation,collect_target
    from oracle_db_migration_generator.runtime.worker import offline_plan
    from oracle_db_migration_generator.model.snapshot import Coverage
    config,profile=inputs();root=Path(__file__).resolve().parents[2]
    desired=load_snapshot(root/'examples/source-snapshot.example.json',require_ddl=True)
    observed=replace(desired,side='TARGET',source_commit=None,target_id='source-db',
                     evidence=tuple(replace(ev,side='TARGET') for ev in desired.evidence))
    source=from_observation(TargetObservation(observed,{'status':'CAPTURED','read_only':True}),connection_id='source-db').snapshot
    target=collect_target(config,lambda _:Credentials('APP','synthetic'),profile,
                          connect=lambda *_:FakeConnection()).snapshot
    # This test uses the example's proven NUMBER/VARCHAR2 table and empty target.
    source=replace(source,completeness=Coverage('COMPLETE','COMPLETE','COMPLETE'))
    bundle=tmp_path/'targets'/target.target_id
    result=offline_plan(source,target,profile,bundle)
    plan=json.loads((bundle/'plan.json').read_bytes())
    assert plan['source']['commit_sha'] is None
    assert plan['source']['origin']['kind']=='ORACLE'
    assert result['counts']['ready_operations']>0
    files=list((bundle/'objects').rglob('*.sql'))
    assert any(b'CREATE TABLE' in p.read_bytes() for p in files)
    aggregate=next(bundle.glob('*ready.sql'),None) or bundle/'migration.sql'
    assert b'-- source_snapshot:' in aggregate.read_bytes()
    assert b'-- source_commit: None' not in aggregate.read_bytes()
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    run=aggregate_run(tmp_path,source_origin=dict(source.source_origin))
    assert run['source_commit'] is None and run['source_origin']['kind']=='ORACLE'
    assert 'Oracle kaynak snapshot' in (tmp_path/'index.html').read_text(encoding='utf-8')


class CommentCursor(FakeCursor):
    def fetchall(self):
        if 'ALL_TAB_COMMENTS' in self.current.upper():return [('DEMO','same comment')]
        if 'ALL_COL_COMMENTS' in self.current.upper():return [('DEMO','ID','column comment')]
        return super().fetchall()


def comment_connection():
    connection=FakeConnection();connection.reader=CommentCursor(inventory=[('TABLE','DEMO','VALID','2026-10-24')])
    return connection


def test_oracle_source_dictionary_failure_never_means_no_change():
    from oracle_db_migration_generator.source.oracle_reader import collect_source
    from oracle_db_migration_generator.oracle.collector import collect_target
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.planning.rules import plan_target,PlanningContext
    config,profile=inputs();creds=lambda _:Credentials('APP','synthetic')
    source=collect_source(config,creds,profile,connect=lambda *_:FakeConnection(denied='ALL_TAB_COMMENTS')).snapshot
    target=collect_target(config,creds,profile,connect=lambda *_:FakeConnection()).snapshot
    diff=compare_snapshots(source,target,profile.policy)
    assert not diff.complete and diff.scope.dictionary=='PARTIAL'
    assert plan_target(diff,PlanningContext(source,target,profile,'Target')).status!='NO_CHANGE'
    target=collect_target(config,creds,profile,connect=lambda *_:comment_connection()).snapshot
    diff=compare_snapshots(source,target,profile.policy)
    comments={o.object_key for o in target.objects if o.identity.object_type=='COMMENT'}
    assert any(d.object_key in comments and d.after.state=='UNKNOWN' for d in diff.differences)


def test_oracle_source_sidecars_are_namespaced_and_roundtrip_with_raw_evidence(tmp_path):
    from oracle_db_migration_generator.source.oracle_reader import collect_source,save_source
    from oracle_db_migration_generator.oracle.collector import collect_target
    from oracle_db_migration_generator.planning.context import PlanningContext
    config,profile=inputs();creds=lambda _:Credentials('APP','synthetic')
    source_observation=collect_source(config,creds,profile,connect=lambda *_:comment_connection())
    target=collect_target(config,creds,profile,connect=lambda *_:comment_connection()).snapshot
    source=source_observation.snapshot
    assert not ({ev.id for ev in source.evidence}&{ev.id for ev in target.evidence})
    PlanningContext(source,target,profile,'Target')
    path=save_source(source_observation,tmp_path/'source')
    restored=load_snapshot(path,require_ddl=True)
    assert restored.semantic_digest==source.semantic_digest
    assert any(ev.path and ev.sha256 not in {o.ddl_sha256 for o in source.objects} for ev in source.evidence)
    assert (path.parent/'capture-receipt.json').is_file()
    assert any(o.identity.object_type=='COMMENT' and o.raw_ddl for o in restored.objects)
    for ev in restored.evidence:
        if ev.path:assert (path.parent/ev.path).is_file()
    blob=next(ev for ev in restored.evidence if ev.path)
    (path.parent/blob.path).write_bytes(b'changed')
    with pytest.raises(ValueError,match='SNAPSHOT_EVIDENCE_INTEGRITY_MISMATCH'):load_snapshot(path,require_ddl=True)
