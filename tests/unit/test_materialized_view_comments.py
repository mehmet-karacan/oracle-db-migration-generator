import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.parsing.statements import sidecar_facts
from tests.factories import source, profile


def test_materialized_view_comment_retains_target_literal_and_raw_sql():
    sql = "COMMENT ON MATERIALIZED VIEW APP.MV IS q'[summary; 'quoted']';"
    facts = sidecar_facts(sql, 'APP')
    assert len(facts) == 1
    assert facts[0]['target'] == 'MV'
    assert facts[0]['target_type'] == 'MATERIALIZED_VIEW'
    assert facts[0]['text'] == "summary; 'quoted'"
    assert facts[0]['raw_ddl'] == sql.encode()
    hint = ObjectIdentity('demo', Identifier.parse('APP'), 'MATERIALIZED_VIEW', Identifier.parse('MV'))
    result = parse_ddl(sql.encode(), hint)
    assert result.coverage == 'COMPLETE'
    assert len(result.sidecars) == 1 and result.sidecars[0]['kind'] == 'COMMENT'


def test_materialized_comment_attaches_to_materialized_view_parent():
    observed = source("CREATE MATERIALIZED VIEW APP.MV AS SELECT 1 ID FROM DUAL;\n"
                      "COMMENT ON MATERIALIZED VIEW APP.MV IS 'summary';", profile())
    view = next(item for item in observed.objects if item.identity.object_type == 'MATERIALIZED_VIEW')
    comment = next(item for item in observed.objects if item.identity.object_type == 'COMMENT')
    assert comment.identity.parent_key == view.object_key
    assert comment.coverage.ddl == 'COMPLETE'
    assert 'target_type' not in comment.properties  # Parent resolution is not a comment difference.


@pytest.mark.parametrize('sql', [
    "COMMENT ON MATERIALIZED VIEW APP.MV IS 'summary' garbage;",
    "COMMENT ON MATERIALIZED VIEW APP.MV IS;",
])
def test_malformed_materialized_comment_remains_unparsed(sql):
    hint = ObjectIdentity('demo', Identifier.parse('APP'), 'MATERIALIZED_VIEW', Identifier.parse('MV'))
    assert parse_ddl(sql.encode(), hint).coverage != 'COMPLETE'
