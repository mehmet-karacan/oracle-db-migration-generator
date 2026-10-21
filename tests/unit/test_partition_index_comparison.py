from dataclasses import replace

from oracle_db_migration_generator.compare.projection_adapter import canonical_fields
from tests.factories import actual, profile
from tests.unit.test_partition_index_status import index


def test_partition_leaf_status_is_used_in_canonical_comparison():
    selected=profile()
    snapshot=actual('CREATE INDEX APP.IDX ON APP.T(ID);',selected)
    obj=snapshot.objects[0]
    obj=replace(obj,properties={**obj.properties,**index().properties})
    assert canonical_fields(obj,snapshot,selected.policy)['/index/availability'].value=='VALID'


def test_unusable_partition_remains_an_observed_index_difference():
    selected=profile()
    snapshot=actual('CREATE INDEX APP.IDX ON APP.T(ID);',selected)
    obj=replace(snapshot.objects[0],properties={**snapshot.objects[0].properties,
                                             **index(statuses=('USABLE','UNUSABLE')).properties})
    value=canonical_fields(obj,snapshot,selected.policy)['/index/availability']
    assert value.state=='KNOWN' and value.value=='UNUSABLE'
