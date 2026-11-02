"""Şema Karşılaştırma sequence bağımlılığında sayaç ilerlemesini denetler.

Yalnız değişmeyen tanım ve ileri giden pozitif sayaç kanıtını kabul eder.

Author: Mehmet KARACAN
Date: 2026-11-01
"""

import hashlib
import re
from collections.abc import Mapping


_START = re.compile(r'\bSTART\s+WITH\s+([0-9]+)\b', re.IGNORECASE)
_INCREMENT = re.compile(r'\bINCREMENT\s+BY\s+([1-9][0-9]*)\b', re.IGNORECASE)
_NOCYCLE = re.compile(r'\bNOCYCLE\b', re.IGNORECASE)


def sequence_definition(raw):
    """Özgün Oracle DDL içinden dar kapsamlı sayaç tanımını çıkarır."""
    if not isinstance(raw, bytes) or not raw or len(raw) > 4 * 1024 * 1024:
        return None
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        return None
    if not text.lstrip().upper().startswith('CREATE SEQUENCE '):
        return None
    starts = list(_START.finditer(text))
    increments = list(_INCREMENT.finditer(text))
    if len(starts) != 1 or len(increments) != 1:
        return None
    nocycle = list(_NOCYCLE.finditer(text))
    if len(nocycle) != 1 or nocycle[0].start() <= starts[0].end():
        return None
    start = int(starts[0].group(1))
    increment = int(increments[0].group(1))
    if start > 10 ** 30 or increment > 10 ** 30:
        return None
    shape = text[:starts[0].start(1)] + '#' + text[starts[0].end(1):]
    return {'shape_sha256': hashlib.sha256(shape.encode('utf-8')).hexdigest(),
            'start_with': start, 'increment_by': increment}


def sequence_advance_matches(snapshot_ddl, current):
    """Eski ve güncel tanımda tek fark ileri giden sayaçsa doğru döner."""
    previous = sequence_definition(snapshot_ddl)
    return (previous is not None and isinstance(current, Mapping)
            and type(current.get('start_with')) is int
            and current.get('shape_sha256') == previous['shape_sha256']
            and current.get('increment_by') == previous['increment_by']
            and current['start_with'] >= previous['start_with'])
