"""Şema Karşılaştırma parser süreçlerinin sınırlı kapanma davranışını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from concurrent.futures import Future
from io import BytesIO
import subprocess

import pytest

from oracle_db_migration_generator.parsing import client


class FakeProcess:
    """Süreç kapanışının belirlenen sayıda gecikmesini taklit eder.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, timeouts=0, exited=False):
        self.timeouts=timeouts
        self.returncode=0 if exited else None
        self.kills=0
        self.waits=[]
        self.stdin=BytesIO()
        self.stdout=BytesIO()

    def poll(self):
        return self.returncode

    def kill(self):
        self.kills+=1

    def wait(self, timeout):
        self.waits.append(timeout)
        if self.timeouts:
            self.timeouts-=1
            raise subprocess.TimeoutExpired('synthetic-parser',timeout)
        self.returncode=0
        return 0


def parser(process):
    result=client.ParserClient.__new__(client.ParserClient)
    result.process=process
    return result


def test_killed_parser_retries_one_delayed_exit_and_closes_streams():
    process=FakeProcess(timeouts=1)
    parser(process).close()
    assert process.kills==2 and process.waits==[5,10]
    assert process.stdin.closed and process.stdout.closed


def test_exited_parser_needs_no_kill():
    process=FakeProcess(exited=True)
    parser(process).close()
    assert process.kills==0 and process.waits==[5]
    assert process.stdin.closed and process.stdout.closed


def test_persistent_exit_timeout_is_reported_after_bounded_retry():
    process=FakeProcess(timeouts=2)
    with pytest.raises(subprocess.TimeoutExpired):
        parser(process).close()
    assert process.kills==2 and process.waits==[5,10]


def test_one_cleanup_failure_does_not_skip_other_parser_slots(monkeypatch):
    processes=[FakeProcess(timeouts=2),FakeProcess()]
    class Executor:
        """Test görevlerini sırayla çalıştırıp bağımsız parser slotları kurar.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def __init__(self, max_workers, initializer):
            self.initializer=initializer
            self.index=0

        def submit(self, function, *args):
            self.initializer()
            client._worker_local.slot['client']=parser(processes[self.index])
            self.index+=1
            future=Future()
            future.set_result(function(*args))
            return future

        def shutdown(self, **kwargs):
            pass
    monkeypatch.setattr(client,'ThreadPoolExecutor',Executor)
    prior=getattr(client._worker_local,'slot',None)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            with client.parallel_parser_map(lambda item:item,[1,2],workers=2) as values:
                assert list(values)==[1,2]
    finally:
        if prior is None:
            del client._worker_local.slot
        else:
            client._worker_local.slot=prior
    assert processes[1].kills==1 and processes[1].stdout.closed
