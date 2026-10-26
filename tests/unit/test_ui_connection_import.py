import json
import pytest

from oracle_db_migration_generator.config.credentials import EnvCredentialResolver
from oracle_db_migration_generator.control.store import ControlStore
from tools.ui_import_connections import import_connections


def test_local_import_is_idempotent_encrypted_and_does_not_overwrite_edits(tmp_path):
    store=ControlStore(tmp_path)
    manifest={'project_code':'SKY','connections':[{'alias':'git','credential_id':'SOURCE',
        'connection':{'name':'Source','kind':'GIT','repository':'https://example.test/repo.git'}}]}
    resolver=EnvCredentialResolver(environ={'SOURCE_USER':'synthetic','SOURCE_PASSWORD':' synthetic secret '})
    imported=import_connections(store,manifest,resolver)
    assert import_connections(store,manifest,resolver)==imported
    c=store.list_records('connection')[0]
    assert c['revision']==1 and c['credential_configured'] is True
    assert store.credentials(c['id']).password==' synthetic secret '
    assert 'synthetic secret' not in json.dumps(c)
    assert all(b'synthetic secret' not in path.read_bytes() for path in tmp_path.rglob('*') if path.is_file())
    store.save_connection({**c,'repository':'https://example.test/changed.git'},actor='shared')
    with pytest.raises(ValueError,match='IMPORT_EXISTING_CONNECTION_DIFFERS'):import_connections(store,manifest,resolver)
    assert store.connection(c['id'])['repository']=='https://example.test/changed.git'
