/**
 * Şema Karşılaştırma çalışma ekranındaki sonuçları ve ilerleme birimlerini sınar.
 * @author Mehmet KARACAN
 * Date: 2026-11-06
 */
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { RunDetail } from './RunDetail'
import { setPreferences } from './preferences'

afterEach(()=>{cleanup();vi.unstubAllGlobals();setPreferences({locale:'tr'})})
const run={id:'fixture',actor:'admin',status:'PARTIAL',stage:'FINISHED',created_at:'2026-10-24T10:00:00Z',targets:[],spec:{profile:{name:'Test comparison',source:{kind:'ORACLE'},target_ids:['target']},connections:{target:{name:'Test target'}}}}
it.each([
  ['SOURCE_PARSE','tr','dosya'], ['SOURCE_CAPTURE','tr','nesne'], ['TARGET_CAPTURE','tr','nesne'],
  ['SOURCE_PARSE','en','files'], ['SOURCE_CAPTURE','en','objects'], ['TARGET_CAPTURE','en','objects'],
] as const)('uses the correct progress unit for %s in %s',async(stage,locale,unit)=>{
  setPreferences({locale})
  const active={...run,status:'RUNNING',stage,progress:{processed:10,total:100}}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/summary')?{source_total:1,counts:{},source_types:{}}:url.includes('/results/objects?')?{available:true,total:0,rows:[]}:active})))
  render(<RunDetail id="fixture" back={()=>{}}/>)
  expect(await screen.findByText(`10 / 100 ${unit}`)).toBeInTheDocument()
})
it('surfaces a failed API request instead of showing success',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('offline')))
  render(<RunDetail id="fixture" back={()=>{}}/>)
  expect(await screen.findByText('Sunucuya ulaşılamadı. Bağlantıyı kontrol edin.')).toBeInTheDocument()
})
it('uses one object workspace and does not repeat legacy operation tables or duration blocks',async()=>{
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/summary')?{source_total:1,counts:{},source_types:{}}:url.includes('/results/objects?')?{available:true,total:0,rows:[]}:run}))
  vi.stubGlobal('fetch',fetcher)
  render(<RunDetail id="fixture" back={()=>{}}/>)
  expect(await screen.findByRole('heading',{name:'Nesneler ve Farklar'})).toBeInTheDocument()
  expect(screen.queryByRole('heading',{name:'İşlemlerin tam listesi'})).not.toBeInTheDocument()
  await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>url.includes('/results/objects?'))).toBe(true))
  expect(fetcher.mock.calls.some(([url])=>url.includes('/operations?'))).toBe(false)
})
it('labels a service-dispatched Jenkins run and links only to its archive',async()=>{
  const remote={...run,executor:'JENKINS',report_available:true,archive_build_url:'https://jenkins.example.test/job/compare/55/'}
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/summary')?{source_total:1,counts:{},source_types:{}}:url.includes('/results/objects?')?{available:true,total:0,rows:[]}:remote})))
  render(<RunDetail id="fixture" back={()=>{}}/>)
  expect(await screen.findByText(/Jenkins Çalışması/)).toBeInTheDocument()
  expect(screen.queryByText(/Yerel Çalışma/)).not.toBeInTheDocument()
  expect(screen.getByRole('link',{name:'HTML raporu'})).toHaveAttribute('href','https://jenkins.example.test/job/compare/55/artifact/output/runs/build-55/index.html')
})
