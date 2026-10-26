import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,beforeEach,expect,it,vi} from 'vitest'
import {UiPreferences} from './UiPreferences'
import {setPreferences,translate} from './preferences'

beforeEach(()=>{setPreferences({locale:'tr',theme:'light'})})
afterEach(()=>vi.restoreAllMocks())

it('switches language and theme and persists only UI preferences',async()=>{
  render(<UiPreferences/>)
  await userEvent.click(screen.getByRole('button',{name:'English'}))
  await waitFor(()=>expect(document.documentElement.lang).toBe('en'))
  expect(translate('Bağlantılar')).toBe('Connections')
  await userEvent.click(screen.getByRole('button',{name:'Dark theme'}))
  await waitFor(()=>expect(document.documentElement.dataset.theme).toBe('dark'))
  expect(screen.getByRole('button',{name:'Dark theme'})).toHaveAttribute('aria-pressed','true')
  expect(JSON.parse(localStorage.getItem('odmg.ui.preferences.v1')!)).toEqual({locale:'en',theme:'dark'})
  expect(screen.getByRole('button',{name:'English'})).toHaveAttribute('aria-pressed','true')
})

it('keeps preference controls usable when local storage is unavailable',async()=>{
  vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked')})
  render(<UiPreferences/>)
  await userEvent.click(screen.getByRole('button',{name:'English'}))
  expect(translate('Bağlantılar')).toBe('Connections')
  expect(screen.getByRole('button',{name:'Dark theme'})).toBeEnabled()
})
