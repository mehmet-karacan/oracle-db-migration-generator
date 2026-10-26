import {expect,it} from 'vitest'
import {alignLines} from './lineDiff'
import {render,screen} from '@testing-library/react'
import {DefinitionComparison} from './DefinitionComparison'
import {afterEach,vi} from 'vitest'
afterEach(()=>vi.unstubAllGlobals())
it('aligns source and target while preserving quotes, literals, repeated lines and final newline',()=>{
 const source='CREATE TABLE "APP"."A" (\n  "N" VARCHAR2(100),\n  "X" VARCHAR2(20) DEFAULT \'a . b\'\n);\n'
 const target=source.replace('(100)','(50)')
 const result=alignLines(source,target)
 expect(result.rows.filter(row=>row.source).map(row=>row.source!.text).join('\n')).toBe(source)
 expect(result.rows.filter(row=>row.target).map(row=>row.target!.text).join('\n')).toBe(target)
 expect(result.rows.filter(row=>row.kind==='changed')).toHaveLength(1)
 expect(alignLines('a\na\nb\n','a\nb\nb\n').rows.filter(row=>row.source).map(row=>row.source!.text).join('\n')).toBe('a\na\nb\n')
})
it('bounds large line alignment and still retains every original line',()=>{
 const source=Array.from({length:1800},(_,i)=>'S'+i).join('\n'),target=Array.from({length:1800},(_,i)=>'T'+i).join('\n')
 const result=alignLines(source,target)
 expect(result.coarse).toBe(true)
 expect(result.rows.map(row=>row.source?.text).join('\n')).toBe(source)
 expect(result.rows.map(row=>row.target?.text).join('\n')).toBe(target)
})
it('shows archived definitions without fetching remote SQL or inventing a comparison',async()=>{
 const fetcher=vi.fn(async()=>({ok:true,json:async()=>({source:{state:'ARCHIVED'},target:{state:'ARCHIVED'},archive_url:'https://jenkins.example.test/job/compare/55/'})}));vi.stubGlobal('fetch',fetcher)
 render(<DefinitionComparison runId="r" targetId="t" objectKey={'a'.repeat(64)} sourceName="SKY" targetName="PROD"/>)
 expect(await screen.findByText('Özgün Tanımlar Jenkins Arşivinde')).toBeInTheDocument()
 expect(screen.queryByText('Tanımlar Aynı')).not.toBeInTheDocument()
 expect(fetcher).toHaveBeenCalledTimes(1)
 expect(screen.getByRole('link',{name:'Jenkins Arşivinde Aç'})).toHaveAttribute('href','https://jenkins.example.test/job/compare/55/')
})
it('renders available original definitions and marks just the changed lines',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({source:{state:'AVAILABLE',text:'BEGIN\n  "A" := 100;\nEND;\n'},target:{state:'AVAILABLE',text:'BEGIN\n  "A" := 50;\nEND;\n'}})})))
 const {container}=render(<DefinitionComparison runId="r" targetId="t" objectKey={'a'.repeat(64)} sourceName="SKY" targetName="PROD"/>)
 expect(await screen.findByText('"A" := 100;')).toBeInTheDocument()
 expect(screen.getByText('"A" := 50;')).toBeInTheDocument()
 expect(container.querySelectorAll('.line-changed')).toHaveLength(1)
})
it('keeps a bounded line window when scrolling a long definition',async()=>{
 const sql=Array.from({length:2500},(_,i)=>'LINE_'+i).join('\n')
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({source:{state:'AVAILABLE',text:sql},target:{state:'AVAILABLE',text:sql+'\nEND;'}})})))
 const {container}=render(<DefinitionComparison runId="r" targetId="t" objectKey={'a'.repeat(64)} sourceName="SKY" targetName="PROD"/>)
 await screen.findAllByText('LINE_0')
 const scroll=screen.getByLabelText('Özgün Tanım Satırları')
 const {fireEvent}=await import('@testing-library/react')
 fireEvent.scroll(scroll,{target:{scrollTop:32000}})
 expect(container.querySelectorAll('tbody tr').length).toBeLessThanOrEqual(302)
 expect(screen.queryByText('LINE_0')).not.toBeInTheDocument()
 expect(screen.getAllByText('LINE_999')).toHaveLength(2)
})
