import {render,screen} from '@testing-library/react'
import {afterEach,expect,it,vi} from 'vitest'
import {SqlViewer} from './SqlViewer'

afterEach(()=>vi.unstubAllGlobals())
it('shows the original local SQL with quoted identifiers and formatting intact',async()=>{
  const sql='CREATE TABLE "TTBP"."DEMO" (\n    "TITLE" VARCHAR2(80)\n);\n'
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,text:async()=>sql})))
  render(<SqlViewer file={{title:'TTBP.DEMO',url:'/api/runs/r/artifacts/targets/t/demo.sql?project_id=p'}} onClose={()=>{}}/>)
  const code=await screen.findByTestId('sql-content')
  expect(code.textContent).toBe(sql)
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
})
it('keeps Jenkins SQL in its archive without an unauthorized cross-origin fetch',async()=>{
  const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher)
  render(<SqlViewer file={{title:'Archived SQL',url:'https://jenkins.example.test/job/compare/55/artifact/demo.sql/*view*/'}} onClose={()=>{}}/>)
  expect(await screen.findByRole('link',{name:'Jenkins Arşivinde Aç'})).toHaveAttribute('href','https://jenkins.example.test/job/compare/55/artifact/demo.sql/*view*/')
  expect(fetcher).not.toHaveBeenCalled()
})
