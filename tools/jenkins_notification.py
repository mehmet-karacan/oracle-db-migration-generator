"""Render the approved general summary directly into a Jenkins HTML email."""
import json
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from oracle_db_migration_generator.reporting.view import build_run_view
from oracle_db_migration_generator.reporting.render import render_email,render_run_reports


def write_notification(output,run,build_url,job_url,*,context_note=None,publication=None,url_check=None):
    parsed=urlsplit(job_url)
    number=run['build_number']
    if (parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password
        or parsed.query or parsed.fragment or not job_url.endswith('/')
        or not isinstance(number,int) or number<1 or build_url!=job_url+str(number)+'/'):
        raise ValueError('JENKINS_BUILD_LINK_MISMATCH')
    plans={target['id']:json.loads((output/target['plan_path']).read_bytes())
           for target in run['targets'] if target.get('plan_path')}
    timing=json.loads((output/'comparison-timing.json').read_bytes()) if (output/'comparison-timing.json').is_file() else None
    if timing and timing.get('source_commit')!=run['source_commit']:raise ValueError('COMPARISON_TIMING_SOURCE_MISMATCH')
    from oracle_db_migration_generator.reporting.inventory import load_scan_summaries
    view=build_run_view(run,plans,publication=publication,url_check=url_check,allowed_link_hosts=('github.com',),comparison_timing=timing,
                        scan_summaries=load_scan_summaries(output,run,plans))
    artifact_root=build_url+'artifact/output/runs/build-'+str(number)+'/'
    for target in view['targets']:
        if target['aggregate_path']:
            target['aggregate_view_path']=artifact_root+target['aggregate_path']+'/*view*/'
        if target['plan_path']:
            target['download_path']=artifact_root+str(PurePosixPath(target['plan_path']).parent)+'/'
    if view['link'] is None:
        view['link']=build_url+'artifact/output/runs/build-'+str(number)+'/index.html'
        view['link_note']=context_note or ('Git yayını doğrulanamadı. Ayrıntılı raporlar ve DDL dosyaları Jenkins çalışma arşivindedir.'
                                         if publication is not None else 'Ayrıntılı raporlar ve DDL dosyaları Jenkins çalışma arşivindedir.')
    for name,raw in render_run_reports(view).items():
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    path=output/'report-email.jenkins.html'
    path.write_bytes(render_email(view,preview=True))
    return path
