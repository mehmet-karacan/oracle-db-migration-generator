"""Link authenticated-browser-observed Jenkins run metadata, never SQL bundles."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

from oracle_db_migration_generator.control.store import ControlStore
from oracle_db_migration_generator.control.jenkins_browser import link_completed_run


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True);parser.add_argument('--run-id',required=True)
    parser.add_argument('--observed-run-json',required=True)
    parser.add_argument('--observed-performance-json')
    args=parser.parse_args()
    timing=json.loads(Path(args.observed_performance_json).read_bytes()) if args.observed_performance_json else None
    result=link_completed_run(ControlStore(args.root),args.run_id,json.loads(Path(args.observed_run_json).read_bytes()),performance=timing)
    print(json.dumps({k:result[k] for k in ('id','status','started_at','finished_at')},ensure_ascii=False))


if __name__=='__main__':main()
