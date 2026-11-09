"""Şema Karşılaştırma canlı toplama süresini ve seri tekrarın eşitliğini ölçer.

Kayıtlı proje profili ve yerel Git commit'i kullanılır. Oracle çağrıları yalnız
metadata okur. Gerçek SQL içeren okuma kaydı özel run dizininde tutulur.
Seri tekrar aynı sorgu sonuçlarını ve parser kanıtlarını kullanarak oturum
paralelliğini diğer değişkenlerden ayırır. Parolalar kayda alınmaz.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
from threading import Lock
from time import perf_counter

from oracle_db_migration_generator.control.runner import execute_run, make_profile
from oracle_db_migration_generator.control.runtime import runtime_settings
from oracle_db_migration_generator.control.store import ControlStore
from oracle_db_migration_generator.model.serialization import canonical_bytes, digest
from oracle_db_migration_generator.oracle import collector
from oracle_db_migration_generator.oracle.connection import connect_read_only
from oracle_db_migration_generator.oracle.preflight import safe_error_code
from oracle_db_migration_generator.source import sidecars


class QueryTrace:
    """Metadata satırlarını özel bellekte ve run arşivinde tutar.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self):
        self.rows = defaultdict(list)
        self.lock = Lock()
        self.positions = defaultdict(int)
        self.missing = []
    def key(self, query, binds):
        return canonical_bytes([query, binds]).decode()
    def append(self, key, method, value):
        with self.lock: self.rows[key+'|'+method].append(value)
    def read(self, key, method):
        combined = key+'|'+method
        with self.lock:
            values = self.rows.get(combined)
            if not values:
                self.missing.append(digest(combined))
                raise ValueError('REPLAY_QUERY_MISSING')
            index = self.positions[combined]
            if index >= len(values):
                self.missing.append(digest(combined))
                raise ValueError('REPLAY_QUERY_EXHAUSTED')
            self.positions[combined] += 1
            return values[index]


class TracedCursor:
    """LOB değerlerini oturumun sahibi olan iş parçacığında okur ve kaydeder.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, native, trace): self.native, self.trace, self.key = native, trace, None
    def execute(self, query, binds=None):
        self.key = self.trace.key(query, binds)
        try: self.native.execute(query, binds)
        except Exception as error:
            self.trace.append(self.key, 'execute', {'error':safe_error_code(error)})
            raise
        self.trace.append(self.key, 'execute', {'ok':True})
        return self
    def _fetch(self, method):
        try:
            value = getattr(self.native, method)()
            def row(items): return tuple(cell.read() if hasattr(cell, 'read') else cell for cell in items)
            value = ([row(item) for item in value] if method == 'fetchall' else row(value) if value is not None else None)
        except Exception as error:
            self.trace.append(self.key, method, {'error':safe_error_code(error)})
            raise
        self.trace.append(self.key, method, {'value':value})
        return value
    def fetchone(self): return self._fetch('fetchone')
    def fetchall(self): return self._fetch('fetchall')
    def __getattr__(self, name): return getattr(self.native, name)


class TracedConnection:
    """Bağlantının metadata cursor çağrılarını izler, bağlantıyı paylaşmaz.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, native, trace): self.native, self.trace = native, trace
    def cursor(self): return TracedCursor(self.native.cursor(), self.trace)
    def __getattr__(self, name): return getattr(self.native, name)


class ReplayCursor:
    """Kaydedilmiş metadata sonuçlarını Oracle bağlantısı açmadan döndürür.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, trace): self.trace, self.key = trace, None
    def execute(self, query, binds=None):
        self.key = self.trace.key(query, binds)
        result = self.trace.read(self.key, 'execute')
        if 'error' in result: raise RuntimeError(result['error'])
        return self
    def _fetch(self, method):
        result = self.trace.read(self.key, method)
        if 'error' in result: raise RuntimeError(result['error'])
        value = result['value']
        return [tuple(row) for row in value] if method == 'fetchall' else tuple(value) if value is not None else None
    def fetchone(self): return self._fetch('fetchone')
    def fetchall(self): return self._fetch('fetchall')
    def close(self): pass


class ReplayConnection:
    """Seri tekrar için yalnız bellekten okunan bir oturum sağlar.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def __init__(self, trace, version): self.trace, self.version = trace, version
    def cursor(self): return ReplayCursor(self.trace)
    def rollback(self): pass
    def close(self): pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=Path('.local/ui-state'))
    parser.add_argument('--profile', required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--read-workers', type=int, default=4)
    parser.add_argument('--parser-workers', type=int, default=8)
    args = parser.parse_args()
    store = ControlStore(args.state)
    spec = store.run_spec(args.profile, actor='shared', role='shared')
    if spec['profile']['source']['kind'] != 'GIT': raise ValueError('BENCHMARK_REQUIRES_GIT_SOURCE')
    commit = subprocess.check_output(['git', '-C', str(args.repo), 'rev-parse', 'HEAD'], text=True).strip()
    spec['profile']['source']['ref'] = commit
    spec['collection_benchmark'] = {'oracle_workers':args.read_workers, 'parser_workers':args.parser_workers}
    os.environ['GENERATOR_ORACLE_DDL_WORKERS'] = str(args.read_workers)
    os.environ['GENERATOR_PARSER_WORKERS'] = str(args.parser_workers)
    run = store.create_run(args.profile, actor='shared', role='shared', spec=spec, executor='LOCAL')
    root = store.root/'runs'/run['id']
    trace, memo, memo_lock, captured = QueryTrace(), {}, Lock(), []
    real_project = collector.project_target_object
    def project(obj, **kwargs):
        key = digest(obj.to_dict())
        result = real_project(obj, **kwargs)
        with memo_lock: memo[key] = (result, dict(kwargs.get('statistics') or {}))
        return result
    collector.project_target_object = project
    version = []
    def connect(config, credentials):
        native = connect_read_only(config, credentials)
        version.append(native.version)
        return TracedConnection(native, trace)
    def collect(config, credentials, profile, **kwargs):
        observation = collector.collect_target(config, credentials, profile, connect=connect, **kwargs)
        captured.append((config, kwargs.get('source'), observation))
        return observation
    def checkout(connection, selection, folder, credentials, settings):
        if selection['ref'] != commit: raise ValueError('BENCHMARK_SOURCE_COMMIT_CHANGED')
        return args.repo
    print(json.dumps({'run_id':run['id'], 'commit':commit}), flush=True)
    started = perf_counter()
    execute_run(store, run['id'], checkout=checkout, target_collector=collect)
    elapsed = perf_counter()-started
    completed = store.run(run['id'])
    print(json.dumps({'stage':'LIVE_FINISHED','run_id':run['id'],'seconds':elapsed,'status':completed['status'],
                      'source_performance':completed.get('source_performance'),'error_code':completed.get('error_code')}), flush=True)
    (root/'metadata-read-trace.json').write_bytes(canonical_bytes(dict(trace.rows)))
    if len(captured) != 1 or captured[0][2].snapshot is None:
        raise ValueError('LIVE_CAPTURE_NOT_AVAILABLE')
    config, source, observation = captured[0]
    def replay_project(obj, **kwargs):
        key = digest(obj.to_dict())
        if key not in memo: raise ValueError('REPLAY_PROJECTION_INPUT_CHANGED')
        result, stats = memo[key]
        if kwargs.get('statistics') is not None: kwargs['statistics'].update(stats)
        return result
    collector.project_target_object = replay_project
    os.environ['GENERATOR_ORACLE_DDL_WORKERS'] = '1'
    def legacy_positions(text, statements):
        return {position:(len(text[:position].encode()),text.count('\n',0,position)+1)
                for statement in statements for position in (statement['start_char'],statement['end_char'])}
    sidecars._statement_positions = legacy_positions
    credentials = lambda key: store.credentials(key, spec['connections'][key]['revision'])
    with runtime_settings(spec['settings']):
        replay = collector.collect_target(config, credentials, make_profile(spec), source=source,
            connect=lambda *_: ReplayConnection(trace, version[0]))
    equal = (replay.snapshot is not None and replay.snapshot.to_dict() == observation.snapshot.to_dict()
             and [(o.object_key,o.raw_ddl) for o in replay.snapshot.objects] == [(o.object_key,o.raw_ddl) for o in observation.snapshot.objects]
             and not trace.missing)
    result = {'run_id':run['id'],'source_commit':commit,'live_seconds':elapsed,'status':completed['status'],
              'serial_replay_equal':equal,'legacy_sidecar_positions_equal':equal,
              'missing_queries':trace.missing,'receipt':observation.receipt,
              'source_performance':completed.get('source_performance')}
    (root/'collection-benchmark.json').write_bytes(canonical_bytes(result))
    print(json.dumps({'stage':'REPLAY_FINISHED','serial_replay_equal':equal,'missing_queries':len(trace.missing)}), flush=True)
    if not equal: raise ValueError('ORACLE_PARALLEL_CAPTURE_MISMATCH')


if __name__ == '__main__': main()
