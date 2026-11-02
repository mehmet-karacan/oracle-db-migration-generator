"""Oracle DB Migration Generator için veri okumadan DDL üretimini sınar.

Sentetik kaynak ve hedef tanımları kullanılır. Veritabanına bağlanılmaz.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from test_rules import plan


def test_missing_required_column_writes_add_column():
    result=plan('CREATE TABLE APP.T(ID NUMBER, C NUMBER DEFAULT 0 NOT NULL);',
                'CREATE TABLE APP.T(ID NUMBER);')
    assert any(op.kind=='ADD_COLUMN' and op.decision=='READY' and op.intent
               and b'C NUMBER DEFAULT 0 NOT NULL' in op.intent.statement
               for op in result.operations)


def test_unique_index_on_existing_table_writes_ddl():
    result=plan('CREATE TABLE APP.T(ID NUMBER); CREATE UNIQUE INDEX APP.UX_T ON APP.T(ID);',
                'CREATE TABLE APP.T(ID NUMBER);')
    assert any(op.kind=='CREATE_INDEX' and op.decision=='READY' and op.intent
               and b'CREATE UNIQUE INDEX' in op.intent.statement
               for op in result.operations)


def test_missing_primary_key_on_existing_table_writes_ddl():
    result=plan('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT PK_T PRIMARY KEY(ID));',
                'CREATE TABLE APP.T(ID NUMBER);')
    assert any(op.kind=='ADD_CONSTRAINT' and op.decision=='READY' and op.intent
               and b'PRIMARY KEY' in op.intent.statement
               for op in result.operations)


def test_trigger_on_existing_table_writes_source_ddl():
    table='CREATE TABLE APP.T(ID NUMBER);'
    trigger='CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T BEGIN NULL; END;'
    result=plan(table+' '+trigger,table)
    assert any(op.identity.object_type=='TRIGGER' and op.decision=='READY' and op.intent
               and b'CREATE OR REPLACE TRIGGER' in op.intent.statement
               for op in result.operations)


def test_changed_trigger_writes_source_ddl():
    table='CREATE TABLE APP.T(ID NUMBER);'
    old='CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T BEGIN NULL; END;'
    new='CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T BEGIN NULL; NULL; END;'
    result=plan(table+' '+new,table+' '+old)
    assert any(op.identity.object_type=='TRIGGER' and op.decision=='READY' and op.intent
               for op in result.operations)
