from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
from tests.factories import actual,profile,source


def declared_procedure(snapshot):
    return replace(snapshot,objects=tuple(replace(obj,properties={**obj.properties,
        'dependencies':KnownValue('KNOWN',[{'owner':'APP','type':'TABLE','name':'P'}],obj.evidence_ids)})
        if obj.identity.object_type=='PROCEDURE' else obj for obj in snapshot.objects))


def key_plan(source_key='NUMBER(10)',target_key='NUMBER(10)',target_pk=True):
    selected=profile()
    desired=source(f'CREATE TABLE APP.P(ID {source_key} NOT NULL, LABEL VARCHAR2(20 BYTE), CONSTRAINT PK_P PRIMARY KEY(ID)); '
                   f'CREATE TABLE APP.CHILD(ID {source_key}, CONSTRAINT FK_CHILD FOREIGN KEY(ID) REFERENCES APP.P(ID));',selected)
    target=actual(f'CREATE TABLE APP.P(ID {target_key} NOT NULL, LABEL VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP'
                  +(', CONSTRAINT PK_P PRIMARY KEY(ID)' if target_pk else '')+');',selected)
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))


def test_unrelated_unknown_column_cannot_hold_a_proven_existing_foreign_key_parent():
    plan=key_plan()
    warning=next(op for op in plan.operations if 'COLUMN_COMPARISON_INCOMPLETE_PRESERVED' in op.reason_codes)
    fk=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert warning.decision=='INFORMATIONAL'
    assert fk.decision=='READY' and fk.intent is not None
    assert b'REFERENCES APP.P(ID)' in fk.intent.statement
    assert warning.operation_id not in fk.dependencies


@pytest.mark.parametrize('source_key,target_key,target_pk',[
    ('NUMBER(10)','NUMBER(19)',True),
    ('NUMBER(10)','NUMBER(10)',False),
])
def test_changed_key_shape_or_unproven_existing_unique_key_remains_held(source_key,target_key,target_pk):
    plan=key_plan(source_key,target_key,target_pk)
    fk=next(op for op in plan.operations if op.kind=='ADD_CONSTRAINT')
    assert fk.decision=='BLOCKED' and fk.intent is None


def test_named_anchor_uses_only_the_proven_required_column_shape():
    selected=profile()
    desired=source('CREATE TABLE APP.P(ID NUMBER(10), LABEL VARCHAR2(20 BYTE)); '
                   'CREATE PROCEDURE APP.DO_WORK(P_ID IN APP.P.ID%TYPE) AS BEGIN NULL; END;\n/',selected)
    desired=declared_procedure(desired)
    target=actual('CREATE TABLE APP.P(ID NUMBER(10), LABEL VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);',selected)
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    procedure=next(op for op in plan.operations if op.identity.object_type=='PROCEDURE')
    assert procedure.decision=='READY' and procedure.intent is not None


def test_named_anchor_still_holds_when_its_own_column_type_is_uncertain():
    selected=profile()
    desired=source('CREATE TABLE APP.P(ID VARCHAR2(20 BYTE)); '
                   'CREATE PROCEDURE APP.DO_WORK(P_ID IN APP.P.ID%TYPE) AS BEGIN NULL; END;\n/',selected)
    desired=declared_procedure(desired)
    target=actual('CREATE TABLE APP.P(ID VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);',selected)
    plan=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    procedure=next(op for op in plan.operations if op.identity.object_type=='PROCEDURE')
    assert procedure.decision=='BLOCKED' and procedure.intent is None
