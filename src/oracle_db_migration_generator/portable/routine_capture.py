"""Şema Karşılaştırma derleyici kanıtını hedef snapshot ile birlikte saklar.

Dosyanın kökenini, hedef bağını ve kanıt hash değerini korur.

Author: Mehmet KARACAN
Date: 2026-11-01
"""

import hashlib
from pathlib import Path

from ..oracle.collector import TargetObservation
from ..oracle.routine_metadata import attach_routine_metadata
from ..runtime.worker import save_observation
from ..source.models import SourceArtifact
from .builder import routine_capture_request
from .stream import MAX_PACKET_BYTES, read_routine_capture


def import_routine_capture(source, target, packet, output):
    """Doğrulanmış SQLcl kaydını yeni bir yerel hedef gözlemine yazar."""
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('CAPTURE_OUTPUT_ALREADY_EXISTS')
    if not isinstance(packet, bytes) or len(packet) > MAX_PACKET_BYTES:
        raise ValueError('CAPTURE_FILE_SIZE')
    request = routine_capture_request(source, target)
    supplement = read_routine_capture(packet, request, target)
    augmented, path, raw = attach_routine_metadata(target, supplement)
    artifact = SourceArtifact(path, request.root_owner, 'TARGET_METADATA', None,
                              raw, hashlib.sha256(raw).hexdigest())
    receipt = {'status': 'CAPTURED', 'target_id': target.target_id,
               'execution_status': 'NOT_EXECUTED', 'read_only': True,
               'routine_metadata': {'status': 'CAPTURED', 'query_count': supplement['query_count']}}
    save_observation(TargetObservation(augmented, receipt, (artifact,)), output)
    return output
