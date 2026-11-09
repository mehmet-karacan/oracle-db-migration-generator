"""Schema Compare uyarı taşıyan farklar için kaynak DDL önerisini tamamlar.

Karar ve bağımlılık kanıtını değiştirmez. Var olan SQL korunur. Kolon ve
kısıt farkları ALTER olarak, yeni nesneler özgün kaynak tanımıyla yazılır.
Veritabanına bağlanmaz ve SQL uygulamaz.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from dataclasses import replace
import hashlib
import json

from .._vendor.analyzer_core.oracle.table import constraint_properties
from ..model.plan import SqlIntent
from ..parsing.statements import quote_identifier
from .table_ddl import qualified, source_projection


def _part(value):
    return value.replace('~1', '/').replace('~0', '~')


def _known(obj, key):
    value = obj.properties.get(key)
    return value.value if value and value.state == 'KNOWN' else None


def _sql_value(value):
    if not isinstance(value, str):
        return None
    if not value.startswith('['):
        return value
    try:
        tokens = json.loads(value)
        return ' '.join(quote_identifier(text) if kind == 'quoted' else text for kind, text in tokens)
    except (ValueError, TypeError):
        return None


def _catalog_constraint_names(actual, details):
    """Adsız kısıtı tür, tablo ve sıralı kolonlarla tek katalog kaydına bağlar."""
    if actual is None:
        return []
    rows = _known(actual, 'dictionary.constraints')
    columns = _known(actual, 'dictionary.constraint_columns')
    if rows is None or columns is None:
        return []
    from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier
    from ..parsing.canonicalize import canonical_sql
    kind = details.get('kind') or details.get('type')
    expected = {'PRIMARY KEY': 'P', 'UNIQUE': 'U', 'FOREIGN KEY': 'R', 'CHECK': 'C'}.get(kind)
    wanted = tuple(identifier(token)[0] for token in code_tokens(details.get('columns') or '') or ()
                   if token.text != ',')
    matches = []
    for row in rows:
        if row.get('table_name') != actual.identity.name.effective_name or row.get('constraint_type') != expected:
            continue
        if kind == 'CHECK':
            if canonical_sql(row.get('search_condition') or '') != canonical_sql(details.get('condition') or ''):
                continue
        else:
            parts = [part for part in columns if part.get('table_name') == row['table_name']
                     and part.get('constraint_name') == row['constraint_name']]
            if any(not isinstance(part.get('position'), int) for part in parts):
                continue
            names = tuple(part['column_name'] for part in sorted(parts, key=lambda part: part['position']))
            if not wanted or names != wanted:
                continue
        matches.append(row['constraint_name'])
    return matches


def _constraint_statement(obj, actual, projection, name, changes, canonical):
    definition = projection.properties.get('constraints', {}).get(name)
    details = constraint_properties(definition) if definition else {}
    prefix = '/constraints/'+name.replace('~', '~0').replace('/', '~1')+'/'
    for key, value in canonical.items():
        if key.startswith(prefix) and value.state == 'KNOWN':
            details[key[len(prefix):]] = _sql_value(value.value)
    for diff in changes:
        if diff.after.state == 'KNOWN':
            details[diff.property_path.rsplit('/', 1)[-1]] = _sql_value(diff.after.value)
    anonymous = name.startswith('@anonymous-')
    kind = details.get('kind') or details.get('type')
    if anonymous:
        if kind == 'PRIMARY KEY':
            selector = 'PRIMARY KEY'
        elif kind == 'UNIQUE' and details.get('columns'):
            selector = 'UNIQUE ('+details['columns']+')'
        else:
            target = source_projection(actual) if actual is not None else None
            candidates = []
            if target:
                from ..parsing.canonicalize import canonical_sql
                for key, statement in target.properties.get('constraints', {}).items():
                    model = constraint_properties(statement)
                    if (not key.startswith('@anonymous-') and model.get('kind') == kind
                            and all(canonical_sql(model.get(field) or '') == canonical_sql(details.get(field) or '')
                                    for field in ('columns', 'condition'))):
                        candidates.append(key)
            if not candidates:
                candidates = _catalog_constraint_names(actual, details)
            if len(candidates) != 1:
                return None
            selector = 'CONSTRAINT '+quote_identifier(candidates[0])
    else:
        selector = 'CONSTRAINT '+quote_identifier(name)
    fields = {diff.property_path.rsplit('/', 1)[-1] for diff in changes}
    if fields <= {'enabled', 'validation', 'rely', 'initially', 'deferrable'}:
        if details.get('initially') in {'IMMEDIATE', 'DEFERRED'}:
            details['initially'] = 'INITIALLY '+details['initially']
        selected = fields | ({'enabled', 'validation'} if fields & {'enabled', 'validation'} else set())
        state = ' '.join(str(details[key]) for key in
                         ('deferrable', 'initially', 'enabled', 'validation', 'rely')
                         if key in selected and details.get(key))
        return 'ALTER TABLE '+qualified(obj.identity)+' MODIFY '+selector+' '+state+';'
    if definition is None:
        if kind not in {'PRIMARY KEY', 'UNIQUE', 'CHECK', 'FOREIGN KEY'}:
            return None
        value = details.get('condition') if kind == 'CHECK' else details.get('columns')
        if not value:
            return None
        definition = ('' if anonymous else 'CONSTRAINT '+quote_identifier(name)+' ')+kind+' ('+value+')'
        if kind == 'FOREIGN KEY':
            if not details.get('reference'):
                return None
            definition += ' REFERENCES '+details['reference']
            if details.get('delete_rule') not in {None, 'NO ACTION'}:
                definition += ' '+details['delete_rule']
        definition += ' '+ ' '.join(details[key] for key in ('enabled', 'validation') if details.get(key))
    return ('ALTER TABLE '+qualified(obj.identity)+' DROP '+selector+';\n'
            'ALTER TABLE '+qualified(obj.identity)+' ADD '+definition.rstrip().rstrip(';')+';')


def _table_statement(obj, actual, changes, canonical):
    projection = source_projection(obj)
    if projection is None:
        return None
    columns = projection.properties.get('columns', {})
    column_changes, constraints, others = {}, {}, []
    for diff in changes:
        parts = diff.property_path.split('/')
        if len(parts) == 4 and parts[1] == 'columns':
            column_changes.setdefault(_part(parts[2]), []).append(diff)
        elif len(parts) == 4 and parts[1] == 'constraints':
            constraints.setdefault(_part(parts[2]), []).append(diff)
        else:
            others.append(diff)
    rows = []
    for name, fields in sorted(column_changes.items()):
        detail = columns.get(name)
        if detail is None:
            return None
        kinds = {diff.property_path.rsplit('/', 1)[-1] for diff in fields}
        clauses = []
        if kinds & {'data_type', 'length', 'length_semantics', 'precision', 'scale', 'fractional_precision'}:
            if not detail.get('data_type'):
                return None
            clauses.append(detail['data_type'])
        if 'nullable' in kinds:
            diff = next(diff for diff in fields if diff.property_path.endswith('/nullable'))
            if diff.after.state != 'KNOWN' or not isinstance(diff.after.value, bool):
                return None
            clauses.append('NULL' if diff.after.value else 'NOT NULL')
        if 'collation' in kinds:
            value = detail.get('collation')
            if not value:
                diff = next(diff for diff in fields if diff.property_path.endswith('/collation'))
                value = diff.after.value if diff.after.state == 'KNOWN' else None
            if not value:
                return None
            clauses.append('COLLATE '+quote_identifier(value))
        if kinds - {'data_type', 'length', 'length_semantics', 'precision', 'scale', 'fractional_precision', 'nullable', 'collation'}:
            return None
        if not clauses:
            return None
        rows.append('ALTER TABLE '+qualified(obj.identity)+' MODIFY ('+quote_identifier(name)+' '+' '.join(clauses)+');')
    for name, fields in sorted(constraints.items()):
        statement = _constraint_statement(obj, actual, projection, name, fields, canonical)
        if statement is None:
            return None
        rows.append(statement)
    for diff in others:
        if diff.property_path != '/table_properties/partitioning':
            return None
        clause = projection.properties.get('table_properties', {}).get('partitioning')
        rows.append('ALTER TABLE '+qualified(obj.identity)+' MODIFY '+
                    (clause.rstrip().rstrip(';') if clause else 'NONPARTITIONED')+';')
    return '\n'.join(rows).encode('utf-8') if rows else None


def _comment_statement(obj):
    target, column, text = (_known(obj, key) for key in ('target', 'column', 'text'))
    if not isinstance(target, str) or not isinstance(text, str):
        return None
    name = quote_identifier(obj.identity.owner.effective_name)+'.'+quote_identifier(target)
    if column is not None:
        if not isinstance(column, str):
            return None
        name += '.'+quote_identifier(column)
    return ('COMMENT ON '+('COLUMN ' if column is not None else 'TABLE ')+name+
            " IS '"+text.replace("'", "''")+"';").encode('utf-8')


def proposal_statement(obj, actual, changes, *, canonical=None):
    """Kaynak tanımından DDL üretir. Tanım yoksa SQL uydurmaz."""
    kind = obj.identity.object_type
    if kind == 'COMMENT':
        return _comment_statement(obj), 'SQL'
    if not obj.raw_ddl or hashlib.sha256(obj.raw_ddl).hexdigest() != obj.ddl_sha256:
        return None, 'SQL'
    if kind == 'TABLE' and actual is not None:
        return _table_statement(obj, actual, changes, canonical or {}), 'SQL'
    if kind in {'PACKAGE_SPEC', 'PACKAGE_BODY', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'VIEW', 'TYPE_SPEC', 'TYPE_BODY', 'SYNONYM'}:
        from .object_rules import replace_header
        try:
            raw = replace_header(obj.raw_ddl)
        except (ValueError, IndexError):
            return None, 'SQL'
        return raw, 'SQL' if kind in {'VIEW', 'SYNONYM'} else 'PLSQL'
    if kind not in {'TABLE', 'INDEX', 'MATERIALIZED_VIEW', 'SEQUENCE', 'SYNONYM'}:
        return None, 'SQL'
    raw = obj.raw_ddl
    if kind == 'TABLE':
        # CTAS veri kopyalar. Bu yol yalnız yapısal kaynak DDL'sini taşır.
        from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
        depth = 0
        tokens = code_tokens(raw.decode('utf-8')) or ()
        for index, token in enumerate(tokens):
            if token.text == '(':
                depth += 1
            elif token.text == ')':
                depth -= 1
            elif depth == 0 and token.upper == 'AS' and (index == 0 or tokens[index-1].upper != 'STORE'):
                return None, 'SQL'
    if actual is not None and kind in {'INDEX', 'MATERIALIZED_VIEW'}:
        raw = ('DROP '+kind.replace('_', ' ')+' '+qualified(obj.identity)+';\n').encode()+raw
    return raw, 'SQL'


def complete_proposals(operations, context, differences):
    """Hazır SQL'i değiştirmeden eksik önerileri aynı fark ve kaynağa bağlar."""
    changes = {diff.difference_id: diff for diff in differences.differences}
    result = []
    canonical = {}
    for operation in operations:
        if operation.decision not in {'BLOCKED', 'REVIEW_REQUIRED'}:
            result.append(operation)
            continue
        if operation.proposal is not None:
            reason = operation.reason_tr.replace('DDL üretilemedi', 'hazır işlem doğrulanamadı')
            result.append(replace(operation, reason_tr=reason) if reason != operation.reason_tr else operation)
            continue
        obj = context.source_objects.get(operation.identity.key)
        if obj is None:
            result.append(operation)
            continue
        if obj.identity.object_type == 'TABLE' and obj.object_key not in canonical:
            from ..compare.projection_adapter import canonical_fields
            canonical[obj.object_key] = canonical_fields(obj, context.source, context.profile.policy)
        raw, kind = proposal_statement(obj, context.target_objects.get(obj.object_key),
                                       [changes[key] for key in operation.change_ids],
                                       canonical=canonical.get(obj.object_key))
        if raw:
            intent = SqlIntent(raw, kind, 30, verification_sha256=hashlib.sha256(raw).hexdigest())
            reason = (operation.reason_tr.replace('DDL dönüşümü henüz tanımlı değil', 'değişim DDL önerisi olarak yazıldı')
                      .replace('DDL üretilemedi', 'hazır işlem doğrulanamadı')
                      .replace('güvenli SQL üretimini engelliyor', 'otomatik uygunluk doğrulamasını engelliyor'))
            operation = replace(operation, proposal=intent,
                                reason_tr='Kaynak tanımına göre DDL dosyası oluşturuldu. '+reason)
        result.append(operation)
    return result
