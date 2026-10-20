from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.emission.sql import render_statement
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
from tests.factories import actual,profile,source


def plan(sql,observed='',capabilities=None):
    selected=profile();desired=source(sql);target=actual(observed)
    assert desired.objects and desired.completeness.ddl=='COMPLETE'
    if capabilities:
        target=replace(target,capabilities={**target.capabilities,**{
            key:KnownValue('KNOWN',value,(target.evidence[0].id,)) for key,value in capabilities.items()}})
    return plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))


@pytest.mark.parametrize('datatype,clause',[
    ('NUMBER','PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10), PARTITION P2 VALUES LESS THAN(MAXVALUE))'),
    ('DATE',"PARTITION BY RANGE(ID) INTERVAL(NUMTOYMINTERVAL(1,'MONTH')) (PARTITION P1 VALUES LESS THAN(TIMESTAMP'2020-01-01 00:00:00'))"),
    ('DATE',"PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(TO_DATE(' 2020-01-01 00:00:00','SYYYY-MM-DD HH24:MI:SS','NLS_CALENDAR=GREGORIAN')))"),
    ('NUMBER','PARTITION BY RANGE(ID) INTERVAL(10)(PARTITION P1 VALUES LESS THAN(100))'),
])
def test_new_range_table_retains_partition_suffix_and_orders_dependents(datatype,clause):
    sql=f'CREATE TABLE APP.T(ID {datatype}, CONSTRAINT PK_T PRIMARY KEY(ID)) {clause};'
    sql+=" COMMENT ON COLUMN APP.T.ID IS 'id'; CREATE INDEX APP.IX ON APP.T(ID);"
    result=plan(sql)
    table=next(op for op in result.operations if op.kind=='CREATE' and op.identity.object_type=='TABLE')
    assert table.decision=='READY'
    assert clause.encode() in table.intent.statement
    emitted=render_statement(table,result.plan_id)
    assert clause.encode() in emitted
    assert result.counts['blocked_operations']==0
    for op in result.operations:
        if op.kind in {'ADD_CONSTRAINT','CREATE_INDEX','COMMENT'}:
            assert op.decision=='READY' and table.operation_id in op.dependencies


@pytest.mark.parametrize('columns,clause',[
    ('ID NUMBER','PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(20), PARTITION P2 VALUES LESS THAN(10))'),
    ('ID NUMBER','PARTITION BY RANGE(MISSING)(PARTITION P1 VALUES LESS THAN(10))'),
    ('ID NUMBER','PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10,20))'),
    ('ID NUMBER','PARTITION BY RANGE(ID) INTERVAL(0)(PARTITION P1 VALUES LESS THAN(10))'),
    ('ID NUMBER','PARTITION BY RANGE(ID) INTERVAL(10)(PARTITION P1 VALUES LESS THAN(MAXVALUE))'),
    ('ID NUMBER, X NUMBER','PARTITION BY RANGE(ID,X) INTERVAL(10)(PARTITION P1 VALUES LESS THAN(10,20))'),
    ('ID DATE',"PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN('01-JAN-2020'))"),
    ('ID LONG','PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10))'),
    ('ID NUMBER, X LONG','PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10))'),
])
def test_partition_grammar_is_not_semantic_proof(columns,clause):
    result=plan(f'CREATE TABLE APP.T({columns}) {clause};')
    assert not any(op.decision=='READY' for op in result.operations)


def test_partition_gate_does_not_admit_lob_storage_or_subpartition():
    lob=plan('CREATE TABLE APP.T(ID NUMBER, TXT CLOB) LOB(TXT) STORE AS BASICFILE (NOCACHE) '
             'PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));')
    assert all(op.decision!='READY' for op in lob.operations)
    sub=plan('CREATE TABLE APP.T(ID NUMBER, X NUMBER) PARTITION BY RANGE(ID) SUBPARTITION BY HASH(X) '
             '(PARTITION P1 VALUES LESS THAN(10)(SUBPARTITION SP1));')
    assert all(op.decision!='READY' for op in sub.operations)


def test_duplicate_partition_diagnostic_is_not_bypassed():
    selected=profile();desired=source('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) '
                                    '(PARTITION P1 VALUES LESS THAN(10), PARTITION P1 VALUES LESS THAN(20));')
    assert desired.objects and desired.completeness.ddl=='PARTIAL'
    target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))
    assert all(op.decision=='BLOCKED' for op in result.operations)


def test_datetime_function_index_keeps_expression_and_table_dependency():
    sql='CREATE TABLE APP.T(ID NUMBER, D DATE); CREATE INDEX APP.IX ON APP.T(TO_CHAR("D", \'YYYYMM\'));'
    result=plan(sql,capabilities={'nls_calendar':'GREGORIAN'})
    index=next(op for op in result.operations if op.identity.object_type=='INDEX')
    table=next(op for op in result.operations if op.identity.object_type=='TABLE')
    assert index.decision=='READY' and table.operation_id in index.dependencies
    assert b'TO_CHAR("D", \'YYYYMM\')' in render_statement(index,result.plan_id)


@pytest.mark.parametrize('columns,expression,capabilities',[
    ('D VARCHAR2(50 BYTE)',"TO_CHAR(D,'YYYYMM')",{'nls_calendar':'GREGORIAN'}),
    ('D DATE',"TO_CHAR(D,'YYYYMM')",{}),
    ('D DATE',"TO_CHAR(D,'YYYYMM')",{'nls_calendar':'THAI BUDDHA'}),
    ('D DATE',"TO_CHAR(MISSING,'YYYYMM')",{'nls_calendar':'GREGORIAN'}),
    ('D DATE',"APP.CUSTOM_FUNCTION(D)",{'nls_calendar':'GREGORIAN'}),
    ('D DATE',"TO_CHAR(D,'MON')",{'nls_calendar':'GREGORIAN'}),
])
def test_expression_index_cannot_infer_type_function_or_nls(columns,expression,capabilities):
    result=plan(f'CREATE TABLE APP.T({columns}); CREATE INDEX APP.IX ON APP.T({expression});',capabilities=capabilities)
    index=next(op for op in result.operations if op.identity.object_type=='INDEX')
    assert index.decision!='READY' and index.intent is None


def test_existing_type_change_cannot_make_expression_index_ready_through_source_shape():
    result=plan("CREATE TABLE APP.T(D DATE); CREATE INDEX APP.IX ON APP.T(TO_CHAR(D,'YYYYMM'));",
                'CREATE TABLE APP.T(D VARCHAR2(50 BYTE));',capabilities={'nls_calendar':'GREGORIAN'})
    assert all(op.decision!='READY' for op in result.operations if op.identity.object_type=='INDEX')


def test_known_existing_partition_change_is_review_with_independent_default_ready():
    result=plan('CREATE TABLE APP.T(ID NUMBER DEFAULT 7) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));',
                'CREATE TABLE APP.T(ID NUMBER DEFAULT 1) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(20));')
    layout=next(op for op in result.operations if '/table_properties/partitioning' in [d.property_path for d in result.differences if d.difference_id in op.change_ids])
    assert layout.decision=='REVIEW_REQUIRED' and 'PARTITION_LAYOUT_REQUIRES_REVIEW' in layout.reason_codes
    assert layout.intent is None
    assert any(op.kind=='MODIFY_COLUMN' and op.decision=='READY' for op in result.operations)


def test_partition_physical_drift_is_information_only_when_logical_layout_matches():
    result=plan('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10));',
                'CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10) PCTFREE 20);')
    assert result.counts['blocked_operations']==0
    assert all(op.decision=='INFORMATIONAL' for op in result.operations)


def resolution(*,kind='TABLE',unqualified=True,status='VALID'):
    return {'requested_owner':'APP','requested_name':'DUAL','unqualified':unqualified,'state':'KNOWN',
            'objects':[{'owner':'SYS','name':'DUAL','object_type':kind,'status':status}],
            'chain':[{'owner':'PUBLIC','name':'DUAL','target_owner':'SYS','target_name':'DUAL'}]}


@pytest.mark.parametrize('status',['VALID','INVALID'])
def test_unqualified_relation_accepts_captured_public_synonym_proof(status):
    result=plan('CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL;',
                capabilities={'resolved_references':[resolution(status=status)]})
    view=next(op for op in result.operations if op.identity.object_type=='VIEW')
    assert view.decision=='READY'
    assert 'ev-target-scope' in view.evidence_ids


@pytest.mark.parametrize('sql,record',[
    ('CREATE VIEW APP.V AS SELECT 1 ID FROM APP.DUAL;',resolution()),
    ('CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL;',resolution(kind='PROCEDURE')),
    ('CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL@REMOTE;',resolution()),
])
def test_public_synonym_proof_cannot_resolve_qualified_wrong_type_or_remote(sql,record):
    result=plan(sql,capabilities={'resolved_references':[record]})
    assert all(op.decision=='BLOCKED' for op in result.operations if op.identity.object_type=='VIEW')


def test_missing_parent_and_shared_namespace_have_concrete_reasons():
    orphan=plan('CREATE INDEX APP.IX ON APP.MISSING(ID);')
    assert any('INDEX_PARENT_MISSING' in op.reason_codes and op.decision=='BLOCKED' for op in orphan.operations)
    collision=plan('CREATE FUNCTION APP.T RETURN NUMBER AS BEGIN RETURN 1; END;\n/',
                   'CREATE TABLE APP.T(ID NUMBER);')
    assert any('TARGET_NAMESPACE_CONFLICT' in op.reason_codes and op.decision=='BLOCKED' for op in collision.operations)


def test_collector_captures_nls_and_bounded_synonym_chain_read_only():
    from tests.unit.test_collector import FakeCursor,FakeConnection,inputs
    from oracle_db_migration_generator.oracle.collector import collect_target
    from oracle_db_migration_generator.config.credentials import Credentials
    class Cursor(FakeCursor):
        def execute(self,query,binds=None):
            self.binds=binds or {};super().execute(query,binds)
        def fetchall(self):
            normalized=' '.join(self.current.upper().split())
            if 'NLS_SESSION_PARAMETERS' in normalized:return [('NLS_CALENDAR','GREGORIAN')]
            if normalized.startswith('SELECT OBJECT_TYPE, STATUS FROM ALL_OBJECTS'):
                return [('TABLE','VALID')] if self.binds=={'owner':'SYS','name':'DUAL'} else []
            if normalized.startswith('SELECT TABLE_OWNER, TABLE_NAME, DB_LINK FROM ALL_SYNONYMS'):
                return [('SYS','DUAL',None)] if self.binds=={'owner':'PUBLIC','name':'DUAL'} else []
            return super().fetchall()
    target,selected=inputs();connection=FakeConnection();connection.reader=Cursor()
    desired=source('CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL;')
    observed=collect_target(target,lambda _:Credentials('APP','synthetic'),selected,source=desired,connect=lambda *_:connection)
    assert observed.snapshot.capabilities['nls_calendar'].value=='GREGORIAN'
    records=observed.snapshot.capabilities['resolved_references'].value
    assert len(records)==1 and records[0]['objects'][0]['owner']=='SYS' and records[0]['unqualified'] is True
    assert connection.closed
    assert all(query=='SET TRANSACTION READ ONLY' or query.lstrip().startswith('SELECT') for query,_ in connection.reader.calls)


@pytest.mark.parametrize('bound',[
    "TO_DATE('2020-01-01 12:30:00','YYYY-MM-DD','NLS_CALENDAR=GREGORIAN')",
    "TO_DATE('2020-01-01 12:30:00.123','YYYY-MM-DD HH24:MI:SS','NLS_CALENDAR=GREGORIAN')",
])
def test_partition_date_bound_must_match_its_exact_format(bound):
    result=plan(f'CREATE TABLE APP.T(D DATE) PARTITION BY RANGE(D)(PARTITION P1 VALUES LESS THAN({bound}));')
    assert all(op.decision!='READY' for op in result.operations)


@pytest.mark.parametrize('bound',['1e126','1e-999','123456789012345678901234567890123456789'])
def test_partition_number_bounds_must_be_representable_without_rounding(bound):
    result=plan(f'CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN({bound}));')
    assert all(op.decision!='READY' for op in result.operations)


def test_index_namespace_does_not_shadow_public_synonym_resolution():
    from oracle_db_migration_generator.oracle.reference_metadata import read_reference_metadata
    from oracle_db_migration_generator.oracle.queries import REFERENCE_OBJECT,REFERENCE_SYNONYM,SESSION_CALENDAR
    desired=source('CREATE TABLE APP.T(ID NUMBER); CREATE INDEX APP.DUAL ON APP.T(ID); CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL;')
    class Cursor:
        def execute(self,query,binds):self.query,self.binds=query,binds
        def fetchall(self):
            if self.query==SESSION_CALENDAR:return [('NLS_CALENDAR','GREGORIAN')]
            if self.query==REFERENCE_OBJECT:
                return [('INDEX','VALID')] if self.binds['owner']=='APP' else [('TABLE','VALID')]
            if self.query==REFERENCE_SYNONYM:
                return [('SYS','DUAL',None)] if self.binds['owner']=='PUBLIC' else []
            raise AssertionError('unexpected query')
    caps,evidence=read_reference_metadata(Cursor(),desired,'APP',target_id='DEMO-TEST')
    assert len(caps['resolved_references'].value)==1
    assert caps['resolved_references'].value[0]['objects'][0]['owner']=='SYS'


def test_target_only_private_synonym_requires_its_resolved_target():
    observed='CREATE SYNONYM APP.DUAL FOR APP.MISSING;'
    result=plan('CREATE VIEW APP.V AS SELECT 1 ID FROM DUAL;',observed)
    assert all(op.decision=='BLOCKED' for op in result.operations if op.identity.object_type=='VIEW')


def test_function_index_links_its_distinct_nls_evidence():
    selected=profile();desired=source("CREATE TABLE APP.T(D DATE); CREATE INDEX APP.IX ON APP.T(TO_CHAR(D,'YYYYMM'));")
    target=actual();evidence=replace(target.evidence[0],id='ev-calendar',kind='TARGET_METADATA',query_id='nls_session_parameters')
    target=replace(target,evidence=(*target.evidence,evidence),capabilities={**target.capabilities,
        'nls_calendar':KnownValue('KNOWN','GREGORIAN',(evidence.id,))})
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))
    index=next(op for op in result.operations if op.identity.object_type=='INDEX')
    assert index.decision=='READY' and evidence.id in index.evidence_ids


@pytest.mark.parametrize('interval',["NUMTOYMINTERVAL(1000000000,'YEAR')","NUMTODSINTERVAL(1000000000,'DAY')"])
def test_interval_constant_must_fit_its_leading_precision(interval):
    result=plan(f"CREATE TABLE APP.T(D DATE) PARTITION BY RANGE(D) INTERVAL({interval}) (PARTITION P1 VALUES LESS THAN(TIMESTAMP'2020-01-01 00:00:00'));")
    assert all(op.decision!='READY' for op in result.operations)


def test_partition_indexing_state_is_not_hidden_as_physical_storage():
    result=plan('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10) INDEXING ON);',
                'CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID)(PARTITION P1 VALUES LESS THAN(10) INDEXING OFF);')
    assert any(op.decision=='REVIEW_REQUIRED' for op in result.operations)


def test_large_ddl_gets_a_bounded_parser_budget(monkeypatch):
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    limits=[]
    def request(raw,owner,**kwargs):
        limits.append(kwargs.get('timeout',30))
        return {'objects':[],'sidecars':[],'diagnostics':[]}
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.request_parse',request)
    parse_ddl(b'CREATE PACKAGE BODY APP.P AS '+b' '*65536+b'END;',None,metadata=True)
    assert 60<=limits[0]<=120
    parse_ddl(b'CREATE TABLE APP.T(ID NUMBER);',None)
    assert limits[1]==30


@pytest.mark.parametrize('definition,expected',[
    ('MINVALUE 1 MAXVALUE 99999 INCREMENT BY 1 CACHE 1000','READY'),
    ('MINVALUE 1 MAXVALUE 9999999 INCREMENT BY 1 CACHE 1000','BLOCKED'),
    ('MINVALUE 1 MAXVALUE 99999 INCREMENT BY 2 CACHE 1000','BLOCKED'),
    ('MINVALUE 1 MAXVALUE 99999 INCREMENT BY 1 CACHE 1000 CYCLE','BLOCKED'),
])
def test_existing_sequence_shape_separates_compatible_consumer_from_settings_review(definition,expected):
    selected=profile()
    desired=source('CREATE SEQUENCE APP.S MINVALUE 1 MAXVALUE 999999 INCREMENT BY 1 CACHE 20; '
                   'CREATE PROCEDURE APP.P AS N NUMBER; BEGIN N:=APP.S.NEXTVAL; END;\n/')
    desired=replace(desired,objects=tuple(replace(o,properties={**o.properties,'dependencies':KnownValue('KNOWN',[],o.evidence_ids)})
        if o.identity.object_type=='PROCEDURE' else o for o in desired.objects))
    target=actual('CREATE SEQUENCE APP.S '+definition+';')
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))
    assert any(op.identity.object_type=='SEQUENCE' and op.decision=='REVIEW_REQUIRED' for op in result.operations)
    consumer=next(op for op in result.operations if op.identity.object_type=='PROCEDURE')
    assert consumer.decision==expected
    assert (consumer.intent is not None)==(expected=='READY')


def test_unknown_editionability_is_metadata_gap_not_a_known_schema_change():
    selected=profile();desired=source('CREATE PACKAGE APP.P AS PROCEDURE R; END;\n/')
    target=actual('CREATE PACKAGE APP.P AS PROCEDURE R; END;\n/')
    obj=target.objects[0]
    obj=replace(obj,raw_ddl=None,projection=None,coverage=replace(obj.coverage,ddl='PARTIAL'),
        properties={**obj.properties,'projection':KnownValue('UNKNOWN',None,obj.evidence_ids),
                    'definition':KnownValue('UNKNOWN',None,obj.evidence_ids)})
    target=replace(target,objects=(obj,),completeness=replace(target.completeness,ddl='PARTIAL'))
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Backend'))
    assert any(op.decision=='BLOCKED' and 'OBJECT_METADATA_INCOMPLETE' in op.reason_codes for op in result.operations)
    assert all('EDITIONABILITY_CHANGE_UNSUPPORTED' not in op.reason_codes for op in result.operations)
