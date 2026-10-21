import pytest

from oracle_db_migration_generator.compare.projection_adapter import table_columns
from tests.factories import profile, source


@pytest.mark.parametrize('state,want_nullable', [('DISABLE',True), ('ENABLE',False), ('',False), ('NOT DEFERRABLE DISABLE',True)])
def test_inline_not_null_state_controls_catalog_nullability(state,want_nullable):
    snapshot=source(f'CREATE TABLE APP.T(C VARCHAR2(20) NOT NULL {state});',profile())
    obj=snapshot.objects[0]
    assert table_columns(obj,snapshot)['C']['nullable'].value is want_nullable


@pytest.mark.parametrize('state,want_nullable', [('DISABLE',True),('ENABLE',False),('',False)])
def test_primary_key_state_controls_catalog_nullability(state,want_nullable):
    snapshot=source(f'CREATE TABLE APP.T(ID NUMBER, PRIMARY KEY(ID) {state});',profile())
    obj=snapshot.objects[0]
    assert table_columns(obj,snapshot)['ID']['nullable'].value is want_nullable


def test_disabled_key_does_not_override_independent_enabled_not_null():
    snapshot=source('CREATE TABLE APP.T(ID NUMBER NOT NULL ENABLE, PRIMARY KEY(ID) DISABLE);',profile())
    assert table_columns(snapshot.objects[0],snapshot)['ID']['nullable'].value is False


def test_reconstructed_column_does_not_enable_disabled_not_null():
    from oracle_db_migration_generator.planning.table_ddl import column_definition, source_projection
    snapshot=source('CREATE TABLE APP.T(C NUMBER NOT NULL DISABLE);',profile())
    detail=source_projection(snapshot.objects[0]).properties['columns']['C']
    sql=column_definition('C',detail,reconstruct=True)
    assert sql == '"C" NUMBER NOT NULL DISABLE'
