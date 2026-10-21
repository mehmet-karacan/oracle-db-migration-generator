import atexit
import base64
import json
import os
import queue
import subprocess
import sys
import threading

_client = None
_lock = threading.RLock()


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


@atexit.register
def close_parser():
    if _client is not None:
        _client.close()
