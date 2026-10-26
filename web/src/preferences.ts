import {useSyncExternalStore} from 'react'
import {english,turkishLabels} from './translations'

export type UiPreferences={locale:'tr'|'en';theme:'light'|'dark'}
const key='odmg.ui.preferences.v1'
const defaults:UiPreferences={locale:'tr',theme:'light'}
function read():UiPreferences{
  try{const value=JSON.parse(localStorage.getItem(key)||'null');return {locale:value?.locale==='en'?'en':'tr',theme:value?.theme==='dark'?'dark':'light'}}catch{return {...defaults}}
}
let current=read()
const listeners=new Set<()=>void>()
function subscribe(listener:()=>void){listeners.add(listener);return()=>{listeners.delete(listener)}}
export function setPreferences(value:Partial<UiPreferences>){
  current={locale:value.locale==='en'?'en':value.locale==='tr'?'tr':current.locale,theme:value.theme==='dark'?'dark':value.theme==='light'?'light':current.theme}
  try{localStorage.setItem(key,JSON.stringify(current))}catch{/* Preferences remain usable in memory. */}
  listeners.forEach(listener=>listener())
}
if(typeof window!=='undefined')window.addEventListener('storage',event=>{if(event.key===key||event.key===null){current=read();listeners.forEach(listener=>listener())}})
export function usePreferences(){
  const value=useSyncExternalStore(subscribe,()=>current,()=>defaults)
  return value
}
export function localeTag(){return current.locale==='en'?'en-GB':'tr-TR'}
export function displayName(value:string){return value.replaceAll(' · ',' - ')}
const reverse=Object.fromEntries(Object.entries(english).map(([tr,en])=>[en,tr]))
const templates=Object.entries(english).filter(([key])=>/\{\d+\}/.test(key)).flatMap(([key,en])=>[key,en].map(text=>{
  const indices:string[]=[]
  const pattern=text.split(/(\{\d+\})/).map(part=>/^\{\d+\}$/.test(part)?(indices.push(part.slice(1,-1)),'(.+?)'):part.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('')
  return {key,indices,pattern:new RegExp('^'+pattern+'$')}
}))
export function translate(text:string,values?:Record<string,unknown>){
  let key=english[text]?text:reverse[text]||text
  if(values===undefined&&!english[key])for(const entry of templates){const match=text.match(entry.pattern);if(match){key=entry.key;values=Object.fromEntries(entry.indices.map((index,i)=>[index,match[i+1]]));break}}
  const template=(current.locale==='en'?(english[key]||key):(turkishLabels[key]||key)).replaceAll(' · ',' - ')
  return template.replace(/\{(\d+)\}/g,(match,index)=>values&&index in values?String(values[index]):match)
}
export function useI18n(){usePreferences();return {t:translate,locale:localeTag()}}
