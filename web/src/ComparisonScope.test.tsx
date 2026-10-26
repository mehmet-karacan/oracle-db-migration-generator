import {chooseOption} from './test-setup'
import { act,render,screen,waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach,expect,it,vi } from 'vitest'
import { ComparisonForm } from './ComparisonForm'
import type { Profile } from './api'

afterEach(()=>vi.unstubAllGlobals())
it('does not navigate the new project when a previous project start completes late',async()=>{
  const profile:Profile={id:'p',revision:1,updated_at:'',name:'First',source:{kind:'GIT',connection_id:'g',schemas:['APP'],ref:'master',layout:'flat',roots:{}},target_ids:['t'],object_types:['TABLE'],excluded_object_types:[],exclude_system_generated:true,compare_physical_storage:false,source_length_semantics:'UNKNOWN'}
  let resolveRun!:(value:unknown)=>void
  const pending=new Promise(resolve=>{resolveRun=resolve})
  const fetcher=vi.fn(async()=>({ok:true,json:async()=>await pending}))
  vi.stubGlobal('fetch',fetcher)
  const onStarted=vi.fn(),view=render(<ComparisonForm connections={[]} profiles={[profile]} admin={false} onSaved={()=>{}} onStarted={onStarted}/>)
  await chooseOption(screen.getByLabelText('Kayıtlı profil'),'p')
  await userEvent.click(screen.getByRole('button',{name:'Karşılaştırmayı başlat'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalled())
  view.unmount() // A different project now owns the page.
  await act(async()=>{resolveRun({id:'old-project-run'});await pending})
  expect(onStarted).not.toHaveBeenCalled()
})
