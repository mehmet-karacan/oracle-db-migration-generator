"""Schema Compare farklarının gerçek DDL dosyası üretmesini sınar.

Sentetik kaynak ve hedef kullanılır. Oracle bağlantısı veya SQL uygulaması yoktur.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from oracle_db_migration_generator.artifacts.bundle import verify_bundle, write_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue
from oracle_db_migration_generator.planning.context import PlanningContext
from oracle_db_migration_generator.planning.graph import _block
from oracle_db_migration_generator.planning.rules import plan_target
from tests.factories import actual, profile, source
from tests.unit.test_rules import plan


def proposed(result, name='T'):
    candidates = [op for op in result.operations if op.identity.name.effective_name == name
                  and op.decision in {'BLOCKED', 'REVIEW_REQUIRED'}]
    assert candidates
    assert all(op.proposal is not None for op in candidates)
    return '\n'.join(op.proposal.statement.decode() for op in candidates)


def test_dependency_failure_preserves_prepared_statement_as_proposal():
    operation = next(op for op in plan('CREATE SEQUENCE APP.T START WITH 1;', '').operations
                     if op.intent is not None)
    blocked = _block(operation, 'DEPENDENCY_UNVERIFIED', ['Bağımlılık doğrulanamadı'])
    assert blocked.decision == 'BLOCKED' and blocked.intent is None
    assert blocked.proposal == operation.intent
    assert blocked.proposal.statement == operation.intent.statement


@pytest.mark.parametrize(('wanted', 'observed', 'ddl'), [
    ('DATE', 'TIMESTAMP(6)', 'MODIFY ("C" DATE)'),
    ('FLOAT(126)', 'NUMBER(18,2)', 'MODIFY ("C" FLOAT(126))'),
    ('NUMBER(*,0)', 'NUMBER', 'MODIFY ("C" NUMBER(*,0))'),
])
def test_existing_column_emits_source_type_without_data_checks(wanted, observed, ddl):
    result = plan(f'CREATE TABLE APP.T(C {wanted});', f'CREATE TABLE APP.T(C {observed});')
    text = proposed(result)
    assert 'ALTER TABLE "APP"."T"' in text and ddl in text
    assert 'CREATE TABLE' not in text


def test_constraint_state_uses_alter_and_preserves_source_validation():
    result = plan('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT C CHECK(ID>0) ENABLE NOVALIDATE);',
                  'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT C CHECK(ID>0) ENABLE VALIDATE);')
    assert 'MODIFY CONSTRAINT "C" ENABLE NOVALIDATE' in proposed(result)
    assert all('henüz tanımlı değil' not in op.reason_tr for op in result.operations if op.proposal)


def test_anonymous_primary_key_uses_kind_instead_of_generated_name():
    result = plan('CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID) DISABLE);',
                  'CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID) ENABLE);')
    text = proposed(result)
    assert 'MODIFY PRIMARY KEY DISABLE' in text
    assert '@anonymous' not in text


def test_constraint_definition_change_emits_drop_and_source_add():
    result = plan('CREATE TABLE APP.T(A NUMBER,B NUMBER, CONSTRAINT C UNIQUE(B));',
                  'CREATE TABLE APP.T(A NUMBER,B NUMBER, CONSTRAINT C UNIQUE(A));')
    text = proposed(result)
    assert 'DROP CONSTRAINT "C"' in text
    assert 'ADD CONSTRAINT C UNIQUE(B)' in text


def test_unverified_nullability_still_has_source_alter_proposal():
    result = plan('CREATE TABLE APP.T(ID NUMBER);', 'CREATE TABLE APP.T(ID NUMBER NOT NULL);')
    assert 'MODIFY ("ID" NULL)' in proposed(result)


def test_function_index_keeps_original_expression_and_create():
    sql = 'CREATE INDEX APP.IX ON APP.T(CASE WHEN ID>0 THEN ID END);'
    result = plan('CREATE TABLE APP.T(ID NUMBER);\n'+sql, 'CREATE TABLE APP.T(ID NUMBER);')
    assert sql.rstrip(';') in proposed(result, 'IX')


def test_changed_index_has_recreation_ddl_without_altering_source_text():
    sql = 'CREATE UNIQUE INDEX APP.IX ON APP.T(ID);'
    result = plan('CREATE TABLE APP.T(ID NUMBER);\n'+sql,
                  'CREATE TABLE APP.T(ID NUMBER); CREATE INDEX APP.IX ON APP.T(ID);')
    text = proposed(result, 'IX')
    assert 'DROP INDEX "APP"."IX";' in text
    assert sql.rstrip(';') in text


def test_partition_bound_change_uses_full_source_partition_clause():
    result = plan('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) (PARTITION P VALUES LESS THAN(20));',
                  'CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) (PARTITION P VALUES LESS THAN(10));')
    text = proposed(result)
    assert 'ALTER TABLE "APP"."T" MODIFY PARTITION BY RANGE(ID)' in text
    assert 'LESS THAN(20)' in text
    assert 'CREATE TABLE' not in text and 'DROP TABLE' not in text


def test_metadata_collation_without_raw_clause_still_emits_the_recorded_value():
    from oracle_db_migration_generator.planning.ddl_proposals import proposal_statement
    obj = source('CREATE TABLE APP.T(C VARCHAR2(10));').objects[0]
    diff = SimpleNamespace(property_path='/columns/C/collation',
                           after=KnownValue('KNOWN', 'USING_NLS_COMP', ()))
    sql, _ = proposal_statement(obj, object(), [diff])
    assert sql is not None and b'COLLATE "USING_NLS_COMP"' in sql


def test_constraint_state_can_come_from_recorded_metadata_without_inline_definition():
    from oracle_db_migration_generator.planning.ddl_proposals import proposal_statement
    from oracle_db_migration_generator.parsing.canonicalize import canonical_sql
    obj = source('CREATE TABLE APP.T(ID NUMBER);').objects[0]
    diff = SimpleNamespace(property_path='/constraints/C/enabled',
                           after=KnownValue('KNOWN', canonical_sql('ENABLE'), ()))
    sql, _ = proposal_statement(obj, object(), [diff])
    assert sql is not None and b'MODIFY CONSTRAINT "C" ENABLE' in sql


@pytest.mark.parametrize('ambiguous', [False, True])
def test_anonymous_foreign_key_resolves_real_catalog_name_without_guessing(ambiguous):
    from oracle_db_migration_generator.planning.ddl_proposals import proposal_statement
    from oracle_db_migration_generator.parsing.canonicalize import canonical_sql
    from oracle_db_migration_generator.planning.table_ddl import source_projection
    desired = source('CREATE TABLE APP.T(C NUMBER, FOREIGN KEY(C) REFERENCES APP.P(ID) DISABLE);').objects[0]
    observed = actual('CREATE TABLE APP.T(C NUMBER, FOREIGN KEY(C) REFERENCES APP.P(ID) ENABLE);').objects[0]
    names = ['SYS_C42', 'SYS_C43'] if ambiguous else ['SYS_C42']
    props = dict(observed.properties)
    props['dictionary.constraints'] = KnownValue('KNOWN', [
        {'table_name': 'T', 'constraint_name': name, 'constraint_type': 'R', 'r_owner': 'APP'} for name in names], ())
    props['dictionary.constraint_columns'] = KnownValue('KNOWN', [
        {'table_name': 'T', 'constraint_name': name, 'column_name': 'C', 'position': 1} for name in names], ())
    observed = replace(observed, properties=props)
    name = next(iter(source_projection(desired).properties['constraints']))
    diff = SimpleNamespace(property_path='/constraints/'+name+'/enabled',
                           after=KnownValue('KNOWN', canonical_sql('DISABLE'), ()))
    sql, _ = proposal_statement(desired, observed, [diff])
    if ambiguous:
        assert sql is None
    else:
        assert sql is not None and b'MODIFY CONSTRAINT "SYS_C42" DISABLE' in sql
        assert b'@anonymous' not in sql


def test_named_lob_source_definition_is_not_downgraded_to_heap():
    sql = 'CREATE TABLE APP.T(ID NUMBER, B BLOB) LOB(B) STORE AS BASICFILE LOB_SEG (NOCACHE LOGGING);'
    result = plan(sql, '')
    assert sql.rstrip(';') == proposed(result).strip().rstrip(';')


def test_incomplete_projection_retains_full_plsql_body_and_warning(tmp_path):
    sql = 'CREATE PROCEDURE APP.P IS BEGIN NULL; END;'
    desired = source(sql)
    obj = desired.objects[0]
    desired = replace(desired, objects=(replace(obj, coverage=Coverage('COMPLETE', 'PARTIAL', 'PARTIAL', ('PARSER_TIMEOUT',))),))
    target = actual('')
    selected = profile()
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Test'))
    operation = next(op for op in result.operations if op.identity.name.effective_name == 'P')
    assert operation.decision == 'BLOCKED' and operation.intent is None
    assert operation.proposal is not None
    assert 'CREATE OR REPLACE PROCEDURE APP.P IS BEGIN NULL; END;' in operation.proposal.statement.decode()
    bundle = tmp_path/'bundle'
    write_bundle(result, bundle, source=desired)
    raw = next(bundle.glob('proposals/**/*.sql')).read_text(encoding='utf-8')
    assert '-- Gerekçe ' in raw and 'END;\n/' in raw
    assert verify_bundle(bundle)['status'] == 'VERIFIED'
