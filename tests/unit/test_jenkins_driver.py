from dataclasses import replace
from unittest.mock import Mock

import pytest

from oracle_db_migration_generator.config.models import TargetConfig,Endpoint


def target_config():
    return TargetConfig('LOCAL-ODI','Synthetic',True,Endpoint('oracle.invalid',1521,service_name='demo'),'thin',())


def test_thin_driver_never_loads_native_client(monkeypatch):
    from tools.jenkins_run import initialize_oracle_driver
    monkeypatch.setattr('oracledb.init_oracle_client',lambda **kw:pytest.fail('Native load forbidden'))
    assert initialize_oracle_driver((target_config(),),None)=='thin'


def test_thick_driver_initializes_once_before_any_connection(tmp_path,monkeypatch):
    from tools.jenkins_run import initialize_oracle_driver
    init=Mock();monkeypatch.setattr('oracledb.init_oracle_client',init)
    monkeypatch.setattr('oracledb.is_thin_mode',lambda:False)
    targets=(replace(target_config(),driver_mode='thick'),)*2
    assert initialize_oracle_driver(targets,tmp_path)=='thick'
    init.assert_called_once_with(lib_dir=str(tmp_path.resolve()))


@pytest.mark.parametrize('case',['mixed','missing','load-error','still-thin'])
def test_driver_rejects_unsafe_mode_or_client_without_connecting(tmp_path,monkeypatch,case):
    from tools.jenkins_run import initialize_oracle_driver
    thin=target_config();thick=replace(thin,driver_mode='thick')
    targets=(thin,thick) if case=='mixed' else (thick,)
    monkeypatch.setattr('oracledb.connect',lambda **kw:pytest.fail('Oracle forbidden'))
    init=Mock(side_effect=RuntimeError('sensitive native details')) if case=='load-error' else Mock()
    monkeypatch.setattr('oracledb.init_oracle_client',init)
    monkeypatch.setattr('oracledb.is_thin_mode',lambda:True)
    with pytest.raises(ValueError,match='^JENKINS_ORACLE_DRIVER_') as caught:
        initialize_oracle_driver(targets,None if case=='missing' else tmp_path)
    assert 'sensitive' not in str(caught.value)
    if case in {'mixed','missing'}:init.assert_not_called()
