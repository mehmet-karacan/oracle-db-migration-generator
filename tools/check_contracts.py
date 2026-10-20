"""Check repository/package contracts and supplied examples without network I/O."""
import json
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator,FormatChecker

from oracle_db_migration_generator.artifacts.validation import validate_plan
from oracle_db_migration_generator.config.loader import read_json,load_source_profile,load_targets


EXAMPLES={'source-profile':'source-profile','targets':'targets','source-snapshot':'snapshot',
          'target-snapshot':'snapshot','plan':'plan','run':'run','bundle-manifest':'bundle-manifest','catalog':'catalog'}


def check_contracts(root):
    root=Path(root)
    packaged=files('oracle_db_migration_generator').joinpath('schemas')
    paths=sorted((root/'schemas').glob('*.schema.json'))
    if not paths or {path.name for path in paths}!={path.name for path in packaged.iterdir() if path.name.endswith('.schema.json')}:
        raise ValueError('CONTRACT_PACKAGE_DRIFT')
    validators={}
    for path in paths:
        if path.read_bytes()!=packaged.joinpath(path.name).read_bytes():raise ValueError('CONTRACT_PACKAGE_DRIFT')
        schema=read_json(path);Draft202012Validator.check_schema(schema)
        validators[path.name]=Draft202012Validator(schema,format_checker=FormatChecker())
    documents={}
    for name,schema in EXAMPLES.items():
        document=read_json(root/'examples'/(name+'.example.json'))
        if next(validators[schema+'.schema.json'].iter_errors(document),None) is not None:
            raise ValueError('CONTRACT_EXAMPLE_INVALID')
        documents[name]=document
    load_source_profile(root/'examples/source-profile.example.json')
    load_targets(root/'examples/targets.example.json',('ALL',))
    plan=validate_plan(documents['plan'])
    manifest=documents['bundle-manifest']
    if (manifest['plan_id']!=plan['plan_id'] or manifest['target_id']!=plan['target']['id']
            or documents['source-snapshot']['source_commit']!=plan['source']['commit_sha']
            or documents['run']['source_commit']!=plan['source']['commit_sha']):
        raise ValueError('CONTRACT_EXAMPLE_LINK_MISMATCH')
    return {'status':'VERIFIED','schemas':len(validators),'examples':len(documents),
            'checks':['PACKAGE_SCHEMA_BYTES','JSON_SCHEMA','EXAMPLE_SCHEMA','CONFIG_SEMANTICS',
                      'PLAN_HASH_AND_REFERENCES','EXAMPLE_LINKS'],'network_accessed':False}


def main():
    try:
        result=check_contracts(Path(__file__).resolve().parents[1])
    except (ValueError,OSError,KeyError):
        print(json.dumps({'status':'FAILED','error_code':'CONTRACT_CHECK_FAILED','network_accessed':False}))
        return 30
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
