"""Ordering equivalence and bounded work for the final dependency queue."""
from random import Random
from types import SimpleNamespace

import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.plan import Operation, SqlIntent
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning import graph


def operation(name, dependencies=(), *, phase=30, decision='READY', owner='APP', kind='VIEW'):
    identity = ObjectIdentity('synthetic', Identifier.parse(owner), kind, Identifier.parse(name))
    value = KnownValue('KNOWN', True, ())
    intent = SqlIntent(b'synthetic', 'SQL', phase) if phase is not None else None
    return Operation(name, identity, 'REPLACE', value, value, decision, 'UNKNOWN', 'synthetic',
                     ('ORIGINAL_REASON',), 'Original reason.', (), (), tuple(dependencies), intent=intent)


def old_reference(operations):
    pending = {op.operation_id: op for op in operations}
    ordered = []
    while pending:
        done = {op.operation_id for op in ordered}
        ready = [op for op in pending.values() if set(op.dependencies) <= done]
        if not ready:
            for op in sorted(pending.values(), key=lambda item: item.operation_id):
                held = [pending[dep] for dep in op.dependencies if dep in pending]
                names = ', '.join(sorted({f'{dep.identity.owner.effective_name}.{dep.identity.name.effective_name} [{dep.identity.object_type}]' for dep in held}))
                ordered.append(graph._block(op, 'DEPENDENCY_CYCLE', ['SQL sırası çözülemeyen gruptaki önkoşullar: ' + names]))
            break
        ready.sort(key=lambda op: (op.intent.phase if op.intent else 999,
                                   (op.identity.owner.effective_name, op.identity.object_type, op.identity.name.effective_name), op.operation_id))
        op = ready[0]
        ordered.append(op)
        pending.pop(op.operation_id)
    return tuple(ordered)


def order(operations):
    implementation = getattr(graph, '_topological_order', None)
    assert implementation is not None, 'Final ordering must use a bounded dependency queue'
    return implementation({op.operation_id: op for op in operations})


def test_independent_operations_do_not_recompute_all_remaining_sort_keys(monkeypatch):
    # A repeated ready-list sort makes key evaluations quadratic, independent of CPU timing.
    operations = tuple(operation(f'N{index:04d}', phase=None, decision='INFORMATIONAL') for index in range(600))
    calls = 0
    original = graph._key
    def counted(identity):
        nonlocal calls
        calls += 1
        return original(identity)
    monkeypatch.setattr(graph, '_key', counted)
    result = graph.bind_and_order(tuple(reversed(operations)), SimpleNamespace())
    assert [op.operation_id for op in result] == [op.operation_id for op in operations]
    assert calls <= 3 * len(operations), f'{calls} ordering key evaluations for {len(operations)} independent operations'


def test_newly_available_lower_phase_precedes_already_available_higher_phase():
    operations = (operation('A', phase=20), operation('B', ('A',), phase=1),
                  operation('C', phase=30), operation('D', ('B',), phase=5),
                  operation('E', phase=None, decision='BLOCKED'))
    result = order(operations)
    assert [op.operation_id for op in result] == ['A', 'B', 'D', 'C', 'E']
    assert result == old_reference(operations)
    assert [op.to_dict() for op in result] == [op.to_dict() for op in old_reference(operations)]


def test_cycles_and_their_downstream_tail_keep_original_blocking_reasons_and_order():
    operations = (operation('A', ('B',)), operation('B', ('A',)),
                  operation('C', ('B',)), operation('D'),
                  operation('E', ('C',), phase=None, decision='BLOCKED'))
    result = order(tuple(reversed(operations)))
    assert [op.operation_id for op in result] == ['D', 'A', 'B', 'C', 'E']
    assert all(op.reason_codes == ('DEPENDENCY_CYCLE', 'ORIGINAL_REASON') for op in result[1:])
    assert result[-1].reason_tr == 'SQL sırası çözülemeyen gruptaki önkoşullar: APP.C [VIEW].'
    assert [op.to_dict() for op in result] == [op.to_dict() for op in old_reference(operations)]


@pytest.mark.parametrize('seed', range(12))
def test_small_graphs_are_byte_equivalent_to_previous_ordering(seed):
    random = Random(seed)
    names = [f'N{index:02d}' for index in range(18)]
    operations = [operation(name, tuple(other for other in names if random.random() < .045),
                            phase=random.choice([None, 1, 20, 60, 999]), owner=random.choice(['APP', 'OTHER']),
                            kind=random.choice(['VIEW', 'TABLE', 'SEQUENCE'])) for name in names]
    random.shuffle(operations)
    expected = old_reference(operations)
    assert [op.to_dict() for op in order(operations)] == [op.to_dict() for op in expected]


def test_large_forest_retains_every_chain_and_is_deterministic():
    operations = tuple(operation(f'R{root:03d}N{depth:02d}',
                                 (f'R{root:03d}N{depth-1:02d}',) if depth else (),
                                 phase=(7-depth) % 5) for root in range(150) for depth in range(8))
    result = order(tuple(reversed(operations)))
    assert len(result) == 1200 and len({op.operation_id for op in result}) == 1200
    positions = {op.operation_id: index for index, op in enumerate(result)}
    assert all(positions[dep] < positions[op.operation_id] for op in result for dep in op.dependencies)
    assert all(op.decision == 'READY' and op.reason_codes == ('ORIGINAL_REASON',) for op in result)
    assert [op.operation_id for op in order(operations)] == [op.operation_id for op in result]
    assert order(()) == ()


def test_queue_enqueues_and_emits_each_eligible_operation_once(monkeypatch):
    pushes = pops = 0
    push, pop = graph.heappush, graph.heappop
    def counted_push(queue, item):
        nonlocal pushes
        pushes += 1
        return push(queue, item)
    def counted_pop(queue):
        nonlocal pops
        pops += 1
        return pop(queue)
    monkeypatch.setattr(graph, 'heappush', counted_push)
    monkeypatch.setattr(graph, 'heappop', counted_pop)
    operations = (operation('A', phase=None, decision='BLOCKED'),
                  operation('B', ('A', 'A'), phase=None, decision='INFORMATIONAL'),
                  operation('C', ('B',)), operation('D', ('MISSING',)),
                  operation('E', ('E',)))
    result = order(operations)
    assert pushes == pops == 3
    assert [op.operation_id for op in result] == ['A', 'B', 'C', 'D', 'E']
    assert [op.to_dict() for op in result] == [op.to_dict() for op in old_reference(operations)]
