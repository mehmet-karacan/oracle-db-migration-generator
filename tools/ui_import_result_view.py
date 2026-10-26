"""Link operator-observed structural metadata to one completed run/target."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

from oracle_db_migration_generator.control.results import import_view
from oracle_db_migration_generator.control.store import ControlStore


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--run-id',required=True);parser.add_argument('--target-id',required=True)
    parser.add_argument('--view',required=True)
    args=parser.parse_args();path=Path(args.view)
    if path.stat().st_size>64*1024*1024:raise ValueError('RESULT_TOO_LARGE')
    result=import_view(ControlStore(args.root),args.run_id,args.target_id,json.loads(path.read_bytes()))
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
