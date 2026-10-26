import {chooseOption} from './test-setup'
import { render,screen,waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach,expect,it,vi } from 'vitest'
import { SchemaMappings } from './SchemaMappings'
import type { Connection,Profile } from './api'

const base={revision:1,updated_at:'',port:1521,driver_mode:'thin' as const,allowed_users:[],credential_configured:true}
const connections:Connection[]=[{...base,id:'source',name:'UAT',kind:'ORACLE',host:'uat.example',service_name:'UAT'},
  {...base,id:'target',name:'PROD',kind:'ORACLE',host:'prod.example',service_name:'PROD'}]
afterEach(()=>vi.unstubAllGlobals())

it('requires an explicit schema pair for each target and saves the selected subset',async()=>{
  const fetcher=vi.fn(async(_url:string,_options?:RequestInit)=>({ok:true,json:async()=>({id:'profile'})}))
  vi.stubGlobal('fetch',fetcher)
  render(<SchemaMappings connections={connections} mappings={[]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Yeni eşleştirme'}))
  await userEvent.type(screen.getByLabelText('Eşleştirme Adı'),'Test mapping')
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'source')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'TTBP, APP')
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'target')
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  expect(screen.getByRole('alert')).toHaveTextContent('PROD için şema eşleştirmesi seçin')
  expect(fetcher).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('checkbox',{name:'PROD: TTBP → TTBP'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  const data=JSON.parse(fetcher.mock.calls[0][1]!.body as string)
  expect(data.source.schemas).toEqual(['TTBP','APP'])
  expect(data.target_mappings).toEqual({target:[{source_schema:'TTBP',target_schema:'TTBP'}]})
  expect(data.source.username).toBeUndefined()
})

it('drops mappings when the source connection or source schema scope changes',async()=>{
  render(<SchemaMappings connections={connections} mappings={[]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Yeni eşleştirme'}))
  await userEvent.type(screen.getByLabelText('Eşleştirme Adı'),'Test mapping')
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'source')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'TTBP')
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'target')
  await userEvent.click(screen.getByRole('checkbox',{name:'PROD: TTBP → TTBP'}))
  await userEvent.clear(screen.getByLabelText('Kaynak Şemaları'))
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'APP')
  expect(screen.queryByRole('checkbox',{name:'PROD: TTBP → TTBP'})).not.toBeInTheDocument()
  expect(screen.getByRole('checkbox',{name:'PROD: APP → APP'})).not.toBeChecked()
  await userEvent.click(screen.getByRole('checkbox',{name:'PROD: APP → APP'}))
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'target')
  expect(screen.getByLabelText('Kaynak Şemaları')).toHaveValue('')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'APP')
  expect(screen.getByRole('checkbox',{name:'PROD: APP → APP'})).not.toBeChecked()
})

it('loads saved schema pairs visibly and removes a deselected target from the request',async()=>{
  const profile:Profile={id:'p',revision:1,updated_at:'',name:'Legacy',source:{kind:'ORACLE',connection_id:'source',schemas:['TTBP'],ref:'master',layout:'flat',roots:{}},target_ids:['source','target'],object_types:['TABLE'],excluded_object_types:[],exclude_system_generated:true,compare_physical_storage:false,source_length_semantics:'UNKNOWN',target_mappings:{source:[{source_schema:'TTBP',target_schema:'TTBP'}],target:[{source_schema:'TTBP',target_schema:'TTBP'}]}}
  const fetcher=vi.fn(async(_url:string,_options?:RequestInit)=>({ok:true,json:async()=>profile}))
  vi.stubGlobal('fetch',fetcher)
  render(<SchemaMappings connections={connections} mappings={[{...profile,target_mappings:profile.target_mappings!}]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Legacy eşleştirmesini düzenle'}))
  expect(screen.getByRole('checkbox',{name:'PROD: TTBP → TTBP'})).toBeChecked()
  await userEvent.click(screen.getByRole('button',{name:'Hedefi Kaldır 1'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  const data=JSON.parse(fetcher.mock.calls[0][1]!.body as string)
  expect(data.target_ids).toEqual(['target'])
  expect(data.target_mappings).toEqual({target:[{source_schema:'TTBP',target_schema:'TTBP'}]})
})
