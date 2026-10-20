"""Python 3.10 compatible, hash-locked release installer in the job workspace."""
import argparse
import hashlib
import json
import os
import re
import posixpath
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def safe(root,relative):
    if not relative or '\\' in relative or ':' in relative or relative.startswith('/') or any(p in {'','..','.'} for p in relative.split('/')):
        raise ValueError('RELEASE_PATH_UNSAFE')
    result=root.joinpath(*PurePosixPath(relative).parts)
    if not result.resolve().is_relative_to(root.resolve()):raise ValueError('RELEASE_PATH_UNSAFE')
    return result


def verify_release(root):
    root=Path(root).resolve();manifest=json.loads((root/'release-manifest.json').read_bytes())
    if set(manifest)!={'schema_version','files'} or manifest['schema_version']!='jenkins-release/1.0':raise ValueError('RELEASE_MANIFEST_INVALID')
    for name,digest in manifest['files'].items():
        p=safe(root,name)
        if p.is_symlink() or not p.is_file() or sha(p)!=digest:raise ValueError('RELEASE_INTEGRITY_CONFLICT')
    files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    if files!=set(manifest['files'])|{'release-manifest.json'}:raise ValueError('RELEASE_INTEGRITY_CONFLICT')
    return manifest


def unpack_release(archive,root,expected):
    root=Path(root).resolve();archive=Path(archive)
    if sha(archive)!=expected:raise ValueError('RELEASE_HASH_MISMATCH')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(set(names))!=len(names) or sum(i.file_size for i in z.infolist())>512*1024*1024:raise ValueError('RELEASE_MANIFEST_INVALID')
        for info in z.infolist():
            safe(root,info.filename)
            if info.is_dir() or stat.S_ISLNK(info.external_attr>>16):raise ValueError('RELEASE_PATH_UNSAFE')
        if root.exists():
            verify_release(root)
            if (root/'release-manifest.json').read_bytes()!=z.read('release-manifest.json'):raise ValueError('RELEASE_INTEGRITY_CONFLICT')
            return root
        root.parent.mkdir(parents=True,exist_ok=True)
        staging=Path(tempfile.mkdtemp(prefix='.generator-release-',dir=root.parent)).resolve()
        assert staging.parent==root.parent
        try:
            for info in z.infolist():
                p=safe(staging,info.filename);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
            verify_release(staging);os.rename(staging,root)
        finally:
            if staging.exists():shutil.rmtree(staging)
    return root


def unpack_python(archive,runtime_root):
    """Materialize links as data, avoiding distro-specific tar symlink semantics."""
    archive=Path(archive);root=Path(runtime_root).resolve();digest=sha(archive)
    marker=root/'python-runtime.json'
    if marker.is_file():
        record=json.loads(marker.read_bytes())
        if record['archive_sha256']!=digest:raise ValueError('PYTHON_RUNTIME_INTEGRITY_CONFLICT')
        for name,expected in record['files'].items():
            p=safe(root,name)
            if p.is_symlink() or not p.is_file() or sha(p)!=expected:raise ValueError('PYTHON_RUNTIME_INTEGRITY_CONFLICT')
        return
    if (root/'python').exists():raise ValueError('PYTHON_RUNTIME_INCOMPLETE')
    root.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.python-staging-',dir=root)).resolve()
    assert staging.parent==root
    try:
        with tarfile.open(archive) as tar:
            members=tar.getmembers();registry={m.name:m for m in members}
            if len(registry)!=len(members) or sum(m.size for m in members)>512*1024*1024:raise ValueError('PYTHON_ARCHIVE_UNSAFE')
            def resolve(member,seen=()):
                name=member.name
                if name in seen:raise ValueError('PYTHON_ARCHIVE_UNSAFE')
                if member.issym() or member.islnk():
                    if member.linkname.startswith('/') or '\\' in member.linkname:raise ValueError('PYTHON_ARCHIVE_UNSAFE')
                    target=posixpath.normpath(posixpath.join(posixpath.dirname(name),member.linkname) if member.issym() else member.linkname)
                    if not target.startswith('python/') or target not in registry:raise ValueError('PYTHON_ARCHIVE_UNSAFE')
                    return resolve(registry[target],seen+(name,))
                if not member.isfile():raise ValueError('PYTHON_ARCHIVE_UNSAFE')
                return member
            resolved=[]
            for member in members:
                name=member.name.rstrip('/')
                if not name.startswith('python/'):raise ValueError('PYTHON_ARCHIVE_UNSAFE')
                path=safe(staging,name)
                if member.isdir():path.mkdir(parents=True,exist_ok=True);continue
                resolved.append((path,resolve(member)))
            hashes={}
            # Read regular members in archive order; resolve all links from staged data.
            for path,member in resolved:
                if path.relative_to(staging).as_posix()!=member.name:continue
                path.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(member) as source,path.open('xb') as dest:shutil.copyfileobj(source,dest)
                path.chmod(member.mode&0o777)
                hashes[path.relative_to(staging).as_posix()]=sha(path)
            for path,member in resolved:
                name=path.relative_to(staging).as_posix()
                if name==member.name:continue
                path.parent.mkdir(parents=True,exist_ok=True)
                source=safe(staging,member.name)
                with source.open('rb') as src,path.open('xb') as dest:shutil.copyfileobj(src,dest)
                path.chmod(member.mode&0o777)
                hashes[name]=hashes[member.name]
        os.rename(staging/'python',root/'python')
        marker.write_text(json.dumps({'archive_sha256':digest,'files':hashes},sort_keys=True)+'\n',encoding='utf-8')
    finally:
        if staging.exists():shutil.rmtree(staging)


def install_runtime(release,runtime_root):
    release=Path(release).resolve();runtime_root=Path(runtime_root).resolve()
    verify_release(release)
    # This exact archive is covered by the signed-off outer release digest and manifest.
    archive=release/'runtime/python.tar.gz'
    python_root=runtime_root/'python';unpack_python(archive,runtime_root)
    python=python_root/'bin/python3'
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
    env['PYTHONDONTWRITEBYTECODE']='1'
    subprocess.run([str(python),'-c','import sys; assert sys.version_info[:2]==(3,12)'],check=True,env=env)
    venv=runtime_root/'venv'
    subprocess.run([str(python),'-m','venv',str(venv)],check=True,env=env)
    executable=venv/'bin/python'
    subprocess.run([str(executable),'-m','pip','install','--disable-pip-version-check','--no-index','--require-hashes',
                    '--find-links',str(release/'wheels'),'-r',str(release/'requirements-linux-cp312.lock')],check=True,env=env)
    subprocess.run([str(executable),'-m','pip','check'],check=True,env=env)
    return executable


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path);parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--runtime',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch('[a-f0-9]{64}',args.sha256):raise ValueError('RELEASE_HASH_INVALID')
    retained=args.release.with_suffix('.zip')
    if args.archive and args.archive.is_file() and args.archive.stat().st_size:
        unpack_release(args.archive,args.release,args.sha256)
        if retained.exists():
            if sha(retained)!=args.sha256:raise ValueError('RELEASE_INTEGRITY_CONFLICT')
        else:
            with retained.open('xb') as dest, args.archive.open('rb') as source:shutil.copyfileobj(source,dest)
    else:
        unpack_release(retained,args.release,args.sha256)
    python=install_runtime(args.release,args.runtime)
    print(json.dumps({'status':'RUNTIME_READY','python':str(python),'read_only':True}))


if __name__=='__main__':main()
