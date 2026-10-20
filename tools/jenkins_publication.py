"""Explicit trusted Jenkins artifact publication. No Oracle or SMTP operations."""
import argparse
import base64
import binascii
import configparser
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request

from oracle_db_migration_generator.artifacts.publisher import (
    Destination, GitCLI, ProviderHTTP, Publication, _destination, publish_run,
)
from oracle_db_migration_generator.artifacts.store import archive_run, owned_files, MARKER, _namespace
from oracle_db_migration_generator.config.loader import read_json, validate_document
from oracle_db_migration_generator.model.serialization import canonical_bytes


def validate_destination(destination):
    _destination(destination)
    if (destination.provider!='github' or destination.branch!='main'
        or tuple(destination.allowed_hosts)!=('github.com',)
        or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+',destination.web_base)
        or destination.remote!='git@github.com:'+destination.web_base.removeprefix('https://github.com/')+'.git'):
        raise ValueError('PUBLICATION_DESTINATION_INVALID')
    return destination


class GitHubHTTP(ProviderHTTP):
    """Verify private GitHub files through authenticated API, never a login page."""
    def __init__(self, token, destination):
        super().__init__(token)
        self.destination=validate_destination(destination)

    def _get(self, url, *, json_response=False):
        api_root='https://api.github.com/repos/'+self.destination.web_base.split('github.com/',1)[1]
        if not (url==api_root or url.startswith(api_root+'/') or url.startswith(api_root+'?')):
            return None
        headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+self.token,
                 'X-GitHub-Api-Version':'2022-11-28'}
        try:
            with self.opener.open(Request(url,headers=headers),timeout=20) as response:
                if response.status!=200 or response.geturl()!=url:return None
                raw=response.read(2*1024*1024+1)
                if len(raw)>2*1024*1024:return None
                return json.loads(raw)
        except (OSError,ValueError):return None

    def private(self, destination):
        if destination!=self.destination:return False
        name=destination.web_base.removeprefix('https://github.com/')
        data=self._get('https://api.github.com/repos/'+name,json_response=True)
        return bool(isinstance(data,dict) and data.get('private') is True
                    and data.get('full_name')==name and isinstance(data.get('permissions'),dict)
                    and data['permissions'].get('push') is True)

    def reachable(self, url):
        if not isinstance(url,str):return False
        prefix=re.escape(self.destination.web_base)
        match=re.fullmatch(prefix+r'/blob/([a-f0-9]{40})/(runs/\d{4}/\d{2}/\d{2}/build-[A-Za-z0-9-]+/README\.md)',url)
        if not match:return False
        commit,path=match.groups()
        name=self.destination.web_base.removeprefix('https://github.com/')
        data=self._get('https://api.github.com/repos/'+name+'/contents/'+path+'?ref='+commit,json_response=True)
        if not (isinstance(data,dict) and data.get('type')=='file' and data.get('path')==path
                and data.get('encoding')=='base64' and type(data.get('size')) is int and 0<data['size']<=2*1024*1024
                and isinstance(data.get('sha'),str) and re.fullmatch('[a-f0-9]{40}',data['sha'])
                and isinstance(data.get('content'),str)):
            return False
        try:
            raw=base64.b64decode(data['content'].replace('\n','').replace('\r',''),validate=True)
            return len(raw)==data['size']
        except (ValueError,binascii.Error):return False


def _dedicated_store(store):
    path=Path(store).absolute()
    expected=Path.cwd()/'.runtime/artifact-store'
    if path!=expected or any(part.is_symlink() for part in (path,path.parent)):
        raise ValueError('ARTIFACT_REPOSITORY_REQUIRED')
    return path.resolve()


def _owned_checkout(root):
    owned=owned_files(root)
    actual=set()
    for path in root.rglob('*'):
        relative=path.relative_to(root)
        if path.is_symlink():raise ValueError('ARTIFACT_REPOSITORY_UNSAFE')
        if '.git' in relative.parts:continue
        if path.is_file():actual.add(relative.as_posix())
    expected=set(owned)|({MARKER} if (root/MARKER).exists() else set())
    if actual!=expected:raise ValueError('ARTIFACT_UNOWNED_CHANGE')
    return owned


class GitHubTokenGit(GitCLI):
    """Canonical SSH origin with a process-only HTTPS transport and header."""
    def __init__(self, token, username):
        if not isinstance(token,str) or not token or '\n' in token or '\r' in token:
            raise ValueError('ARTIFACT_CREDENTIAL_REQUIRED')
        if not isinstance(username,str) or not re.fullmatch(r'[A-Za-z0-9_.@-]{1,100}',username):
            raise ValueError('ARTIFACT_IDENTITY_INVALID')
        self.token=token;self.username=username

    def _run(self, root, *args):
        # get-url expands insteadOf; check the stored canonical origin instead.
        if args==('remote','get-url','origin'):args=('config','--get','remote.origin.url')
        env={key:value for key,value in os.environ.items() if not key.upper().startswith(('GIT_','GCM_'))}
        env.update({'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never','GIT_CONFIG_NOSYSTEM':'1','GIT_ALLOW_PROTOCOL':'https',
                    'GIT_CONFIG_SYSTEM':os.devnull,'GIT_CONFIG_GLOBAL':os.devnull,
                    'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'url.https://github.com/.insteadOf',
                    'GIT_CONFIG_VALUE_0':'git@github.com:',
                    'GIT_CONFIG_KEY_1':'http.https://github.com/.extraHeader',
                    'GIT_CONFIG_VALUE_1':'Authorization: Basic '+base64.b64encode(('x-access-token:'+self.token).encode()).decode(),
                    'GIT_AUTHOR_NAME':self.username,'GIT_COMMITTER_NAME':self.username,
                    'GIT_AUTHOR_EMAIL':'mkaracan@innova.com.tr','GIT_COMMITTER_EMAIL':'mkaracan@innova.com.tr'})
        command=['git','-c','core.hooksPath='+os.devnull,'-c','core.attributesFile='+os.devnull,'-c','core.longpaths=true',
                 '-c','credential.helper=','-c','protocol.file.allow=never','-c','protocol.ext.allow=never',*args]
        try:
            result=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                  timeout=120,shell=False)
            if result.returncode:raise ValueError('ARTIFACT_GIT_COMMAND_FAILED')
            return result.stdout.decode('utf-8').strip()
        except (OSError,subprocess.SubprocessError,UnicodeError):
            raise ValueError('ARTIFACT_GIT_COMMAND_FAILED') from None

    def _local_config(self, root):
        path=root/'.git/config'
        if path.is_symlink() or not path.is_file():raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE')
        config=configparser.RawConfigParser(strict=True)
        try:config.read_string(path.read_text(encoding='utf-8'))
        except (ValueError,configparser.Error):raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE') from None
        allowed={'core':{'repositoryformatversion','filemode','bare','logallrefupdates','ignorecase','symlinks'},
                 'remote "origin"':{'url','fetch'},'branch "main"':{'remote','merge'}}
        for section in config.sections():
            if section not in allowed or not set(config[section])<=allowed[section]:
                raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE')
        if config.get('core','bare',fallback='false')!='false':raise ValueError('ARTIFACT_GIT_CONFIG_UNSAFE')

    def prepare(self, root, destination):
        root=_dedicated_store(root);validate_destination(destination)
        if root.exists() and not (root/'.git').exists() and any(root.iterdir()):
            raise ValueError('ARTIFACT_REPOSITORY_REQUIRED')
        root.mkdir(parents=True,exist_ok=True)
        if not (root/'.git').exists():
            self._run(root,'init','--initial-branch=main','--template=')
            self._run(root,'remote','add','origin',destination.remote)
        if not (root/'.git').is_dir() or (root/'.git').is_symlink():raise ValueError('ARTIFACT_REPOSITORY_REQUIRED')
        self._local_config(root)
        owned=_owned_checkout(root)
        self.check(root,destination,set(owned)|{MARKER})
        if self._run(root,'status','--porcelain','--untracked-files=all'):raise ValueError('ARTIFACT_CHECKOUT_NOT_CLEAN')
        remote=self._run(root,'ls-remote','origin','refs/heads/main')
        if remote:
            if not re.fullmatch(r'[a-f0-9]{40}\s+refs/heads/main',remote):raise ValueError('ARTIFACT_REMOTE_INVALID')
            self._run(root,'fetch','--no-tags','origin','refs/heads/main:refs/remotes/origin/main')
            tree=self._run(root,'ls-tree','-r','--name-only','refs/remotes/origin/main').splitlines()
            for path in tree:
                if path!=MARKER:_namespace(path)
            modes=self._run(root,'ls-tree','-r','refs/remotes/origin/main').splitlines()
            if any(not re.match(r'100(?:644|755) blob [a-f0-9]{40}\t',line) for line in modes):
                raise ValueError('ARTIFACT_REMOTE_TREE_UNSAFE')
            self._run(root,'merge','--ff-only','refs/remotes/origin/main')
            _owned_checkout(root)
        elif self._run(root,'for-each-ref','--format=%(objectname)','refs/heads/main'):
            raise ValueError('ARTIFACT_REMOTE_BRANCH_MISSING')


def _current_run(run_root):
    raw=os.environ.get('BUILD_NUMBER','')
    if not re.fullmatch(r'[1-9][0-9]*',raw):raise ValueError('PUBLICATION_BUILD_INVALID')
    number=int(raw);root=Path(run_root).absolute()
    if root!=Path.cwd()/('output/runs/build-'+raw) or root.is_symlink():raise ValueError('PUBLICATION_BUILD_INVALID')
    if any(path.is_symlink() for path in root.parents if path.is_relative_to(Path.cwd())):
        raise ValueError('PUBLICATION_BUILD_INVALID')
    run=read_json(root/'run.json');validate_document(run,'run.schema.json')
    if (run.get('build_number')!=number or run.get('build_url')!=os.environ.get('BUILD_URL')
            or not run.get('build_url') or not run['build_url'].endswith('/'+raw+'/')):
        raise ValueError('PUBLICATION_BUILD_INVALID')
    return root.resolve(),run


def publish_artifacts(run_root, store, destination, token, username, *, git=None, http=None):
    """Preserve the input run; return only a secret-free publication result."""
    try:
        root,run=_current_run(run_root);store=_dedicated_store(store);validate_destination(destination)
        git=git or GitHubTokenGit(token,username);http=http or GitHubHTTP(token,destination)
        if http.private(destination) is not True:raise ValueError('ARTIFACT_REPOSITORY_NOT_PRIVATE')
        git.prepare(store,destination)
        receipt=archive_run(root,store,build_number=run['build_number'],secret_values=(token,))
        return publish_run(store,receipt['run_path'],destination,git=git,private_check=http.private,
                           url_check=http.reachable,secret_values=(token,))
    except (ValueError,OSError,subprocess.SubprocessError,configparser.Error,TypeError):
        return Publication('FAILED',error_code='ARTIFACT_PUBLICATION_NOT_CONFIRMED')


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--release',type=Path,required=True);parser.add_argument('--run-root',type=Path,required=True)
    args=parser.parse_args(argv)
    result=Publication('FAILED',error_code='ARTIFACT_PUBLICATION_NOT_CONFIRMED');http=None
    notification_status='NOT_RUN';notification_error=None
    try:
        root,run=_current_run(args.run_root)
        config=args.release/'config';settings=read_json(config/'job-settings.json')
        if os.environ['BUILD_URL']!=settings['job_url']+str(run['build_number'])+'/':
            raise ValueError('PUBLICATION_BUILD_INVALID')
        data=read_json(config/'artifact-publication.json')
        if set(data)!={'provider','web_base','remote','branch','allowed_hosts','storage_approved','push_authorized'}:
            raise ValueError('PUBLICATION_DESTINATION_INVALID')
        destination=validate_destination(Destination(**{**data,'allowed_hosts':tuple(data['allowed_hosts'])}))
        token=os.environ.get('GENERATOR_ARTIFACT_PASSWORD','');username=os.environ.get('GENERATOR_ARTIFACT_USER','')
        http=GitHubHTTP(token,destination)
        result=publish_artifacts(root,Path.cwd()/'.runtime/artifact-store',destination,token,username,http=http)
    except (ValueError,OSError,KeyError,TypeError):pass
    try:
        root,run=_current_run(args.run_root)
        (root/'publication.json').write_bytes(canonical_bytes(result)+b'\n')
        settings=read_json(args.release/'config/job-settings.json')
        try:
            from .jenkins_notification import write_notification
        except ImportError:
            from jenkins_notification import write_notification
        write_notification(root,run,os.environ['BUILD_URL'],settings['job_url'],publication=result,
                           url_check=http.reachable if http else lambda url:False)
        notification_status='RENDERED'
    except Exception:
        # Publication is already recorded; a renderer error cannot undo a push.
        notification_status='FAILED';notification_error='ARTIFACT_NOTIFICATION_FAILED'
    print(json.dumps({'status':result.status,'error_code':result.error_code,
                      'notification_status':notification_status,'notification_error_code':notification_error}),flush=True)
    if notification_status=='FAILED':return 30
    return 0 if result.status=='PUBLISHED' else 10


if __name__=='__main__':raise SystemExit(main())
