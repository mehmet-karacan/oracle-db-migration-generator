import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('example,schema', [
    ('source-profile', 'source-profile'), ('targets', 'targets'),
    ('source-snapshot', 'snapshot'), ('target-snapshot', 'snapshot'),
    ('plan', 'plan'), ('run', 'run'), ('bundle-manifest', 'bundle-manifest'),
])
def test_supplied_examples_follow_closed_contracts(example, schema):
    document = json.loads((ROOT / f'examples/{example}.example.json').read_text(encoding='utf-8'))
    contract = json.loads((ROOT / f'schemas/{schema}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(contract)
    Draft202012Validator(contract).validate(document)


@pytest.mark.parametrize('name', ['source-profile', 'targets'])
def test_packaged_configuration_contracts_match_authoritative_schemas(name):
    expected = (ROOT / f'schemas/{name}.schema.json').read_bytes()
    assert files('oracle_db_migration_generator').joinpath('schemas', f'{name}.schema.json').read_bytes() == expected


def test_contract_command_checks_all_packaged_schemas_and_semantic_plan(tmp_path):
    import shutil
    from tools.check_contracts import check_contracts
    result=check_contracts(ROOT)
    assert result['status']=='VERIFIED' and result['schemas']==7 and result['examples']==8
    shutil.copytree(ROOT/'schemas',tmp_path/'schemas')
    shutil.copytree(ROOT/'examples',tmp_path/'examples')
    schema=tmp_path/'schemas/plan.schema.json'
    document=json.loads(schema.read_text(encoding='utf-8'));document['description']='unpackaged drift'
    schema.write_text(json.dumps(document),encoding='utf-8')
    with pytest.raises(ValueError,match='CONTRACT_PACKAGE_DRIFT'):check_contracts(tmp_path)
    shutil.copyfile(ROOT/'schemas/plan.schema.json',schema)
    plan=tmp_path/'examples/plan.example.json'
    document=json.loads(plan.read_text(encoding='utf-8'));document['counts']['ready_operations']+=1
    plan.write_text(json.dumps(document),encoding='utf-8')
    with pytest.raises(ValueError,match='PLAN_ID_MISMATCH'):check_contracts(tmp_path)
