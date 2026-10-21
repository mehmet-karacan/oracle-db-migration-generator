from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import Coverage
from tests.factories import actual, profile, source


def partial_inventory(snapshot):
    return replace(snapshot, completeness=Coverage('PARTIAL', 'PARTIAL',
                   snapshot.completeness.dictionary, ('SOURCE_FILE_UNPARSED', 'PARSER_TIMEOUT')))


@pytest.mark.parametrize('side', ['SOURCE', 'TARGET'])
@pytest.mark.parametrize('extension,prefix', [
    (', TARGET_ONLY NUMBER', '/columns/TARGET_ONLY/'),
    (', CONSTRAINT CK_TARGET_ONLY CHECK(ID>0)', '/constraints/CK_TARGET_ONLY/'),
])
def test_complete_object_absence_does_not_depend_on_unrelated_inventory(side, extension, prefix):
    left = 'CREATE TABLE APP.DEMO(ID NUMBER);'
    right = f'CREATE TABLE APP.DEMO(ID NUMBER{extension});'
    desired = source(left if side == 'SOURCE' else right)
    target = actual(right if side == 'SOURCE' else left)
    if side == 'SOURCE':
        desired = partial_inventory(desired)
    else:
        target = partial_inventory(target)
    originals = desired.to_dict(), target.to_dict()
    result = compare_snapshots(desired, target, profile().policy)
    rows = [diff for diff in result.differences if diff.property_path.startswith(prefix)]
    assert rows
    assert all(diff.kind == ('UNKNOWN' if side=='SOURCE' else
                           'INFORMATIONAL' if diff.property_path.endswith('/position') else 'MISSING') for diff in rows)
    assert all((diff.after if side == 'SOURCE' else diff.before).state ==
               ('UNKNOWN' if side=='SOURCE' else 'ABSENT') for diff in rows)
    assert all((diff.after if side == 'SOURCE' else diff.before).evidence_ids for diff in rows)
    assert not result.complete and result.scope.inventory == 'PARTIAL'
    assert (desired.to_dict(), target.to_dict()) == originals


@pytest.mark.parametrize('missing_proof', ['partial_ddl', 'partial_object_inventory', 'no_evidence'])
def test_object_field_absence_stays_unknown_without_complete_object_proof(missing_proof):
    desired = partial_inventory(source('CREATE TABLE APP.DEMO(ID NUMBER);'))
    target = actual('CREATE TABLE APP.DEMO(ID NUMBER, TARGET_ONLY NUMBER);')
    obj = desired.objects[0]
    if missing_proof == 'partial_ddl':
        obj = replace(obj, coverage=replace(obj.coverage, ddl='PARTIAL'))
    elif missing_proof == 'partial_object_inventory':
        obj = replace(obj, coverage=replace(obj.coverage, inventory='PARTIAL'))
    else:
        obj = replace(obj, evidence_ids=())
    desired = replace(desired, objects=(obj,))
    rows = [diff for diff in compare_snapshots(desired, target, profile().policy).differences
            if diff.property_path.startswith('/columns/TARGET_ONLY/')]
    assert rows and all(diff.kind == 'UNKNOWN' and diff.after.state == 'UNKNOWN' for diff in rows)


@pytest.mark.parametrize('side', ['SOURCE', 'TARGET'])
def test_global_object_presence_stays_unknown_when_inventory_is_partial(side):
    desired = source('CREATE TABLE APP.DEMO(ID NUMBER);')
    target = actual('CREATE TABLE APP.DEMO(ID NUMBER);')
    if side == 'SOURCE':
        desired = replace(partial_inventory(desired), objects=())
    else:
        target = replace(partial_inventory(target), objects=())
    rows = compare_snapshots(desired, target, profile().policy).differences
    assert len(rows) == 1 and rows[0].property_path == '/presence'
    assert rows[0].kind == 'UNKNOWN'
    assert (rows[0].after if side == 'SOURCE' else rows[0].before).state == 'UNKNOWN'
