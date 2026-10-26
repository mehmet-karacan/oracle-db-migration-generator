import base64
import hashlib
import json

import pytest

from oracle_db_migration_generator.portable.builder import query_contract
from oracle_db_migration_generator.oracle.queries import CAPTURE_QUERIES
from oracle_db_migration_generator.portable.stream import read_capture


def encoded(value):
    if value is None:return None
    if isinstance(value,int):return {'number':str(value)}
    return {'encoding':'base64-utf8','chunks':[base64.b64encode(value.encode()).decode()]}


def packet(records):
    records=[dict(r) for r in records]
    if records[-1]['kind']=='footer':records[-1]['messages']=len(records)
    lines=[]
    for number,record in enumerate(records,1):
        raw=json.dumps(record,ensure_ascii=False).encode()
        chunks=[raw[i:i+12000] for i in range(0,len(raw),12000)]
        for part,chunk in enumerate(chunks):
            lines.append(json.dumps({'record':'chunk','message':number,'part':part,'sha256':hashlib.sha256(chunk).hexdigest().upper(),'data':base64.b64encode(chunk).decode()}))
        lines.append(json.dumps({'record':'end_message','message':number,'parts':len(chunks)}))
    return ('\n'.join(lines)+'\n').encode()


def records(ddl='CREATE TABLE APP.DEMO (ID NUMBER);', *, authority='OWN', failed=(), inventory=None):
    inventory=[['TABLE','DEMO','VALID','2026-10-25T12:00:00']] if inventory is None else inventory
    rows=[{'kind':'header','schema_version':'portable-capture/1.0','collector_version':'1.0','query_contract':query_contract(),'session_user':'APP','database_version':'19.0','captured_at':'2026-10-25T12:00:00.000Z','environment':'Synthetic','selection':{'schemas':'APP','object_types':'TABLE','object_names':None,'data_types':None,'include_related':True,'exclude_system_generated':True}},
          {'kind':'schema_start','schema':'APP','authority':authority}]
    def query(name,columns,values):
        rows.append({'kind':'query_start','schema':'APP','query':name,'columns':list(columns)})
        for i,value in enumerate(values):rows.append({'kind':'row','schema':'APP','query':name,'index':i,'values':[encoded(v) for v in value]})
        end={'kind':'query_end','schema':'APP','query':name,'rows':len(values),'status':'ERROR' if name in failed else 'COMPLETE'}
        if name in failed:end['error_code']='ORA-01031'
        rows.append(end)
    query('inventory_before',('object_type','object_name','status','last_ddl_time'),inventory)
    for name,(columns,_) in CAPTURE_QUERIES.items():query(name,columns,[])
    query('collation_parameters',('name','value'),[])
    query('trigger_parents',('trigger_name','table_owner','table_name'),[])
    chosen=[]
    for kind,name,*_ in inventory:
        query('ddl:'+kind+':'+name,('ddl',),[[ddl]])
        chosen.append({'object_type':kind.replace(' ','_'),'name':name})
    rows.append({'kind':'selection','schema':'APP','roots':chosen,'objects':chosen})
    query('inventory_after',('object_type','object_name','status','last_ddl_time'),inventory)
    rows.extend([{'kind':'schema_end','schema':'APP','authority':authority,'inventory_complete':authority!='VISIBLE','stable':True},
                 {'kind':'footer','status':'PARTIAL' if failed else 'COMPLETE','messages':0,'objects':len(chosen),'errors':len(failed)}])
    return rows


def test_capture_roundtrip_unicode_long_exact_number_and_failure():
    text='CREATE TABLE APP.DEMO (ID NUMBER);\r\n-- Türkçe & "alıntı" 😀\n'+('x'*20000)
    values=records(text,failed=('grants',))
    capture=read_capture(packet(values))
    assert capture.schemas['APP'].queries['ddl:TABLE:DEMO'].rows==((text,),)
    assert capture.schemas['APP'].queries['grants'].rows is None
    assert capture.schemas['APP'].inventory_complete
    assert capture.status=='PARTIAL' and len(capture.sha256)==64


@pytest.mark.parametrize('damage',['hash','sequence','truncated','duplicate','unstable','false_authority','contract'])
def test_invalid_capture_is_never_imported_as_complete(damage):
    values=records()
    data=packet(values)
    if damage=='hash':data=data.replace(b'"sha256": "',b'"sha256": "0',1)
    if damage=='sequence':data=data.replace(b'"part": 0',b'"part": 1',1)
    if damage=='truncated':data=b'\n'.join(data.splitlines()[:-2])
    if damage=='duplicate':values.insert(2,values[2]);data=packet(values)
    if damage=='unstable':values[-2]['stable']=False;data=packet(values)
    if damage=='false_authority':values[0]['session_user']='OTHER';data=packet(values)
    if damage=='contract':values[0]['query_contract']='0'*64;data=packet(values)
    with pytest.raises(ValueError,match='CAPTURE_'):read_capture(data)


def test_visible_inventory_is_partial_even_when_no_objects():
    capture=read_capture(packet(records(authority='VISIBLE',inventory=[])))
    assert not capture.schemas['APP'].inventory_complete


def test_decimal_metadata_retains_38_digits():
    values=records()
    index=next(i for i,r in enumerate(values) if r.get('query')=='sequences' and r['kind']=='query_end')
    row=[None]*len(CAPTURE_QUERIES['sequences'][0]);row[0]='SEQ';row[1]=10**37+123456789
    values.insert(index,{'kind':'row','schema':'APP','query':'sequences','index':0,'values':[encoded(v) for v in row]})
    values[index+1]['rows']=1
    capture=read_capture(packet(values))
    assert capture.schemas['APP'].queries['sequences'].rows[0][1]==10**37+123456789
