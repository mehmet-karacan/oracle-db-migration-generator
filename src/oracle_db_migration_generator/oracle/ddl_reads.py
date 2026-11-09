"""Şema Karşılaştırma DDL metinlerini sınırlı sayıda salt okunur oturumla toplar.

Her çalışan kendi bağlantısını açar, yetkisini doğrular ve aynı iş parçacığında
kapatır. Kuyruk dolduğunda yeni okuma bekler. SQL metinleri çalıştırılmaz.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import copy_context
import os
import re
from queue import Queue, Empty, Full
from threading import Event, Lock
import time

from ..config.runtime import current_settings
from ..model.identity import Identifier
from .preflight import safe_error_code
from .queries import SAMPLE_DDL, DDL_TYPES, READ_ONLY_TRANSACTION, IDENTITY


class DDLReadError(ValueError):
    """Oturum veya toplama hatasını sır içermeyen bir kodla taşır.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """


def reader_count(*, builtin_connector):
    value = current_settings().get('oracle_ddl_workers', os.environ.get('GENERATOR_ORACLE_DDL_WORKERS'))
    try:
        count = int(value) if value is not None else (8 if builtin_connector else 1)
    except (ValueError, TypeError):
        raise DDLReadError('ORACLE_DDL_WORKERS_INVALID') from None
    if not 1 <= count <= 8:
        raise DDLReadError('ORACLE_DDL_WORKERS_INVALID')
    return count


def _read(cursor, index, row, owner):
    started = time.monotonic()
    raw, reasons = None, []
    try:
        cursor.execute(SAMPLE_DDL, {'ddl_type': DDL_TYPES[row[0]], 'name': row[1], 'owner': owner})
        result = cursor.fetchone()
        if not result or result[0] is None:
            raise ValueError('GET_DDL_RETURNED_EMPTY')
        text = result[0].read() if hasattr(result[0], 'read') else str(result[0])
        if not text.strip():
            raise ValueError('GET_DDL_RETURNED_EMPTY')
        raw = text.encode('utf-8')
    except Exception as error:
        reasons.append(safe_error_code(error))
    return index, raw, reasons, started, time.monotonic()


@contextmanager
def ddl_records(rows, cursor, *, target, mapping, credential, connect, owner, deadline, workers):
    """DDL byte değerlerini ve sürelerini verir. Ek oturumların sahipliği çalışandadır."""
    if workers == 1 or not rows:
        def serial():
            for index, row in enumerate(rows):
                if time.monotonic() > deadline:
                    raise DDLReadError('TARGET_CAPTURE_TIMEOUT')
                yield _read(cursor, index, row, owner)
        yield serial()
        return
    tasks, results = Queue(), Queue(maxsize=workers * 2)
    for indexed in enumerate(rows): tasks.put(indexed)
    stopped, ownership_lock = Event(), Lock()
    connection_ids = {}
    def publish(value):
        while not stopped.is_set():
            try:
                results.put(value, timeout=.1)
                return
            except Full:
                pass
    def read_session():
        connection = reader = None
        failed = False
        try:
            connection = connect(target, credential)
            with ownership_lock:
                if id(connection) in connection_ids:
                    connection = None
                    raise DDLReadError('DDL_READER_CONNECTION_REUSED')
                connection_ids[id(connection)] = connection
            reader = connection.cursor()
            reader.execute(READ_ONLY_TRANSACTION)
            if mapping.metadata_reader is not None:
                from .catalog_reader import authorize_catalog_reader, CatalogCursor
                authorize_catalog_reader(reader, Identifier.parse(mapping.metadata_reader).effective_name, owner)
                reader = CatalogCursor(reader)
            else:
                reader.execute(IDENTITY)
                if reader.fetchone() != (owner,):
                    raise DDLReadError('SESSION_OWNER_MISMATCH')
            while not stopped.is_set():
                if time.monotonic() > deadline:
                    raise DDLReadError('TARGET_CAPTURE_TIMEOUT')
                try:
                    index, row = tasks.get_nowait()
                except Empty:
                    break
                publish(_read(reader, index, row, owner))
        except Exception as error:
            failed = True
            code = str(error) if isinstance(error, DDLReadError) else safe_error_code(error)
            if isinstance(error, ValueError) and re.fullmatch('CATALOG_[A-Z_]+', str(error)):
                code = str(error)
            publish(DDLReadError(code))
            stopped.set()
            raise DDLReadError(code) from None
        finally:
            cleanup_failed = False
            for action in (reader.close if reader else None, connection.rollback if connection else None,
                           connection.close if connection else None):
                if action:
                    try: action()
                    except Exception: cleanup_failed = True
            if cleanup_failed and not failed:
                publish(DDLReadError('DDL_READER_CLEANUP_FAILED'))
                stopped.set()
                raise DDLReadError('DDL_READER_CLEANUP_FAILED')
    def completed():
        pending = len(rows)
        while pending:
            if time.monotonic() > deadline:
                raise DDLReadError('TARGET_CAPTURE_TIMEOUT')
            try:
                result = results.get(timeout=.1)
            except Empty:
                continue
            if isinstance(result, DDLReadError): raise result
            pending -= 1
            yield result
    executor = ThreadPoolExecutor(max_workers=min(workers, len(rows)), thread_name_prefix='oracle-ddl')
    futures = [executor.submit(copy_context().run, read_session) for _ in range(min(workers, len(rows)))]
    error = False
    try:
        yield completed()
    except BaseException:
        error = True
        raise
    finally:
        stopped.set()
        executor.shutdown(wait=True, cancel_futures=True)
        if not error:
            for future in futures:
                if not future.cancelled() and future.exception() is not None:
                    raise future.exception()


def active_read_seconds(intervals):
    """Eşzamanlı okumaların kesişen sürelerini yalnız bir kez sayar."""
    total, end = 0.0, 0.0
    for begin, finish in sorted(intervals):
        total += max(0.0, finish - max(begin, end))
        end = max(end, finish)
    return total
