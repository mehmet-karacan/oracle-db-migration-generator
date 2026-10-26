import {chooseOption} from './test-setup'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { ComparisonForm } from './ComparisonForm'

describe('Comparison form', () => {
  it('requires a saved mapping and shows Git settings only for a Git source', async () => {
    const scope={revision:1,target_ids:['t'],target_mappings:{t:[{source_schema:'APP',target_schema:'APP'}]}}
    render(<ComparisonForm connections={[]} profiles={[]} mappings={[
      {...scope,id:'git',name:'Git mapping',source:{kind:'GIT',connection_id:'g',schemas:['APP']}},
      {...scope,id:'oracle',name:'Oracle mapping',source:{kind:'ORACLE',connection_id:'o',schemas:['APP']}}
    ]} admin onSaved={vi.fn()} onStarted={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Profili kaydet' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Şema eşleştirmesi seçin')
    await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'git')
    expect(screen.getByLabelText('Branch, tag veya commit')).toBeInTheDocument()
    await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'oracle')
    expect(screen.queryByLabelText('Branch, tag veya commit')).not.toBeInTheDocument()
  })
})
it('sends the explicitly selected local executor with the current project',async()=>{
  const scope={revision:1,target_ids:['t'],target_mappings:{t:[{source_schema:'APP',target_schema:'APP'}]}}
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/api/profiles'?{id:'p'}:{id:'r'}}))
  vi.stubGlobal('fetch',fetcher)
  try{
    render(<ComparisonForm projectId="project-a" localExecution connections={[]} profiles={[]} mappings={[{...scope,id:'oracle',name:'Oracle mapping',source:{kind:'ORACLE',connection_id:'o',schemas:['APP']}}]} admin onSaved={vi.fn()} onStarted={vi.fn()}/>)
    await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'oracle')
    await chooseOption(screen.getByLabelText('Çalıştırma Yeri'),'LOCAL')
    await userEvent.click(screen.getByRole('button',{name:'Karşılaştırmayı başlat'}))
    const request=fetcher.mock.calls.find(([url])=>url==='/api/runs')
    expect(request).toBeDefined()
    expect(JSON.parse((request as unknown as [string,RequestInit])[1].body as string)).toEqual({profile_id:'p',project_id:'project-a',executor:'LOCAL'})
  }finally{vi.unstubAllGlobals()}
})

it('loads portable source filters and selects the local executor visibly',async()=>{
  const source={id:'s',revision:1,updated_at:'',name:'Imported',kind:'SNAPSHOT' as const,port:1521,driver_mode:'thin' as const,allowed_users:[],credential_configured:false,
    capture_summary:{sha256:'a'.repeat(64),captured_at:'2026-10-25T12:00:00Z',status:'COMPLETE',inventory_complete:true,selected_objects:1,filter:{object_types:['TABLE'],object_names:['DEMO'],data_types:['NUMBER'],include_related:true}}}
  render(<ComparisonForm localExecution connections={[source]} profiles={[]} mappings={[{id:'m',revision:1,name:'Imported mapping',source:{kind:'SNAPSHOT',connection_id:'s',schemas:['APP']},target_ids:['t'],target_mappings:{t:[{source_schema:'APP',target_schema:'APP'}]}}]} admin onSaved={vi.fn()} onStarted={vi.fn()}/> )
  await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'m')
  expect(screen.getByLabelText('Nesne Adları')).toHaveValue('DEMO')
  expect(screen.getByLabelText('Kolon Veri Tipleri')).toHaveValue('NUMBER')
  expect(screen.getByLabelText('Çalıştırma Yeri')).toHaveTextContent('Bu Bilgisayar')
  expect(screen.queryByLabelText('Branch, tag veya commit')).not.toBeInTheDocument()
})
