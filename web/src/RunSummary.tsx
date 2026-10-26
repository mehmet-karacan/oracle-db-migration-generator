import {useEffect,useState} from 'react'
import {Database,FileCheck2,SearchCheck,TriangleAlert,ListChecks,ShieldQuestion,Clock3} from 'lucide-react'
import {api,duration,typeLabel} from './api'
import type {Run} from './api'
import {translate as t,localeTag} from './preferences'

type Summary={source_total:number|null;verified_difference_count:number|null;source_inventory:string;source_types:Record<string,number>;counts:Record<string,number>|null;unknown_count:number|null}
const number=(value:number|null|undefined)=>typeof value==='number'?value.toLocaleString(localeTag()):t('Bilinmiyor')
export function RunSummary({run}:{run:Run}){
  const [summary,setSummary]=useState<Summary|null>(null),[error,setError]=useState('')
  useEffect(()=>{let active=true;void api<Summary>(`/runs/${run.id}/summary`).then(value=>{if(active){setSummary(value);setError('')}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[run.id,run.status,run.targets.length])
  const cards=[
    {label:t('Toplam Süre'),value:duration(run.started_at,run.finished_at),icon:Clock3,tone:'info',hint:t('Gerçek başlangıç ve bitişten')},
    {label:t('Toplam Taranan Nesne'),value:number(summary?.source_total),icon:Database,tone:'oracle',hint:t('Kaynak envanteri')},
    {label:t('Bulunan Fark'),value:number(summary?.verified_difference_count),icon:SearchCheck,tone:'info',hint:t('Hedeflerde kaydedilen farklar')},
    {label:t('Üretilen DDL'),value:number(summary?.counts?.ready_operations),icon:FileCheck2,tone:'positive',hint:t('İncelemeye sunulan işlemler')},
    {label:t('İnceleme Gereken'),value:number(summary?.counts?.review_operations),icon:ListChecks,tone:'warning',hint:t('Ek kontrol gereken işlemler')},
    {label:t('Üretilemeyen DDL'),value:number(summary?.counts?.blocked_operations),icon:TriangleAlert,tone:'negative',hint:t('Engellenen işlemler')},
    {label:t('Doğrulanamayan Fark'),value:number(summary?.unknown_count),icon:ShieldQuestion,tone:'warning',hint:t('Eksik veya belirsiz bilgi')},
  ]
  return <section className="recorded-summary" aria-label={t('Çalışma Özeti')}>
    {error&&<p role="alert" className="error-banner">{t(error)}</p>}
    <div className="summary-grid">{cards.map(card=><article key={card.label} title={card.hint} className={`summary-metric tone-${card.tone}`}><span title={card.hint}><card.icon size={17}/>{card.label}</span><strong>{card.value}</strong></article>)}</div>
    <div className="summary-metadata">{run.source_performance&&<p className="summary-source-time">{t('Kaynak Hazırlama')}: {t('{0} sn',{0:run.source_performance.seconds.toLocaleString(localeTag(),{maximumFractionDigits:1})})}</p>}
    {summary?.source_inventory==='PARTIAL'&&<p className="scope-warning">{t('Kaynak envanteri eksik. Nesne sayısı gözlenen alt sınırdır.')}</p>}
    {summary?.source_inventory==='UNAVAILABLE'&&<p className="micro-copy">{t('Bu çalışma için kaynak envanteri kaydedilmemiş. Nesne sayısı bilinmiyor.')}</p>}
    {!!summary?.source_types&&Object.keys(summary.source_types).length>0&&<details className="inventory-breakdown"><summary>{t('Nesne Türlerine Göre Dağılım')}</summary><div>{Object.entries(summary.source_types).map(([kind,count])=><span key={kind}>{typeLabel(kind)}<strong>{number(count)}</strong></span>)}</div></details>}
    </div>
  </section>
}
