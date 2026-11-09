"""Schema Compare envanterde sıra değişimini gerçek metadata değişiminden ayırır.

Sentetik cursor kullanır. Veritabanına bağlanmaz veya SQL uygulamaz.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.oracle.collector import collect_target
from tests.unit.test_collector import FakeConnection, FakeCursor, inputs


def test_same_inventory_in_different_row_order_does_not_restart_capture():
    class Reordered(FakeCursor):
        def fetchall(self):
            if 'LAST_DDL_TIME' in self.current.upper():
                self.inventory_reads += 1
                rows = [('INDEX PARTITION', 'PART_INDEX', 'VALID', '2026-11-08'),
                        ('INDEX PARTITION', 'PART_INDEX', 'VALID', '2026-11-09')]
                return rows if self.inventory_reads == 1 else list(reversed(rows))
            return super().fetchall()
    target, profile = inputs()
    connection = FakeConnection()
    connection.reader = Reordered()
    opened = []
    def connect(*args):
        opened.append(connection)
        return connection
    result = collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert result.snapshot is not None
    assert result.receipt['status'] == 'CAPTURED'
    assert len(opened) == 1
    check = result.receipt['schemas'][0]['inventory_check']
    assert check['same_rows'] is True and check['row_order_changed'] is True
    assert check['added_count'] == check['removed_count'] == 0


def test_inventory_comparison_preserves_duplicate_multiplicity_and_real_stamp_changes():
    from oracle_db_migration_generator.oracle.inventory_consistency import inventory_check
    first = ('TABLE PARTITION', 'T', 'VALID', '2026-11-08')
    second = ('TABLE PARTITION', 'T', 'VALID', '2026-11-09')
    same = inventory_check([first, second, first], [first, first, second])
    assert same['same_rows'] is True
    changed = inventory_check([first, first, second], [first, second, second])
    assert changed['same_rows'] is False
    assert changed['added_count'] == changed['removed_count'] == 1
    assert changed['added_examples'][0]['last_ddl_time'] == '2026-11-09'
    assert changed['removed_examples'][0]['last_ddl_time'] == '2026-11-08'
    assert inventory_check([first], [])['same_rows'] is False
    assert inventory_check([], [first])['same_rows'] is False
    assert inventory_check([], [])['same_rows'] is True


def test_real_changes_still_block_with_a_bounded_object_diagnostic():
    target, profile = inputs()
    connections = []
    def connect(*args):
        connection = FakeConnection(changing=True)
        connections.append(connection)
        return connection
    result = collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert result.snapshot is None and result.receipt['status'] == 'INCONSISTENT'
    assert len(connections) == 2 and all(c.closed for c in connections)
    failure = result.receipt['schemas'][0]
    assert failure['error_code'] == 'CHANGED_DURING_CAPTURE'
    assert failure['inventory_check']['same_rows'] is False
    assert failure['inventory_check']['added_examples'][0]['object_name'] == 'DEMO'
    assert failure['capture_attempts'] == 2


def test_large_inventory_change_keeps_complete_counts_with_only_eight_examples():
    from oracle_db_migration_generator.oracle.inventory_consistency import inventory_check
    rows = [('TABLE', 'T'+str(i), 'VALID', None) for i in range(100)]
    result = inventory_check([], rows)
    assert result['same_rows'] is False
    assert result['added_count'] == result['after_count'] == 100
    assert len(result['added_examples']) == 8
    assert result['removed_count'] == 0
