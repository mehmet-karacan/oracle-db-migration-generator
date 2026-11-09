"""Şema Karşılaştırma sidecar byte konumlarını ve doğrusal hesaplama maliyetini sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import hashlib

from oracle_db_migration_generator.source.models import SourceArtifact
from oracle_db_migration_generator.source.sidecars import merge_sidecars
from tests.factories import actual


def test_unicode_sidecar_positions_do_not_rescan_every_prefix():
    work = [0]
    class CountedText(str):
        """Konum hesabı için tekrar okunan metin miktarını sayar.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def __getitem__(self, key):
            value = super().__getitem__(key)
            if isinstance(key, slice): work[0] += len(value)
            return value
    class CountedBytes(bytes):
        """Ürün koduna izlenebilir UTF-8 metni verir.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def decode(self, *args, **kwargs):
            return CountedText(super().decode(*args, **kwargs))
    raw = CountedBytes(''.join(f"COMMENT ON COLUMN APP.T.C{i} IS 'Türkçe açıklama {i}\nİkinci satır';\n" for i in range(200)).encode())
    artifact = SourceArtifact('comments.sql', 'APP', 'COMMENT', 'COMMENT', raw, hashlib.sha256(raw).hexdigest())
    snapshot = merge_sidecars(actual('CREATE TABLE APP.T(ID NUMBER);'), (artifact,))
    assert len([obj for obj in snapshot.objects if obj.identity.object_type == 'COMMENT']) == 200
    registry = {ev.id: ev for ev in snapshot.evidence}
    for obj in snapshot.objects:
        if obj.identity.object_type != 'COMMENT': continue
        ev = registry[obj.evidence_ids[0]]
        assert raw[ev.start_byte:ev.end_byte] == obj.raw_ddl
        assert ev.start_line == bytes(raw[:ev.start_byte]).count(b'\n') + 1
        assert ev.end_line == bytes(raw[:ev.end_byte]).count(b'\n') + 1
    assert work[0] <= 2 * len(raw), f'prefix work {work[0]} for {len(raw)} bytes'
