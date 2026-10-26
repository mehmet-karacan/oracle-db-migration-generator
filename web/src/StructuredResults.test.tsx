import {render,screen,within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import {ObjectComparisonPanel} from './ObjectComparisonPanel'
import {chooseOption} from './test-setup'
import {ObjectResults} from './ObjectResults'

afterEach(()=>vi.unstubAllGlobals())
const value={state:'KNOWN',value:true},absent={state:'ABSENT',value:null}
const groups=['FK_CUSTOMER','FK_ORDER'].map(name=>({id:'/constraints/'+name,name,entity_type:'FOREIGN_KEY',section:'constraints',status:'MISSING',unknown_count:0,difference_count:2,operation_ids:['op1'],rows:[
 {id:name+'-exists',property_path:'/constraints/'+name+'/exists',kind:'MISSING',source:value,target:absent},
 {id:name+'-ref',property_path:'/constraints/'+name+'/reference',kind:'MISSING',source:{state:'KNOWN',value:'APP.CUSTOMER (ID)'},target:absent}]}))
const detail={key:'a'.repeat(64),owner:'APP',name:'ORDERS',object_type:'TABLE',total:4,rows:[],sections:{columns:0,constraints:4,indexes:0,other:0},group_sections:{columns:0,constraints:2,indexes:0,other:0},groups,group_total:2,summary:{group_count:2,unknown_count:0,object_presence:null,items:[{entity_type:'FOREIGN_KEY',status:'MISSING',count:2}]},operations:[{id:'op1',decision:'READY',change_ids:['x'],reason_tr:'Yabancı anahtar eklenecek.',depends_on:[],evidence_ids:[],sql_url:'/api/runs/r/artifacts/targets/t/fk.sql'}],operation_total:1,object_operation_total:1}
it('shows a full object summary, connection context and one expandable card per foreign key',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>detail})))
 render(<ObjectComparisonPanel runId="r" targetId="t" targetName="PROD" objectKey={detail.key} sourceName="SKY Git" targetSchema="APP"/>)
 expect(await screen.findByText('2 Yabancı Anahtar - Hedefte Eksik')).toBeInTheDocument()
 expect(screen.getByText('SKY Git / APP')).toBeInTheDocument()
 expect(screen.getByText('PROD / APP')).toBeInTheDocument()
 expect(screen.getAllByText('FK_CUSTOMER')).toHaveLength(1)
 const card=screen.getByTestId('group-/constraints/FK_CUSTOMER')
 expect(card).not.toHaveAttribute('open')
 await userEvent.click(within(card).getByText('FK_CUSTOMER'))
 expect(card).toHaveAttribute('open')
 expect(within(card).getByRole('columnheader',{name:'Kaynak'})).toBeInTheDocument()
 expect(within(card).getByText('APP.CUSTOMER (ID)')).toBeVisible()
 await userEvent.click(within(card).getByRole('button',{name:'İlgili İşlemler ve SQL'}))
 expect(await screen.findByText('Yabancı anahtar eklenecek.')).toBeInTheDocument()
 expect(screen.queryByText('2 Yabancı Anahtar - Hedefte Eksik')).not.toBeInTheDocument()
 expect(screen.getByRole('tabpanel')).toHaveAttribute('aria-labelledby',screen.getByRole('tab',{selected:true}).id)
 expect(screen.getByRole('button',{name:'SQL Görüntüle'})).toBeInTheDocument()
})
it('sends difference filtering to the server independently of DDL decisions',async()=>{
 const fetcher=vi.fn(async()=>({ok:true,json:async()=>({available:true,total:0,rows:[]})}));vi.stubGlobal('fetch',fetcher)
 render(<ObjectResults runId="r" targets={[{id:'t',name:'PROD'}]}/>)
 await chooseOption(screen.getByLabelText('Fark Türü'),'UNKNOWN')
 await screen.findByText('Bu filtreye uygun nesne yok')
 expect(fetcher.mock.calls.some(call=>(call as unknown as [string])[0].includes('difference_kind=UNKNOWN'))).toBe(true)
})
it('presents structured metadata as labelled values instead of raw JSON',async()=>{
 const structured={...detail,groups:[{...groups[0],status:'CHANGED',rows:[{id:'structured',property_path:'/constraints/FK_CUSTOMER/reference',kind:'CHANGED',source:{state:'KNOWN',value:{columns:['ID','TENANT_ID'],enabled:true}},target:{state:'UNKNOWN',value:null}}]}],group_total:1}
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>structured})))
 render(<ObjectComparisonPanel runId="r" targetId="t" targetName="PROD" objectKey={detail.key}/>)
 expect(await screen.findByText('TENANT_ID')).toBeInTheDocument()
 expect(screen.getByText('ID')).toBeInTheDocument()
 expect(screen.queryByText('{"columns":["ID","TENANT_ID"],"enabled":true}')).not.toBeInTheDocument()
 expect(screen.getByText('Bilinmiyor')).toBeInTheDocument()
})
it('translates entity names, context and plural summaries in English',async()=>{
 const {setPreferences}=await import('./preferences');setPreferences({locale:'en'})
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>detail})))
 render(<ObjectComparisonPanel runId="r" targetId="t" targetName="PROD" objectKey={detail.key}/>)
 expect(await screen.findByText('2 Foreign Keys - Missing on Target')).toBeInTheDocument()
 expect(screen.getByText('Target - Current Structure')).toBeInTheDocument()
})
