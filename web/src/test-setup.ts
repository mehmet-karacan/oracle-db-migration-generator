import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import {screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {setProjectScope} from './api'
import {setPreferences} from './preferences'

Element.prototype.hasPointerCapture=()=>false
Element.prototype.setPointerCapture=()=>{}
Element.prototype.releasePointerCapture=()=>{}
Element.prototype.scrollIntoView=()=>{}
afterEach(()=>{cleanup();setProjectScope('');setPreferences({locale:'tr',theme:'light'})})
export async function chooseOption(element:HTMLElement,value:string){
  await userEvent.click(element)
  const option=screen.getAllByRole('option').find(item=>item.dataset.value===value)
  if(!option)throw new Error(`Choice option not found: ${value}`)
  await userEvent.click(option)
}
