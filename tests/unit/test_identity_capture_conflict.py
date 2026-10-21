from dataclasses import replace
import pytest
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from tests.factories import actual,source,profile


@pytest.mark.parametrize('ddl_identity,metadata_identity',[(True,'NO'),(False,'YES')])
def test_target_ddl_dictionary_identity_conflict_cannot_report_no_change(ddl_identity,metadata_identity):
    selected=profile();desired=source('CREATE TABLE APP.T(ID NUMBER NOT NULL);',selected)
    target=actual('CREATE TABLE APP.T(ID NUMBER '+('GENERATED ALWAYS AS IDENTITY ' if ddl_identity else '')+'NOT NULL);',selected)
    obj=target.objects[0]
    row={'table_name':'T','column_name':'ID','data_type':'NUMBER','data_type_owner':None,'data_length':22,
         'char_length':0,'char_used':None,'data_precision':None,'data_scale':None,'nullable':'N','data_default':None,
         'column_id':1,'hidden_column':'NO','virtual_column':'NO','identity_column':metadata_identity,
         'default_on_null':'NO','user_generated':'YES','collation':None}
    target=replace(target,objects=(replace(obj,properties={**obj.properties,
        'dictionary.columns':KnownValue('KNOWN',[row],obj.evidence_ids)}),))
    result=compare_snapshots(desired,target,selected.policy)
    identity=next(item for item in result.differences if item.property_path=='/columns/ID/identity')
    assert identity.kind=='UNKNOWN' and identity.before.state=='UNKNOWN'
    assert not result.complete
