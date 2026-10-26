import {Moon,Sun} from 'lucide-react'
import {useEffect} from 'react'
import {Button} from '@/components/ui/button'
import {setPreferences,usePreferences,translate as t} from './preferences'

export function UiPreferences(){
  const {locale,theme}=usePreferences()
  useEffect(()=>{document.documentElement.lang=locale;document.documentElement.dataset.theme=theme;document.documentElement.classList.toggle('dark',theme==='dark');document.title=locale==='en'?'Schema Compare':'Şema Karşılaştırma'},[locale,theme])
  return <div className="ui-preferences"><div role="group" aria-label="Dil / Language" className="language-switch"><button type="button" aria-label="Türkçe" aria-pressed={locale==='tr'} onClick={()=>setPreferences({locale:'tr'})}>TR</button><button type="button" aria-label="English" aria-pressed={locale==='en'} onClick={()=>setPreferences({locale:'en'})}>EN</button></div><Button variant="ghost" size="icon" aria-label={t('Koyu tema')} aria-pressed={theme==='dark'} onClick={()=>setPreferences({theme:theme==='light'?'dark':'light'})}>{theme==='light'?<Moon/>:<Sun/>}</Button></div>
}
