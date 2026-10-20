import hashlib
import json
import zipfile
from pathlib import Path

import pytest


def test_release_rejects_digest_and_traversal_before_extract(tmp_path):
    from tools.jenkins_bootstrap import unpack_release
    archive=tmp_path/'release.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('../outside.txt','unsafe')
    with pytest.raises(ValueError,match='RELEASE_HASH_MISMATCH'):
        unpack_release(archive,tmp_path/'cache','0'*64)
    with pytest.raises(ValueError,match='RELEASE_PATH_UNSAFE'):
        unpack_release(archive,tmp_path/'cache',hashlib.sha256(archive.read_bytes()).hexdigest())
    assert not (tmp_path/'outside.txt').exists() and not (tmp_path/'cache').exists()


def test_release_cache_is_immutable_and_rechecked(tmp_path):
    from tools.jenkins_bootstrap import unpack_release,verify_release
    archive=tmp_path/'release.zip'
    raw=b'payload';manifest={'schema_version':'jenkins-release/1.0','files':{'file.txt':hashlib.sha256(raw).hexdigest()}}
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('file.txt',raw);z.writestr('release-manifest.json',json.dumps(manifest))
    expected=hashlib.sha256(archive.read_bytes()).hexdigest()
    unpack_release(archive,tmp_path/'cache',expected)
    verify_release(tmp_path/'cache')
    (tmp_path/'cache/file.txt').write_text('tampered')
    with pytest.raises(ValueError,match='RELEASE_INTEGRITY_CONFLICT'):verify_release(tmp_path/'cache')


def test_jenkins_settings_reject_unapproved_scope_and_publish(tmp_path):
    from tools.jenkins_run import validate_settings
    settings={'target_id':'LOCAL-ODI','schemas':['INNOVA_ODI'],'source_url':'https://example.invalid/scm/sky/sky-db.git',
              'source_ref':'master','source_host':'example.invalid','publish':False,'send_email':False,'apply_sql':False}
    assert validate_settings(settings)==settings
    for key,value in [('schemas',['TTBP']),('publish',True),('apply_sql',True),('source_url','https://elsewhere.invalid/scm/sky/sky-db.git')]:
        with pytest.raises(ValueError,match='JENKINS_SCOPE_INVALID'):validate_settings({**settings,key:value})


def test_environment_check_does_not_connect_or_archive_credentials(tmp_path,monkeypatch):
    from tools.jenkins_run import environment_check
    from tests.factories import profile,ROOT
    def forbidden(*a,**kw):raise AssertionError('Oracle connection forbidden')
    monkeypatch.setattr('oracledb.connect',forbidden)
    result=environment_check(profile(),('INNOVA_ODI',))
    assert result['database_connections']==0 and result['read_only'] is True
    assert result['python_supported'] is True


def test_jenkins_archive_excludes_unscanned_raw_observations():
    text=Path('templates/jenkins-generator.groovy').read_text(encoding='utf-8')
    assert 'excludes: "output/runs/build-${env.BUILD_NUMBER}/observations/**"' in text


def test_python_archive_materializes_safe_relative_links_without_tar_extraction(tmp_path):
    from tools.jenkins_bootstrap import unpack_python
    import io,tarfile
    archive=tmp_path/'python.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        target=tarfile.TarInfo('python/share/terminfo/a/adm1178');target.size=4;tar.addfile(target,io.BytesIO(b'data'))
        link=tarfile.TarInfo('python/share/terminfo/1/1178');link.type=tarfile.SYMTYPE;link.linkname='../a/adm1178';tar.addfile(link)
        binary=tarfile.TarInfo('python/bin/python3');binary.size=3;binary.mode=0o755;tar.addfile(binary,io.BytesIO(b'bin'))
    unpack_python(archive,tmp_path/'runtime')
    actual=tmp_path/'runtime/python/share/terminfo/1/1178'
    assert actual.read_bytes()==b'data' and not actual.is_symlink()
    assert (tmp_path/'runtime/python/bin/python3').read_bytes()==b'bin'


def test_python_archive_outside_link_is_rejected(tmp_path):
    from tools.jenkins_bootstrap import unpack_python
    import tarfile
    archive=tmp_path/'bad.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        link=tarfile.TarInfo('python/bin/python3');link.type=tarfile.SYMTYPE;link.linkname='../../../outside';tar.addfile(link)
    with pytest.raises(ValueError,match='PYTHON_ARCHIVE_UNSAFE'):unpack_python(archive,tmp_path/'runtime')
    assert not (tmp_path/'runtime/python').exists()


def test_jenkins_mail_has_one_explicit_recipient_and_no_distribution_provider():
    text=Path('templates/jenkins-generator.groovy').read_text(encoding='utf-8')
    assert "to: '@@NOTIFY_TO@@'" in text and 'recipientProviders' not in text
    assert "params.RUN_MODE == 'COMPARE'" in text


def test_empty_jenkins_upload_uses_retained_release(tmp_path,monkeypatch,capsys):
    import tools.jenkins_bootstrap as bootstrap
    upload=tmp_path/'empty-upload';upload.write_bytes(b'')
    release=tmp_path/'cache';calls=[]
    monkeypatch.setattr('sys.argv',['bootstrap','--archive',str(upload),'--release',str(release),'--sha256','a'*64,'--runtime',str(tmp_path/'runtime')])
    monkeypatch.setattr(bootstrap,'unpack_release',lambda *args:calls.append(args))
    monkeypatch.setattr(bootstrap,'install_runtime',lambda *args:tmp_path/'python')
    bootstrap.main()
    assert calls==[(release.with_suffix('.zip'),release,'a'*64)]


def test_runtime_subprocesses_and_pipeline_disable_bytecode(tmp_path,monkeypatch):
    import tools.jenkins_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap,'verify_release',lambda *args:None)
    monkeypatch.setattr(bootstrap,'unpack_python',lambda *args:None)
    calls=[]
    monkeypatch.setattr(bootstrap.subprocess,'run',lambda *a,**kw:calls.append(kw))
    bootstrap.install_runtime(tmp_path/'release',tmp_path/'runtime')
    assert calls and all(c['env'].get('PYTHONDONTWRITEBYTECODE')=='1' for c in calls)
    assert "PYTHONDONTWRITEBYTECODE = '1'" in Path('templates/jenkins-generator.groovy').read_text(encoding='utf-8')


def test_python_archive_reads_regular_member_once_for_multiple_links(tmp_path,monkeypatch):
    from tools.jenkins_bootstrap import unpack_python
    import io,tarfile
    archive=tmp_path/'python.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        target=tarfile.TarInfo('python/data');target.size=4;tar.addfile(target,io.BytesIO(b'data'))
        for name in ('a','b'):
            link=tarfile.TarInfo('python/'+name);link.type=tarfile.SYMTYPE;link.linkname='data';tar.addfile(link)
    original=tarfile.TarFile.extractfile;reads=[]
    def tracked(self,member):
        reads.append(member.name)
        return original(self,member)
    monkeypatch.setattr(tarfile.TarFile,'extractfile',tracked)
    unpack_python(archive,tmp_path/'runtime')
    assert reads==['python/data']
    assert (tmp_path/'runtime/python/a').read_bytes()==(tmp_path/'runtime/python/b').read_bytes()==b'data'


def test_jenkins_notification_is_visible_html_body_with_consistent_subject():
    text=Path('templates/jenkins-generator.groovy').read_text(encoding='utf-8')
    assert "mimeType: 'text/html'" in text
    assert 'SKY | Oracle DB Migration Generator | ${currentBuild.currentResult} | Build #${env.BUILD_NUMBER}' in text
    assert 'body: fileExists(report) ? readFile(report)' in text
    assert "attachmentsPattern: ''" in text


def test_ddl_stays_in_jenkins_without_artifact_git_stage_or_credential():
    text=Path('templates/jenkins-generator.groovy').read_text(encoding='utf-8')
    assert 'jenkins_publication.py' not in text
    assert 'GENERATOR_ARTIFACT_PASSWORD' not in text and '@@ARTIFACT_CREDENTIAL@@' not in text
    assert 'archiveArtifacts(artifacts: "output/runs/build-${env.BUILD_NUMBER}/**"' in text
    assert 'excludes: "output/runs/build-${env.BUILD_NUMBER}/observations/**"' in text


def test_notification_has_fixed_build_link_and_no_sql_body(tmp_path):
    import json
    from tools.jenkins_notification import write_notification
    plan=json.loads(Path('examples/plan.example.json').read_bytes())
    folder=tmp_path/'targets'/plan['target']['id'];folder.mkdir(parents=True)
    (folder/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
    run={'run_id':'test-run','finished_at':'2026-10-20','source_commit':'a'*40,'build_number':7,
         'targets':[{'id':plan['target']['id'],'status':plan['status'],'difference_count':1,
                     'plan_path':'targets/'+plan['target']['id']+'/plan.json'}]}
    url='http://jenkins.example.invalid/job/generator/'
    path=write_notification(tmp_path,run,url+'7/',url)
    html=path.read_text(encoding='utf-8')
    assert 'Genel' in html and url+'7/artifact/output/runs/build-7/index.html' in html
    assert 'CREATE TABLE' not in html and 'ALTER TABLE' not in html
    with pytest.raises(ValueError,match='JENKINS_BUILD_LINK_MISMATCH'):
        write_notification(tmp_path,run,'https://other.invalid/7/',url)


@pytest.mark.parametrize('published',[False,True])
def test_notification_links_to_verified_private_publication_or_jenkins_fallback(tmp_path,published):
    import json
    from tools.jenkins_notification import write_notification
    from oracle_db_migration_generator.artifacts.publisher import Publication
    from tests.unit.test_report_views import inputs
    run,plans=inputs();run['build_number']=9
    for target in run['targets']:
        path=tmp_path/target['plan_path'];path.parent.mkdir(parents=True)
        path.write_text(json.dumps(plans[target['id']]),encoding='utf-8')
    job='http://jenkins.example.invalid/job/generator/'
    sha='b'*40
    url='https://github.com/acme/artifacts/blob/'+sha+'/runs/2026/10/20/build-9-run-test/README.md'
    publication=Publication('PUBLISHED',url,sha) if published else Publication('FAILED',error_code='ARTIFACT_PUBLICATION_NOT_CONFIRMED')
    path=write_notification(tmp_path,run,job+'9/',job,publication=publication,url_check=lambda value:value==url)
    html=path.read_text(encoding='utf-8')
    if published:
        assert url in html and 'sabit Git commit kaydı' in html
    else:
        assert job+'9/artifact/output/runs/build-9/index.html' in html
        assert 'Git yayını doğrulanamadı' in html and url not in html
