"""Şema Karşılaştırma çözümleyicilerini sınırlı süreçlerle çalıştırır.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import atexit
import base64
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from contextvars import copy_context
import json
import os
import queue
import subprocess
import sys
import threading

_client = None
_lock = threading.RLock()
_worker_local = threading.local()


def parser_workers():
    """Kaynak çözümlemesinde kullanılacak süreç sınırını okur."""
    try:
        count = int(os.environ.get('GENERATOR_PARSER_WORKERS', '4'))
    except ValueError:
        raise ValueError('PARSER_WORKERS_INVALID') from None
    if not 1 <= count <= 8:
        raise ValueError('PARSER_WORKERS_INVALID')
    return count


@contextmanager
def parallel_parser_map(function, items, *, workers=None, ordered=True):
    """Bağımsız girdileri çözümler ve seçilen sırada sonuçları verir.

    Her iş parçacığı kendi parser sürecini kullanır. Bekleyen işler sınırlıdır.
    Varsayılan girdi sırasıdır. Tamamlanma sırası uzun girdinin diğer
    görevlerin başlamasını geciktirmesini önler. Çıkışta süreçler kapatılır.
    """
    count = parser_workers() if workers is None else workers
    if not isinstance(count, int) or not 1 <= count <= 8:
        raise ValueError('PARSER_WORKERS_INVALID')
    if hasattr(items, '__len__'):
        count = min(count, max(1, len(items)))
    if count == 1:
        yield map(function, items)
        return
    slots = []
    def initialize():
        slot = {'client': None}
        _worker_local.slot = slot
        with _lock:
            slots.append(slot)
    executor = ThreadPoolExecutor(max_workers=count, initializer=initialize)
    pending = deque()
    source = iter(items)
    def submit_one():
        try:
            item = next(source)
        except StopIteration:
            return False
        pending.append(executor.submit(copy_context().run, function, item))
        return True
    def ordered_results():
        for _ in range(count * 2):
            if not submit_one():
                break
        while pending:
            result = pending.popleft().result()
            submit_one()
            yield result
    def completed_results():
        for _ in range(count * 2):
            if not submit_one():
                break
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                pending.remove(future)
                result = future.result()
                submit_one()
                yield result
    try:
        yield ordered_results() if ordered else completed_results()
    finally:
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        for slot in slots:
            if slot['client'] is not None:
                slot['client'].close()


class ParserClient:
    def __init__(self):
        self.process = subprocess.Popen([sys.executable, '-m', 'oracle_db_migration_generator.parsing.worker'],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.responses = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            self.responses.put(line)
        self.responses.put(None)

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()

    def request(self, raw, default_schema, timeout,metadata=False):
        payload = {'raw': base64.b64encode(raw).decode('ascii'), 'default_schema': default_schema,'metadata':metadata}
        self.process.stdin.write(json.dumps(payload).encode() + b'\n'); self.process.stdin.flush()
        try:
            line = self.responses.get(timeout=timeout)
        except queue.Empty:
            self.close()
            raise TimeoutError('PARSER_TIMEOUT') from None
        if line is None:
            raise RuntimeError('PARSER_WORKER_TERMINATED')
        return json.loads(line)


def request_parse(raw: bytes, default_schema: str | None, timeout: float = 30,*,metadata=False):
    global _client
    slot = getattr(_worker_local, 'slot', None)
    if slot is not None:
        return _isolated_request(slot, raw, default_schema, timeout, metadata)
    with _lock:
        cache = None
        if os.environ.get('GENERATOR_PARSER_CACHE_DIR'):
            from .response_cache import configured_cache
            cache = configured_cache(raw, default_schema, metadata)
        if cache is not None:
            cached = cache.load()
            if cached is not None:
                return cached
        if _client is None or _client.process.poll() is not None:
            _client = ParserClient()
        try:
            result = _client.request(raw, default_schema, timeout,metadata)
            if cache is not None:
                cache.store(result)
            return result
        except (TimeoutError, BrokenPipeError, RuntimeError):
            _client.close()
            _client = None
            raise


def _isolated_request(slot, raw, default_schema, timeout, metadata):
    cache = None
    if os.environ.get('GENERATOR_PARSER_CACHE_DIR'):
        from .response_cache import configured_cache
        cache = configured_cache(raw, default_schema, metadata)
    if cache is not None:
        cached = cache.load()
        if cached is not None:
            return cached
    if slot['client'] is None or slot['client'].process.poll() is not None:
        slot['client'] = ParserClient()
    try:
        result = slot['client'].request(raw, default_schema, timeout, metadata)
        if cache is not None:
            cache.store(result)
        return result
    except (TimeoutError, BrokenPipeError, RuntimeError):
        slot['client'].close()
        slot['client'] = None
        raise


@atexit.register
def close_parser():
    if _client is not None:
        _client.close()
