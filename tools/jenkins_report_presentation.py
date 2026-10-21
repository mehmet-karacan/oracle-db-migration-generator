"""Refresh human reports from verified artifacts without comparing or connecting."""
import argparse
import hashlib
import json
import mimetypes
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from oracle_db_migration_generator.artifacts.bundle import verify_bundle
from oracle_db_migration_generator.config.loader import validate_document
from oracle_db_migration_generator.model.serialization import canonical_bytes
from oracle_db_migration_generator.model.snapshot_io import safe_path
from oracle_db_migration_generator.reporting.render import render_reports
from oracle_db_migration_generator.reporting.formatting import difference_counts


def refresh_bundle(previous, output):
    previous = Path(previous).resolve(); output = Path(output).resolve()
    if output.exists(): raise ValueError('OUTPUT_ALREADY_EXISTS')
    verify_bundle(previous)
    manifest = json.loads((previous/'bundle-manifest.json').read_bytes())
    plan = json.loads((previous/'plan.json').read_bytes())
    payload = {row['path']:safe_path(previous, row['path']).read_bytes() for row in manifest['files']}
    reports = render_reports(plan, payload)
    retained = {name:raw for name,raw in payload.items()
                if not (name=='index.html' or name.startswith('changes/') and name.endswith('.html'))}
    retained.update(reports)
    manifest['files'] = [{'path':name, 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw),
                          'media_type':mimetypes.guess_type(name)[0] or 'application/octet-stream'}
                         for name,raw in sorted(retained.items())]
    validate_document(manifest, 'bundle-manifest.schema.json')
    immutable = {name:raw for name,raw in payload.items() if name not in reports
                 and not (name.startswith('changes/') and name.endswith('.html'))}
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.presentation-staging-',dir=output.parent) as temporary:
        staging=Path(temporary).resolve()
        if staging.parent!=output.parent or not staging.name.startswith('.presentation-staging-'):
            raise ValueError('PRESENTATION_STAGING_INVALID')
        for name,raw in retained.items():
            path=safe_path(staging,name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        (staging/'bundle-manifest.json').write_bytes(canonical_bytes(manifest)+b'\n')
        verify_bundle(staging)
        if any(safe_path(staging,name).read_bytes()!=raw for name,raw in immutable.items()):
            raise ValueError('PRESENTATION_REFRESH_PAYLOAD_CHANGED')
        os.rename(staging,output)
    return {'plan_id':plan['plan_id'], 'counts':plan['counts'], 'difference_summary':difference_counts(plan),
            'plan_sha256':hashlib.sha256(payload['plan.json']).hexdigest(),
            'sql_files_verified':sum(name.endswith('.sql') for name in immutable),
            'immutable_files_verified':len(immutable)}


def comparison_origin(base):
    """Keep the real comparison clock when a report is refreshed repeatedly."""
    base=Path(base).resolve();commit=None
    for _ in range(20):
        run=json.loads((base/'run.json').read_bytes())
        if commit is not None and run['source_commit']!=commit: raise ValueError('COMPARISON_TIMING_SOURCE_MISMATCH')
        commit=run['source_commit']
        if (base/'comparison-timing.json').is_file():
            timing=json.loads((base/'comparison-timing.json').read_bytes())
            if timing.get('source_commit')!=commit:raise ValueError('COMPARISON_TIMING_SOURCE_MISMATCH')
            return timing
        if not (base/'presentation-refresh-receipt.json').is_file():
            return {'schema_version':'comparison-timing/1.0','source_commit':commit,
                    'build_number':run['build_number'],'started_at':run['started_at'],'finished_at':run['finished_at']}
        previous=json.loads((base/'presentation-refresh-receipt.json').read_bytes())['base_build']
        if type(previous) is not int or not 0<previous<run['build_number']:raise ValueError('COMPARISON_TIMING_BUILD_INVALID')
        base=base.parent/('build-'+str(previous))
    raise ValueError('COMPARISON_TIMING_CHAIN_TOO_LONG')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--previous-build', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args();number=int(os.environ['BUILD_NUMBER']);output=args.output.resolve()
    if not 0<args.previous_build<number or output!=Path('output/runs').resolve()/('build-'+str(number)) or output.exists():
        raise ValueError('PRESENTATION_BUILD_INVALID')
    base=output.parent/('build-'+str(args.previous_build))
    old=json.loads((base/'run.json').read_bytes())
    timing=comparison_origin(base)
    if len(old['targets'])!=1 or old['targets'][0]['id']!='LOCAL-TTBP' or os.environ['GENERATOR_SCHEMA_SCOPE']!='TTBP':
        raise ValueError('PRESENTATION_SCOPE_INVALID')
    target=old['targets'][0]
    if target['plan_path']!='targets/LOCAL-TTBP/plan.json': raise ValueError('PRESENTATION_PLAN_INVALID')
    proof=refresh_bundle(base/'targets/LOCAL-TTBP',output/'targets/LOCAL-TTBP')
    (output/'targets/LOCAL-TTBP.result.json').write_bytes(canonical_bytes(target)+b'\n')
    (output/'comparison-timing.json').write_bytes(canonical_bytes(timing)+b'\n')
    for name in ('source-scopes.json','scope-exclusions.json'):
        if (base/name).is_file(): (output/name).write_bytes((base/name).read_bytes())
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from jenkins_notification import write_notification
    started=datetime.fromtimestamp(int(os.environ['GENERATOR_BUILD_STARTED_AT_MS'])/1000,timezone.utc).isoformat()
    run=aggregate_run(output,source_commit=old['source_commit'],started_at=started,
                      build_number=number,build_url=os.environ['BUILD_URL'])
    if run['targets']!=old['targets']: raise ValueError('PRESENTATION_TARGETS_CHANGED')
    settings=json.loads((args.release/'config/job-settings.json').read_bytes())
    note=(f"Bu rapor #{args.previous_build} karşılaştırmasının görünümü yenilenerek hazırlandı. "
          f"Karşılaştırma tarihi: {old['finished_at']}. Yeni Oracle bağlantısı açılmadı; DDL dosyaları değişmedi. "
          'Karşılaştırma ve rapor yenileme süreleri ayrı gösterilir. DDL dosyaları Jenkins arşivindedir.')
    write_notification(output,run,os.environ['BUILD_URL'],settings['job_url'],context_note=note)
    proof.update(base_build=args.previous_build,previous_finished_at=old['finished_at'],comparison_timing=timing,
                 fresh_capture=False,comparison_rerun=False,sql_regenerated=False,
                 database_connections=0,execution_status='NOT_EXECUTED',read_only=True)
    (output/'presentation-refresh-receipt.json').write_bytes(canonical_bytes(proof)+b'\n')
    print(json.dumps({'status':'PRESENTATION_REFRESH_VERIFIED',**proof}),flush=True)
    return run['exit_code']


if __name__=='__main__': raise SystemExit(main())
