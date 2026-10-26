"""Standalone worker survives a closed browser or restarted API."""
import argparse
import os
import threading
import time

from .runner import execute_run
from .store import ControlStore,now


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--run',required=True)
    args=parser.parse_args();store=ControlStore(args.root);run=store.run(args.run)
    def expired():
        store.update_run(args.run,status='FAILED',stage='FAILED',error_code='JOB_TIMEOUT',finished_at=now())
        os._exit(124)
    timer=threading.Timer(run['spec']['settings']['job_timeout_seconds'],expired);timer.daemon=True;timer.start()
    try:
        while store.run(args.run)['status']=='QUEUED':
            execute_run(store,args.run)
            if store.run(args.run)['status']=='QUEUED':time.sleep(.75)
        return {'COMPLETE':0,'PARTIAL':10}.get(store.run(args.run)['status'],20)
    finally:timer.cancel()


if __name__=='__main__':raise SystemExit(main())
