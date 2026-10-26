import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import App from './App'
import {valueText} from './resultApi'
import {typeLabel} from './api'
import {setPreferences,translate} from './preferences'

afterEach(()=>vi.unstubAllGlobals())
it('updates the shared screens and connection form without changing saved names or credentials',async()=>{
  const connection={id:'c',revision:1,kind:'ORACLE',name:'PROD · TTBP',host:'db.example',port:1521,sid:'TTBP',driver_mode:'thin',credential_configured:true,allowed_users:[]}
  const fetcher=vi.fn(async(url:string,_options?:RequestInit)=>({ok:true,json:async()=>url==='/api/session'?{role:'shared',mode:'local'}:url==='/api/projects'?[{id:'p',name:'SKY',code:'SKY'}]:url.includes('/access-info?')?{username:'READER'}:url.startsWith('/api/connections?')?[connection]:url==='/api/settings'?{revision:0}:[]}))
  vi.stubGlobal('fetch',fetcher)
  render(<App/>)
  await screen.findByRole('button',{name:'Bağlantılar'})
  await userEvent.click(screen.getByRole('button',{name:'English'}))
  await userEvent.click(screen.getByRole('button',{name:'Dark theme'}))
  await userEvent.click(screen.getByRole('button',{name:'Connections'}))
  await screen.findByText('PROD - TTBP')
  expect(screen.getByRole('tab',{name:'Schema Mappings'})).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button',{name:'Edit'}))
  await screen.findByDisplayValue('READER')
  const type=screen.getByLabelText('Connection Type'),name=screen.getByLabelText('Connection Name')
  expect(type.compareDocumentPosition(name)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(screen.getByLabelText('Password')).toHaveValue('')
  expect(name).toHaveValue('PROD - TTBP')
  expect(connection.name).toBe('PROD · TTBP')
  expect(fetcher.mock.calls.every(([,options])=>!options?.method&&!options?.body)).toBe(true)
  await waitFor(()=>expect(document.documentElement.dataset.theme).toBe('dark'))
})

it('keeps SQL values unchanged and translates transient messages back to Turkish',()=>{
  setPreferences({locale:'en'})
  const message=translate('{0} için şema eşleştirmesi seçin.',{0:'PROD'})
  expect(message).toBe('Select a schema mapping for PROD.')
  const sql='SELECT\n    COL\nFROM\n    APP.T;'
  expect(valueText({state:'KNOWN',value:sql})).toBe(sql)
  setPreferences({locale:'tr'})
  expect(translate(message)).toBe('PROD için şema eşleştirmesi seçin.')
})

it('translates every supported object type including triggers and grants',()=>{
  setPreferences({locale:'en'})
  expect(typeLabel('TRIGGER')).toBe('Trigger')
  expect(typeLabel('GRANT')).toBe('Grant')
})

it('updates an API error when the selected language changes',async()=>{
  const connection={id:'c',revision:1,kind:'GIT',name:'Test Git',repository:'https://example.test/repo.git',credential_configured:true,allowed_users:[]}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:!url.endsWith('/test'),status:url.endsWith('/test')?422:200,json:async()=>url.endsWith('/test')?{error_code:'GIT_ACCESS_FAILED'}:url==='/api/session'?{role:'shared',mode:'local'}:url==='/api/projects'?[{id:'p',name:'SKY',code:'SKY'}]:url.startsWith('/api/connections?')?[connection]:url==='/api/settings'?{revision:0}:[]})))
  render(<App/>)
  await screen.findByRole('button',{name:'Bağlantılar'})
  await userEvent.click(screen.getByRole('button',{name:'English'}))
  await userEvent.click(screen.getByRole('button',{name:'Connections'}))
  await userEvent.click(await screen.findByRole('button',{name:'Test connection'}))
  expect(await screen.findByRole('alert')).toHaveTextContent('Cannot access the Git repository')
  await userEvent.click(screen.getByRole('button',{name:'Türkçe'}))
  expect(screen.getByRole('alert')).toHaveTextContent('Git deposuna erişilemedi')
})
