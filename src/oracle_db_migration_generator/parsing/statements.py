"""Validated sidecar token handling, independent of SQL execution."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier, source_span, top_level_items


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def qualified_parts(tokens):
    if not tokens or len(tokens) % 2 == 0 or any(token.text != '.' for token in tokens[1::2]):
        raise ValueError('SIDECAR_TARGET_UNRESOLVED')
    return tuple(identifier(token)[0] for token in tokens[::2])


def literal_value(raw: str):
    if raw.upper() == 'NULL' or raw == "''":
        return None
    lower = raw.lower()
    if lower.startswith("nq'") or lower.startswith("q'"):
        offset = 4 if lower.startswith("nq'") else 3
        return raw[offset:-2]
    if lower.startswith("n'"):
        return raw[2:-1].replace("''", "'")
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    raise ValueError('COMMENT_LITERAL_UNRESOLVED')


def sidecar_facts(text: str, default_schema: str):
    tokens = code_tokens(text)
    if not tokens:
        raise ValueError('SIDECAR_TOKENS_UNRESOLVED')
    tokens = tuple(token for token in tokens if token.text != ';')
    words = tuple(token.upper for token in tokens)
    if words[:3] in {('COMMENT', 'ON', 'TABLE'), ('COMMENT', 'ON', 'COLUMN')}:
        end = words.index('IS', 3)
        names = qualified_parts(tokens[3:end])
        column = None
        if words[2] == 'COLUMN':
            if len(names) == 2:
                owner, table, column = default_schema, *names
            elif len(names) == 3:
                owner, table, column = names
            else:
                raise ValueError('COMMENT_TARGET_UNRESOLVED')
        elif len(names) == 1:
            owner, table = default_schema, names[0]
        elif len(names) == 2:
            owner, table = names
        else:
            raise ValueError('COMMENT_TARGET_UNRESOLVED')
        expression = source_span(text, tokens[end + 1:])
        return ({'kind':'COMMENT', 'owner':owner, 'target':table, 'column':column,
                 'text':literal_value(expression), 'raw_ddl':text.encode('utf-8')},)
    if words[0] == 'GRANT':
        to=words.index('TO')
        on=max(index for index,word in enumerate(words[:to]) if word=='ON')
        names = qualified_parts(tokens[on + 1:to])
        if len(names) == 1:
            owner, table = default_schema, names[0]
        elif len(names) == 2:
            owner, table = names
        else:
            raise ValueError('GRANT_TARGET_UNRESOLVED')
        option = words[-3:] == ('WITH', 'GRANT', 'OPTION')
        grants = tokens[to + 1:-3] if option else tokens[to + 1:]
        grantees = top_level_items(grants)
        privileges = top_level_items(tokens[1:on])
        if not grantees or not privileges:
            raise ValueError('GRANT_SYNTAX_UNRESOLVED')
        result = []
        for privilege in privileges:
            column_grant = any(token.text == '(' for token in privilege)
            privilege_text = source_span(text, privilege)
            for grantee in grantees:
                if len(grantee) != 1:
                    raise ValueError('GRANT_GRANTEE_UNRESOLVED')
                name = identifier(grantee[0])[0]
                raw = f'GRANT {privilege_text} ON {quote_identifier(owner)}.{quote_identifier(table)} TO {quote_identifier(name)}'
                raw += ' WITH GRANT OPTION;' if option else ';'
                result.append({'kind':'GRANT', 'owner':owner, 'target':table, 'grantee':name,
                               'privilege':privilege_text.upper(), 'grantable':option,
                               'column_grant':column_grant, 'raw_ddl':raw.encode('utf-8')})
        return tuple(result)
    return ()
