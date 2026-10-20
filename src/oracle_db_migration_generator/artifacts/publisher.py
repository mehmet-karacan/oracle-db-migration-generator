"""Explicit opt-in Git publisher. Merely archiving/rendering never invokes this API."""
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from ..config.loader import read_json
from ..model.serialization import canonical_bytes
from ..model.snapshot_io import safe_path
from ..reporting.links import safe_https
from .store import StoreLock, owned_files, write_owned
from .bundle import _scan


@dataclass(frozen=True)
class Destination:
    provider: str
    web_base: str
    remote: str
    branch: str
    allowed_hosts: tuple[str, ...]
    storage_approved: bool
    # A human must explicitly opt in to a real push; tests use a Git adapter.
    push_authorized: bool = False


@dataclass(frozen=True)
class Publication:
    status: str
    url: str | None = None
    commit_sha: str | None = None
    error_code: str | None = None


def _destination(d):
    p = safe_https(d.web_base, d.allowed_hosts)
    if p.query or d.storage_approved is not True or d.push_authorized is not True: raise ValueError('PUBLICATION_NOT_AUTHORIZED')
    if d.provider not in {'github','bitbucket'}: raise ValueError('PUBLICATION_PROVIDER_UNSUPPORTED')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/_-]{0,100}',d.branch) or '..' in d.branch or d.branch.endswith('/'):
        raise ValueError('PUBLICATION_BRANCH_UNSAFE')
    # SSH remotes only: no tokens or arbitrary Git transport helpers in argv/config.
    match = re.fullmatch(r'git@([A-Za-z0-9.-]+):([A-Za-z0-9_./-]+)\.git',d.remote)
    ssh = urlsplit(d.remote) if d.remote.startswith('ssh://') else None
    if not match and not (ssh and ssh.scheme=='ssh' and ssh.username=='git' and ssh.password is None and ssh.hostname in d.allowed_hosts and re.fullmatch(r'/[A-Za-z0-9_./-]+\.git',ssh.path) and not ssh.query and not ssh.fragment):
        raise ValueError('PUBLICATION_REMOTE_UNSAFE')
    host = match[1] if match else ssh.hostname
    if host != p.hostname or '..' in d.remote: raise ValueError('PUBLICATION_REMOTE_MISMATCH')
    if d.provider=='github':
        if p.hostname!='github.com' or not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',p.path):
            raise ValueError('PUBLICATION_REPOSITORY_UNSAFE')
        remote_path=match[2] if match else ssh.path[1:-4]
        if remote_path != p.path.lstrip('/'): raise ValueError('PUBLICATION_REMOTE_MISMATCH')
    else:
        m = re.fullmatch(r'/projects/([A-Za-z0-9_-]+)/repos/([A-Za-z0-9_.-]+)', p.path)
        remote_path = match[2] if match else ssh.path[1:-4]
        if not m or remote_path.casefold()!=f'{m[1]}/{m[2]}'.casefold(): raise ValueError('PUBLICATION_REMOTE_MISMATCH')


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args): return None


class ProviderHTTP:
    """Tokens stay in request headers. Redirects/login pages never prove accessibility."""
    def __init__(self, token=None): self.token=token; self.opener=build_opener(_NoRedirect())
    def _get(self,url,*,json_response=False):
        headers={'Accept':'application/json' if json_response else 'text/html'}
        if self.token: headers['Authorization']='Bearer '+self.token
        try:
            with self.opener.open(Request(url,headers=headers),timeout=20) as r:
                if r.status!=200 or r.geturl()!=url: return None
                data=r.read(2*1024*1024)
                if json_response: return json.loads(data)
                return b'<html' in data.lower() and b'type="password"' not in data.lower()
        except (OSError,ValueError): return None
    def private(self,d):
        p=urlsplit(d.web_base)
        if d.provider=='github':
            data=self._get('https://api.github.com/repos'+p.path,json_response=True)
            return bool(isinstance(data,dict) and data.get('private') is True and data.get('full_name','').casefold()==p.path[1:].casefold())
        m=re.fullmatch(r'/projects/([^/]+)/repos/([^/]+)',p.path)
        data=self._get(f'https://{p.netloc}/rest/api/1.0/projects/{m[1]}/repos/{m[2]}',json_response=True)
        return bool(isinstance(data,dict) and data.get('public') is False and data.get('slug')==m[2]
                    and data.get('project',{}).get('key','').casefold()==m[1].casefold())
    def reachable(self,url): return self._get(url) is True


class GitCLI:
    def _run(self,root,*args):
        env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'}
        result=subprocess.run(['git','-c','core.hooksPath='+os.devnull,*args],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120,shell=False)
        if result.returncode: raise ValueError('ARTIFACT_GIT_COMMAND_FAILED')
        return result.stdout.decode('utf-8').strip()
    def check(self,root,d,paths):
        # Artifact checkout must be independent of Generator or source working trees.
        if not (root/'.git').is_dir() or (root/'src').exists() or (root/'AKTIF_GOREV.md').exists(): raise ValueError('ARTIFACT_REPOSITORY_REQUIRED')
        if Path(self._run(root,'rev-parse','--show-toplevel')).resolve()!=root: raise ValueError('ARTIFACT_REPOSITORY_REQUIRED')
        if self._run(root,'remote','get-url','origin')!=d.remote: raise ValueError('PUBLICATION_REMOTE_MISMATCH')
        if self._run(root,'branch','--show-current')!=d.branch: raise ValueError('PUBLICATION_BRANCH_MISMATCH')
        if self._run(root,'diff','--cached','--name-only'): raise ValueError('ARTIFACT_INDEX_NOT_EMPTY')
        changed=self._run(root,'ls-files','--modified','--others','--exclude-standard').splitlines()
        if any(path not in paths for path in changed): raise ValueError('ARTIFACT_UNOWNED_CHANGE')
        # Refuse configured execution/filter mechanisms in the dedicated checkout.
        if any(p.name in {'.gitattributes','.gitmodules'} for p in root.rglob('*') if '.git' not in p.relative_to(root).parts):
            raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE')
        config=self._run(root,'config','--list').lower()
        if any(key in config for key in ('filter.','core.sshcommand','core.gitproxy','remote.origin.pushurl','include.','includeif.')):
            raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE')
    def commit(self,root,paths,message):
        if paths:
            # Git pathspec file is outside the checkout and contains only owned paths.
            import tempfile
            fd,name=tempfile.mkstemp(prefix='artifact-pathspec-')
            try:
                with os.fdopen(fd,'wb') as stream: stream.write(b'\0'.join(p.encode() for p in paths)+b'\0')
                self._run(root,'--literal-pathspecs','add','--pathspec-from-file='+name,'--pathspec-file-nul')
            finally: os.unlink(name)
        if self._run(root,'diff','--cached','--name-only'):
            self._run(root,'-c','commit.gpgSign=false','commit','-m',message)
        return self._run(root,'rev-parse','HEAD')
    def push(self,root,d,commit): self._run(root,'push','origin',f'{commit}:refs/heads/{d.branch}')
    def confirmed(self,root,d,commit):
        return self._run(root,'ls-remote','origin','refs/heads/'+d.branch).split('\t')[0]==commit


def publish_run(store, run_path, destination, *, git=None, private_check=None, url_check=None, secret_values=()):
    """Fail closed. Local bundles are preserved even when remote verification fails."""
    try:
        _destination(destination)
        http=ProviderHTTP();private_check=private_check or http.private;url_check=url_check or http.reachable
        if private_check(destination) is not True: raise ValueError('ARTIFACT_REPOSITORY_NOT_PRIVATE')
        root=Path(store).resolve();git=git or GitCLI()
        with StoreLock(root):
            owned=owned_files(root)
            _scan((safe_path(root,path).read_bytes() for path in owned),secret_values)
            if not re.fullmatch(r'runs/\d{4}/\d{2}/\d{2}/build-[A-Za-z0-9-]+',run_path): raise ValueError('RUN_PATH_UNSAFE')
            if run_path+'/run.json' not in owned: raise ValueError('RUN_NOT_ARCHIVED')
            git.check(root,destination,set(owned)|{'.artifact-store.json'})
            plans=sorted(p for p in owned if p.startswith('plans/'))
            if plans:
                plan_commit=git.commit(root,plans,'Archive immutable migration plans')
                if not re.fullmatch('[a-f0-9]{40}',plan_commit): raise ValueError('ARTIFACT_COMMIT_INVALID')
                updates={}
                for path in owned:
                    if not path.startswith('runs/') or not path.endswith('/run.json'): continue
                    run=read_json(safe_path(root,path))
                    if run.get('artifact_git_sha') is None and any(t['plan_id'] for t in run['targets']):
                        run['artifact_git_sha']=plan_commit
                        updates[path]=canonical_bytes(run)+b'\n'
                if updates: write_owned(root,updates,secret_values=secret_values)
            final=git.commit(root,sorted(set(owned)|{'.artifact-store.json'}),'Archive migration run references')
            if not re.fullmatch('[a-f0-9]{40}',final): raise ValueError('ARTIFACT_COMMIT_INVALID')
            git.push(root,destination,final)
            if not git.confirmed(root,destination,final): raise ValueError('ARTIFACT_REMOTE_NOT_CONFIRMED')
            base=destination.web_base.rstrip('/')
            path=quote(run_path+'/README.md',safe='/')
            url=f'{base}/blob/{final}/{path}' if destination.provider=='github' else f'{base}/browse/{path}?at={final}'
            if url_check(url) is not True: raise ValueError('ARTIFACT_LINK_NOT_ACCESSIBLE')
            return Publication('PUBLISHED',url,final)
    except (ValueError,OSError,subprocess.SubprocessError):
        return Publication('FAILED',error_code='ARTIFACT_PUBLICATION_NOT_CONFIRMED')
