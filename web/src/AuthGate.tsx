import {BrandLogo} from './BrandLogo'
import {useEffect,useState} from 'react'
import type {ReactNode,FormEvent} from 'react'
import {LogIn,KeyRound,LoaderCircle} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {api} from './api'
import {translate as t,usePreferences} from './preferences'
import {UiPreferences} from './UiPreferences'

type AuthStatus={password_login?:boolean;setup_required?:boolean;setup_allowed?:boolean}
export function AuthGate({children}:{children:(logout:()=>void)=>ReactNode}){
  usePreferences()
  const [status,setStatus]=useState<AuthStatus|null>(null),[ready,setReady]=useState(false)
  const [error,setError]=useState(''),[password,setPassword]=useState(''),[confirm,setConfirm]=useState(''),[busy,setBusy]=useState(false)
  useEffect(()=>{let active=true;void api<AuthStatus>('/auth/status').then(async status=>{
    if(!active)return;setStatus(status)
    if(!status.password_login){setReady(true);return}
    if(!status.setup_required)try{await api('/session');if(active)setReady(true)}catch{/* The login form remains visible. */}
  }).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[])
  useEffect(()=>{const expired=()=>{setReady(false);setPassword('');setConfirm('')};window.addEventListener('odmg-session-expired',expired);return()=>window.removeEventListener('odmg-session-expired',expired)},[])
  async function submit(event:FormEvent){
    event.preventDefault();setError('')
    if(status?.setup_required&&password!==confirm){setError(t('Parolalar eşleşmiyor.'));return}
    setBusy(true)
    try{
      if(status?.setup_required){await api('/auth/setup',{password});setStatus({...status,setup_required:false})}
      else{await api('/auth/login',{username:'mkaracan',password});setReady(true)}
      setPassword('');setConfirm('')
    }catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  async function logout(){try{await api('/auth/logout',{})}finally{setReady(false);setPassword('');setConfirm('')}}
  if(ready)return children(()=>void logout())
  return <div className="login-page"><div className="login-preferences"><UiPreferences/></div><form className="login-card" onSubmit={event=>void submit(event)}>
    <BrandLogo/><p className="login-app-name">{t('Şema Karşılaştırma')}</p>
    {!status&&!error?<div role="status"><LoaderCircle className="spin"/>{t('Uygulamaya bağlanılıyor…')}</div>:<>
      <div className="login-symbol">{status?.setup_required?<KeyRound/>:<LogIn/>}</div><h1>{status?.setup_required?t('İlk Giriş'):t('Giriş Yap')}</h1>
      <p className="muted">{status?.setup_required?t('Mehmet KARACAN hesabı için parolanızı belirleyin.'):t('Projelerinize erişmek için oturum açın.')}</p>
      {error&&<div role="alert" className="error-banner">{t(error)}</div>}
      {status?.setup_required&&status.setup_allowed===false?<p role="status" className="scope-warning">{t('İlk parola kurulumu sunucunun yerel adresinden yapılmalı.')}</p>:status&&<><div className="field"><Label htmlFor="login-user">{t('Kullanıcı Adı')}</Label><Input id="login-user" autoComplete="username" value="mkaracan" readOnly/></div>
      <div className="field"><Label htmlFor="login-password">{t('Parola')}</Label><Input id="login-password" type="password" autoComplete={status.setup_required?'new-password':'current-password'} value={password} minLength={status.setup_required?12:undefined} maxLength={256} required onChange={e=>setPassword(e.target.value)}/>{status.setup_required&&<small>{t('En az 12 karakter kullanın.')}</small>}</div>
      {status.setup_required&&<div className="field"><Label htmlFor="login-confirm">{t('Parolayı Doğrula')}</Label><Input id="login-confirm" type="password" autoComplete="new-password" value={confirm} required maxLength={256} onChange={e=>setConfirm(e.target.value)}/></div>}
      <Button type="submit" disabled={busy}>{busy?<LoaderCircle className="spin"/>:<LogIn/>}{status.setup_required?t('Parolayı Belirle'):t('Giriş Yap')}</Button></>}
    </>}
  </form><footer className="company-footer">{t('© 2026 İnnova Bilişim Çözümleri A.Ş.')}</footer></div>
}
