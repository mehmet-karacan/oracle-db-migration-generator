import {render,screen,waitFor} from '@testing-library/react'
import {afterEach,expect,it,vi} from 'vitest'
import {RunSummary} from './RunSummary'
import type {Run} from './api'

afterEach(()=>vi.unstubAllGlobals())
const run={id:'r',status:'PARTIAL',targets:[],started_at:'2026-10-24T10:00:00Z',finished_at:'2026-10-24T10:18:40Z'} as unknown as Run
it('separates verified differences and unknown records in the summary',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({source_total:3805,source_inventory:'PARTIAL',source_types:{TABLE:1271},counts:{observed_differences:11949,ready_operations:1381,review_operations:655,blocked_operations:136},verified_difference_count:11946,unknown_count:3})})))
  render(<RunSummary run={run}/>)
  await screen.findByText('11.946')
  expect(screen.queryByText('11.949')).not.toBeInTheDocument()
  expect(screen.getByText('3.805')).toBeInTheDocument()
  expect(screen.getByText('Kaynak envanteri eksik. Nesne sayısı gözlenen alt sınırdır.')).toBeInTheDocument()
})
it('keeps unavailable counts unknown instead of showing zero',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({source_total:null,source_inventory:'UNAVAILABLE',source_types:{},counts:null,verified_difference_count:null,unknown_count:null})})))
  render(<RunSummary run={run}/>)
  await waitFor(()=>expect(screen.getAllByText('Bilinmiyor')).toHaveLength(6))
  expect(screen.queryByText('0')).not.toBeInTheDocument()
})

it('includes total duration as one of the compact summary cards',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({source_total:1,source_inventory:'COMPLETE',source_types:{},counts:{},verified_difference_count:0,unknown_count:0})})))
  const {container}=render(<RunSummary run={run}/>)
  await screen.findByText('Toplam Süre')
  expect(container.querySelectorAll('.summary-metric')).toHaveLength(7)
  expect(container.querySelector('.summary-metric')?.textContent).toContain('18 dk 40 sn')
})
