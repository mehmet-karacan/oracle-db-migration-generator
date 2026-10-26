import {translate as t} from './preferences'
import { useState,useRef,useEffect } from 'react'
import { Clock3, Gauge, HardDrive, Bell, Save } from 'lucide-react'
import { Card,CardHeader,CardTitle,CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { api } from './api'
import type { Settings } from './api'

export function SettingsPage({initial,local,onSaved,projectId,hasSchedule=true}:{hasSchedule?:boolean;projectId?:string;initial:Settings;local:boolean;onSaved:()=>void}) {
  const mounted=useRef(true)
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[])
  const [settings,setSettings]=useState(initial),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false)
  const field=(key:string,label:string,unit:string,min:number,max:number)=><div className="field" key={key}><Label htmlFor={key}>{t(label)}</Label><div className="unit-input"><Input id={key} type="number" min={min} max={max} value={String(settings[key])} onChange={e=>setSettings(s=>({...s,[key]:Number(e.target.value)}))}/><span>{t(unit)}</span></div></div>
  async function save() {setBusy(true);setError('');setNotice('');try{const saved=await api<Settings>('/settings',{...settings,project_id:projectId||settings.project_id},'PUT');if(!mounted.current)return;setSettings(saved);setNotice(t("Ayarlar kaydedildi. Yeni çalışmalarda geçerli olacak."));onSaved()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  return <>{error&&<div role="alert" className="error-banner">{t(error)}</div>}{notice&&<div role="status" className="success-banner">{t(notice)}</div>}<div className="settings-intro"><span className="version-pill">{t("Ayar sürümü ·") }{' '}{settings.revision}</span><p>{t("Değişiklikler yeni işleri etkiler. Çalışan işler ve geçmiş sonuçlar kendi ayar kopyalarını korur.") }</p></div>
    <div className="settings-grid"><Card><CardHeader><CardTitle><Clock3 size={18}/>{t("Bağlantı ve yakalama") }</CardTitle></CardHeader><CardContent className="two-fields">{field('capture_timeout_seconds',t("Metadata yakalama bütçesi"),'sn',30,7200)}{field('connect_timeout_seconds',t("Bağlantı zaman aşımı"),'sn',1,60)}{field('call_timeout_ms',t("Oracle çağrı zaman aşımı"),'ms',1000,120000)}{field('job_timeout_seconds',t("Toplam çalışma bütçesi"),'sn',60,14400)}</CardContent></Card>
    <Card><CardHeader><CardTitle><Gauge size={18}/>{t("Çözümleme ve kuyruk") }</CardTitle></CardHeader><CardContent className="two-fields">{field('parser_regular_seconds',t("Normal SQL çözümleme"),'sn',1,600)}{field('parser_large_seconds',t("Büyük SQL çözümleme"),'sn',1,600)}{field('parser_package_seconds',t("Büyük paket gövdesi"),'sn',1,600)}{field('max_parallel_jobs',t("Eşzamanlı çalışma"),t("iş"),1,4)}{field('git_attempts',t("Git erişim denemesi"),'deneme',1,5)}{field('git_retry_seconds',t("Git tekrar bekleme"),'sn',0,60)}</CardContent></Card>
    <Card><CardHeader><CardTitle><HardDrive size={18}/>{t("Doğrulanmış önbellek") }</CardTitle></CardHeader><CardContent className="field-stack"><label className="switch-field"><Switch checked={Boolean(settings.cache_enabled)} onCheckedChange={v=>setSettings(s=>({...s,cache_enabled:v}))}/>{t("Önbellek kullanımını etkinleştir") }</label><div className="two-fields">{field('cache_entries',t("Hazırlanmış kaynak sınırı"),t("kayıt"),1,16)}{field('cache_megabytes',t("Hazırlanmış kaynak kapasitesi"),'MiB',64,4096)}</div><p className="micro-copy">{t("Girdiler ve ayarlar doğrulanmadan önbellek kullanılmaz. Kapasite dolunca yeni kayıt atlanır. Bu ekran mevcut dosyaları silmez.") }</p></CardContent></Card>
    <Card><CardHeader><CardTitle><Bell size={18}/>{t("Bildirim ve zamanlama") }</CardTitle></CardHeader><CardContent className="field-stack"><label className="switch-field"><Switch checked={Boolean(settings.notify_enabled)} onCheckedChange={v=>setSettings(s=>({...s,notify_enabled:v}))}/>{t("Jenkins sonuç bildirimi") }</label><div className="field"><Label htmlFor="notify-to">{t("İzinli alıcı") }</Label><Input id="notify-to" readOnly value={String(settings.notify_to)}/></div>{hasSchedule?<div className="schedule-note"><strong>{t("08:00 · Europe/Istanbul") }</strong><span>{t("Mevcut günlük TTBP işi Jenkins tarafından yönetiliyor.") }</span></div>:<p className="micro-copy">{t("Bu proje için zamanlanmış çalışma tanımlanmadı.")}</p>}<p className="micro-copy">{local?t("Yerel önizleme mail göndermez. Ortak ortamda bildirim yetkili Jenkins işinden gönderilir."):t("Bildirim ve arşivleme yetkili Jenkins işinde uygulanır.")}{' '}{t("Zamanlama bu sürümde burada değiştirilemez.") }</p></CardContent></Card></div>
    <div className="settings-save"><Button disabled={busy} onClick={()=>void save()}><Save/>{busy?t('Kaydediliyor…'):t("Ayarları kaydet")}</Button></div>
  </>
}
