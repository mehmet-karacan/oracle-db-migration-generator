"""IN subqueries must validate complete CTE syntax without rewriting SQL."""
import base64

import pytest

from oracle_db_migration_generator.parsing.grammar_compat import grammar_text
from oracle_db_migration_generator.parsing.worker import checked_units, parse_payload


def package(query):
    return f'''CREATE OR REPLACE PACKAGE BODY APP.PKG_CTE AS
  PROCEDURE run IS
    result NUMBER;
  BEGIN
    SELECT
      COUNT(*) INTO result
    FROM APP.items
    WHERE id IN ({query});
  END run;
END PKG_CTE;
/
'''


@pytest.mark.parametrize('query', [
    'WITH chosen AS (SELECT id FROM APP.lookup) SELECT id FROM chosen',
    'WITH a AS (SELECT id FROM APP.lookup), b AS (SELECT id FROM a) SELECT id FROM b',
    'WITH a (id) AS (SELECT id FROM APP.lookup) SELECT id FROM a UNION SELECT id FROM APP.other',
    'WITH a AS (SELECT id FROM APP.lookup WHERE id IN (WITH b AS (SELECT id FROM APP.other) SELECT id FROM b)) SELECT id FROM a',
])
def test_in_with_subquery_validates_full_package_and_keeps_source_spans(query):
    text = package(query)
    assert grammar_text(text) == text
    ok, units = checked_units(text, 'PACKAGE_BODY')
    assert ok
    assert len(units) == 1
    assert text[units[0][1]:units[0][2]].endswith('END PKG_CTE;')
    result = parse_payload({'raw': base64.b64encode(text.encode()).decode(), 'default_schema': 'APP'})
    assert result['diagnostics'] == []
    assert result['objects'][0]['parse_ok']
    assert text[result['objects'][0]['start_char']:result['objects'][0]['end_char']].endswith('END PKG_CTE;')


@pytest.mark.parametrize('query', [
    'WITH chosen AS (SELECT FROM APP.lookup) SELECT id FROM chosen',
    'WITH chosen AS (SELECT id FROM APP.lookup) SELECT FROM chosen',
    'WITH chosen AS (SELECT id FROM APP.lookup) garbage SELECT id FROM chosen',
    'WITH chosen (id) (SELECT id FROM APP.lookup) SELECT id FROM chosen',
    'WITH chosen AS (SELECT id FROM APP.lookup) SELECT id FROM chosen; DELETE FROM APP.items',
])
def test_in_with_subquery_rejects_malformed_cte_or_unvalidated_suffix(query):
    assert not checked_units(package(query), 'PACKAGE_BODY')[0]


@pytest.mark.parametrize('query', ['1, 2, 3', 'SELECT id FROM APP.lookup', "'WITH broken syntax'"])
def test_ordinary_in_remains_supported(query):
    assert checked_units(package(query), 'PACKAGE_BODY')[0]


def test_cte_adapter_does_not_mutate_generated_atn_or_prediction_caches():
    from oracle_db_migration_generator.parsing.grammar_compat import CompatiblePlSqlParser
    from oracle_db_migration_generator._vendor.analyzer_core.oracle.generated.PlSqlParser import PlSqlParser
    from antlr4.atn.Transition import RuleTransition

    def targets(atn):
        return [transition.ruleIndex for state in atn.states
                if state is not None and state.ruleIndex == PlSqlParser.RULE_in_elements
                for transition in state.transitions if isinstance(transition, RuleTransition)]

    assert PlSqlParser.RULE_subquery in targets(PlSqlParser.atn)
    assert PlSqlParser.RULE_subquery not in targets(CompatiblePlSqlParser.atn)
    assert PlSqlParser.RULE_select_only_statement in targets(CompatiblePlSqlParser.atn)
    assert PlSqlParser.atn is not CompatiblePlSqlParser.atn
    assert PlSqlParser.decisionsToDFA is not CompatiblePlSqlParser.decisionsToDFA
    assert PlSqlParser.sharedContextCache is not CompatiblePlSqlParser.sharedContextCache
