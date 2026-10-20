"""Portable object paths and escaped Markdown; database names are never paths."""
import hashlib
import re
from ..reporting.labels import object_label


def component(value):
    value = str(value)
    # Uppercase Oracle identifiers stay readable; all other spellings get a digest.
    if re.fullmatch(r'[A-Z][A-Z0-9_-]{0,59}', value) and not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])', value):
        return value
    return 'id-' + hashlib.sha256(value.encode('utf-8')).hexdigest()


def object_folder(obj):
    return 'objects/' + '/'.join(component(obj[key]) for key in ('owner', 'object_type', 'name'))


def object_sql_path(operation):
    return object_folder(operation.to_dict()['object']) + '/' + operation.operation_id + '.sql'


def markdown(value):
    # HTML entities also protect pipes, backticks and link syntax in Markdown.
    return ''.join(c if c.isalnum() or c in ' ._-' else f'&#{ord(c)};' for c in str(value))


def navigation(document):
    result = {}
    groups = {}
    for op in document['operations']:
        groups.setdefault(object_folder(op['object']), []).append(op)
        if op['decision'] in {'BLOCKED', 'REVIEW_REQUIRED'}:
            from ..model.serialization import canonical_bytes
            result['review/' + op['id'] + '.json'] = canonical_bytes({'plan_id': document['plan_id'], 'operation': op}) + b'\n'
    lines = ['# Hedef planı', '', f"Hedef: {markdown(document['target']['name'])}",
             f"Plan: `{document['plan_id']}`", '', f"Durum: {document['status']}", '',
             'Üretildi · Veritabanına uygulanmadı. Source ve target salt okunur.', '',
             '[Plan JSON](plan.json) · [Manifest](bundle-manifest.json) · [Web raporu](index.html)', '',
             'Genel script bağımlılık sırasını korur. Nesne dosyası tek başına ek bağımlılık gerektirebilir.', '',
             'İnceleme/engelli işlemler hazır SQL içine alınmaz. partial-ready.sql yalnız bağımsız hazır alt kümedir.', '']
    if any(op['sql'] for op in document['operations']):
        aggregate = 'migration.sql' if document['status'] == 'READY' else 'partial-ready.sql'
        lines += [f'[Genel DDL]({aggregate})', '']
    lines += ['## Nesne dosyaları', '']
    for folder, ops in sorted(groups.items()):
        obj = ops[0]['object']
        label = markdown(f"{object_label(obj)} · {obj['object_type']}")
        lines.append(f'- [{label}]({folder}/README.md)')
        body = [f'# {label}', '', 'Üretildi · Veritabanına uygulanmadı.', '',
                'Tek nesne SQL dosyası ek bağımlılık gerektirebilir; genel planı ve işlem sırasını inceleyin.', '']
        for op in ops:
            status={'READY':'AUTO_GENERATED','INFORMATIONAL':'NO_ACTION'}.get(op['decision'],op['decision'])
            body += [f"## {op['kind']} · {status}", '', markdown(op['reason_tr']), '',
                     f"İşlem: `{op['id']}`", '', 'Bağımlılıklar: ' + markdown(', '.join(op['depends_on']) or 'Yok'), '']
            if op['sql']:
                body += [f"[Nesne DDL]({op['id']}.sql)", '']
            elif op['decision'] in {'BLOCKED', 'REVIEW_REQUIRED'}:
                body += [f"[İnceleme kanıtı](../../../../review/{op['id']}.json)", '']
        body += ['[Plan JSON](../../../../plan.json)', '']
        result[folder + '/README.md'] = '\n'.join(body).encode('utf-8')
    result['README.md'] = '\n'.join(lines).encode('utf-8')
    return result
