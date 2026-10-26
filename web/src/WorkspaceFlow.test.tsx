import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import App from './App'
import {ComparisonForm} from './ComparisonForm'
import {Connections} from './Connections'
import {chooseOption} from './test-setup'

afterEach(()=>vi.unstubAllGlobals())
it('has one clear page heading, a named application and a company footer',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/api/session'?{role:'shared',mode:'local'}:url==='/api/projects'?[{id:'p',name:'SKY',code:'SKY'}]:url==='/api/settings'?{revision:0}:[]})))
  render(<App/>);await screen.findByRole('heading',{name:'Yeni karşılaştırma'})
  expect(screen.queryByText('YEREL GELİŞTİRME')).not.toBeInTheDocument()
  expect(screen.queryByText('ORACLE ŞEMA KARŞILAŞTIRMA')).not.toBeInTheDocument()
  expect(screen.getByText('Şema Karşılaştırma')).toBeInTheDocument()
  expect(screen.getByRole('contentinfo')).toHaveTextContent('© 2026 İnnova Bilişim Çözümleri A.Ş.')
  expect(screen.queryByText('KARŞILAŞTIRMA PROFİLİ')).not.toBeInTheDocument()
  expect((await screen.findByLabelText('Profil Adı')).closest('.profile-setup')).not.toBeNull()
})

it('first configures a password, then authenticates the named shared user',async()=>{
  let setup=true,logged=false
  const fetcher=vi.fn(async(url:string,_options?:RequestInit)=>({ok:true,json:async()=>{
    if(url==='/api/auth/status')return {password_login:true,setup_required:setup}
    if(url==='/api/auth/setup'){setup=false;return {configured:true}}
    if(url==='/api/auth/login'){logged=true;return {authenticated:true}}
    if(url==='/api/session')return logged?{user:'mkaracan',display_name:'Mehmet KARACAN',role:'shared',mode:'password'}:null
    if(url==='/api/projects')return [{id:'p',name:'SKY',code:'SKY'}]
    if(url==='/api/settings')return {revision:0}
    return []
  }}))
  vi.stubGlobal('fetch',fetcher);render(<App/>)
  await screen.findByRole('heading',{name:'İlk Giriş'})
  await userEvent.type(screen.getByLabelText('Parola'),'test-only-password-123')
  await userEvent.type(screen.getByLabelText('Parolayı Doğrula'),'test-only-password-123')
  await userEvent.click(screen.getByRole('button',{name:'Parolayı Belirle'}))
  await screen.findByRole('heading',{name:'Giriş Yap'})
  expect(screen.getByLabelText('Kullanıcı Adı')).toHaveValue('mkaracan')
  expect(screen.getByLabelText('Parola')).toHaveValue('')
  await userEvent.type(screen.getByLabelText('Parola'),'test-only-password-123')
  await userEvent.click(screen.getByRole('button',{name:'Giriş Yap'}))
  await screen.findByText('Mehmet KARACAN')
  expect(fetcher.mock.calls.some(([url,options])=>url==='/api/auth/login'&&JSON.parse(options!.body as string).username==='mkaracan')).toBe(true)
})

it('does not launch a run after its project form was unmounted during profile saving',async()=>{
  let finish:(value:unknown)=>void=()=>{}
  const fetcher=vi.fn(()=>new Promise(resolve=>{finish=resolve}))
  vi.stubGlobal('fetch',fetcher)
  const mapping={id:'m',revision:1,name:'Scope',source:{kind:'ORACLE' as const,connection_id:'s',schemas:['APP']},target_ids:['t'],target_mappings:{t:[{source_schema:'APP',target_schema:'APP'}]}}
  const view=render(<ComparisonForm projectId="old" connections={[]} profiles={[]} mappings={[mapping]} admin onSaved={()=>{}} onStarted={()=>{}}/>)
  await chooseOption(screen.getByLabelText('Şema Eşleştirmesi'),'m')
  await userEvent.click(screen.getByRole('button',{name:'Karşılaştırmayı başlat'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(1));view.unmount()
  finish({ok:true,json:async()=>({id:'saved'})})
  await new Promise(resolve=>setTimeout(resolve,0))
  expect(fetcher).toHaveBeenCalledTimes(1)
})

it('does not test a saved connection after switching away from its project',async()=>{
  let finish:(value:unknown)=>void=()=>{}
  const fetcher=vi.fn(()=>new Promise(resolve=>{finish=resolve}))
  vi.stubGlobal('fetch',fetcher)
  const connection={id:'c',name:'Public Git',revision:1,updated_at:'',kind:'GIT' as const,repository:'https://example.test/repo.git',port:1521,driver_mode:'thin' as const,allowed_users:[],credential_configured:false}
  const view=render(<Connections projectId="old" connections={[connection]} admin refresh={()=>{}}/>)
  await userEvent.click(screen.getByRole('button',{name:'Düzenle'}))
  await userEvent.click(screen.getByRole('button',{name:'Kaydet ve test et'}))
  await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(1));view.unmount()
  finish({ok:true,json:async()=>connection})
  await new Promise(resolve=>setTimeout(resolve,0))
  expect(fetcher).toHaveBeenCalledTimes(1)
})

it('ignores the old project response after selecting another project',async()=>{
  let finish:(value:unknown)=>void=()=>{}
  const connection=(id:string,name:string)=>({id,name,kind:'GIT',repository:'https://example.test/repo.git',credential_configured:false})
  const fetcher=vi.fn(async(url:string,_options?:RequestInit)=>{
    if(url==='/api/connections?project_id=p1')return new Promise(resolve=>{finish=resolve})
    return {ok:true,json:async()=>url==='/api/session'?{role:'shared',mode:'local'}:url==='/api/projects'?[{id:'p1',name:'SKY',code:'SKY'},{id:'p2',name:'Other',code:'OTHER'}]:url==='/api/settings'?{revision:0}:url==='/api/connections?project_id=p2'?[connection('new','Other Project Repo')]:[]}
  })
  vi.stubGlobal('fetch',fetcher);render(<App/>)
  await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>url==='/api/connections?project_id=p1')).toBe(true))
  await chooseOption(screen.getByRole('combobox',{name:'Proje'}),'p2')
  await userEvent.click(screen.getByRole('button',{name:'Bağlantılar'}))
  await screen.findByText('Other Project Repo')
  finish({ok:true,json:async()=>[connection('old','Old Project Repo')]})
  await new Promise(resolve=>setTimeout(resolve,0))
  expect(screen.queryByText('Old Project Repo')).not.toBeInTheDocument()
  expect(fetcher.mock.calls.find(([url])=>url==='/api/connections?project_id=p2')?.[1]).toEqual(expect.objectContaining({headers:{'X-ODMG-Project':'p2'}}))
})
