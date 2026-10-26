import hashlib

from ..parsing.adapter import parse_ddl


def render_statement(operation,plan_id):
    intent=operation.intent
    if operation.decision!='READY' or intent is None:
        raise ValueError('EMITTED_SQL_NOT_READY')
    if hashlib.sha256(intent.statement).hexdigest()!=intent.verification_sha256:
        raise ValueError('EMITTED_SQL_INTEGRITY_MISMATCH')
    parsed=parse_ddl(intent.statement,operation.identity)
    if parsed.diagnostics:
        raise ValueError('EMITTED_SQL_PARSE_FAILED')
    if operation.kind in {'CREATE','REPLACE','CREATE_INDEX'}:
        if len(parsed.objects)!=1 or parsed.sidecars or parsed.objects[0].identity.key!=operation.identity.key or not parsed.objects[0].parse_ok:
            raise ValueError('EMITTED_SQL_IDENTITY_OR_STATEMENT_MISMATCH')
    else:
        expected={'ADD_COLUMN':'ALTER_TABLE','MODIFY_COLUMN':'ALTER_TABLE','ADD_CONSTRAINT':'ALTER_TABLE','GRANT':'GRANT','COMMENT':'COMMENT'}[operation.kind]
        if parsed.objects or len(parsed.sidecars)!=1 or parsed.sidecars[0]['kind']!=expected:
            raise ValueError('EMITTED_SQL_STATEMENT_MISMATCH')
    text=intent.statement.decode('utf-8').rstrip()
    # The parser clips a runner slash from source units. Only the renderer adds it.
    if text.endswith('\n/'):
        text=text[:-2].rstrip()
    if not text.endswith(';'): text+=';'
    suffix='\n/\n' if intent.statement_kind=='PLSQL' else '\n'
    return (f'-- plan_id: {plan_id}\n-- operation_id: {operation.operation_id}\n'+text+suffix).encode('utf-8')


def aggregate_sql(paths,plan_id,*,partial=False,source_commit=None,target_id=None,source_origin=None):
    title='PARTIAL READY SUBSET - REVIEW THE COMPLETE PLAN' if partial else 'READY MIGRATION PLAN'
    header=f'-- {title}\n-- plan_id: {plan_id}\n-- source_commit: {source_commit}\n-- target_id: {target_id}\n-- Generated offline; NOT EXECUTED.\nWHENEVER OSERROR EXIT FAILURE\nWHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK\nSET DEFINE OFF\nSET SQLBLANKLINES ON\n\n'
    if source_origin:
        header=header.replace(f'-- source_commit: {source_commit}\n',f"-- source_kind: ORACLE\n-- source_snapshot: {source_origin['snapshot_id']}\n")
    import re
    if any(not re.fullmatch(r'objects/(?:[A-Za-z0-9_-]{1,80}/[A-Za-z0-9_-]{1,80}/[A-Za-z0-9_-]{1,80}/)?op-[0-9a-f]{64}\.sql',path) for path in paths):
        raise ValueError('EMITTED_SQL_INCLUDE_PATH_UNSAFE')
    return header.encode()+''.join('@@'+path+'\n' for path in paths).encode()
