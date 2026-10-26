from pathlib import Path
import pytest
from oracle_db_migration_generator.model.atomic import rename_new_directory


def test_transient_windows_file_lock_retries_without_changing_payload(tmp_path,monkeypatch):
    from oracle_db_migration_generator.model import atomic
    source=tmp_path/'staging';source.mkdir();(source/'source.sql').write_bytes(b'CREATE TABLE APP.A (ID NUMBER);\n')
    actual=atomic.os.rename;calls=[];delays=[]
    def rename(a,b):
        calls.append((a,b))
        if len(calls)==1:
            error=PermissionError('synthetic lock');error.winerror=5;raise error
        return actual(a,b)
    monkeypatch.setattr(atomic.os,'rename',rename);monkeypatch.setattr(atomic.time,'sleep',delays.append)
    rename_new_directory(source,tmp_path/'ready')
    assert len(calls)==2 and len(delays)==1
    assert (tmp_path/'ready'/'source.sql').read_bytes()==b'CREATE TABLE APP.A (ID NUMBER);\n'
    assert not source.exists()


def test_existing_destination_is_never_replaced(tmp_path):
    source=tmp_path/'staging';source.mkdir();destination=tmp_path/'ready';destination.mkdir()
    (destination/'user.txt').write_text('keep')
    with pytest.raises(FileExistsError):rename_new_directory(source,destination)
    assert (destination/'user.txt').read_text()=='keep' and source.exists()


def test_non_transient_permission_error_is_not_hidden(tmp_path,monkeypatch):
    from oracle_db_migration_generator.model import atomic
    source=tmp_path/'staging';source.mkdir();calls=[]
    def denied(*args):calls.append(args);raise PermissionError('synthetic ACL')
    monkeypatch.setattr(atomic.os,'rename',denied)
    with pytest.raises(PermissionError):rename_new_directory(source,tmp_path/'ready')
    assert len(calls)==1 and source.exists()
