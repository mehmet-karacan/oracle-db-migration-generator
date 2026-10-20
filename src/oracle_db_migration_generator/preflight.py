import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .config.credentials import EnvCredentialResolver
from .config.loader import ConfigError, load_source_profile, load_targets, read_json
from .oracle.preflight import probe_target
from .references import git_read, validate_project_root
from .source.access import git_read_environment


def probe_source(source: dict, credentials=None) -> dict:
    repository = source.get('repository', '')
    ref = source.get('suggested_ref', 'master')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*', ref) or '..' in ref:
        raise ConfigError('SOURCE_REF_INVALID')
    try:
        with git_read_environment(source, credentials) as env:
            result = subprocess.run(['git', 'ls-remote', '--exit-code', '--refs', '--', repository, 'refs/heads/' + ref],
                                    capture_output=True, env=env, timeout=25)
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'FAILED', 'error_code': 'SOURCE_CONNECTION_TIMEOUT_OR_UNAVAILABLE', 'commit': None}
    if result.returncode:
        code = 'SSH_PUBLICKEY_REJECTED' if b'Permission denied (publickey)' in result.stderr else 'SOURCE_ACCESS_OR_REF_FAILED'
        if b'Authentication failed' in result.stderr:
            code = 'SOURCE_AUTHENTICATION_FAILED'
        if b'certificate' in result.stderr.lower():
            code = 'SOURCE_TLS_VERIFICATION_FAILED'
        return {'status': 'FAILED', 'error_code': code, 'commit': None}
    rows = [line.split() for line in result.stdout.decode('ascii', errors='replace').splitlines()]
    if len(rows) != 1 or len(rows[0]) != 2 or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', rows[0][0]) or rows[0][1] != 'refs/heads/' + ref:
        return {'status': 'FAILED', 'error_code': 'SOURCE_REF_NOT_RESOLVED', 'commit': None}
    return {'status': 'PASSED', 'commit': rows[0][0], 'read_only': True, 'layout_status': 'NOT_VERIFIED'}


def write_report(path: Path, document: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='.preflight-', dir=path.parent)
    try:
        with os.fdopen(handle, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.isfile(temporary):
            os.unlink(temporary)


def _assert_ignored(root: Path, paths: list[Path]):
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or resolved.is_symlink():
            raise ConfigError('LOCAL_FILE_OUTSIDE_PROJECT')
        relative = resolved.relative_to(root).as_posix()
        if git_read(root, 'ls-files', '--', relative):
            raise ConfigError('LOCAL_FILE_IS_TRACKED')
        try:
            git_read(root, 'check-ignore', '--no-index', '--', relative)
        except ValueError:
            raise ConfigError('LOCAL_FILE_IS_NOT_IGNORED') from None


def run_preflight(settings_path: Path, output: Path) -> dict:
    context = read_json(settings_path)
    root = Path(context['project_root']).resolve()
    validate_project_root(root, context['generator_repository'])
    output = output.resolve()
    output_root = (root / 'output').resolve()
    if not output.is_relative_to(output_root) or output.suffix.lower() != '.json':
        raise ConfigError('PREFLIGHT_OUTPUT_MUST_BE_UNDER_OUTPUT')
    execution = context.get('execution', {})
    if execution.get('mode') != 'LOCAL_FIRST' or execution.get('jenkins_enabled') is not False or execution.get('publication_enabled') is not False:
        raise ConfigError('LOCAL_FIRST_SETTINGS_REQUIRED')
    profile_path = root / '.local/source-profile.sky.json'
    registry_path = root / '.local/targets.json'
    credentials_path = root / execution['credentials_file']
    _assert_ignored(root, [settings_path, profile_path, registry_path, credentials_path, output])
    profile = load_source_profile(profile_path)
    targets = load_targets(registry_path, ('ALL',))
    active = execution.get('active_schema')
    if active != 'INNOVA_ODI' or {r.source_schema for r in profile.schema_roots} != {active}:
        raise ConfigError('INITIAL_SCOPE_MUST_BE_INNOVA_ODI')
    if any(m.source_schema != active or m.target_schema != active for t in targets for m in t.schema_mappings):
        raise ConfigError('INITIAL_SCOPE_MUST_BE_INNOVA_ODI')
    if context['source'].get('read_only') is not True:
        raise ConfigError('SOURCE_READ_ONLY_REQUIRED')
    resolver = EnvCredentialResolver(credentials_path)
    source = probe_source(context['source'], resolver)
    observations = [probe_target(target, resolver) for target in targets]
    report = {'schema_version': 'local-preflight/1.0', 'captured_at': datetime.now(timezone.utc).isoformat(),
              'status': 'PASSED' if source['status'] == 'PASSED' and all(t['status'] == 'PASSED' for t in observations) else 'FAILED',
              'source': source, 'targets': observations, 'comparison_status': 'NOT_RUN',
              'difference_count': None, 'execution_status': 'NOT_EXECUTED', 'jenkins_enabled': False,
              'publication_enabled': False}
    write_report(output, report)
    return report
