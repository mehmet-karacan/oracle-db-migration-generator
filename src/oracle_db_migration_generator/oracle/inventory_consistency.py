"""Schema Compare envanter satırlarının sırasını değil içeriğini karşılaştırır.

Aynı satırın tekrar sayısı korunur. Gerçek farklarda sınırlı metadata örneği
üretilir. Nesne tanımları veya bağlantı bilgileri bu kayda eklenmez.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from collections import Counter

from ..model.serialization import canonical_bytes, digest


def inventory_check(before, after):
    """İki katalog okumasındaki eklenen ve çıkarılan satırları özetler."""
    old = Counter(map(tuple, before))
    new = Counter(map(tuple, after))
    if any(len(row) != 4 for row in (*old, *new)):
        raise ValueError('INVENTORY_ROW_SHAPE_INVALID')
    def ordered(counter):
        return sorted(counter.items(), key=lambda item: canonical_bytes(item[0]))
    def examples(counter):
        return [dict(object_type=row[0], object_name=row[1], status=row[2],
                     last_ddl_time=row[3], occurrences=count)
                for row, count in ordered(counter)[:8]]
    same = old == new
    return {'same_rows': same, 'row_order_changed': same and before != after,
            'before_count': len(before), 'after_count': len(after),
            'before_digest': digest(ordered(old)), 'after_digest': digest(ordered(new)),
            'added_count': sum((new-old).values()), 'removed_count': sum((old-new).values()),
            'added_examples': examples(new-old), 'removed_examples': examples(old-new)}
