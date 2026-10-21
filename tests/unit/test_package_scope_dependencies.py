from oracle_db_migration_generator.parsing.dependencies import references
from tests.factories import source


def package_body(sql):
    snapshot=source(sql)
    return next(obj for obj in snapshot.objects if obj.identity.object_type=='PACKAGE_BODY')


def test_nested_routine_does_not_hide_external_call_from_its_sibling():
    obj=package_body('CREATE PACKAGE BODY APP.P AS PROCEDURE A IS PROCEDURE X IS BEGIN NULL; END; BEGIN X; END; PROCEDURE B IS BEGIN X; END; END P;')
    calls=[(ref.owner,ref.object_type,ref.name) for ref in references(obj) if ref.role=='ROUTINE_CALL']
    assert calls==[('APP','CALLABLE','X')]


def test_nested_routine_and_ancestor_calls_keep_their_lexical_binding():
    obj=package_body('CREATE PACKAGE BODY APP.P AS PROCEDURE A IS PROCEDURE X IS BEGIN A; END; PROCEDURE Y IS BEGIN X; END; BEGIN X; Y; END; PROCEDURE B IS BEGIN A; END; END P;')
    assert not [ref for ref in references(obj) if ref.role=='ROUTINE_CALL']


def test_external_call_with_arguments_uses_only_the_callee_name():
    obj=package_body('CREATE PACKAGE BODY APP.P AS PROCEDURE A IS BEGIN APP.X(1); PKG_Y.RUN(2); END; END P;')
    calls=[(ref.owner,ref.object_type,ref.name) for ref in references(obj) if ref.role=='ROUTINE_CALL']
    assert calls==[('APP','CALLABLE','X'),('PKG_Y','CALLABLE','RUN')]


def test_type_dependencies_follow_effective_final_attribute_definition():
    desired=source('CREATE TYPE APP.T AS OBJECT (X NUMBER) ALTER TYPE APP.T MODIFY ATTRIBUTE (X APP.MISSING) CASCADE;')
    refs=references(desired.objects[0])
    assert [(ref.owner,ref.object_type,ref.name) for ref in refs]==[('APP','TYPE_SPEC','MISSING')]
    reverse=source('CREATE TYPE APP.T AS OBJECT (X APP.OLD) ALTER TYPE APP.T MODIFY ATTRIBUTE (X NUMBER) CASCADE;')
    assert not references(reverse.objects[0])

def test_sibling_external_call_blocks_missing_prerequisite_in_the_plan():
    from tests.unit.test_backend_completion import plan
    result=plan('CREATE PACKAGE APP.P AS PROCEDURE A; PROCEDURE B; END P; CREATE PACKAGE BODY APP.P AS PROCEDURE A IS PROCEDURE X IS BEGIN NULL; END; BEGIN X; END; PROCEDURE B IS BEGIN X; END; END P;')
    body=next(op for op in result.operations if op.identity.object_type=='PACKAGE_BODY')
    assert body.decision=='BLOCKED'
    assert 'APP.X' in body.reason_tr


def test_final_type_attribute_blocks_when_its_new_type_is_missing():
    from tests.unit.test_backend_completion import plan
    result=plan('CREATE TYPE APP.T AS OBJECT (X NUMBER) ALTER TYPE APP.T MODIFY ATTRIBUTE (X APP.MISSING) CASCADE;')
    assert result.operations[0].decision=='BLOCKED'
    assert 'APP.MISSING' in result.operations[0].reason_tr


def test_qualified_package_call_uses_observed_external_package_owner():
    from dataclasses import replace
    from oracle_db_migration_generator.model.snapshot import KnownValue
    obj=package_body("CREATE PACKAGE BODY APP.P AS PROCEDURE A IS BEGIN DBMS_OUTPUT.PUT_LINE('x'); END; END P;")
    obj=replace(obj,properties={**obj.properties,'dependencies':KnownValue('KNOWN',[{'owner':'SYS','name':'DBMS_OUTPUT','type':'PACKAGE'}],obj.evidence_ids)})
    calls=[(ref.owner,ref.object_type,ref.name) for ref in references(obj) if ref.role=='ROUTINE_CALL']
    assert calls==[('SYS','PACKAGE_SPEC','DBMS_OUTPUT')]
