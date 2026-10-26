"""Prepare authorized Jenkins artifacts without publishing the private control state."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import shutil

from oracle_db_migration_generator.config.loader import validate_document
from oracle_db_migration_generator.control.store import ControlStore
from jenkins_notification import write_notification


def prepare_archive(store,run_id,output,build_number,build_url,job_url):
    if not re.fullmatch('[0-9a-f]{32}',run_id):raise ValueError('RUN_ID_INVALID')
    if build_number<1 or build_url!=job_url+str(build_number)+'/':raise ValueError('JENKINS_BUILD_LINK_MISMATCH')
    run=store.run(run_id)
    if run['status'] in {'QUEUED','RUNNING'}:raise ValueError('RUN_NOT_FINISHED')
    output=Path(output)
    if output.exists():raise ValueError('OUTPUT_ALREADY_EXISTS')
    source=store.root/'runs'/run_id
    if source.is_dir():
        shutil.copytree(source,output,ignore=shutil.ignore_patterns('repository','source','observations'))
    else:output.mkdir(parents=True)
    if (output/'run.json').is_file():
        document=json.loads((output/'run.json').read_bytes())
        document.update(build_number=build_number,build_url=build_url)
        validate_document(document,'run.schema.json')
        (output/'run.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        write_notification(output,document,build_url,job_url)
    else:
        body=(f'<html><body><h2>SKY · Karşılaştırma tamamlanamadı</h2><p>{escape(run["spec"]["profile"]["name"])}</p>'
              f'<p>{escape(run.get("error_code") or run["status"])}</p><p>Eksik sonuç sıfır fark olarak değerlendirilmedi. SQL uygulanmadı.</p>'
              f'<p><a href="{escape(build_url,quote=True)}">Jenkins çalışma kaydı</a></p></body></html>')
        (output/'report-email.jenkins.html').write_text(body,encoding='utf-8')
    store.update_run(run_id,archive_build_url=build_url,notification_status='PREPARED_NOT_SENT')
    return {'enabled':run['spec']['settings']['notify_enabled'],'to':'mkaracan@innova.com.tr',
            'report':str(output/'report-email.jenkins.html')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--run',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--build-number',required=True,type=int)
    parser.add_argument('--build-url',required=True);parser.add_argument('--job-url',required=True)
    args=parser.parse_args()
    result=prepare_archive(ControlStore(args.root),args.run,args.output,args.build_number,args.build_url,args.job_url)
    destination=Path('.local')/f'ui-notify-build-{args.build_number}.json';destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result),encoding='utf-8')


if __name__=='__main__':main()
