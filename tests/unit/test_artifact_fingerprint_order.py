import hashlib
from pathlib import Path

from oracle_db_migration_generator.parsing import fingerprint


def portable_hash(package, paths):
    result = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(package).as_posix()):
        result.update(path.relative_to(package).as_posix().encode())
        result.update(b'\0')
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def test_generator_fingerprint_uses_portable_path_order():
    package = Path(fingerprint.__file__).resolve().parents[1]
    paths = [path for path in package.rglob('*')
             if path.is_file() and path.suffix in {'.py', '.json', '.j2', '.css', '.png', '.txt'}
             and '__pycache__' not in path.parts]
    fingerprint.generator_artifact_sha256.cache_clear()
    assert fingerprint.generator_artifact_sha256() == portable_hash(package, paths)


def test_parser_fingerprint_uses_portable_path_order():
    package = Path(fingerprint.__file__).resolve().parents[1]
    paths = list((package / 'parsing').glob('*.py'))
    paths += list((package / '_vendor/analyzer_core/oracle').rglob('*.py'))
    paths += list((package / '_vendor/analyzer_core/licenses').glob('*'))
    fingerprint.parser_artifact_sha256.cache_clear()
    assert fingerprint.parser_artifact_sha256() == portable_hash(package, paths)
