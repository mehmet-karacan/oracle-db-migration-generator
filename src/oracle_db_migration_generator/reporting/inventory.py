"""Snapshot inventory counters, separate from differences and executable SQL."""
import json
import hashlib
from collections import Counter

from .labels import TYPES, type_label


def build_scan_summary(source, target, policy, plan):
    from ..compare.scope import scoped_objects
    def side(snapshot):
        counts = {owner: Counter() for owner in target.schemas}
        raw = sum(obj.identity.owner.effective_name in counts for obj in snapshot.objects)
        for obj in scoped_objects(snapshot, policy):
            if obj.identity.owner.effective_name in counts:
                counts[obj.identity.owner.effective_name][obj.identity.object_type] += 1
        return {'by_schema': {owner: dict(sorted(rows.items())) for owner, rows in sorted(counts.items())},
                'inventory': snapshot.completeness.inventory,
                'excluded': raw - sum(sum(rows.values()) for rows in counts.values())}
    return {'schema_version': 'scan-summary/1.0', 'plan_id': plan['plan_id'] if isinstance(plan,dict) else plan.plan_id,
            'source_digest': source.semantic_digest, 'target_digest': target.semantic_digest,
            'target_id': target.target_id, 'source': side(source), 'target': side(target)}


def validate_scan_summary(summary, plan):
    if (not isinstance(summary, dict)
            or set(summary) != {'schema_version', 'plan_id', 'source_digest', 'target_digest', 'target_id', 'source', 'target'}
            or summary['schema_version'] != 'scan-summary/1.0'
            or summary['plan_id'] != plan['plan_id'] or summary['target_id'] != plan['target']['id']
            or summary['source_digest'] != plan['source']['ddl_digest']
            or summary['target_digest'] != plan['target_snapshot_digest']):
        raise ValueError('SCAN_SUMMARY_PLAN_MISMATCH')
    for key in ('source', 'target'):
        side = summary[key]
        if (not isinstance(side, dict) or set(side) != {'by_schema', 'inventory', 'excluded'}
                or side['inventory'] not in {'COMPLETE', 'PARTIAL', 'UNAVAILABLE'}
                or type(side['excluded']) is not int or side['excluded'] < 0
                or not isinstance(side['by_schema'], dict)
                or set(side['by_schema']) != set(plan['target']['schemas'])):
            raise ValueError('SCAN_SUMMARY_INVALID')
        for counts in side['by_schema'].values():
            if not isinstance(counts, dict) or any(not isinstance(kind, str) or not kind
                    or type(count) is not int or count < 0 for kind, count in counts.items()):
                raise ValueError('SCAN_SUMMARY_INVALID')
    return summary


def load_scan_summaries(root, run, plans):
    from ..model.snapshot_io import safe_path
    summaries = {}
    for target in run['targets']:
        if target.get('plan_path'):
            folder = safe_path(root, target['plan_path']).parent
            path = folder/'scan-summary.json'
            if path.is_file():
                raw = path.read_bytes()
                manifest = json.loads((folder/'bundle-manifest.json').read_bytes())
                rows = [row for row in manifest['files'] if row['path'] == 'scan-summary.json']
                if (len(rows) != 1 or rows[0]['bytes'] != len(raw)
                        or rows[0]['sha256'] != hashlib.sha256(raw).hexdigest()
                        or manifest['plan_id'] != plans[target['id']]['plan_id']):
                    raise ValueError('SCAN_SUMMARY_INTEGRITY_MISMATCH')
                summaries[target['id']] = validate_scan_summary(json.loads(raw), plans[target['id']])
    return summaries


def scan_scope_view(plans, summaries, target_ids):
    source_schemas = {}; partial = False; expected_schemas = set()
    for target_id in target_ids:
        plan = plans.get(target_id); summary = summaries.get(target_id) if plan else None
        if plan:
            expected_schemas.update(plan['target']['schemas'])
        if summary is None:
            continue
        validate_scan_summary(summary, plan)
        if summary['source']['inventory'] != 'UNAVAILABLE':
            for owner, counts in summary['source']['by_schema'].items():
                record = (summary['source_digest'], counts)
                if owner in source_schemas and source_schemas[owner] != record:
                    raise ValueError('SCAN_SUMMARY_SOURCE_CONFLICT')
                source_schemas[owner] = record
        partial = partial or summary['source']['inventory'] != 'COMPLETE'
    sources = Counter()
    for _, counts in source_schemas.values():
        sources.update({kind: count for kind, count in counts.items() if kind not in {'COMMENT', 'GRANT'}})
    kinds = sorted(sources, key=lambda kind: (list(TYPES).index(kind) if kind in TYPES else len(TYPES), kind))
    notes = ['Seçili şemalardaki kaynak nesneleri sayılır, değişmeyen nesneler dahildir. '
             'Hedef sayısı toplamı artırmaz. Kapsam dışı kayıtlar, açıklamalar ve yetkiler nesne toplamına dahil değildir. '
             'Paket tanımı ve gövdesi ayrı nesnelerdir.']
    if partial:
        notes.append('Envanter eksik, sayılar gözlenen alt sınırdır.')
    if not source_schemas:
        notes.append('Tarama kapsamı bilgisi kaydedilmedi, kaynak nesne sayısı bilinmiyor.')
    elif expected_schemas - source_schemas.keys():
        notes.append('Bazı kaynak şemalarının tarama kapsamı bilgisi kaydedilmedi, toplam yalnız bilinen şemaları içerir.')
    return {'source_total': sum(sources.values()) if source_schemas else None,
            'rows': [{'label': type_label(kind), 'count': sources[kind]} for kind in kinds],
            'note': ' '.join(notes)}
