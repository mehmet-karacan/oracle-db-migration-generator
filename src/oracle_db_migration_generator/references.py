"""Inspect references and project identity without modifying either checkout."""
import hashlib
import subprocess
from pathlib import Path, PurePosixPath


def git_read(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args], capture_output=True,
                            timeout=20, check=False)
    if result.returncode:
        raise ValueError('GIT_READ_FAILED')
    return result.stdout.decode('utf-8', errors='replace').strip()


def validate_project_root(root: Path, expected_origin: str) -> dict:
    root = root.resolve()
    top = Path(git_read(root, 'rev-parse', '--show-toplevel')).resolve()
    if root != top or git_read(root, 'remote', 'get-url', 'origin').rstrip('/') != expected_origin.rstrip('/'):
        raise ValueError('PROJECT_ROOT_OR_ORIGIN_MISMATCH')
    return {'valid': True, 'dirty': bool(git_read(root, 'status', '--porcelain'))}


def verify_references(lock: dict, paths: dict) -> dict:
    summary = {'matched': 0, 'changed': 0, 'missing': 0}
    projects = []
    for project in lock['projects']:
        root = Path(paths[project['id']]).resolve()
        records = []
        for file in project['files']:
            rel = PurePosixPath(file['path'])
            candidate = root.joinpath(*rel.parts)
            if rel.is_absolute() or '..' in rel.parts or not candidate.resolve().is_relative_to(root):
                raise ValueError('INVALID_REFERENCE_PATH')
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None
            status = 'missing' if digest is None else 'matched' if digest == file['sha256'] else 'changed'
            summary[status] += 1
            records.append({'path': file['path'], 'expected_sha256': file['sha256'], 'actual_sha256': digest, 'status': status})
        try:
            commit = git_read(root, 'rev-parse', 'HEAD')
            status = git_read(root, 'status', '--porcelain')
        except ValueError:
            commit, status = None, None
        projects.append({'id': project['id'], 'commit': commit, 'git_status': status, 'files': records})
    return {'schema_version': 'reference-check/1.0', 'summary': summary, 'projects': projects,
            'status': 'DRIFT_REQUIRES_REVIEW' if summary['changed'] or summary['missing'] else 'MATCHED'}
