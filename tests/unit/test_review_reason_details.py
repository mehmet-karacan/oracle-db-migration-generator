"""Oracle DB Migration Generator DDL karar açıklamalarını sınar.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from test_rules import plan


def test_proven_shared_namespace_conflict_is_not_hidden_by_dependency_review():
    result=plan('CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN OTHER.PKG.F(); END;',
                'CREATE TABLE APP.COLLISION(ID NUMBER);')
    function=next(o for o in result.operations if o.identity.object_type=='FUNCTION')
    assert function.decision=='BLOCKED' and 'TARGET_NAMESPACE_CONFLICT' in function.reason_codes
    assert 'TABLE' in function.reason_tr and 'APP.COLLISION' in function.reason_tr


def test_type_change_writes_source_size():
    result=plan('CREATE TABLE APP.T(C VARCHAR2(5 BYTE));','CREATE TABLE APP.T(C VARCHAR2(50 BYTE));')
    ready=next(o for o in result.operations if o.kind=='MODIFY_COLUMN' and o.decision=='READY')
    assert b'"C" VARCHAR2(5 BYTE)' in ready.intent.statement


def test_not_null_tightening_writes_source_ddl():
    result=plan('CREATE TABLE APP.T(C NUMBER NOT NULL);','CREATE TABLE APP.T(C NUMBER);')
    ready=next(o for o in result.operations if o.kind=='MODIFY_COLUMN' and o.decision=='READY')
    assert b'"C" NOT NULL' in ready.intent.statement
