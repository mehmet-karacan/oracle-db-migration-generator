import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))

def test_failed_ui_run_archives_only_public_run_files_and_self_notification(tmp_path):
    from ui_jenkins_archive import prepare_archive
    from test_control_review import setup_runs
    store,runs=setup_runs(tmp_path/'state');run=runs[0]
    store.update_run(run['id'],status='FAILED',error_code='SOURCE_CAPTURE_ERROR')
    root=store.root/'runs'/run['id'];root.mkdir(parents=True)
    for name in ('repository','source','observations'):
        (root/name).mkdir();(root/name/'private.txt').write_text('private capture')
    (root/'source-preparation-performance.json').write_text('{}')
    output=tmp_path/'output/runs/build-7'
    result=prepare_archive(store,run['id'],output,7,'https://jenkins.example.invalid/job/ui/7/','https://jenkins.example.invalid/job/ui/')
    assert result['to']=='mkaracan@innova.com.tr' and result['enabled']==run['spec']['settings']['notify_enabled']
    assert not (output/'repository').exists() and not (output/'source').exists() and not (output/'observations').exists()
    assert (output/'source-preparation-performance.json').exists()
    body=(output/'report-email.jenkins.html').read_text(encoding='utf-8')
    assert 'SOURCE_CAPTURE_ERROR' in body and 'private capture' not in body
    assert store.run(run['id'])['archive_build_url'].endswith('/7/')
