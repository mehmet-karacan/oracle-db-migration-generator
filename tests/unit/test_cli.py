import json
from pathlib import Path

import pytest

from oracle_db_migration_generator.cli import main
from oracle_db_migration_generator.config.loader import ConfigError
from oracle_db_migration_generator.preflight import probe_source, run_preflight

ROOT = Path(__file__).resolve().parents[2]


def test_validate_config_is_offline_and_errors_are_sanitized(tmp_path, capsys):
    result = main(['validate-config', '--source-profile', str(ROOT / 'examples/source-profile.example.json'),
                   '--targets', str(ROOT / 'examples/targets.example.json')])
    assert result == 0
    assert json.loads(capsys.readouterr().out)['network_accessed'] is False
    invalid = tmp_path / 'bad.json'
    invalid.write_text('{"secret": "synthetic-secret"}', encoding='utf-8')
    assert main(['validate-config', '--source-profile', str(invalid), '--targets', str(invalid)]) == 30
    assert 'synthetic-secret' not in capsys.readouterr().out


def test_source_probe_is_read_only_and_does_not_leak_provider_errors(monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return type('Result', (), {'returncode': 128, 'stderr': b'Permission denied (publickey). synthetic-secret'})()
    monkeypatch.setattr('oracle_db_migration_generator.preflight.subprocess.run', run)
    result = probe_source({'repository': 'ssh://git@source.example.invalid:7999/demo/schema.git', 'suggested_ref':'master'})
    assert result['error_code'] == 'SSH_PUBLICKEY_REJECTED'
    assert 'synthetic-secret' not in json.dumps(result)
    argv, kwargs = calls[0]
    assert argv[:4] == ['git', 'ls-remote', '--exit-code', '--refs']
    assert 'StrictHostKeyChecking=yes' in kwargs['env']['GIT_SSH_COMMAND']
    assert 'BatchMode=yes' in kwargs['env']['GIT_SSH_COMMAND']


def test_preflight_refuses_output_over_local_configuration(tmp_path, monkeypatch):
    local = tmp_path / '.local'
    local.mkdir()
    settings = local / 'session-context.json'
    document = {'project_root': str(tmp_path), 'generator_repository': 'https://example.invalid/generator.git',
                'execution': {'mode':'LOCAL_FIRST', 'jenkins_enabled':False, 'publication_enabled':False,
                              'credentials_file':'.local/credentials.env'}}
    settings.write_text(json.dumps(document), encoding='utf-8')
    monkeypatch.setattr('oracle_db_migration_generator.preflight.validate_project_root', lambda *_: {})
    monkeypatch.setattr('oracle_db_migration_generator.preflight._assert_ignored', lambda *_: None)
    before = settings.read_bytes()
    with pytest.raises(ConfigError, match='PREFLIGHT_OUTPUT_MUST_BE_UNDER_OUTPUT'):
        run_preflight(settings, settings)
    assert settings.read_bytes() == before


def test_https_source_uses_askpass_without_credentials_in_url_or_argv(monkeypatch):
    from oracle_db_migration_generator.config.credentials import Credentials
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        script = Path(kwargs['env']['GIT_ASKPASS'])
        assert script.exists()
        assert 'synthetic-source-password' not in script.read_text(encoding='utf-8')
        assert 'synthetic-source-password' not in ' '.join(argv)
        assert kwargs['env']['ODMG_SOURCE_PASSWORD'] == 'synthetic-source-password'
        return type('Result', (), {'returncode': 0, 'stdout': (('a' * 40) + '\trefs/heads/master\n').encode(), 'stderr': b''})()
    monkeypatch.setattr('oracle_db_migration_generator.preflight.subprocess.run', run)
    source = {'repository': 'https://source.example.invalid/scm/demo/schema.git',
              'suggested_ref': 'master', 'credential_id': 'LOCAL_SOURCE'}
    result = probe_source(source, lambda _: Credentials('demo', 'synthetic-source-password'))
    assert result['commit'] == 'a' * 40 and result['status'] == 'PASSED'
    assert not Path(calls[0][1]['env']['GIT_ASKPASS']).exists()
    assert 'synthetic-source-password' not in json.dumps(result)


def test_prepare_source_creates_a_pinned_self_contained_snapshot(tmp_path,capsys):
    import subprocess
    repo = tmp_path/'repo';repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL)
    git('init','-b','main')
    sql = repo/'app/tables/DEMO/ddl.sql';sql.parent.mkdir(parents=True)
    sql.write_text('CREATE TABLE APP.DEMO (ID NUMBER);',encoding='utf-8')
    git('add','app')
    git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-m','fixture')
    result = main(['prepare-source','--repo',str(repo),'--ref','main',
                   '--source-profile',str(ROOT/'examples/source-profile.example.json'),
                   '--output',str(tmp_path/'prepared')])
    assert result==0
    assert (tmp_path/'prepared/source-snapshot.json').is_file()
    assert (tmp_path/'prepared/app/tables/DEMO/ddl.sql').read_bytes()==sql.read_bytes()
    assert json.loads(capsys.readouterr().out.splitlines()[-1])['status']=='PREPARED'
