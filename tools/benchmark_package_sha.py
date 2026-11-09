"""Şema Karşılaştırma kayıtlı paketlerde süreyi ve DDL gövdesi eşitliğini ölçer.

İki akış aynı kaynak ve hedef dosyalarını ayrı Python süreçlerinde okur.
Oracle bağlantısı açılmaz. Parser önbelleği kapatılır. Sonuç özel çıktı
dizinine yazılır. Kaynak ilk hazırlığı bu ölçüme dahil değildir.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.model.serialization import digest, thaw
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from oracle_db_migration_generator.oracle.ddl_model import project_target_object
from oracle_db_migration_generator.parsing.client import parallel_parser_map
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target


def measure(args):
    source = load_snapshot(args.source, require_ddl=True)
    target = load_snapshot(args.target)
    profile = load_source_profile(args.profile)
    packages = {obj.object_key: obj for obj in source.objects
                if obj.identity.object_type in {'PACKAGE_SPEC', 'PACKAGE_BODY'}}
    items = [obj for obj in target.objects if obj.identity.object_type in {'PACKAGE_SPEC', 'PACKAGE_BODY'}]
    print(json.dumps({'mode': args.mode, 'stage': 'PACKAGE_PROJECTION', 'packages': len(items)}), flush=True)
    statistics = {'raw_sha_match': 0, 'content_sha_match': 0}
    started = perf_counter()
    def project(obj):
        counts = {}
        result, _ = project_target_object(obj, source=packages.get(obj.object_key) if args.mode == 'sha' else None,
                                          statistics=counts)
        return result, counts
    projected = {}
    with parallel_parser_map(project, items) as results:
        for obj, counts in results:
            projected[obj.object_key] = obj
            for key, value in counts.items(): statistics[key] += value
    projection_seconds = perf_counter() - started
    print(json.dumps({'mode': args.mode, 'stage': 'COMPARE_PLAN',
                      'projection_seconds': projection_seconds, 'reuse': statistics}), flush=True)
    target = replace(target, objects=tuple(projected.get(obj.object_key, obj) for obj in target.objects))
    started = perf_counter()
    differences = compare_snapshots(source, target, profile.policy)
    plan = plan_target(differences, PlanningContext(source, target, profile, target.target_id))
    statements = []
    for op in plan.operations:
        statements.append({'id': op.operation_id, 'decision': op.decision, 'kind': op.kind,
                           'dependencies': list(op.dependencies), 'reasons': list(op.reason_codes),
                           'sql': hashlib.sha256(op.intent.statement).hexdigest() if op.intent else None,
                           'proposal': hashlib.sha256(op.proposal.statement).hexdigest() if op.proposal else None})
    args.output.with_suffix('.operations.json').write_text(json.dumps(statements, indent=2), encoding='utf-8')
    args.output.with_suffix('.differences.json').write_text(json.dumps([
        {'id': diff.difference_id, 'object_key': diff.object_key, 'path': diff.property_path, 'kind': diff.kind}
        for diff in differences.differences], indent=2), encoding='utf-8')
    return {'mode': args.mode, 'source_commit': source.source_commit,
            'source_digest': source.semantic_digest, 'target_id': target.target_id,
            'packages': len(items), 'reuse': statistics, 'projection_seconds': projection_seconds,
            'compare_plan_seconds': perf_counter() - started,
            'difference_digest': digest(thaw(differences.differences)),
            'ddl_digest': digest(statements), 'operations': len(statements),
            'ready_sql': sum(op.intent is not None for op in plan.operations),
            'proposals': sum(op.proposal is not None for op in plan.operations),
            'status': plan.status, 'execution_status': 'NOT_EXECUTED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'target', 'profile', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--mode', choices=('baseline', 'sha'))
    args = parser.parse_args()
    os.environ.pop('GENERATOR_PARSER_CACHE_DIR', None)
    if args.mode:
        result = measure(args)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result), flush=True)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for mode in ('baseline', 'sha'):
        output = args.output / (mode + '.json')
        command = [sys.executable, str(Path(__file__).resolve()), '--mode', mode]
        for name in ('source', 'target', 'profile'):
            command += ['--' + name, str(getattr(args, name).resolve())]
        command += ['--output', str(output.resolve())]
        subprocess.run(command, check=True)
        results.append(json.loads(output.read_text(encoding='utf-8')))
    before, after = results
    equal = all(before[key] == after[key] for key in ('difference_digest', 'ddl_digest', 'source_digest'))
    result = {'equal': equal, 'baseline': before, 'sha': after,
              'projection_saved_seconds': before['projection_seconds'] - after['projection_seconds']}
    (args.output / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not equal:
        raise SystemExit('PACKAGE_SHA_OUTPUT_MISMATCH')


if __name__ == '__main__':
    main()
