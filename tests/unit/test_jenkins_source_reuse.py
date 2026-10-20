"""Resume a trusted prior source only after fresh pinned Git and blob checks."""
import json
import hashlib
from dataclasses import replace

import pytest


def prepared_case(tmp_path, *, partial=False):
    from tests.unit.test_source import git, commit, profile
    from oracle_db_migration_generator.source.git_reader import GitRepository, resolve_source, read_source
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.model.snapshot_io import write_source_snapshot
    from oracle_db_migration_generator.model.snapshot import Coverage
    repo=tmp_path/'repo';repo.mkdir();git(repo,'init','-b','main')
    sha=commit(repo,'CREATE TABLE APP.DEMO (ID NUMBER);')
    selected=profile(tmp_path)
    inputs=read_source(resolve_source(GitRepository(repo),sha),selected)
    snapshot=parse_source(inputs,selected)
    if partial:
        snapshot=replace(snapshot,completeness=Coverage('PARTIAL','PARTIAL','NOT_APPLICABLE',('SOURCE_FILE_UNPARSED',)))
    root=tmp_path/'output/source-snapshots';root.mkdir(parents=True)
    cached=root/'build-41';output=root/'build-42'
    write_source_snapshot(snapshot,inputs,cached)
    return repo,sha,selected,snapshot,cached,output


@pytest.mark.parametrize('partial',[False,True])
def test_reuse_verifies_current_git_preserves_partial_and_never_reparses(tmp_path,monkeypatch,partial):
    from tools.jenkins_run import reuse_prepared_source
    from oracle_db_migration_generator.model.snapshot_io import load_snapshot
    repo,sha,selected,original,cached,output=prepared_case(tmp_path,partial=partial)
    before={p.relative_to(cached).as_posix():p.read_bytes() for p in cached.rglob('*') if p.is_file()}
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.parse_source',lambda *a,**kw:pytest.fail('Reuse must not parse again'))
    monkeypatch.setattr('oracledb.connect',lambda *a,**kw:pytest.fail('Reuse must not connect to Oracle'))
    pinned=hashlib.sha256((cached/'source-snapshot.json').read_bytes()).hexdigest()
    result,proof=reuse_prepared_source(cached,output,repo,sha,selected,snapshot_sha256=pinned)
    assert result.semantic_digest==original.semantic_digest
    assert result.completeness==original.completeness
    assert load_snapshot(output/'source-snapshot.json',require_ddl=True).semantic_digest==original.semantic_digest
    assert {p.relative_to(cached).as_posix():p.read_bytes() for p in cached.rglob('*') if p.is_file()}==before
    assert proof['status']=='REUSED_VERIFIED' and proof['origin_build']==41
    assert proof['source_commit']==sha and proof['source_semantic_digest']==original.semantic_digest
    assert proof['read_only'] is True


@pytest.mark.parametrize('tamper',['blob','manifest','profile','commit','snapshot-input','future-build','other-root',
                                  'coverage','objects','projection','snapshot-hash'])
def test_reuse_rejects_mismatch_before_creating_new_source(tmp_path,tamper):
    from tools.jenkins_run import reuse_prepared_source
    repo,sha,selected,original,cached,output=prepared_case(tmp_path,partial=tamper=='coverage')
    pinned=hashlib.sha256((cached/'source-snapshot.json').read_bytes()).hexdigest()
    if tamper=='blob':(cached/'app/tables/DEMO/ddl.sql').write_bytes(b'CREATE TABLE APP.OTHER(ID NUMBER);')
    elif tamper=='manifest':
        path=cached/'source-input.json';data=json.loads(path.read_bytes());data['files'][0]['sha256']='0'*64;path.write_text(json.dumps(data))
    elif tamper=='profile':
        path=cached/'source-profile.json';data=json.loads(path.read_bytes());data['policy']['allow_drop']=True;path.write_text(json.dumps(data))
    elif tamper=='commit':
        from tests.unit.test_source import commit
        sha=commit(repo,'CREATE TABLE APP.DEMO (ID NUMBER, C NUMBER);')
    elif tamper=='snapshot-input':
        path=cached/'source-snapshot.json';data=json.loads(path.read_bytes());data['capabilities']['source_input_digest']['value']='0'*64;path.write_text(json.dumps(data))
    elif tamper=='future-build':output=output.with_name('build-40')
    elif tamper=='other-root':output=tmp_path/'other/build-42'
    elif tamper in {'coverage','objects','projection'}:
        path=cached/'source-snapshot.json';data=json.loads(path.read_bytes())
        if tamper=='coverage':data['coverage'].update(inventory='COMPLETE',ddl='COMPLETE',diagnostics=[])
        elif tamper=='objects':data['objects']=[]
        else:data['objects'][0]['properties']['projection']['value']={'forged':True}
        path.write_text(json.dumps(data))
    elif tamper=='snapshot-hash':pinned='0'*64
    with pytest.raises(ValueError):reuse_prepared_source(cached,output,repo,sha,selected,snapshot_sha256=pinned)
    assert not output.exists()
