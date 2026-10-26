import {render,screen} from '@testing-library/react'
import {expect,it} from 'vitest'
import {RunSchemaScope} from './RunSchemaScope'
import type {Run} from './api'

it('shows frozen connection and schema pairs without exposing login credentials',()=>{
  const run={spec:{profile:{source:{connection_id:'s',schemas:['APP','TTBP']},target_ids:['t'],target_mappings:{t:[{source_schema:'TTBP',target_schema:'TTBP'}]}},connections:{s:{name:'UAT'},t:{name:'PROD'}}}} as unknown as Run
  render(<RunSchemaScope run={run}/>)
  expect(screen.getByRole('table',{name:'Karşılaştırılan şemalar'})).toHaveTextContent('UAT / TTBP')
  expect(screen.getByRole('table')).toHaveTextContent('PROD / TTBP')
  expect(screen.getByRole('table')).not.toHaveTextContent('APP')
})
