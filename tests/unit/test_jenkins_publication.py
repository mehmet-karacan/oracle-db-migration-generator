"""Trusted CI publication boundaries; synthetic data and no remote Git/Oracle."""
import base64
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from tests.unit.test_publication import Git, destination
from tests.unit.test_report_artifact_update import run_fixture


def workspace_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root=tmp_path/'output/runs/build-42'
    run_fixture(root)
    run=json.loads((root/'run.json').read_bytes());run['build_number']=42
    run['build_url']='https://jenkins.example/job/generator/42/'
    (root/'run.json').write_text(json.dumps(run))
    monkeypatch.setenv('BUILD_NUMBER','42');monkeypatch.setenv('BUILD_URL',run['build_url'])
    return root


class PreparedGit(Git):
    def prepare(self, root, d):root.mkdir(parents=True,exist_ok=True)


class HTTP:
    def private(self, d):return True
    def reachable(self, url):return True


def test_publish_reuses_real_immutable_store_and_two_commit_publisher(tmp_path,monkeypatch):
    from tools.jenkins_publication import publish_artifacts
    root=workspace_run(tmp_path,monkeypatch);git=PreparedGit();store=tmp_path/'.runtime/artifact-store'
    result=publish_artifacts(root,store,destination(),'synthetic-token','bot',git=git,http=HTTP())
    assert result.status=='PUBLISHED' and result.commit_sha=='2'*40
    assert '/blob/'+('2'*40)+'/runs/' in result.url
    assert len(git.commits)==2
    archived=list((store/'runs').rglob('run.json'))
    assert len(archived)==1 and json.loads(archived[0].read_bytes())['artifact_git_sha']=='1'*40


@pytest.mark.parametrize('case',['public','unapproved','wrong-root','wrong-build','wrong-url','wrong-store'])
def test_rejection_happens_before_archive_or_git(tmp_path,monkeypatch,case):
    from tools.jenkins_publication import publish_artifacts
    root=workspace_run(tmp_path,monkeypatch);store=tmp_path/'.runtime/artifact-store';d=destination();http=HTTP()
    if case=='public':http.private=lambda d:False
    if case=='unapproved':d=replace(d,storage_approved=False)
    if case=='wrong-root':root=tmp_path/'other'
    if case=='wrong-build':monkeypatch.setenv('BUILD_NUMBER','43')
    if case=='wrong-url':monkeypatch.setenv('BUILD_URL','https://jenkins.example/job/generator/43/')
    if case=='wrong-store':store=tmp_path/'user-files'
    result=publish_artifacts(root,store,d,'synthetic-token','bot',git=PreparedGit(),http=http)
    assert result.status=='FAILED' and result.url is None and not store.exists()


def test_push_failure_preserves_original_comparison_and_sql(tmp_path,monkeypatch):
    from tools.jenkins_publication import publish_artifacts
    root=workspace_run(tmp_path,monkeypatch)
    before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    result=publish_artifacts(root,tmp_path/'.runtime/artifact-store',destination(),'synthetic-token','bot',git=PreparedGit(fail=True),http=HTTP())
    assert result.status=='FAILED' and result.url is None
    assert before=={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_github_readme_proof_uses_scoped_api_contents_at_exact_commit(monkeypatch):
    from tools.jenkins_publication import GitHubHTTP
    http=GitHubHTTP('synthetic-token',destination());calls=[]
    path='runs/2026/10/20/build-42-abc/README.md'
    def get(url,**kw):
        calls.append(url)
        return {'type':'file','path':path,'encoding':'base64','sha':'b'*40,'size':5,'content':base64.b64encode(b'proof').decode()}
    monkeypatch.setattr(http,'_get',get)
    assert http.reachable('https://github.com/acme/artifacts/blob/'+('a'*40)+'/'+path)
    assert calls==['https://api.github.com/repos/acme/artifacts/contents/'+path+'?ref='+('a'*40)]
    for bad in ['https://github.com/acme/artifacts/blob/main/'+path,
                'https://github.com/acme/other/blob/'+('a'*40)+'/'+path,
                'https://github.com/login',
                'https://github.com/acme/artifacts/blob/'+('a'*40)+'/'+path+'?download=1']:
        assert not http.reachable(bad)
    assert len(calls)==1


@pytest.mark.parametrize('change',[{'type':'dir'},{'path':'README.md'},{'size':0},{'sha':'x'*40},{'encoding':'none'},{'content':'!!!!'}])
def test_readme_proof_rejects_malformed_api_payload(monkeypatch,change):
    from tools.jenkins_publication import GitHubHTTP
    http=GitHubHTTP('synthetic-token',destination());path='runs/2026/10/20/build-42-abc/README.md'
    data={'type':'file','path':path,'encoding':'base64','sha':'b'*40,'size':5,'content':'cHJvb2Y='}
    monkeypatch.setattr(http,'_get',lambda *a,**kw:{**data,**change})
    assert not http.reachable('https://github.com/acme/artifacts/blob/'+('a'*40)+'/'+path)


@pytest.mark.parametrize('private,push,expected',[(True,True,True),(False,True,False),(True,False,False),(True,None,False)])
def test_private_proof_requires_fresh_write_permission(monkeypatch,private,push,expected):
    from tools.jenkins_publication import GitHubHTTP
    http=GitHubHTTP('synthetic-token',destination())
    monkeypatch.setattr(http,'_get',lambda *a,**kw:{'private':private,'full_name':'acme/artifacts','permissions':{'push':push}})
    assert http.private(destination()) is expected


def test_git_token_is_only_in_isolated_process_environment(tmp_path,monkeypatch):
    from tools.jenkins_publication import GitHubTokenGit
    calls=[]
    monkeypatch.setenv('GIT_CONFIG_COUNT','1');monkeypatch.setenv('GIT_CONFIG_KEY_0','include.path')
    def execute(args,**kw):
        calls.append((args,kw))
        return subprocess.CompletedProcess(args,0,b'git@github.com:acme/artifacts.git\n',b'')
    monkeypatch.setattr(subprocess,'run',execute)
    git=GitHubTokenGit('synthetic-token','bot')
    assert git._run(tmp_path,'remote','get-url','origin')=='git@github.com:acme/artifacts.git'
    args,kw=calls[0];env=kw['env']
    assert 'synthetic-token' not in repr(args) and 'synthetic-token' not in repr(kw.get('input'))
    assert args[-3:]==['config','--get','remote.origin.url']
    assert env['GIT_CONFIG_COUNT']=='2' and env['GIT_CONFIG_KEY_0']=='url.https://github.com/.insteadOf'
    assert env['GIT_CONFIG_VALUE_0']=='git@github.com:'
    assert env['GIT_CONFIG_KEY_1']=='http.https://github.com/.extraHeader'
    assert env['GIT_CONFIG_VALUE_1']=='Authorization: Basic '+base64.b64encode(b'x-access-token:synthetic-token').decode()
    assert env['GIT_CONFIG_GLOBAL']==__import__('os').devnull and kw['shell'] is False
    assert env['GIT_ALLOW_PROTOCOL']=='https' and env['GIT_AUTHOR_EMAIL']=='mkaracan@innova.com.tr'


def test_git_failure_never_exposes_secret_stderr(tmp_path,monkeypatch):
    from tools.jenkins_publication import GitHubTokenGit
    monkeypatch.setattr(subprocess,'run',lambda args,**kw:subprocess.CompletedProcess(args,1,b'',b'synthetic-token'))
    with pytest.raises(ValueError,match='^ARTIFACT_GIT_COMMAND_FAILED$'):
        GitHubTokenGit('synthetic-token','bot')._run(tmp_path,'status')


def test_prepare_refuses_unowned_directory_before_running_git(tmp_path,monkeypatch):
    from tools.jenkins_publication import GitHubTokenGit
    monkeypatch.chdir(tmp_path);store=tmp_path/'.runtime/artifact-store';store.mkdir(parents=True)
    (store/'user.txt').write_text('preserve')
    monkeypatch.setattr(subprocess,'run',lambda *a,**kw:pytest.fail('Git must not run'))
    with pytest.raises(ValueError):GitHubTokenGit('synthetic-token','bot').prepare(store,destination())
    assert (store/'user.txt').read_text()=='preserve'


def test_prepare_initializes_empty_dedicated_repository_without_head(tmp_path,monkeypatch):
    from tools.jenkins_publication import GitHubTokenGit
    monkeypatch.chdir(tmp_path);store=tmp_path/'.runtime/artifact-store'
    git=GitHubTokenGit('synthetic-token','bot');execute=git._run
    def offline(root,*args):
        if args==('ls-remote','origin','refs/heads/main'):return ''
        return execute(root,*args)
    monkeypatch.setattr(git,'_run',offline)
    git.prepare(store,destination())
    assert execute(store,'branch','--show-current')=='main'
    assert execute(store,'config','--get','remote.origin.url')=='git@github.com:acme/artifacts.git'
    assert not list(store.glob('runs/*'))


def test_cli_writes_failed_receipt_and_notification_without_mutating_run(tmp_path,monkeypatch,capsys):
    from tools import jenkins_publication as publication,jenkins_notification
    from oracle_db_migration_generator.artifacts.publisher import Publication
    root=workspace_run(tmp_path,monkeypatch);before=(root/'run.json').read_bytes()
    config=tmp_path/'release/config';config.mkdir(parents=True)
    from dataclasses import asdict
    (config/'artifact-publication.json').write_text(json.dumps(asdict(destination())))
    (config/'job-settings.json').write_text(json.dumps({'job_url':'https://jenkins.example/job/generator/'}))
    monkeypatch.setenv('GENERATOR_ARTIFACT_PASSWORD','synthetic-token');monkeypatch.setenv('GENERATOR_ARTIFACT_USER','bot')
    monkeypatch.setattr(publication,'publish_artifacts',lambda *a,**kw:Publication('FAILED',error_code='ARTIFACT_PUBLICATION_NOT_CONFIRMED'))
    calls=[]
    monkeypatch.setattr(jenkins_notification,'write_notification',lambda *a,**kw:calls.append((a,kw)))
    assert publication.main(['--release',str(config.parent),'--run-root',str(root)])==10
    receipt=json.loads((root/'publication.json').read_bytes())
    assert receipt=={'status':'FAILED','url':None,'commit_sha':None,'error_code':'ARTIFACT_PUBLICATION_NOT_CONFIRMED'}
    assert calls[0][1]['publication'].status=='FAILED' and (root/'run.json').read_bytes()==before
    assert 'synthetic-token' not in (root/'publication.json').read_text()+capsys.readouterr().out


def test_local_bare_git_first_push_and_existing_clean_store_fast_forward(tmp_path,monkeypatch):
    """Only replace GitHub transport; init/check/hash/commit/ff are real Git."""
    from tools.jenkins_publication import GitHubTokenGit,publish_artifacts
    remote=tmp_path/'remote.git'
    subprocess.run(['git','init','--bare',str(remote)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    real_subprocess_run=subprocess.run
    def local_only(command,**kw):
        # The test replaces HTTPS with a local filesystem transport only.
        kw['env']={**kw['env'],'GIT_ALLOW_PROTOCOL':'file'}
        return real_subprocess_run(command,**kw)
    monkeypatch.setattr(subprocess,'run',local_only)
    root=workspace_run(tmp_path,monkeypatch);store=tmp_path/'.runtime/artifact-store'
    class LocalGit(GitHubTokenGit):
        def _run(self,root,*args):
            if args and args[0] in {'ls-remote','fetch','push'}:
                args=tuple(str(remote) if arg=='origin' else arg for arg in args)
                args=('-c','protocol.file.allow=always',*args)
            try:return super()._run(root,*args)
            except ValueError:pytest.fail('Local Git command failed: '+repr(args))
    git=LocalGit('synthetic-token','bot')
    first=publish_artifacts(root,store,destination(),'synthetic-token','bot',git=git,http=HTTP())
    assert first.status=='PUBLISHED'
    assert git._run(store,'status','--porcelain')==''
    assert b'synthetic-token' not in (store/'.git/config').read_bytes()
    second_root=tmp_path/'output/runs/build-43';run_fixture(second_root)
    run=json.loads((second_root/'run.json').read_bytes());run['build_number']=43;run['build_url']='https://jenkins.example/job/generator/43/'
    (second_root/'run.json').write_text(json.dumps(run));monkeypatch.setenv('BUILD_NUMBER','43');monkeypatch.setenv('BUILD_URL',run['build_url'])
    second=publish_artifacts(second_root,store,destination(),'synthetic-token','bot',git=git,http=HTTP())
    assert second.status=='PUBLISHED' and second.commit_sha!=first.commit_sha
    assert len(list((store/'runs').rglob('run.json')))==2
    assert len(list((store/'plans').glob('*/*/*')))==1


def test_unsafe_local_git_include_is_rejected_before_network(tmp_path,monkeypatch):
    from tools.jenkins_publication import GitHubTokenGit
    monkeypatch.chdir(tmp_path);store=tmp_path/'.runtime/artifact-store';store.mkdir(parents=True)
    git=GitHubTokenGit('synthetic-token','bot')
    git._run(store,'init','--initial-branch=main','--template=')
    with (store/'.git/config').open('a') as stream:stream.write('\n[include]\n path = malicious-config\n')
    monkeypatch.setattr(git,'_run',lambda *a,**kw:pytest.fail('No Git/network call with unsafe config'))
    with pytest.raises(ValueError,match='ARTIFACT_GIT_CONFIG_UNSAFE'):git.prepare(store,destination())


def test_notification_failure_keeps_confirmed_publication_receipt(tmp_path,monkeypatch,capsys):
    from tools import jenkins_publication as publication,jenkins_notification
    from oracle_db_migration_generator.artifacts.publisher import Publication
    from dataclasses import asdict
    root=workspace_run(tmp_path,monkeypatch);config=tmp_path/'release/config';config.mkdir(parents=True)
    (config/'artifact-publication.json').write_text(json.dumps(asdict(destination())))
    (config/'job-settings.json').write_text(json.dumps({'job_url':'https://jenkins.example/job/generator/'}))
    result=Publication('PUBLISHED','https://github.com/acme/artifacts/blob/'+('a'*40)+'/runs/2026/10/20/build-42-abc/README.md','a'*40)
    monkeypatch.setattr(publication,'publish_artifacts',lambda *a,**kw:result)
    def fail(*a,**kw):raise ValueError('synthetic-secret-render-failure')
    monkeypatch.setattr(jenkins_notification,'write_notification',fail)
    assert publication.main(['--release',str(config.parent),'--run-root',str(root)])==30
    assert json.loads((root/'publication.json').read_bytes())['status']=='PUBLISHED'
    output=json.loads(capsys.readouterr().out)
    assert output['status']=='PUBLISHED' and output['notification_status']=='FAILED'
    assert output['notification_error_code']=='ARTIFACT_NOTIFICATION_FAILED'
    assert 'synthetic-secret-render-failure' not in json.dumps(output)
