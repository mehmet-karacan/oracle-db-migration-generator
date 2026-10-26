import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {projectPlan} from './ui_result_projection.mjs'

test('browser projection preserves recorded direction and removes whole SQL definitions',()=>{
  const plan=JSON.parse(readFileSync(new URL('../examples/plan.example.json',import.meta.url),'utf8'))
  plan.differences.push({...plan.differences[0],id:'body',property_path:'/definition',before:{state:'KNOWN',value:'SECRET BODY'},after:{state:'KNOWN',value:'NEW SECRET BODY'}})
  const original=JSON.stringify(plan)
  const view=projectPlan(plan)
  assert.equal(view.differences[0].source.value,80)
  assert.equal(view.differences[0].target.value,40)
  assert.equal(view.differences[1].source.omitted,true)
  assert.equal(JSON.stringify(view).includes('SECRET'),false)
  assert.equal('before' in view.operations[0],false)
  assert.equal(plan.differences[1].after.value,'NEW SECRET BODY')
  assert.equal(JSON.stringify(plan),original)
})

test('restores original UTF-8 bytes when Jenkins displays JSON as windows-1254',async()=>{
  const {decodeDocumentText}=await import('./ui_result_projection.mjs')
  const original=JSON.stringify({reason:'Aynı tip, bağımlılık ve genişletme koşulu; İŞ ğüşıöç',literal:'Ã¶'})
  const displayed=new TextDecoder('windows-1254').decode(new TextEncoder().encode(original))
  assert.notEqual(displayed,original)
  assert.equal(decodeDocumentText(displayed,'windows-1254'),original)
  assert.equal(decodeDocumentText(original,'UTF-8'),original)
  assert.throws(()=>decodeDocumentText(displayed,'unknown-charset'))
})

test('recovers only projected metadata without requiring raw SQL to leave the DOM',async()=>{
  const {decodeProjectedView}=await import('./ui_result_projection.mjs')
  const original={reason:'Türkçe İŞ ğüşıöç 😀 %100',source:{state:'KNOWN',value:'Ã¶'},target:{state:'KNOWN',value:null},rows:[{name:'ÖRNEK'}]}
  const displayed=new TextDecoder('windows-1254').decode(new TextEncoder().encode(JSON.stringify(original)))
  assert.deepEqual(decodeProjectedView(JSON.parse(displayed),'windows-1254'),original)
})
