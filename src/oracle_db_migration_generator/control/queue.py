"""Bounded local development queue; production uses its configured Jenkins executor."""
import os
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime,timezone

from .store import now


def process_alive(pid):
    if not isinstance(pid,int) or pid<=0:return False
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return False
        try:
            code=wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False
    except PermissionError:return True


class LocalQueue:
    def __init__(self,store):self.store=store;self.stop=threading.Event();self.children={}

    def tick(self):
        for run in self.store.scheduler_runs():
            if (run['status']=='RUNNING' or run.get('claimed')) and not run.get('pid'):
                age=(datetime.now(timezone.utc)-datetime.fromisoformat(run.get('claimed_at',run['created_at']))).total_seconds()
                if age>60:self.store.update_run(run['id'],status='FAILED',stage='FAILED',error_code='WORKER_INTERRUPTED',finished_at=now())
            if run['status']=='RUNNING' or run['status']=='QUEUED' and run.get('pid'):
                if run.get('pid') and not process_alive(run['pid']):self.store.update_run(run['id'],status='FAILED',stage='FAILED',error_code='WORKER_INTERRUPTED',finished_at=now())
        for id,child in list(self.children.items()):
            if child.poll() is not None:
                current=self.store.run(id)
                if current['status'] in {'QUEUED','RUNNING'}:
                    self.store.update_run(id,status='FAILED',stage='FAILED',error_code='WORKER_INTERRUPTED',finished_at=now())
                del self.children[id]
        while True:
            run=self.store.reserve_next_run(4)
            if run is None:break
            log=self.store.root/'worker-logs';log.mkdir(exist_ok=True)
            with (log/(run['id']+'.log')).open('ab') as stream:
                child=subprocess.Popen([sys.executable,'-m','oracle_db_migration_generator.control.worker',
                    '--root',str(self.store.root),'--run',run['id']],stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            self.children[run['id']]=child;self.store.update_run(run['id'],pid=child.pid)

    def start(self):
        def loop():
            while not self.stop.wait(.75):
                try:self.tick()
                except (OSError,ValueError,KeyError):continue
        self.thread=threading.Thread(target=loop,daemon=True);self.thread.start()

    def close(self):
        # Workers intentionally continue and retain their own deadline.
        self.stop.set();self.thread.join(timeout=2)
