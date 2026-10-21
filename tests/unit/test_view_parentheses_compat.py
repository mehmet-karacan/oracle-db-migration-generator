"""Whole VIEW query parentheses must not hide valid SELECT/ORDER BY facts."""
import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.parsing.grammar_compat import grammar_text

HINT = ObjectIdentity('demo-source', Identifier.parse('APP'), 'VIEW', Identifier.parse('V'))


@pytest.mark.parametrize('query,ordering', [
    ('SELECT A FROM APP.T', None),
    ('SELECT A FROM APP.T UNION ALL SELECT A FROM APP.U', None),
    ('SELECT A FROM APP.T UNION SELECT A FROM APP.U', 'ORDER BY A DESC'),
    ('SELECT T.A FROM APP.T T LEFT JOIN APP.U U ON U.A=T.A', 'ORDER BY T.A'),
    ("SELECT q'[literal (SELECT X) ORDER BY]' A FROM APP.T", None),
])
def test_view_outer_query_parentheses_preserve_raw_and_expose_query(query, ordering):
    raw = ('CREATE OR REPLACE FORCE EDITIONABLE VIEW APP.V(A) AS\r\n (' + query + ')'
           + (' ' + ordering if ordering else '') + ';').encode()
    result = parse_ddl(raw, HINT)
    assert result.coverage == 'COMPLETE'
    view = result.objects[0]
    assert view.parse_ok and not view.diagnostics
    assert view.raw_ddl == raw
    assert view.projection.properties['declared_columns'] == ('A',)
    assert view.projection.properties['projection']
    assert view.projection.properties['query_clauses']['ordering'] == ordering
    compatible = grammar_text(raw.decode())
    assert len(compatible) == len(raw.decode())
    assert compatible.count('\r\n') == raw.decode().count('\r\n')


@pytest.mark.parametrize('query', [
    'CREATE VIEW APP.V AS (SELECT A FROM APP.T;',
    'CREATE VIEW APP.V AS (SELECT A FROM APP.T)) ORDER BY A;',
    'CREATE VIEW APP.V AS (SELECT FROM APP.T) ORDER BY A;',
    'CREATE VIEW APP.V AS (SELECT A FROM) ORDER BY A;',
    'CREATE VIEW APP.V AS (SELECT A FROM APP.T) ORDER BY;',
    'CREATE VIEW APP.V AS (SELECT A FROM APP.T) WHERE A=1;',
])
def test_view_parentheses_compatibility_does_not_validate_invalid_syntax(query):
    result = parse_ddl(query.encode(), HINT)
    assert result.coverage != 'COMPLETE'
    assert not any(view.parse_ok and not view.diagnostics for view in result.objects)


def test_nested_subquery_parentheses_and_set_branch_grouping_stay_intact():
    raw = ('CREATE VIEW APP.V AS (SELECT A FROM APP.T WHERE A IN (SELECT A FROM APP.U)) '
           'UNION SELECT A FROM APP.W;')
    assert grammar_text(raw) == raw


def test_parentheses_mask_does_not_hide_a_trailing_statement():
    raw = b'CREATE VIEW APP.V AS (SELECT A FROM APP.T); DROP TABLE APP.T;'
    result = parse_ddl(raw, HINT)
    assert result.coverage == 'PARTIAL'
    assert 'UNSUPPORTED_STATEMENT' in result.diagnostics
    assert not any(b'DROP' in item.raw_ddl and item.parse_ok for item in result.objects)
