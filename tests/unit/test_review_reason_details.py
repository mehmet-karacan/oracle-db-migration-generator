from test_rules import plan


def test_proven_shared_namespace_conflict_is_not_hidden_by_dependency_review():
    result=plan('CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN OTHER.PKG.F(); END;',
                'CREATE TABLE APP.COLLISION(ID NUMBER);')
    function=next(o for o in result.operations if o.identity.object_type=='FUNCTION')
    assert function.decision=='BLOCKED' and 'TARGET_NAMESPACE_CONFLICT' in function.reason_codes
    assert 'TABLE' in function.reason_tr and 'APP.COLLISION' in function.reason_tr


def test_type_review_names_column_and_both_sizes():
    result=plan('CREATE TABLE APP.T(C VARCHAR2(5 BYTE));','CREATE TABLE APP.T(C VARCHAR2(50 BYTE));')
    held=next(o for o in result.operations if o.decision=='REVIEW_REQUIRED')
    assert 'C' in held.reason_tr and 'VARCHAR2(50 BYTE)' in held.reason_tr and 'VARCHAR2(5 BYTE)' in held.reason_tr


def test_not_null_tightening_explains_required_data_check():
    result=plan('CREATE TABLE APP.T(C NUMBER NOT NULL);','CREATE TABLE APP.T(C NUMBER);')
    held=next(o for o in result.operations if o.decision=='REVIEW_REQUIRED')
    assert 'C' in held.reason_tr and 'NULL' in held.reason_tr and 'veri' in held.reason_tr.lower()
