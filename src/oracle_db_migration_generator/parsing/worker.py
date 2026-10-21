"""Bounded child process: validate grammar and extract complete unit spans."""
import base64
import json
import sys
from dataclasses import replace

from antlr4 import CommonTokenStream, InputStream
from antlr4.atn.PredictionMode import PredictionMode

from .._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
from .._vendor.analyzer_core.oracle.generated.PlSqlParser import PlSqlParser
from .._vendor.analyzer_core.oracle.parser_worker import CollectingErrorListener
from .._vendor.analyzer_core.oracle.scanner import scan
from .._vendor.analyzer_core.oracle.projections import project
from .canonicalize import canonical_sql
from .codec import encode
from .grammar_compat import grammar_text,scanner_text,storage_scope_valid,grammar_token_stream
from .inline_keys import inline_backing_keys

SIDECAR_RULES = {'Grant_statementContext': 'GRANT', 'Comment_on_tableContext': 'COMMENT',
                 'Comment_on_columnContext': 'COMMENT', 'Alter_tableContext': 'ALTER_TABLE',
                 'Alter_triggerContext': 'ALTER_TRIGGER', 'Alter_indexContext':'ALTER_INDEX'}


def checked_units(text,object_type=None,*,metadata=False):
    original=text
    text=grammar_text(text)
    modes=(PredictionMode.LL,PredictionMode.SLL) if object_type in {'VIEW','PACKAGE_SPEC','PACKAGE_BODY'} else (PredictionMode.SLL,PredictionMode.LL)
    for mode in modes:
        lexer = PlSqlLexer(InputStream(text))
        lex_errors = CollectingErrorListener()
        lexer.removeErrorListeners(); lexer.addErrorListener(lex_errors)
        parser = PlSqlParser(grammar_token_stream(lexer,object_type))
        parse_errors = CollectingErrorListener()
        parser.removeErrorListeners(); parser.addErrorListener(parse_errors)
        parser._interp.predictionMode = mode
        if metadata:
            statements=[];commands=[]
            while parser.getCurrentToken().type!=-1:
                if parser.getCurrentToken().type in {PlSqlParser.SEMICOLON,PlSqlParser.SOLIDUS}:
                    parser.getTokenStream().consume();continue
                before=parser.getCurrentToken().tokenIndex
                statements.append(parser.unit_statement())
                if parser.getCurrentToken().tokenIndex<=before:
                    parse_errors.errors.append({'line':1,'column':0,'code':'UNCONSUMED_METADATA_INPUT'})
                    break
        else:
            tree = parser.sql_script();statements=tree.unit_statement();commands=tree.sql_plus_command()
        errors = lex_errors.errors + parse_errors.errors
        if not errors and not storage_scope_valid(original,statements):
            return False, []
        if not errors:
            units = []
            for unit in statements:
                start, end = unit.start.start, unit.stop.stop + 1
                while end < len(text) and text[end].isspace():
                    end += 1
                if end < len(text) and text[end] == ';':
                    end += 1
                units.append((type(unit.getChild(0)).__name__, start, end,unit.getChild(0)))
            for command in commands:
                units.append(('Sql_plus_commandContext',command.start.start,command.stop.stop+1,command))
            units.sort(key=lambda item:item[1])
            return True, units
    return False, []


def parse_payload(payload):
    raw = base64.b64decode(payload['raw'], validate=True)
    if len(raw) > 2 * 1024 * 1024:
        return {'objects': [], 'sidecars': [], 'diagnostics': ['PARSE_UNIT_TOO_LARGE']}
    try:
        text = raw.decode('utf-8', errors='strict')
    except UnicodeError:
        return {'objects': [], 'sidecars': [], 'diagnostics': ['ENCODING_UNRESOLVED']}
    scanned = scan(scanner_text(text).encode('utf-8'), default_schema=payload.get('default_schema'))
    result = {'objects': [], 'sidecars': [], 'diagnostics': []}
    ranges = []
    if scanned.occurrences:
        first = scanned.occurrences[0].start_char
        if canonical_sql(text[:first]) != '[]':
            ranges.append((None, 0, first))
        ranges += [(occ, occ.start_char, occ.end_char) for occ in scanned.occurrences]
    else:
        ranges.append((None, 0, len(text)))
    for occurrence, start, end in ranges:
        original_fragment = text[start:end]
        leading_bom = len(original_fragment) - len(original_fragment.lstrip('\ufeff'))
        start += leading_bom
        fragment = text[start:end]
        ok, units = checked_units(fragment,occurrence.object_type if occurrence else None,metadata=bool(payload.get('metadata')))
        diagnostics = []
        if not ok:
            diagnostics.append('PARSER_SYNTAX_ERROR')
        create = None
        inline_keys=[]
        for rule, begin, finish,unit in units:
            statement = fragment[begin:finish]
            if rule.startswith('Create_') and occurrence is not None and create is None:
                create = (statement, start + begin, start + finish,unit if begin==0 else None)
                if ok and occurrence.object_type=='TABLE': inline_keys=inline_backing_keys(unit,fragment)
            elif rule in SIDECAR_RULES:
                result['sidecars'].append({'kind': SIDECAR_RULES[rule], 'text': statement,
                                           'start_char': start + begin, 'end_char': start + finish})
            else:
                diagnostics.append('UNSUPPORTED_STATEMENT')
        if occurrence is not None:
            if create is None:
                create = (fragment, start, end,None)
            statement, begin, finish,parsed_root = create
            parse_statement=statement if occurrence.object_type in {'TABLE','INDEX'} else grammar_text(statement)
            supplemental=()
            if ok and occurrence.object_type=='TABLE':
                from .table_logging import table_projection_input
                parse_statement,supplemental=table_projection_input(parse_statement)
            projection = project(occurrence, parse_statement, parse_ok=ok,parsed_root=parsed_root)
            if supplemental:
                from .projections import effective_key
                columns={effective_key(key) for key in projection.properties.get('columns',{})}
                props=dict(projection.properties);table_props=dict(props.get('table_properties',{}))
                table_props['supplemental_logging']=', '.join(item['definition'] for item in supplemental)
                props.update(table_properties=table_props,_generator_supplemental_logging=supplemental)
                projection=replace(projection,properties=props)
                if any(name not in columns for item in supplemental for name in item['columns']):
                    diagnostics.append('SUPPLEMENTAL_LOG_COLUMN_UNVERIFIED')
            if inline_keys:
                props=dict(projection.properties);props['_generator_inline_backing_keys']=inline_keys
                projection=replace(projection,properties=props)
            if ok and occurrence.object_type in {'PROCEDURE','FUNCTION'}:
                from .._vendor.analyzer_core.oracle.package import extract_standalone_routine
                extracted=extract_standalone_routine(parse_statement,occurrence.object_type,parsed_root=parsed_root)
                if extracted.diagnostics or not extracted.routines:
                    diagnostics.append('ROUTINE_DEPENDENCY_ANALYSIS_UNAVAILABLE')
                else:
                    props=dict(projection.properties)
                    props['_generator_routine_analysis']=[{'name':routine.name,
                        'types':[parameter.data_type for parameter in routine.parameters]+([routine.return_type] if routine.return_type else []),
                        'calls':list(routine.call_references),'dynamic_sql':bool(routine.dynamic_sql)} for routine in extracted.routines]
                    projection=replace(projection,properties=props)
            # Scanner calls standalone TYPE "TYPE"; Generator distinguishes spec/body.
            object_type = 'TYPE_SPEC' if occurrence.object_type == 'TYPE' else occurrence.object_type
            projection = replace(projection, object_type=object_type)
            result['objects'].append({'object_type': object_type, 'raw_schema': occurrence.raw_schema,
                                      'schema_quoted': occurrence.schema_quoted,
                                      'raw_name': occurrence.raw_name, 'name_quoted': occurrence.name_quoted,
                                      'start_char': begin, 'end_char': finish,
                                      'parse_ok': ok and not diagnostics, 'diagnostics': diagnostics,
                                      'projection': encode(projection)})
        result['diagnostics'].extend(diagnostics)
    result['diagnostics'] = sorted(set(result['diagnostics']))
    return result


def main():
    while True:
        line = sys.stdin.buffer.readline(4 * 1024 * 1024)
        if not line:
            break
        try:
            result = parse_payload(json.loads(line))
        except Exception:
            result = {'objects': [], 'sidecars': [], 'diagnostics': ['PARSER_INTERNAL_ERROR']}
        rendered = json.dumps(result, ensure_ascii=True, separators=(',', ':'))
        if len(rendered) > 32 * 1024 * 1024:
            rendered = '{"objects":[],"sidecars":[],"diagnostics":["PARSER_OUTPUT_TOO_LARGE"]}'
        sys.stdout.write(rendered + '\n'); sys.stdout.flush()


if __name__ == '__main__':
    main()
