import { act,render,screen,waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach,expect,it,vi } from 'vitest'
import { Connections } from './Connections'
import type { Connection } from './api'

const git:Connection={id:'git',revision:2,updated_at:'',name:'Bitbucket',kind:'GIT',repository:'https://git.example/scm/app/source.git',port:1521,driver_mode:'thin',allowed_users:[],credential_configured:true}
afterEach(()=>vi.unstubAllGlobals())

it('explains Git token creation and restores the username without returning the token',async()=>{
  const fetcher=vi.fn(async(url:string,_options?:RequestInit)=>({ok:true,json:async()=>url.endsWith('/access-info?revision=2')?{username:'test-user',credential_configured:true}:({...git,revision:3})}))
  vi.stubGlobal('fetch',fetcher)
  render(<Connections connections={[git]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Düzenle'}))
  expect(await screen.findByDisplayValue('test-user')).toBeInTheDocument()
  expect(screen.getByLabelText('Git Kullanıcı Adı')).toHaveValue('test-user')
  expect(screen.getByLabelText('Erişim Token’ı')).toHaveValue('')
  expect(screen.getByText(/HTTP access tokens/)).toBeInTheDocument()
  expect(screen.getByText(/Token kayıtlı/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button',{name:'Kaydet'}))
  const body=JSON.parse(fetcher.mock.calls.find(([url])=>url==='/api/connections')![1]!.body as string)
  expect(body.username).toBe('test-user')
  expect(body.password).toBeNull()
})

it('does not replace user edits with a late response after the dialog closes',async()=>{
  let resolve!:(value:unknown)=>void
  const pending=new Promise(r=>{resolve=r})
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>await pending})))
  render(<Connections connections={[git]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Düzenle'}))
  expect(screen.getByRole('button',{name:'Kaydet'})).toBeDisabled()
  await userEvent.keyboard('{Escape}')
  await userEvent.click(screen.getByRole('button',{name:'Bağlantı ekle'}))
  await userEvent.type(screen.getByLabelText('Kullanıcı Adı'),'new-user')
  await act(async()=>{resolve({username:'old-user',credential_configured:true});await pending})
  expect(screen.getByLabelText('Kullanıcı Adı')).toHaveValue('new-user')
  expect(screen.getByLabelText('Parola')).toHaveValue('')
})

it('keeps save disabled when stored access details cannot be loaded',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:409,json:async()=>({detail:'REVISION_CONFLICT'})})))
  render(<Connections connections={[git]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Düzenle'}))
  await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('başka bir kullanıcı'))
  expect(screen.getByRole('button',{name:'Kaydet'})).toBeDisabled()
})
