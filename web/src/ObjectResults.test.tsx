import {chooseOption} from './test-setup'
import {act,fireEvent,render,screen,waitFor,within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import {ObjectResults} from './ObjectResults'
import {valueText} from './resultApi'

afterEach(()=>vi.unstubAllGlobals())
const key='a'.repeat(64)
const overview={available:true,total:1,total_objects:1,counts:{observed_differences:2},scope:{inventory:'PARTIAL',ddl:'COMPLETE',dictionary:'COMPLETE'},rows:[{key,owner:'APP',name:'CUSTOMER',object_type:'TABLE',difference_count:2,operation_count:1,decisions:['READY']}]}
const detail={key,owner:'APP',name:'CUSTOMER',object_type:'TABLE',total:2,page:1,size:50,sections:{columns:2,constraints:0,indexes:0,other:0},rows:[
  {id:'length',object_key:key,property_path:'/columns/NAME/length',kind:'CHANGED',source:{state:'KNOWN',value:100},target:{state:'KNOWN',value:50}},
  {id:'default',object_key:key,property_path:'/columns/NAME/default',kind:'UNKNOWN',source:{state:'UNKNOWN',value:null},target:{state:'KNOWN',value:null}}],operations:[],operation_total:0,operation_page:1,recorded_differences_only:true}

it('opens recorded column differences with source and target values and explicit unknown/null',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/'+key)?detail:overview})))
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  await userEvent.click(await screen.findByRole('button',{name:'APP.CUSTOMER ayrıntıları'}))
  expect(await screen.findByRole('columnheader',{name:'Kaynak'})).toBeInTheDocument()
  expect(screen.getByRole('columnheader',{name:'PROD'})).toBeInTheDocument()
  expect(screen.getByText('100')).toBeInTheDocument();expect(screen.getByText('50')).toBeInTheDocument()
  expect(screen.getByText('Bilinmiyor')).toBeInTheDocument();expect(screen.getByText('NULL')).toBeInTheDocument()
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(screen.getByRole('region',{name:'Nesne listesi'})).toBeInTheDocument()
  expect(within(screen.getByRole('region',{name:'Seçili nesne karşılaştırması'})).getByText(/Yalnız kaydedilmiş farklar/)).toBeInTheDocument()
})

it('does not show a late result for the previous target',async()=>{
  let resolveOld!:(value:unknown)=>void
  const old=new Promise(resolve=>{resolveOld=resolve})
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('target_id=old')?await old:{available:true,total:0,total_objects:0,rows:[]}}))
  vi.stubGlobal('fetch',fetcher)
  render(<ObjectResults runId="run" targets={[{id:'old',name:'Old'},{id:'new',name:'New'}]}/>)
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  await chooseOption(screen.getByLabelText('İncelenecek hedef'),'new')
  await waitFor(()=>expect(screen.getByText('Bu filtreye uygun nesne yok')).toBeInTheDocument())
  await act(async()=>{resolveOld(overview);await old})
  await waitFor(()=>expect(screen.queryByRole('button',{name:'APP.CUSTOMER ayrıntıları'})).not.toBeInTheDocument())
})

it('keeps unknown, absence and not-applicable visible even for omitted definitions',()=>{
  expect(valueText({state:'UNKNOWN',value:null,omitted:true})).toBe('Bilinmiyor')
  expect(valueText({state:'ABSENT',value:null,omitted:true})).toBe('Yok')
  expect(valueText({state:'NOT_APPLICABLE',value:null,omitted:true})).toBe('Uygulanamaz')
  expect(valueText({state:'KNOWN',value:null,omitted:true})).toBe('Tanım arşivde')
  expect(valueText({state:'KNOWN',value:null})).toBe('NULL')
})

it('uses the canonical display name for a comment object',async()=>{
  const comment={...overview,rows:[{...overview.rows[0],name:'S_123',display_name:'APP.CUSTOMER.TITLE',object_type:'COMMENT'}]}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/'+key)?{...detail,object_type:'COMMENT',display_name:'APP.CUSTOMER.TITLE'}:comment})))
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  await chooseOption(screen.getByLabelText('Nesne Türü'),'COMMENT')
  expect(await screen.findByRole('button',{name:'APP.CUSTOMER.TITLE ayrıntıları'})).toBeInTheDocument()
  expect(screen.queryByText('S_123')).not.toBeInTheDocument()
})

it('keeps the list visible and rejects a late detail after selecting another object',async()=>{
  const second='b'.repeat(64)
  let resolveFirst!:(value:unknown)=>void
  const pending=new Promise(resolve=>{resolveFirst=resolve})
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/'+key)?await pending:url.includes('/objects/'+second)?{...detail,key:second,name:'ORDERS',rows:[{...detail.rows[0],source:{state:'KNOWN',value:777}}]}:{...overview,total:2,rows:[overview.rows[0],{...overview.rows[0],key:second,name:'ORDERS'}]}})))
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  await userEvent.click(await screen.findByRole('button',{name:'APP.CUSTOMER ayrıntıları'}))
  await userEvent.click(screen.getByRole('button',{name:'APP.ORDERS ayrıntıları'}))
  expect(await screen.findByText('777')).toBeInTheDocument()
  await act(async()=>{resolveFirst(detail);await pending})
  expect(screen.queryByText('100')).not.toBeInTheDocument()
  expect(screen.getByRole('button',{name:'APP.CUSTOMER ayrıntıları'})).toBeVisible()
  expect(within(screen.getByRole('region',{name:'Seçili nesne karşılaştırması'})).getByRole('heading',{name:'APP.ORDERS'})).toBeInTheDocument()
})

it('appends objects while scrolling and keeps the selected object without page buttons',async()=>{
  const rows=Array.from({length:25},(_,i)=>({...overview.rows[0],key:i.toString(16).padStart(64,'0'),name:'CUSTOMER_'+i}))
  const extra={...rows[0],key:'f'.repeat(64),name:'LAST_CUSTOMER'}
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/')?detail:{...overview,total:26,rows:url.includes('page=2')?[extra]:rows}}))
  vi.stubGlobal('fetch',fetcher)
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  await userEvent.click(await screen.findByRole('button',{name:'APP.CUSTOMER_1 ayrıntıları'}))
  const list=screen.getByTestId('object-scroll')
  Object.defineProperty(list,'scrollHeight',{value:1000,configurable:true})
  Object.defineProperty(list,'clientHeight',{value:200,configurable:true})
  fireEvent.scroll(list,{target:{scrollTop:850}})
  expect(await screen.findByRole('button',{name:'APP.LAST_CUSTOMER ayrıntıları'})).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'APP.CUSTOMER_1 ayrıntıları'})).toHaveAttribute('aria-pressed','true')
  expect(fetcher.mock.calls.filter(([url])=>url.includes('/results/objects?')&&url.includes('page=2'))).toHaveLength(1)
  expect(screen.queryByRole('button',{name:'Önceki nesneler'})).not.toBeInTheDocument()
  expect(screen.queryByRole('button',{name:'Sonraki nesneler'})).not.toBeInTheDocument()
})

it('uses explicit object existence labels instead of context-free yes or no',async()=>{
  const presence={...detail,total:1,rows:[{...detail.rows[0],property_path:'/exists',kind:'EXTRA',source:{state:'ABSENT',value:null},target:{state:'KNOWN',value:true}}]}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/')?presence:overview})))
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  expect(await screen.findByText('Nesne Var')).toBeInTheDocument()
  expect(screen.getByText('Nesne Yok')).toBeInTheDocument()
  expect(screen.queryByText('Evet')).not.toBeInTheDocument()
})
it('keeps loaded objects after an append failure and retries the same page',async()=>{
  const rows=Array.from({length:25},(_,i)=>({...overview.rows[0],key:i.toString(16).padStart(64,'0'),name:'CUSTOMER_'+i}))
  let failed=false
  const fetcher=vi.fn(async(url:string)=>{
    if(url.includes('page=2')&&!failed){failed=true;throw new Error('offline')}
    return {ok:true,json:async()=>url.includes('/objects/')?detail:{...overview,total:26,rows:url.includes('page=2')?[{...rows[0],key:'f'.repeat(64),name:'LAST_CUSTOMER'}]:rows}}
  })
  vi.stubGlobal('fetch',fetcher)
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  await userEvent.click(await screen.findByRole('button',{name:'APP.CUSTOMER_1 ayrıntıları'}))
  const list=screen.getByTestId('object-scroll')
  Object.defineProperty(list,'scrollHeight',{value:1000,configurable:true});Object.defineProperty(list,'clientHeight',{value:200,configurable:true})
  fireEvent.scroll(list,{target:{scrollTop:850}});fireEvent.scroll(list,{target:{scrollTop:850}})
  expect(await screen.findByRole('alert')).toHaveTextContent('Sunucuya ulaşılamadı')
  expect(screen.getByRole('button',{name:'APP.CUSTOMER_1 ayrıntıları'})).toHaveAttribute('aria-pressed','true')
  await userEvent.click(screen.getByRole('button',{name:'Tekrar Dene'}))
  expect(await screen.findByRole('button',{name:'APP.LAST_CUSTOMER ayrıntıları'})).toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([url])=>url.includes('/results/objects?')&&url.includes('page=2'))).toHaveLength(2)
})
it('renders canonical metadata tokens as readable values without changing literal contents',async()=>{
  const readable={...detail,total:1,rows:[{...detail.rows[0],property_path:'/constraints/FK_DEMO/reference',source:{state:'KNOWN',value:'[["code","APP"],["code","."],["quoted","TABLE"],["code","("],["code","ID"],["code",")"],["literal","\'a . b\'"]]'},target:{state:'ABSENT',value:null}}]}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/objects/')?readable:overview})))
  render(<ObjectResults runId="run" targets={[{id:'target',name:'PROD'}]}/>)
  expect(await screen.findByText('APP."TABLE" (ID) \'a . b\'')).toBeInTheDocument()
  expect(screen.queryByText(/\[\["code"/)).not.toBeInTheDocument()
})
