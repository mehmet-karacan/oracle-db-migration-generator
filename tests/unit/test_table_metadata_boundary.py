import hashlib

import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import Coverage, SnapshotObject
from oracle_db_migration_generator.oracle.ddl_model import project_target_object
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.planning.table_ddl import table_base


@pytest.mark.parametrize('separator', ['\n', ';\n'])
def test_table_create_preserves_its_tail_without_appending_metadata_context(separator):
    table = '''CREATE TABLE "APP"."EXAMPLE" (
  "ID" NUMBER,
  "NOTE" VARCHAR2(30 CHAR) DEFAULT 'Türkçe CREATE INDEX'
) SEGMENT CREATION IMMEDIATE TABLESPACE "USERS"'''
    raw = (table + separator + '''CREATE UNIQUE INDEX "APP"."PK_EXAMPLE"
ON "APP"."EXAMPLE" ("ID") TABLESPACE "USERS"''' + separator + '''ALTER TABLE "APP"."EXAMPLE"
ADD CONSTRAINT "PK_EXAMPLE" PRIMARY KEY ("ID")
USING INDEX "APP"."PK_EXAMPLE" ENABLE''').encode('utf-8')
    identity = ObjectIdentity('test', Identifier.parse('APP'), 'TABLE', Identifier.parse('EXAMPLE'))
    obj, _ = project_target_object(SnapshotObject(identity, {}, 'table.sql', hashlib.sha256(raw).hexdigest(),
        Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'), ('ev-synthetic',), raw))
    assert obj.coverage.ddl == 'COMPLETE'
    emitted = table_base(obj)
    parsed = parse_ddl(emitted, identity)
    assert parsed.coverage == 'COMPLETE'
    assert len(parsed.objects) == 1 and parsed.objects[0].identity == identity
    assert parsed.sidecars == ()
    assert b'CREATE UNIQUE INDEX' not in emitted and b'ALTER TABLE' not in emitted
    assert b'SEGMENT CREATION IMMEDIATE TABLESPACE "USERS"' in emitted
    assert "DEFAULT 'Türkçe CREATE INDEX'".encode('utf-8') in emitted
    assert obj.raw_ddl == raw
    assert any('PK_EXAMPLE' in definition for definition in obj.projection.properties['constraints'].values())


def test_metadata_data_export_statement_is_rejected_instead_of_silently_dropped():
    raw = b'CREATE TABLE APP.EXAMPLE (ID NUMBER); INSERT INTO APP.EXAMPLE SELECT ID FROM APP.EXAMPLE@KU$;'
    identity = ObjectIdentity('test', Identifier.parse('APP'), 'TABLE', Identifier.parse('EXAMPLE'))
    obj, _ = project_target_object(SnapshotObject(identity, {}, 'table.sql', hashlib.sha256(raw).hexdigest(),
        Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'), ('ev-synthetic',), raw))
    assert obj.coverage.ddl == 'PARTIAL'
    assert obj.properties['projection'].state == 'UNKNOWN'
    with pytest.raises(ValueError, match='SOURCE_TABLE_BODY_UNAVAILABLE'):
        table_base(obj)
