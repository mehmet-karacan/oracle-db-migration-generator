"""Import approved local endpoint/credential references into the encrypted UI vault."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

from oracle_db_migration_generator.config.credentials import EnvCredentialResolver
from oracle_db_migration_generator.control.models import ConnectionInput
from oracle_db_migration_generator.control.store import ControlStore


def import_connections(store,manifest,resolver):
    project=next(p for p in store.list_records('project') if p['code']==manifest['project_code'])
    result={}
    for item in manifest['connections']:
        values={**item['connection'],'project_id':project['id']}
        if item.get('credential_id'):
            secret=resolver(item['credential_id'])
            values.update(username=secret.username,password=secret.password)
        expected=ConnectionInput.model_validate(values).model_dump(exclude={'username','password'})
        existing=[c for c in store.list_records('connection',project_id=project['id']) if c['name']==values['name']]
        if existing:
            if len(existing)!=1 or any(existing[0].get(k)!=v for k,v in expected.items()):
                raise ValueError('IMPORT_EXISTING_CONNECTION_DIFFERS')
            saved=existing[0]
            if item.get('credential_id') and store.credentials(saved['id'])!=secret:
                raise ValueError('IMPORT_EXISTING_CREDENTIAL_DIFFERS')
        else:saved=store.save_connection(values,actor='shared')
        result[item['alias']]=saved['id']
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--manifest',required=True);parser.add_argument('--credentials-file',required=True)
    args=parser.parse_args()
    result=import_connections(ControlStore(args.root),json.loads(Path(args.manifest).read_text(encoding='utf-8-sig')),
                              EnvCredentialResolver(Path(args.credentials_file)))
    print(json.dumps({'imported':result}))


if __name__=='__main__':main()
