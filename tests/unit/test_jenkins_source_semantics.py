from dataclasses import replace

import pytest

from tests.factories import source,profile
from oracle_db_migration_generator.model.serialization import thaw


def observation(length=20,stable=True):
    return {'status':'CAPTURED','read_only':True,'ddl_executed':False,'business_data_read':False,
            'owner':'APP','inventory_before':[['TABLE','T','VALID','fixed']],
            'inventory_after':[['TABLE','T','VALID','fixed' if stable else 'changed']],
            'columns':[{'table_name':'T','column_name':'C','data_type':'VARCHAR2',
                'char_length':length,'data_length':length,'char_used':'B','data_precision':None,
                'data_scale':None,'nullable':'Y','data_default':None,'column_id':1,
                'hidden_column':'NO','virtual_column':'NO','identity_column':'NO',
                'default_on_null':'NO','user_generated':'YES','collation':'USING_NLS_COMP'}]}


def test_source_semantics_fills_omissions_only_and_preserves_git_bytes(tmp_path):
    from tools.jenkins_source_semantics import reconcile_source
    original=source('CREATE TABLE APP.T (C VARCHAR2(20));',replace(profile(),source_length_semantics='UNKNOWN'))
    updated,proof=reconcile_source(original,observation(),tmp_path)
    before=original.objects[0];after=updated.objects[0]
    detail=thaw(after.properties['projection'].value)['columns']['C']
    assert detail['length_semantics']=='BYTE' and detail['collation']=='USING_NLS_COMP'
    assert after.raw_ddl==before.raw_ddl and after.ddl_sha256==before.ddl_sha256
    assert updated.source_commit==original.source_commit
    assert proof['matched_tables']==1 and proof['rejected_tables']==[]
    assert (tmp_path/'metadata/source-column-semantics.json').is_file()


def test_source_semantics_refuses_known_fact_or_inventory_drift(tmp_path):
    from tools.jenkins_source_semantics import reconcile_source
    original=source('CREATE TABLE APP.T (C VARCHAR2(20));',replace(profile(),source_length_semantics='UNKNOWN'))
    updated,proof=reconcile_source(original,observation(length=30),tmp_path)
    assert updated.objects==original.objects and proof['matched_tables']==0
    assert proof['rejected_tables'][0]['reason_code']=='SOURCE_KNOWN_COLUMN_FACT_DRIFT'
    with pytest.raises(ValueError,match='SOURCE_METADATA_UNTRUSTED'):
        reconcile_source(original,observation(stable=False),tmp_path/'unstable')
    with pytest.raises(ValueError,match='SOURCE_METADATA_UNTRUSTED'):
        reconcile_source(original,{**observation(),'read_only':False},tmp_path/'unsafe')


def test_source_metadata_capture_uses_closed_queries_and_rolls_back():
    from tools.jenkins_source_semantics import capture_source_metadata
    from oracle_db_migration_generator.oracle.queries import CAPTURE_INVENTORY,CAPTURE_QUERIES,IDENTITY,READ_ONLY_TRANSACTION
    queries=[]
    class Cursor:
        def execute(self,query,*a,**kw): queries.append(query);self.query=query
        def fetchone(self): return ('INNOVA_ODI',)
        def fetchall(self): return [('TABLE','T','VALID','fixed')] if self.query==CAPTURE_INVENTORY else []
        def close(self): pass
    class Connection:
        closed=False;rollbacks=0;version='19'
        def cursor(self): return Cursor()
        def rollback(self): self.rollbacks+=1
        def close(self): self.closed=True
    conn=Connection()
    capture=capture_source_metadata(None,None,connect=lambda *a:conn)
    assert capture['status']=='CAPTURED' and conn.closed and conn.rollbacks==2
    assert queries==[READ_ONLY_TRANSACTION,IDENTITY,CAPTURE_INVENTORY,CAPTURE_QUERIES['columns'][1],READ_ONLY_TRANSACTION,CAPTURE_INVENTORY]


@pytest.mark.parametrize('duplicate',[False,True])
def test_source_semantics_rejects_missing_or_duplicate_live_columns(tmp_path,duplicate):
    from tools.jenkins_source_semantics import reconcile_source
    original=source('CREATE TABLE APP.T (C VARCHAR2(20)'+('' if duplicate else ', D NUMBER')+');',replace(profile(),source_length_semantics='UNKNOWN'))
    capture=observation()
    if duplicate:capture['columns'].append(dict(capture['columns'][0]))
    updated,proof=reconcile_source(original,capture,tmp_path)
    assert proof['matched_tables']==0 and updated.objects==original.objects
    assert proof['rejected_tables'][0]['reason_code']=='SOURCE_COLUMN_SET_DRIFT'


def test_source_observation_time_does_not_change_plan_identity(tmp_path):
    from tools.jenkins_source_semantics import reconcile_source
    from tests.factories import actual
    from oracle_db_migration_generator.runtime.worker import offline_plan
    selected=replace(profile(),source_length_semantics='UNKNOWN')
    original=source('CREATE TABLE APP.T (C VARCHAR2(20));',selected)
    first={**observation(),'started_at':'first','finished_at':'first'}
    later={**observation(),'started_at':'later','finished_at':'later'}
    a,_=reconcile_source(original,first,tmp_path/'a')
    b,_=reconcile_source(original,later,tmp_path/'b')
    target=actual('CREATE TABLE APP.T (C VARCHAR2(30 BYTE));',selected)
    p1=offline_plan(a,target,selected,tmp_path/'plan-a')
    p2=offline_plan(b,target,selected,tmp_path/'plan-b')
    assert a.semantic_digest==b.semantic_digest and p1['plan_id']==p2['plan_id']


def test_ttbp_metadata_capture_binds_exact_owner_and_closes_on_session_mismatch():
    from tools.jenkins_source_semantics import capture_source_metadata
    from oracle_db_migration_generator.oracle.queries import CAPTURE_INVENTORY
    queries=[]
    class Cursor:
        def execute(self,query,*args):queries.append((query,args));self.query=query
        def fetchone(self):return ('TTBP',)
        def fetchall(self):return [('TABLE','T','VALID','fixed')] if self.query==CAPTURE_INVENTORY else []
        def close(self):pass
    class Connection:
        closed=False;rollbacks=0
        def cursor(self):return Cursor()
        def rollback(self):self.rollbacks+=1
        def close(self):self.closed=True
    connection=Connection()
    result=capture_source_metadata(None,None,owner='TTBP',connect=lambda *a:connection)
    assert result['owner']=='TTBP' and result['status']=='CAPTURED'
    assert all(args==({'owner':'TTBP'},) for query,args in queries if ':owner' in query)
    assert connection.closed and connection.rollbacks==2
    connection=Connection()
    with pytest.raises(ValueError,match='SOURCE_METADATA_OWNER_MISMATCH'):
        capture_source_metadata(None,None,owner='INNOVA_ODI',connect=lambda *a:connection)
    assert connection.closed and connection.rollbacks==1
    with pytest.raises(ValueError,match='SOURCE_METADATA_OWNER_NOT_ALLOWED'):
        capture_source_metadata(None,None,owner='OTHER',connect=lambda *a:pytest.fail('No connection for unapproved owner'))


def test_multi_owner_correspondence_isolated_by_owner_and_evidence_path(tmp_path):
    import hashlib
    from tools.jenkins_source_semantics import reconcile_source
    from oracle_db_migration_generator.config.models import SchemaRoot
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.source.models import SourceArtifact,SourceInput,SourceRevision
    selected=replace(profile(),source_length_semantics='UNKNOWN',schema_roots=(SchemaRoot('odi','INNOVA_ODI'),SchemaRoot('ttbp','TTBP')))
    artifacts=[]
    for owner in ('INNOVA_ODI','TTBP'):
        raw=f'CREATE TABLE {owner}.T (C VARCHAR2(20));'.encode()
        artifacts.append(SourceArtifact(owner+'/table.sql',owner,'DDL','TABLE',raw,hashlib.sha256(raw).hexdigest()))
    original=parse_source(SourceInput(SourceRevision('a'*40,None),tuple(artifacts),'b'*64),selected)
    first,proof=reconcile_source(original,{**observation(),'owner':'INNOVA_ODI'},tmp_path)
    by_owner=lambda snapshot:{obj.identity.owner.effective_name:obj for obj in snapshot.objects}
    assert by_owner(first)['TTBP']==by_owner(original)['TTBP'] and proof['matched_tables']==1
    second,ttbp_proof=reconcile_source(first,{**observation(length=30),'owner':'TTBP'},tmp_path)
    assert by_owner(second)['TTBP']==by_owner(original)['TTBP']
    assert by_owner(second)['INNOVA_ODI']==by_owner(first)['INNOVA_ODI']
    assert ttbp_proof['matched_tables']==0 and len(ttbp_proof['rejected_tables'])==1
    assert {path.name for path in (tmp_path/'metadata').glob('*.json')}=={
        'source-column-semantics.INNOVA_ODI.json','source-column-semantics.TTBP.json'}
    for old,new in zip(original.objects,second.objects):assert old.raw_ddl==new.raw_ddl and old.ddl_sha256==new.ddl_sha256
