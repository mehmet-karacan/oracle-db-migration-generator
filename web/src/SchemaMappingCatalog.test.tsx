import {chooseOption} from './test-setup'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import {ConnectionWorkspace} from './ConnectionWorkspace'
import {ComparisonForm} from './ComparisonForm'
import type {Connection,SchemaMapping} from './api'

const base={revision:1,updated_at:'',port:1521,driver_mode:'thin' as const,allowed_users:[],credential_configured:true}
const connections:Connection[]=[{...base,id:'source',name:'UAT',kind:'ORACLE',host:'uat.example',service_name:'UAT'},
  {...base,id:'target',name:'PROD',kind:'ORACLE',host:'prod.example',service_name:'PROD'}]
const mapping:SchemaMapping={id:'mapping',revision:2,name:'UAT to PROD',source:{kind:'ORACLE',connection_id:'source',schemas:['TTBP']},target_ids:['target'],target_mappings:{target:[{source_schema:'TTBP',target_schema:'TTBP'}]}}
afterEach(()=>vi.unstubAllGlobals())

it('creates schema pairs on a separate tab under Connections',async()=>{
  const fetcher=vi.fn(async(_url:string,_options?:RequestInit)=>({ok:true,json:async()=>mapping}))
  vi.stubGlobal('fetch',fetcher)
  render(<ConnectionWorkspace connections={connections} mappings={[]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('tab',{name:'Şema Eşleştirmeleri'}))
  await userEvent.click(screen.getByRole('button',{name:'Yeni eşleştirme'}))
  await userEvent.type(screen.getByLabelText('Eşleştirme Adı'),'UAT to PROD')
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'source')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'TTBP')
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'target')
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  expect(screen.getByRole('alert')).toHaveTextContent('PROD için şema eşleştirmesi seçin')
  expect(fetcher).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('checkbox',{name:'PROD: TTBP → TTBP'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  expect(fetcher.mock.calls[0][0]).toBe('/api/schema-mappings')
  const data=JSON.parse(fetcher.mock.calls[0][1]!.body as string)
  expect(data.target_mappings).toEqual(mapping.target_mappings)
  expect(data.source.connection_id).toBe('source')
})

it('keeps each target selectable and drops old schema pairs when the target changes',async()=>{
  const fetcher=vi.fn(async()=>({ok:true,json:async()=>mapping}))
  vi.stubGlobal('fetch',fetcher)
  render(<ConnectionWorkspace connections={connections} mappings={[]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('tab',{name:'Şema Eşleştirmeleri'}))
  await userEvent.click(screen.getByRole('button',{name:'Yeni eşleştirme'}))
  await userEvent.type(screen.getByLabelText('Eşleştirme Adı'),'Test')
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'source')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'TTBP')
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'target')
  await userEvent.click(screen.getByRole('checkbox',{name:'PROD: TTBP → TTBP'}))
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'source')
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  expect(screen.getByRole('alert')).toHaveTextContent('UAT için şema eşleştirmesi seçin')
  expect(fetcher).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('button',{name:'Hedef Ekle'}))
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı 2'),'target')
  expect(screen.getAllByRole('combobox')).toHaveLength(3)
})

it('selects a saved mapping in comparison without editing connection or schema fields',async()=>{
  const fetcher=vi.fn(async(_url:string,_options?:RequestInit)=>({ok:true,json:async()=>({id:'profile'})}))
  vi.stubGlobal('fetch',fetcher)
  render(<ComparisonForm connections={connections} mappings={[mapping]} profiles={[]} admin onSaved={()=>{}} onStarted={()=>{}}/>)
  await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'mapping')
  expect(screen.queryByLabelText('Kaynak Şemaları')).not.toBeInTheDocument()
  expect(screen.getByText('UAT')).toBeInTheDocument()
  expect(screen.getByText('PROD')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button',{name:'Profili kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  const data=JSON.parse(fetcher.mock.calls[0][1]!.body as string)
  expect(data.mapping_id).toBe('mapping')
  expect(data.mapping_revision).toBe(2)
  expect(data.source.schemas).toEqual(['TTBP'])
  expect(data.target_mappings).toEqual(mapping.target_mappings)
})

it('restores the profile scope when returning from another catalog mapping',async()=>{
  const profile={id:'p',revision:1,updated_at:'',name:'Existing',source:{kind:'ORACLE' as const,connection_id:'source',schemas:['APP'],ref:'master',layout:'flat' as const,roots:{}},target_ids:['target'],target_mappings:{target:[{source_schema:'APP',target_schema:'APP'}]},object_types:['TABLE'],excluded_object_types:[],exclude_system_generated:true,compare_physical_storage:false,source_length_semantics:'UNKNOWN'}
  const fetcher=vi.fn(async(_url:string,_options?:RequestInit)=>({ok:true,json:async()=>profile}))
  vi.stubGlobal('fetch',fetcher)
  render(<ComparisonForm connections={connections} mappings={[mapping]} profiles={[profile]} admin onSaved={()=>{}} onStarted={()=>{}}/>)
  await chooseOption(screen.getByLabelText('Kayıtlı profil'),'p')
  await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'mapping')
  expect(screen.getByText('Kaynak TTBP → Hedef TTBP')).toBeInTheDocument()
  await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'profile')
  expect(screen.getByText('Kaynak APP → Hedef APP')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button',{name:'Profili kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  const data=JSON.parse(fetcher.mock.calls[0][1]!.body as string)
  expect(data.source.schemas).toEqual(['APP'])
  expect(data.target_mappings).toEqual(profile.target_mappings)
})
