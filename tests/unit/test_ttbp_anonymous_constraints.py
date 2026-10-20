"""Anonymous constraint multiplicity and ALTER provenance remain explicit."""
import hashlib
from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.oracle.ddl_model import project_target_object
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
from tests.factories import actual,profile,source


BASE='CREATE TABLE APP.T(ID NUMBER, CODE NUMBER, PRIMARY KEY(ID) USING INDEX ENABLE);'
CONTEXT='ALTER TABLE APP.T ADD UNIQUE(CODE) USING INDEX APP.IX_CODE ENABLE;'
CHECK='CHECK (ID IN (0 /* no */, 1 /* yes */)) ENABLE'


def test_anonymous_add_unique_keeps_source_create_span_and_alter_evidence():
    snapshot=source(BASE+' '+CONTEXT)
    table=next(obj for obj in snapshot.objects if obj.identity.object_type=='TABLE')
    assert table.coverage.ddl=='COMPLETE'
    assert table.raw_ddl==BASE.encode()
    assert len(table.evidence_ids)==2
    constraints=table.properties['projection'].value['constraints']
    assert len(constraints)==2 and all(name.startswith('@anonymous-') for name in constraints)
    assert 'UNIQUE(CODE) USING INDEX APP.IX_CODE ENABLE' in constraints.values()
    proof={ev.id:ev for ev in snapshot.evidence}[table.evidence_ids[-1]]
    full=(BASE+' '+CONTEXT).encode()
    assert full[proof.start_byte:proof.end_byte]==CONTEXT.encode()


def test_anonymous_add_unique_keeps_target_context_and_backing_association():
    snapshot=actual(BASE)
    raw=(BASE+' '+CONTEXT).encode()
    original=replace(snapshot.objects[0],raw_ddl=raw,ddl_sha256=hashlib.sha256(raw).hexdigest())
    updated,evidence=project_target_object(original)
    assert updated.coverage.ddl=='COMPLETE'
    assert updated.raw_ddl==raw and updated.ddl_sha256==original.ddl_sha256
    assert len(updated.projection.properties['constraints'])==2
    assert 'UNIQUE(CODE) USING INDEX APP.IX_CODE ENABLE' in updated.projection.properties['constraints'].values()
    assert len(evidence)==1 and evidence[0].sha256==original.ddl_sha256
    assert raw[evidence[0].start_byte:evidence[0].end_byte]==CONTEXT.encode()


def test_identical_anonymous_checks_are_distinct_and_raw_definitions_are_preserved():
    raw=f'CREATE TABLE APP.T(ID NUMBER, {CHECK}, {CHECK});'.encode()
    first=parse_ddl(raw,None);second=parse_ddl(raw,None)
    assert first.coverage==second.coverage=='COMPLETE'
    obj=first.objects[0]
    constraints=obj.projection.properties['constraints']
    assert len(constraints)==2 and list(constraints.values())==[CHECK,CHECK]
    assert constraints==second.objects[0].projection.properties['constraints']
    assert obj.raw_ddl==raw
    assert all(name.startswith('@anonymous-') for name in constraints)


def test_both_duplicate_checks_are_emitted_with_distinct_operation_ids():
    selected=profile();desired=source(f'CREATE TABLE APP.T(ID NUMBER, {CHECK}, {CHECK});');target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Synthetic'))
    checks=[op for op in result.operations if op.kind=='ADD_CONSTRAINT']
    assert len(checks)==2 and len({op.operation_id for op in checks})==2
    assert all(op.decision=='READY' and op.intent.statement==f'ALTER TABLE "APP"."T" ADD {CHECK};'.encode() for op in checks)


def test_duplicate_anonymous_checks_match_two_named_target_checks():
    desired=source('CREATE TABLE APP.T(ID NUMBER, CHECK(ID>0), CHECK(ID>0));')
    target=actual('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT C1 CHECK(ID>0), CONSTRAINT C2 CHECK(ID>0));')
    changes=compare_snapshots(desired,target,profile().policy)
    assert not changes.differences


def test_add_an_identical_anonymous_check_preserves_both_occurrences():
    snapshot=source('CREATE TABLE APP.T(ID NUMBER, CHECK(ID>0)); ALTER TABLE APP.T ADD CHECK(ID>0);')
    table=snapshot.objects[0]
    assert table.coverage.ddl=='COMPLETE'
    assert len(table.properties['projection'].value['constraints'])==2
    assert len(table.evidence_ids)==2


@pytest.mark.parametrize('definitions',[
    'CHECK(ID>0) ENABLE, CHECK(ID>0) DISABLE',
    'UNIQUE(ID), UNIQUE(ID)',
    'PRIMARY KEY(ID), PRIMARY KEY(ID)',
    'FOREIGN KEY(ID) REFERENCES APP.A(ID), FOREIGN KEY(ID) REFERENCES APP.B(ID)',
])
def test_ambiguous_anonymous_constraint_collision_stays_partial(definitions):
    result=parse_ddl(f'CREATE TABLE APP.T(ID NUMBER, {definitions});'.encode(),None)
    assert result.coverage=='PARTIAL'
    assert 'UNNAMED_CONSTRAINT_UNRESOLVED' in result.objects[0].diagnostics


def test_duplicate_named_constraint_in_context_stays_blocked():
    result=source('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT C1 CHECK(ID>0)); ALTER TABLE APP.T ADD CONSTRAINT C1 CHECK(ID>0);')
    assert result.objects[0].coverage.ddl=='PARTIAL'
    assert result.objects[0].properties['projection'].state=='UNKNOWN'
