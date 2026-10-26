import {chooseOption} from './test-setup'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import App from './App'
import { ProjectSwitcher } from './ProjectSwitcher'

afterEach(()=>vi.unstubAllGlobals())
it('opens a keyboard accessible project menu and selects another project',async()=>{
  const onSelect=vi.fn()
  render(<ProjectSwitcher projects={[{id:'p1',revision:1,name:'SKY',code:'SKY'},{id:'p2',revision:1,name:'Other',code:'OTHER'}]} selected="p1" onSelect={onSelect} onCreated={()=>{}}/>)
  screen.getByRole('combobox',{name:'Proje'}).focus()
  await userEvent.keyboard('{ArrowDown}')
  expect(screen.getByRole('listbox')).toBeInTheDocument()
  await userEvent.keyboard('{ArrowDown}{Enter}')
  expect(onSelect).toHaveBeenCalledWith('p2')
})
it('scopes requests to the selected project and exposes one shared workspace',async()=>{
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/api/session'?{role:'shared',user:'shared',mode:'local'}:url==='/api/projects'?[{id:'p1',name:'SKY',code:'SKY'},{id:'p2',name:'Other',code:'OTHER'}]:url==='/api/settings'?{revision:0}:[]}))
  vi.stubGlobal('fetch',fetcher)
  render(<App/>)
  const selector=await screen.findByLabelText('Proje')
  await chooseOption(selector,'p2')
  await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>url==='/api/connections?project_id=p2')).toBe(true))
  expect(fetcher.mock.calls.some(([url])=>url==='/api/profiles?project_id=p2')).toBe(true)
  expect(fetcher.mock.calls.some(([url])=>url==='/api/schema-mappings?project_id=p2')).toBe(true)
  expect(fetcher.mock.calls.some(([url])=>url==='/api/runs?project_id=p2')).toBe(true)
  expect(screen.getByText('Şema Karşılaştırma')).toBeInTheDocument()
  expect(screen.queryByText('Yönetici')).not.toBeInTheDocument()
  expect(screen.queryByText('local-admin')).not.toBeInTheDocument()
})

it('creates a project through the dialog and selects the persisted record',async()=>{
  const created={id:'new-project',revision:1,name:'Second project',code:'SECOND'}
  const fetcher=vi.fn(async()=>({ok:true,json:async()=>created})),onCreated=vi.fn()
  vi.stubGlobal('fetch',fetcher)
  render(<ProjectSwitcher projects={[]} selected="" onSelect={()=>{}} onCreated={onCreated}/>)
  await userEvent.click(screen.getByRole('button',{name:'Proje ekle'}))
  await userEvent.type(screen.getByLabelText('Proje Adı'),'Second project')
  await userEvent.type(screen.getByLabelText('Proje Kodu'),'second')
  await userEvent.click(screen.getByRole('button',{name:'Projeyi oluştur'}))
  await waitFor(()=>expect(onCreated).toHaveBeenCalledWith(created))
  expect(fetcher).toHaveBeenCalledWith('/api/projects',expect.objectContaining({body:JSON.stringify({name:'Second project',code:'SECOND'})}))
})
