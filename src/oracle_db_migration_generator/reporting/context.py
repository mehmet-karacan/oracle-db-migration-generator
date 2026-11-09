"""Schema Compare kaynak sayımlarını hedef okumasından bağımsız saklar.

Rapor yalnız aynı kaynak kaydı ve hedef listesiyle eşleşen bilgiyi kullanır.
Bağlantı bilgileri ve parolalar rapor bağlamına yazılmaz.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import json
import re


def build_report_context(source, profile, targets):
    """Hazırlanmış kaynaktan hedef adlarını ve kapsam içi tür sayılarını alır."""
    from ..model.source_scope import source_for_schemas
    from .inventory import inventory_side
    records = []
    for target in targets:
        schemas = tuple(mapping.source_schema for mapping in target.schema_mappings)
        scoped = source_for_schemas(source, profile, schemas)
        records.append({'id': target.id, 'name': target.name, 'schemas': list(schemas),
            'source_digest': scoped.semantic_digest,
            'source': inventory_side(scoped, profile.policy, schemas)})
    return {'schema_version': 'report-context/1.0', 'source_commit': source.source_commit,
            'targets': records}


def validate_report_context(context, run, plans):
    """Eski çalışma veya başka hedefe ait sunum bilgisini reddeder."""
    if context is None:
        return {}
    def invalid():
        raise ValueError('REPORT_CONTEXT_MISMATCH')
    if (not isinstance(context, dict)
            or set(context) != {'schema_version', 'source_commit', 'targets'}
            or context['schema_version'] != 'report-context/1.0'
            or context['source_commit'] != run['source_commit']
            or not isinstance(context['targets'], list)):
        invalid()
    records = {}
    for record in context['targets']:
        if (not isinstance(record, dict)
                or set(record) != {'id', 'name', 'schemas', 'source_digest', 'source'}
                or not isinstance(record['id'], str) or not record['id']
                or record['id'] in records
                or not isinstance(record['name'], str) or not record['name'].strip()
                or len(record['name']) > 500
                or not isinstance(record['schemas'], list) or not record['schemas']
                or any(not isinstance(s, str) or not s or len(s) > 128 for s in record['schemas'])
                or len(set(record['schemas'])) != len(record['schemas'])
                or not isinstance(record['source_digest'], str)
                or not re.fullmatch('[a-f0-9]{64}', record['source_digest'])):
            invalid()
        side = record['source']
        if (not isinstance(side, dict) or set(side) != {'by_schema', 'inventory', 'excluded'}
                or side['inventory'] not in {'COMPLETE', 'PARTIAL', 'UNAVAILABLE'}
                or type(side['excluded']) is not int or side['excluded'] < 0
                or not isinstance(side['by_schema'], dict)
                or set(side['by_schema']) != set(record['schemas'])):
            invalid()
        for counts in side['by_schema'].values():
            if not isinstance(counts, dict) or any(not isinstance(k, str) or not k
                    or type(v) is not int or v < 0 for k, v in counts.items()):
                invalid()
        plan = plans.get(record['id'])
        if plan and (plan['source']['ddl_digest'] != record['source_digest']
                     or set(plan['target']['schemas']) != set(record['schemas'])):
            invalid()
        records[record['id']] = record
    if set(records) != {target['id'] for target in run['targets']}:
        invalid()
    return records


def load_report_context(root, run, plans):
    """Varsa bu çalışma için kaydedilen rapor bağlamını doğrulayarak okur."""
    path = root/'report-context.json'
    if not path.is_file():
        return None
    context = json.loads(path.read_bytes())
    validate_report_context(context, run, plans)
    return context
