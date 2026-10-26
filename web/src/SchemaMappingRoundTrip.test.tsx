import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import {SchemaMappings} from './SchemaMappings'
import {chooseOption} from './test-setup'
import type {Connection,SchemaMapping} from './api'

afterEach(()=>vi.unstubAllGlobals())
it('round-trips distinct target pairs and requires a new selection after a persisted removal',async()=>{
  const base={revision:1,updated_at:'',port:1521,driver_mode:'thin' as const,allowed_users:[],credential_configured:false,project_id:'project'}
  const connections:Connection[]=[{...base,id:'git',name:'Source',kind:'GIT',repository:'https://example.invalid/repo.git'},
    {...base,id:'a',name:'Target A',kind:'ORACLE'},{...base,id:'b',name:'Target B',kind:'ORACLE'}]
  let saved:SchemaMapping|undefined
  const fetcher=vi.fn(async(_url:string,options?:RequestInit)=>{
    const payload=JSON.parse(options!.body as string)
    saved={...payload,id:'mapping',revision:(saved?.revision||0)+1}
    return {ok:true,json:async()=>saved}
  })
  vi.stubGlobal('fetch',fetcher)
  const mount=()=>render(<SchemaMappings projectId="project" connections={connections} mappings={saved?[saved]:[]} admin refresh={()=>{}}/>)
  let view=mount()
  await userEvent.click(screen.getByRole('button',{name:'Yeni eşleştirme'}))
  await userEvent.type(screen.getByLabelText('Eşleştirme Adı'),'Multi targets')
  await chooseOption(screen.getByLabelText('Kaynak Bağlantısı'),'git')
  await userEvent.type(screen.getByLabelText('Kaynak Şemaları'),'TEST_SCHEMA, TEST_AUX')
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı'),'a')
  await userEvent.click(screen.getByRole('checkbox',{name:'Target A: TEST_SCHEMA → TEST_SCHEMA'}))
  await userEvent.click(screen.getByRole('button',{name:'Hedef Ekle'}))
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı 2'),'b')
  await userEvent.click(screen.getByRole('checkbox',{name:'Target B: TEST_AUX → TEST_AUX'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(1))
  expect(saved!.project_id).toBe('project')
  const expected={a:[{source_schema:'TEST_SCHEMA',target_schema:'TEST_SCHEMA'}],b:[{source_schema:'TEST_AUX',target_schema:'TEST_AUX'}]}
  expect(saved!.target_mappings).toEqual(expected)

  view.unmount();view=mount()
  await userEvent.click(screen.getByRole('button',{name:'Multi targets eşleştirmesini düzenle'}))
  expect(screen.getByRole('checkbox',{name:'Target A: TEST_SCHEMA → TEST_SCHEMA'})).toBeChecked()
  expect(screen.getByRole('checkbox',{name:'Target A: TEST_AUX → TEST_AUX'})).not.toBeChecked()
  expect(screen.getByRole('checkbox',{name:'Target B: TEST_AUX → TEST_AUX'})).toBeChecked()
  expect(screen.getByRole('checkbox',{name:'Target B: TEST_SCHEMA → TEST_SCHEMA'})).not.toBeChecked()
  await userEvent.click(screen.getByRole('button',{name:'Hedefi Kaldır 2'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2))
  expect(saved!.target_ids).toEqual(['a'])
  expect(saved!.target_mappings).toEqual({a:expected.a})

  view.unmount();view=mount()
  await userEvent.click(screen.getByRole('button',{name:'Multi targets eşleştirmesini düzenle'}))
  await userEvent.click(screen.getByRole('button',{name:'Hedef Ekle'}))
  await chooseOption(screen.getByLabelText('Hedef Bağlantısı 2'),'b')
  expect(screen.getByRole('checkbox',{name:'Target B: TEST_AUX → TEST_AUX'})).not.toBeChecked()
  expect(screen.getByRole('checkbox',{name:'Target B: TEST_SCHEMA → TEST_SCHEMA'})).not.toBeChecked()
  expect(screen.getByRole('checkbox',{name:'Target A: TEST_SCHEMA → TEST_SCHEMA'})).toBeChecked()
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  expect(screen.getByRole('alert')).toHaveTextContent('Target B için şema eşleştirmesi seçin')
  expect(fetcher).toHaveBeenCalledTimes(2)
  await userEvent.click(screen.getByRole('checkbox',{name:'Target B: TEST_AUX → TEST_AUX'}))
  await userEvent.click(screen.getByRole('button',{name:'Eşleştirmeyi kaydet'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(3))
  expect(saved!.revision).toBe(3)
  expect(saved!.target_mappings).toEqual(expected)
  view.unmount();mount()
  await userEvent.click(screen.getByRole('button',{name:'Multi targets eşleştirmesini düzenle'}))
  expect(screen.getAllByRole('checkbox').filter(e=>e.getAttribute('data-state')==='checked')).toHaveLength(2)
  expect(screen.getByRole('checkbox',{name:'Target B: TEST_AUX → TEST_AUX'})).toBeChecked()
},15000)
