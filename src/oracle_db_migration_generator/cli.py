"""Local configuration validation and read-only readiness commands."""
import argparse
import json
from pathlib import Path

from . import __version__
from .config.loader import ConfigError, load_source_profile, load_targets
from .oracle.preflight import safe_error_code
from .preflight import run_preflight


def main(argv=None):
    parser = argparse.ArgumentParser(description='Oracle Migration Generator — yerel, salt okunur başlangıç')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    validate = commands.add_parser('validate-config', help='Bağlantı açmadan yapılandırmayı doğrula')
    validate.add_argument('--source-profile', type=Path, required=True)
    validate.add_argument('--targets', type=Path, required=True)
    validate.add_argument('--target-ids', default='ALL')
    preflight = commands.add_parser('preflight', help='Source ve target salt okuma erişimini kontrol et; karşılaştırma yapmaz')
    preflight.add_argument('--settings', type=Path, default=Path('.local/session-context.json'))
    preflight.add_argument('--output', type=Path, default=Path('output/local-preflight.json'))
    prepare = commands.add_parser('prepare-source',help='Tek Git SHA üzerinden source snapshot hazırla; source deposuna yazmaz')
    prepare.add_argument('--repo',type=Path,required=True)
    prepare.add_argument('--ref',required=True)
    prepare.add_argument('--source-profile',type=Path,required=True)
    prepare.add_argument('--output',type=Path,required=True)
    offline=commands.add_parser('plan-offline',help='Snapshot üzerinden ağsız SQL/JSON/HTML planı üret')
    offline.add_argument('--source-snapshot',type=Path,required=True)
    offline.add_argument('--target-snapshot',type=Path,required=True)
    offline.add_argument('--source-profile',type=Path,required=True)
    offline.add_argument('--output',type=Path,required=True)
    live=commands.add_parser('plan-target',help='Seçili hedefin yalnız metadata bilgisini okuyarak yerel plan üret')
    live.add_argument('--source-snapshot',type=Path,required=True)
    live.add_argument('--source-profile',type=Path)
    live.add_argument('--targets',type=Path,required=True)
    live.add_argument('--target-id',required=True)
    live.add_argument('--credentials-file',type=Path)
    live.add_argument('--output',type=Path,required=True)
    verify=commands.add_parser('verify-bundle',help='Plan, kanıt bağlantıları ve bütün dosya hash değerlerini ağsız doğrula')
    verify.add_argument('--bundle',type=Path,required=True)
    aggregate=commands.add_parser('aggregate',help='Yerel hedef sonuçlarından koşu raporu üret')
    aggregate.add_argument('--run-root',type=Path,required=True)
    archive=commands.add_parser('archive-run',help='Doğrulanmış koşuyu yerel benzersiz plan arşivine kaydet; yayın yapmaz')
    archive.add_argument('--run-root',type=Path,required=True)
    archive.add_argument('--store',type=Path,required=True)
    archive.add_argument('--build-number',type=int)
    args = parser.parse_args(argv)
    try:
        if args.command=='archive-run':
            from .artifacts.store import archive_run
            print(json.dumps(archive_run(args.run_root,args.store,build_number=args.build_number)));return 0
        if args.command=='verify-bundle':
            from .artifacts.bundle import verify_bundle
            print(json.dumps(verify_bundle(args.bundle)));return 0
        if args.command=='aggregate':
            from .runtime.aggregate import aggregate_run
            result=aggregate_run(args.run_root)
            print(json.dumps({'status':result['status'],'targets':len(result['targets'])}));return result['exit_code']
        if args.command in {'plan-offline','plan-target'}:
            from .model.snapshot_io import load_snapshot
            from .runtime.worker import offline_plan,run_target
            profile=load_source_profile(args.source_profile or args.source_snapshot.parent/'source-profile.json')
            source=load_snapshot(args.source_snapshot,require_ddl=True)
            if args.command=='plan-offline':
                result=offline_plan(source,load_snapshot(args.target_snapshot),profile,args.output)
                print(json.dumps(result));return 0 if result['decision'] in {'READY','NO_CHANGE','NO_ACTION'} else 10
            from .config.credentials import EnvCredentialResolver
            from .runtime.aggregate import aggregate_run
            target=load_targets(args.targets,(args.target_id,))[0]
            def progress(index,total):
                if index%50==0: print(json.dumps({'phase':'capture_target','processed':index,'total':total}),flush=True)
            result=run_target(source,target,profile,EnvCredentialResolver(args.credentials_file),args.output,progress=progress)
            run=aggregate_run(args.output,source_commit=source.source_commit)
            print(json.dumps(result));return run['exit_code']
        if args.command=='prepare-source':
            from .model.snapshot_io import write_source_snapshot
            from .parsing.adapter import parse_source
            from .source.git_reader import GitRepository,resolve_source,read_source
            profile = load_source_profile(args.source_profile)
            inputs = read_source(resolve_source(GitRepository(args.repo),args.ref),profile)
            def progress(index,total):
                if index and index%50==0:
                    print(json.dumps({'phase':'parse_source','processed':index,'total':total}),flush=True)
            snapshot = parse_source(inputs,profile,progress=progress)
            write_source_snapshot(snapshot,inputs,args.output)
            print(json.dumps({'status':'PREPARED','source_commit':snapshot.source_commit,
                              'objects':len(snapshot.objects),'inventory':snapshot.completeness.inventory,
                              'ddl':snapshot.completeness.ddl,'comparison_status':'NOT_RUN'}))
            return 0 if snapshot.completeness.inventory==snapshot.completeness.ddl=='COMPLETE' else 10
        if args.command == 'validate-config':
            profile = load_source_profile(args.source_profile)
            targets = load_targets(args.targets, tuple(args.target_ids.split(',')))
            expected = {r.source_schema for r in profile.schema_roots}
            if any(m.source_schema not in expected for t in targets for m in t.schema_mappings):
                raise ConfigError('TARGET_SCHEMA_OUTSIDE_SOURCE_SCOPE')
            print(json.dumps({'status': 'VALID', 'target_count': len(targets), 'network_accessed': False}))
            return 0
        result = run_preflight(args.settings, args.output)
        print(json.dumps({'status': result['status'], 'source_status': result['source']['status'],
                          'target_statuses': {t['target_id']: t['status'] for t in result['targets']},
                          'comparison_status': 'NOT_RUN', 'difference_count': None}))
        return 0 if result['status'] == 'PASSED' else 20
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'status': 'INPUT_ERROR', 'error_code': safe_error_code(error)}))
        return 30


if __name__ == '__main__':
    raise SystemExit(main())
