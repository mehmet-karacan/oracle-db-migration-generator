"""Şema Karşılaştırma ortam adlarının yalnız bağlı raporda görünmesini sınar.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
from copy import deepcopy

import pytest

from oracle_db_migration_generator.reporting.render import render_email
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


def context(run, **changes):
    return {'run_id': run['run_id'], 'source_commit': run['source_commit'],
            'source_environment': 'UAT', 'target_environments': {'TARGET-000': 'PROD'}, **changes}


def test_target_display_hides_connection_account_without_changing_the_plan():
    run, plans = inputs()
    plans['TARGET-000']['target']['name'] = 'SKY - PROD - LOGIN_ACCOUNT'
    before = deepcopy((run, plans))
    view = build_run_view(run, plans, display_context=context(run))
    view['source_schemas'] = ['APP']
    html = render_email(view, preview=True).decode()
    assert view['source_environment'] == 'UAT'
    assert 'APP - UAT' in html and 'APP - PROD' in html and 'LOGIN_ACCOUNT' not in html
    assert view['targets'][0]['schemas'] == ['APP']
    assert (run, plans) == before


@pytest.mark.parametrize('changes', [{'run_id': 'other-project-run'},
    {'source_commit': 'b'*40}, {'target_environments': {'OTHER': 'PROD'}}])
def test_environment_context_cannot_be_used_for_another_run_or_target(changes):
    run, plans = inputs()
    with pytest.raises(ValueError, match='REPORT_DISPLAY_CONTEXT_MISMATCH'):
        build_run_view(run, plans, display_context=context(run, **changes))
