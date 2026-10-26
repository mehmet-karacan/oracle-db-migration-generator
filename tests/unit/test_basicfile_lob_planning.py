from dataclasses import replace

import pytest

from test_rules import plan
from tests.factories import actual, source, profile
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from oracle_db_migration_generator.emission.sql import render_statement


@pytest.mark.parametrize('datatype', ['CLOB', 'BLOB', 'NCLOB'])
def test_new_heap_lob_preserves_basicfile_clause_and_separate_constraint(datatype):
    tail = '''LOB ("PAYLOAD") STORE AS BASICFILE (
  TABLESPACE "USERS" ENABLE STORAGE IN ROW CHUNK 8192 RETENTION
  NOCACHE LOGGING STORAGE (INITIAL 65536 NEXT 1048576 MINEXTENTS 1
  MAXEXTENTS 2147483645 PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT))'''
    result = plan(f'CREATE TABLE APP.DOCS (ID NUMBER, PAYLOAD {datatype}, CONSTRAINT PK_DOCS PRIMARY KEY(ID)) {tail};')
    create = next((o for o in result.operations if o.kind == 'CREATE' and o.decision == 'READY'), None)
    assert create is not None
    assert tail.encode() in create.intent.statement
    assert any(o.kind == 'ADD_CONSTRAINT' and o.decision == 'READY' for o in result.operations)
    emitted = render_statement(create, 'test')
    assert tail.encode() in emitted


@pytest.mark.parametrize('tail', [
    'LOB (PAYLOAD) STORE AS SECUREFILE (NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE NAMED_SEGMENT (NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE (CHUNK 65536 NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE (ENCRYPT)',
    'LOB (ID) STORE AS BASICFILE (NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE ()',
    'LOB (PAYLOAD) STORE AS BASICFILE (RETENTION NONE)',
    'LOB (PAYLOAD) STORE AS BASICFILE (CHUNK 8192 CHUNK 16384 NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE (TABLESPACE USERS TABLESPACE OTHER NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE (CACHE NOCACHE LOGGING)',
    'LOB (PAYLOAD) STORE AS BASICFILE (NOCACHE LOGGING STORAGE(INITIAL 65536 INITIAL 131072))',
])
def test_unproven_lob_variants_do_not_become_ready(tail):
    result = plan(f'CREATE TABLE APP.DOCS (ID NUMBER, PAYLOAD CLOB) {tail};')
    assert result.operations and not any(o.decision == 'READY' for o in result.operations)


def test_lob_creation_needs_target_version_proof():
    selected = profile(); desired = source('CREATE TABLE APP.DOCS (PAYLOAD CLOB) LOB(PAYLOAD) STORE AS BASICFILE (NOCACHE LOGGING);', selected)
    target = actual('', selected)
    target = replace(target, capabilities={k:v for k,v in target.capabilities.items() if k != 'oracle_major'})
    result = plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Target'))
    assert result.operations and not any(o.decision == 'READY' for o in result.operations)
