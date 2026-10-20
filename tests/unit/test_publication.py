from dataclasses import replace
import json

import pytest

from tests.unit.test_report_artifact_update import run_fixture


class Git:
    def __init__(self, fail=False): self.commits=[]; self.fail=fail
    def check(self, root, destination, paths): self.paths=paths
    def commit(self, root, paths, message):
        self.commits.append((paths, message)); return str(len(self.commits))*40
    def push(self, root, destination, commit):
        if self.fail: raise ValueError('PUSH_FAILED')
    def confirmed(self, root, destination, commit): return True


def setup_store(tmp_path):
    from oracle_db_migration_generator.artifacts.store import archive_run
    root=tmp_path/'run';run_fixture(root)
    receipt=archive_run(root,tmp_path/'store',build_number=42)
    return tmp_path/'store', receipt['run_path']


def destination():
    from oracle_db_migration_generator.artifacts.publisher import Destination
    return Destination('github','https://github.com/acme/artifacts','git@github.com:acme/artifacts.git',
                       'main',('github.com',),True,True)


def test_private_publication_uses_two_commits_and_final_immutable_link(tmp_path):
    from oracle_db_migration_generator.artifacts.publisher import publish_run
    store,path=setup_store(tmp_path);git=Git()
    result=publish_run(store,path,destination(),git=git,private_check=lambda d: True,url_check=lambda u: True)
    assert result.status=='PUBLISHED' and '/blob/'+('2'*40)+'/'+path+'/README.md' in result.url
    assert json.loads((store/path/'run.json').read_bytes())['artifact_git_sha']=='1'*40
    assert all(p.startswith('plans/') for p in git.commits[0][0])
    assert path+'/run.json' in git.commits[1][0]


@pytest.mark.parametrize('case',['public','policy','host','push','404','remote'])
def test_failed_publication_never_produces_git_link(tmp_path,case):
    from oracle_db_migration_generator.artifacts.publisher import publish_run
    store,path=setup_store(tmp_path);d=destination();git=Git(fail=case=='push')
    if case=='policy': d=replace(d,storage_approved=False)
    if case=='host': d=replace(d,allowed_hosts=('elsewhere.invalid',))
    if case=='remote': git.confirmed=lambda *a: False
    receipt=publish_run(store,path,d,git=git,private_check=lambda d:case!='public',url_check=lambda u:case!='404')
    assert receipt.status=='FAILED' and receipt.url is None
    if case in ('public','policy','host'): assert not git.commits


def test_fallback_requires_accessible_immutable_build_not_latest():
    from oracle_db_migration_generator.reporting.links import verified_archive
    good='https://jenkins.example/job/migration/142/artifact/report/index.html'
    build='https://jenkins.example/job/migration/142/'
    assert verified_archive(good,('jenkins.example',),lambda u:True,build_url=build).url==good
    assert verified_archive(good,('jenkins.example',),lambda u:False,build_url=build) is None
    assert verified_archive(good.replace('142','lastSuccessfulBuild'),('jenkins.example',),lambda u:True,build_url=build) is None
    assert verified_archive(good.replace('142','141'),('jenkins.example',),lambda u:True,build_url=build) is None


def test_first_error_only_publication_does_not_require_existing_git_head(tmp_path):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.artifacts.store import archive_run
    from oracle_db_migration_generator.artifacts.publisher import publish_run
    folder=tmp_path/'run/targets/FAILED';folder.mkdir(parents=True)
    (folder/'target-error.json').write_text(json.dumps(dict(id='FAILED',status='ERROR',difference_count=None,
        plan_id=None,plan_path=None,captured_at=None,error_code='ORA-01031',publication='NOT_REQUESTED')))
    aggregate_run(tmp_path/'run',source_commit='a'*40)
    receipt=archive_run(tmp_path/'run',tmp_path/'store')
    git=Git();original=git.commit
    def unborn(root,paths,message):
        assert paths, 'Empty initial plan commit attempts rev-parse HEAD on unborn repository'
        return original(root,paths,message)
    git.commit=unborn
    result=publish_run(tmp_path/'store',receipt['run_path'],destination(),git=git,private_check=lambda d:True,url_check=lambda u:True)
    assert result.status=='PUBLISHED' and len(git.commits)==1


def test_all_pending_run_references_get_the_plan_commit_before_publication(tmp_path):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.artifacts.store import archive_run
    from oracle_db_migration_generator.artifacts.publisher import publish_run
    store,path=setup_store(tmp_path)
    aggregate_run(tmp_path/'run')
    second=archive_run(tmp_path/'run',store,build_number=43)
    result=publish_run(store,second['run_path'],destination(),git=Git(),private_check=lambda d:True,url_check=lambda u:True)
    assert result.status=='PUBLISHED'
    for run in (store/'runs').rglob('run.json'):
        assert json.loads(run.read_bytes())['artifact_git_sha']=='1'*40


def test_ownership_marker_cannot_claim_an_arbitrary_namespace(tmp_path):
    from oracle_db_migration_generator.artifacts.store import write_owned
    store,_=setup_store(tmp_path)
    with pytest.raises(ValueError,match='STORE_NAMESPACE_UNSAFE'):
        write_owned(store,{'src/user.py':b'user file'})
    assert not (store/'src/user.py').exists()


def test_publication_scans_existing_sql_for_supplied_secrets_before_any_commit(tmp_path):
    from oracle_db_migration_generator.artifacts.publisher import publish_run
    store,path=setup_store(tmp_path);git=Git()
    result=publish_run(store,path,destination(),git=git,private_check=lambda d:True,url_check=lambda u:True,secret_values=('NUMBER',))
    assert result.status=='FAILED' and not git.commits


@pytest.mark.parametrize('metadata,expected',[
    ({'private':True,'full_name':'acme/artifacts'},True),
    ({'private':False,'full_name':'acme/artifacts'},False),
    ({'private':True,'full_name':'acme/other'},False),
    ({'private':'true','full_name':'acme/artifacts'},False),
    (None,False)])
def test_provider_privacy_proof_is_for_the_exact_repository(metadata,expected):
    from oracle_db_migration_generator.artifacts.publisher import ProviderHTTP
    http=ProviderHTTP('synthetic-private-token')
    http._get=lambda *a,**kw:metadata
    assert http.private(destination()) is expected


def test_git_cli_stages_literal_owned_paths_only(tmp_path):
    from oracle_db_migration_generator.artifacts.publisher import GitCLI
    from pathlib import Path
    git=GitCLI();calls=[];paths=['plans/APP/TEST/'+('a'*64)+'/objects/APP/TABLE/T/op-'+('b'*64)+'.sql']
    def execute(root,*args):
        calls.append(args)
        if 'add' in args:
            filename=next(arg.split('=',1)[1] for arg in args if arg.startswith('--pathspec-from-file='))
            assert Path(filename).read_bytes()==b'\0'.join(p.encode() for p in paths)+b'\0'
            assert args[0]=='--literal-pathspecs'
        if args[:3]==('diff','--cached','--name-only'): return paths[0]
        if args==('rev-parse','HEAD'): return 'c'*40
        return ''
    git._run=execute
    assert git.commit(tmp_path,paths,'Synthetic archive')=='c'*40
    assert not any('push' in command or '--force' in command for command in calls)
