import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from oracle_db_migration_generator.references import verify_references, validate_project_root


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)


def test_reference_paths_are_read_only(tmp_path):
    reference = tmp_path / 'reference'
    reference.mkdir()
    file = reference / 'module.py'
    file.write_text('content', encoding='utf-8')
    before = (file.read_bytes(), file.stat().st_mtime_ns)
    manifest = {'projects': [{'id': 'ref', 'files': [{'path': 'module.py', 'sha256': hashlib.sha256(b'content').hexdigest()}]}]}
    result = verify_references(manifest, {'ref': str(reference)})
    assert result['summary'] == {'matched': 1, 'changed': 0, 'missing': 0}
    assert before == (file.read_bytes(), file.stat().st_mtime_ns)
    file.write_text('new version', encoding='utf-8')
    assert verify_references(manifest, {'ref': str(reference)})['summary']['changed'] == 1


def test_wrong_or_dirty_project_root_is_not_deleted(tmp_path):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'remote', 'add', 'origin', 'https://example.invalid/wrong.git')
    marker = tmp_path / 'important.txt'
    marker.write_text('keep', encoding='utf-8')
    before = git(tmp_path, 'status', '--porcelain')
    with pytest.raises(ValueError):
        validate_project_root(tmp_path, 'https://example.invalid/expected.git')
    assert marker.read_text(encoding='utf-8') == 'keep'
    assert git(tmp_path, 'status', '--porcelain') == before
    git(tmp_path, 'remote', 'set-url', 'origin', 'https://example.invalid/expected.git')
    assert validate_project_root(tmp_path, 'https://example.invalid/expected.git')['dirty']
