"""Exercise the metadata I/O boundary, not a source-text whitelist assertion."""
import pytest


class Cursor:
    def __init__(self,*,denied=False,drift=False):
        self.denied=denied;self.drift=drift;self.object_reads=0;self.executed=[];self.rows=[]

    def execute(self,sql,binds=None):
        self.executed.append((sql,binds));text=' '.join(sql.upper().split());binds=binds or {}
        assert text.startswith('SELECT ')
        assert not any(word in text for word in ('NEXTVAL','COMPILE','CREATE OR','APP.P('))
        if 'SESSION_USER' in text and 'FROM DUAL' in text:self.rows=[('APP',)]
        elif 'FROM ALL_OBJECTS' in text:
            self.object_reads+=1
            self.rows=[('PROCEDURE','INVALID' if self.drift and self.object_reads>1 else 'VALID','2026-10-26T10:00:00',None)]
        elif 'FROM ALL_DEPENDENCIES' in text:
            if self.denied:raise RuntimeError('secret must not enter evidence')
            self.rows=[('P','PROCEDURE','SYS','STANDARD','PACKAGE',None,'HARD')]
        elif 'GET_DDL' in text:self.rows=[('CREATE PROCEDURE APP.P IS BEGIN NULL; END;',)]
        else:self.rows=[]

    def fetchall(self):return self.rows


def test_reader_records_metadata_denial_as_unknown_without_exception_text():
    from oracle_db_migration_generator.oracle.routine_metadata import read_routine_metadata
    cur=Cursor(denied=True)
    result=read_routine_metadata(cur,[('PROCEDURE','P')],owner='APP',oracle_version='19.0.0.0.0')
    unit=next(r for r in result['records'] if r['name']=='P')
    assert unit['dependencies']['state']=='UNKNOWN'
    assert 'secret' not in str(result)
    assert all(binds.get('name')=='P' for sql,binds in cur.executed if binds and ':name' in sql)


def test_reader_brackets_unit_observation_to_expose_metadata_drift():
    from oracle_db_migration_generator.oracle.routine_metadata import read_routine_metadata
    result=read_routine_metadata(Cursor(drift=True),[('PROCEDURE','P')],owner='APP',oracle_version='19.0.0.0.0')
    unit=next(r for r in result['records'] if r['name']=='P')
    assert unit['before']!=unit['after']


def test_reader_rejects_unbounded_or_non_program_unit_requests_before_io():
    from oracle_db_migration_generator.oracle.routine_metadata import read_routine_metadata
    cur=Cursor()
    with pytest.raises(ValueError):read_routine_metadata(cur,[('TABLE','T')],owner='APP',oracle_version='19')
    with pytest.raises(ValueError):read_routine_metadata(cur,[('PROCEDURE',str(n)) for n in range(65)],owner='APP',oracle_version='19')
    assert not cur.executed
