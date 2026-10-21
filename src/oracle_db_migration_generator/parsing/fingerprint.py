import hashlib
from functools import lru_cache
from pathlib import Path

PARSER_VERSION = 'antlr-plsql-4.13.2/generator-adapter-1.0'


@lru_cache(maxsize=1)
def parser_artifact_sha256():
    package = Path(__file__).resolve().parents[1]
    paths = list((package/'parsing').glob('*.py'))
    paths += list((package/'_vendor/analyzer_core/oracle').rglob('*.py'))
    paths += list((package/'_vendor/analyzer_core/licenses').glob('*'))
    manifest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(package).as_posix()):
        manifest.update(path.relative_to(package).as_posix().encode());manifest.update(b'\0')
        manifest.update(hashlib.sha256(path.read_bytes()).digest())
    return manifest.hexdigest()


@lru_cache(maxsize=1)
def generator_artifact_sha256():
    """Unreleased local builds still need distinct immutable payload identities."""
    package=Path(__file__).resolve().parents[1]
    manifest=hashlib.sha256()
    for path in sorted(package.rglob('*'), key=lambda item: item.relative_to(package).as_posix()):
        if path.is_file() and path.suffix in {'.py','.json','.j2','.css','.png','.txt'} and '__pycache__' not in path.parts:
            manifest.update(path.relative_to(package).as_posix().encode());manifest.update(b'\0')
            manifest.update(hashlib.sha256(path.read_bytes()).digest())
    return manifest.hexdigest()
