from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.model.identity import Identifier,ObjectIdentity
from oracle_db_migration_generator.parsing.canonicalize import canonical_sql
HINT=ObjectIdentity('demo-source',Identifier.parse('APP'),'TYPE_SPEC',Identifier.parse('T'))

def test_type_modify_attribute_models_final_structure_and_retains_full_raw():
    raw=b'CREATE TYPE APP.T AS OBJECT (ID NUMBER, X VARCHAR2(100)) ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR(200)) CASCADE;'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE'
    item=result.objects[0]
    assert item.raw_ddl==raw
    assert item.projection.properties['_generator_effective_definition']==canonical_sql('CREATE TYPE APP.T AS OBJECT (ID NUMBER, X VARCHAR2(200))')


def test_type_modify_attribute_is_sequential_and_rejects_foreign_or_unknown_attribute():
    for alter in ('ALTER TYPE APP.OTHER MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;',
                  'ALTER TYPE APP.T MODIFY ATTRIBUTE (Y VARCHAR2(200)) CASCADE;',
                  'ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200) garbage) CASCADE;',
                  'ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE; DROP TABLE APP.VICTIM;'):
        result=parse_ddl(('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)) '+alter).encode(),HINT)
        assert result.coverage!='COMPLETE',alter


def test_type_repeated_attribute_modification_has_last_verified_value():
    result=parse_ddl(b'CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)); ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE; ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(300)) CASCADE;',HINT)
    assert result.coverage=='COMPLETE'
    assert result.objects[0].projection.properties['_generator_effective_definition']==canonical_sql('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(300))')

def test_missing_type_emits_verified_final_create_preserving_other_attributes():
    from tests.unit.test_backend_completion import plan
    from oracle_db_migration_generator.emission.sql import render_statement
    sql='CREATE TYPE APP.T AS OBJECT (ID    NUMBER,\n  X VARCHAR2(100)) ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR(200)) CASCADE;'
    result=plan(sql)
    operation=next(op for op in result.operations if op.identity.object_type=='TYPE_SPEC')
    assert operation.decision=='READY'
    emitted=render_statement(operation,result.plan_id)
    assert b'ID    NUMBER,\n  X VARCHAR(200)' in emitted
    assert b'ALTER TYPE' not in emitted
    assert b'CREATE OR REPLACE TYPE APP.T AS OBJECT' in emitted


def test_type_final_definition_matches_direct_export():
    from tests.factories import source,actual,profile
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    desired=source('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)) ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR(200)) CASCADE;')
    target=actual('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(200));')
    differences=compare_snapshots(desired,target,profile().policy)
    assert not differences.differences

def test_type_modify_attribute_accepts_standalone_sqlplus_delimiters_only():
    raw=b'CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100));\n/\nALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;\n/'
    result=parse_ddl(raw,HINT)
    assert result.coverage=='COMPLETE'
    assert result.objects[0].raw_ddl==raw
    assert result.objects[0].projection.properties['_generator_effective_definition']==canonical_sql('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(200))')
    malformed=parse_ddl(b'CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)) / ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;',HINT)
    assert malformed.coverage!='COMPLETE'

def test_derived_type_create_cannot_drift_from_its_raw_sql():
    from dataclasses import replace
    from oracle_db_migration_generator.parsing.projections import normalize_projection
    raw=b'CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)) ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;'
    projection=parse_ddl(raw,HINT).objects[0].projection
    tampered=replace(projection,properties={**projection.properties,'_generator_effective_create':'CREATE TYPE APP.T AS OBJECT (X VARCHAR2(999))'})
    checked=normalize_projection(tampered,raw.decode())
    assert 'DERIVED_TYPE_DEFINITION_SOURCE_MISMATCH' in checked.diagnostics

def test_planner_rejects_derived_type_create_that_was_changed_after_parsing():
    from dataclasses import replace
    from tests.factories import source,actual,profile
    from oracle_db_migration_generator.model.snapshot import KnownValue
    from oracle_db_migration_generator.model.serialization import thaw
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
    desired=source('CREATE TYPE APP.T AS OBJECT (X VARCHAR2(100)) ALTER TYPE APP.T MODIFY ATTRIBUTE (X VARCHAR2(200)) CASCADE;')
    obj=desired.objects[0];values=thaw(obj.properties['projection'].value)
    values['_generator_effective_create']='CREATE TYPE APP.T AS OBJECT (X VARCHAR2(999))'
    obj=replace(obj,projection=None,properties={**obj.properties,'projection':KnownValue('KNOWN',values,obj.evidence_ids)})
    desired=replace(desired,objects=(obj,));target=actual();selected=profile()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))
    assert result.operations[0].decision=='BLOCKED'
    assert 'TYPE_EFFECTIVE_DEFINITION_UNVERIFIED' in result.operations[0].reason_codes

