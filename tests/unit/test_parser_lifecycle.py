import subprocess
import sys


def test_parser_child_exits_with_its_calling_cli():
    code="from oracle_db_migration_generator.parsing.client import request_parse; print(request_parse(b'CREATE TABLE APP.T(ID NUMBER);','APP')['diagnostics'],flush=True)"
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=15)
    assert result.returncode==0 and result.stdout.strip()==b'[]'
