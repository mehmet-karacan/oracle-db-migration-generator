"""One isolated driver lifetime per test; inputs contain no plaintext credentials."""
import argparse
import json
import re
import sys

from .runner import test_connection
from .runtime import runtime_settings
from .store import ControlStore
from ..oracle.preflight import safe_error_code


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--connection',required=True);parser.add_argument('--revision',required=True,type=int)
    args=parser.parse_args()
    try:
        data=json.load(sys.stdin);store=ControlStore(args.root)
        with store.transaction() as db:
            row=db.execute("SELECT document FROM records WHERE kind='connection' AND id=? AND revision=?",(args.connection,args.revision)).fetchone()
        if row is None:raise ValueError('RECORD_NOT_FOUND')
        with runtime_settings(data['settings']):
            result=test_connection(store,json.loads(row[0]),schemas=data['schemas'],settings=data['settings'])
        print(json.dumps(result));return 0
    except Exception as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]{1,100}',str(error)) else safe_error_code(error)
        print(json.dumps({'status':'FAILED','error_code':code}));return 1


if __name__=='__main__':raise SystemExit(main())
