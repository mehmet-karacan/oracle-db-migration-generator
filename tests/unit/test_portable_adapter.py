from dataclasses import replace
import json

from oracle_db_migration_generator.portable.adapter import observation_from_capture, scope_comparison
from oracle_db_migration_generator.portable.stream import read_capture
from oracle_db_migration_generator.source.oracle_reader import from_observation,save_source
from oracle_db_migration_generator.runtime.worker import offline_plan
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from test_collector import inputs
from test_portable_stream import records,packet


def test_import_produces_real_sql_and_exact_source_bytes_without_network(tmp_path):
    _,profile=inputs()
    ddl='CREATE TABLE APP.DEMO (ID NUMBER);\n-- özgün & "metin"\n'
    source_capture=read_capture(packet(records(ddl)))
    desired=from_observation(observation_from_capture(source_capture,profile,target_id='import-source'),connection_id='import-source')
    source_path=save_source(desired,tmp_path/'source')
    restored=load_snapshot(source_path,require_ddl=True)
    assert restored.objects[0].raw_ddl==ddl.encode()
    target=observation_from_capture(read_capture(packet(records(inventory=[]))),profile,target_id='offline-target').snapshot
    source,target=scope_comparison(restored,target)
    result=offline_plan(source,target,profile,tmp_path/'plan')
    assert result['counts']['ready_operations']>0
    sql=b'\n'.join(p.read_bytes() for p in (tmp_path/'plan'/'objects').rglob('*.sql'))
    assert b'CREATE TABLE' in sql and b'APP.DEMO' in sql
    plan=json.loads((tmp_path/'plan'/'plan.json').read_bytes())
    assert plan['source']['origin']['kind']=='ORACLE' and desired.receipt['execution_status']=='NOT_EXECUTED'


def test_visible_empty_target_never_proves_absence(tmp_path):
    _,profile=inputs()
    source=from_observation(observation_from_capture(read_capture(packet(records())),profile,target_id='s'),connection_id='s').snapshot
    target=observation_from_capture(read_capture(packet(records(authority='VISIBLE',inventory=[]))),profile,target_id='t').snapshot
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    changes=compare_snapshots(source,target,profile.policy)
    assert not changes.complete and any(d.kind=='UNKNOWN' for d in changes.differences)
    assert not any(ev.kind=='ABSENCE_SCOPE' for ev in target.evidence)


def test_dtype_selects_source_table_but_retains_different_target_type():
    _,profile=inputs()
    source=from_observation(observation_from_capture(read_capture(packet(records())),profile,target_id='s'),connection_id='s').snapshot
    target=observation_from_capture(read_capture(packet(records('CREATE TABLE APP.DEMO (ID VARCHAR2(20));'))),profile,target_id='t').snapshot
    # Projection is available even when synthetic dictionary rows are empty.
    left,right=scope_comparison(source,target,{'schemas':['APP'],'object_types':['TABLE'],'data_types':['NUMBER']})
    assert len(left.objects)==len(right.objects)==1
    assert left.objects[0].object_key==right.objects[0].object_key
    assert right.objects[0].raw_ddl==b'CREATE TABLE APP.DEMO (ID VARCHAR2(20));'


def test_unselected_inventory_object_is_unknown_instead_of_absent():
    _,profile=inputs();values=records()
    for r in values:
        if r.get('query','').startswith('ddl:') and r['kind']=='query_end':r['status']='ERROR';r['error_code']='ORA-01031'
    values[-1].update(status='PARTIAL',errors=1)
    capture=read_capture(packet(values))
    snapshot=observation_from_capture(capture,profile,target_id='t').snapshot
    assert snapshot.objects[0].coverage.ddl=='PARTIAL'
    assert snapshot.objects[0].properties['projection'].state=='UNKNOWN'


def test_imported_session_calendar_is_evidence_backed_and_legacy_files_stay_unknown():
    from test_portable_stream import encoded
    _,profile=inputs()
    values=records()
    at=next(i for i,r in enumerate(values) if r['kind']=='selection')
    values[at:at]=[
        {'kind':'query_start','schema':'APP','query':'session_calendar','columns':['parameter','value']},
        {'kind':'row','schema':'APP','query':'session_calendar','index':0,
         'values':[encoded('NLS_CALENDAR'),encoded('GREGORIAN')]},
        {'kind':'query_end','schema':'APP','query':'session_calendar','rows':1,'status':'COMPLETE'}]
    observed=observation_from_capture(read_capture(packet(values)),profile,target_id='file').snapshot
    calendar=observed.capabilities['nls_calendar']
    assert calendar.state=='KNOWN' and calendar.value=='GREGORIAN'
    assert calendar.evidence_ids and all(any(e.id==key for e in observed.evidence) for key in calendar.evidence_ids)
    old=observation_from_capture(read_capture(packet(records())),profile,target_id='legacy').snapshot
    assert old.capabilities['nls_calendar'].state=='UNKNOWN'


def test_imported_external_dependency_status_has_its_own_evidence_without_network():
    from test_portable_stream import encoded
    _,profile=inputs();values=records()
    at=next(i for i,r in enumerate(values) if r['kind']=='selection')
    values[at:at]=[
        {'kind':'query_start','schema':'APP','query':'dependency_objects',
         'columns':['owner','object_name','object_type','status']},
        {'kind':'row','schema':'APP','query':'dependency_objects','index':0,
         'values':[encoded(v) for v in ('OTHER','PARENT','TABLE','VALID')]},
        {'kind':'query_end','schema':'APP','query':'dependency_objects','rows':1,'status':'COMPLETE'}]
    target=observation_from_capture(read_capture(packet(values)),profile,target_id='file').snapshot
    proof=target.capabilities['reference_objects']
    assert proof.state=='KNOWN'
    assert tuple(dict(row) for row in proof.value)==({'owner':'OTHER','name':'PARENT','object_type':'TABLE','status':'VALID'},)
    assert all(any(e.id==key and e.query_id=='dependency_objects' for e in target.evidence) for key in proof.evidence_ids)
    legacy=observation_from_capture(read_capture(packet(records())),profile,target_id='legacy').snapshot
    assert legacy.capabilities['reference_objects'].state=='UNKNOWN'


def test_denied_dependency_metadata_never_becomes_an_empty_known_inventory():
    _,profile=inputs();values=records()
    at=next(i for i,r in enumerate(values) if r['kind']=='selection')
    values[at:at]=[
        {'kind':'query_start','schema':'APP','query':'dependency_objects',
         'columns':['owner','object_name','object_type','status']},
        {'kind':'query_end','schema':'APP','query':'dependency_objects','rows':0,
         'status':'ERROR','error_code':'ORA-01031'}]
    values[-1].update(status='PARTIAL',errors=1)
    capture=read_capture(packet(values))
    target=observation_from_capture(capture,profile,target_id='file').snapshot
    assert capture.status=='PARTIAL'
    assert target.capabilities['reference_objects'].state=='UNKNOWN'
    assert target.capabilities['reference_objects'].value is None


def test_related_table_objects_survive_a_table_only_profile():
    from test_portable_stream import encoded
    from oracle_db_migration_generator.oracle.queries import CAPTURE_QUERIES
    _,profile=inputs();profile=replace(profile,object_types=('TABLE',))
    values=records(inventory=[['TABLE','DEMO','VALID','2026-10-25'],['INDEX','IX_DEMO','VALID','2026-10-25']])
    for row in values:
        if row['kind']=='row' and row.get('query')=='ddl:INDEX:IX_DEMO':row['values']=[encoded('CREATE INDEX APP.IX_DEMO ON APP.DEMO (ID);')]
        if row['kind']=='selection':row['roots']=[{'object_type':'TABLE','name':'DEMO'}]
    index=next(i for i,r in enumerate(values) if r.get('query')=='indexes' and r['kind']=='query_end')
    cols=CAPTURE_QUERIES['indexes'][0]
    data={'index_name':'IX_DEMO','index_type':'NORMAL','table_owner':'APP','table_name':'DEMO','uniqueness':'NONUNIQUE'}
    values.insert(index,{'kind':'row','schema':'APP','query':'indexes','index':0,'values':[encoded(data.get(c)) for c in cols]});values[index+1]['rows']=1
    capture=read_capture(packet(values))
    snapshot=from_observation(observation_from_capture(capture,profile,target_id='s'),connection_id='s').snapshot
    scoped,_=scope_comparison(snapshot,snapshot,{'schemas':['APP'],'object_types':['TABLE'],'object_names':['DEMO'],'include_related':True})
    assert {o.identity.object_type for o in scoped.objects}=={'TABLE','INDEX'}
    narrow,_=scope_comparison(snapshot,snapshot,{'schemas':['APP'],'object_types':['TABLE'],'object_names':['DEMO'],'include_related':False})
    assert {o.identity.object_type for o in narrow.objects}=={'TABLE'}


def test_parser_projection_related_objects_include_quoted_dotted_table_names():
    from test_portable_stream import encoded
    _,profile=inputs()
    values=records(inventory=[['TABLE','DE.MO','VALID','2026-10-25'],['INDEX','IX_DEMO','VALID','2026-10-25'],['TRIGGER','TR_DEMO','VALID','2026-10-25']])
    ddls={'TABLE':'CREATE TABLE APP."DE.MO" (ID NUMBER);','INDEX':'CREATE INDEX APP.IX_DEMO ON APP."DE.MO" (ID);',
          'TRIGGER':'CREATE OR REPLACE TRIGGER APP.TR_DEMO BEFORE INSERT ON APP."DE.MO" FOR EACH ROW BEGIN NULL; END;'}
    for row in values:
        if row['kind']=='row' and row.get('query','').startswith('ddl:'):row['values']=[encoded(ddls[row['query'].split(':')[1]])]
    snapshot=from_observation(observation_from_capture(read_capture(packet(values)),profile,target_id='s'),connection_id='s').snapshot
    scoped,_=scope_comparison(snapshot,snapshot,{'schemas':['APP'],'object_types':['TABLE'],'object_names':['"DE.MO"'],'include_related':True})
    assert {o.identity.object_type for o in scoped.objects}=={'TABLE','INDEX','TRIGGER'}
