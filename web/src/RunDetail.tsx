import {RunSummary} from './RunSummary'
import {translate as t,localeTag} from './preferences'
import {useEffect,useState} from 'react'
import {ArrowLeft,ArrowUpRight,LoaderCircle} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {Progress} from '@/components/ui/progress'
import {JenkinsRunDetail} from './JenkinsRunDetail'
import {RunSchemaScope} from './RunSchemaScope'
import {ObjectResults} from './ObjectResults'
import {resultTargets} from './resultApi'
import {api,artifactUrl,statusLabel,stageLabel,errorText} from './api'
import type {Run} from './api'

export function RunDetail({id,back}:{id:string;back:()=>void}){
  const [run,setRun]=useState<Run|null>(null),[error,setError]=useState('')
  useEffect(()=>{let active=true;const load=async()=>{try{const value=await api<Run>(`/runs/${id}`);if(active){setRun(value);setError('')}}catch(e){if(active)setError((e as Error).message)}};void load();const timer=setInterval(()=>void load(),2500);return()=>{active=false;clearInterval(timer)}},[id])
  if(!run)return <div className="empty-state">{error||<LoaderCircle className="spin"/>}</div>
  if(run.external)return <JenkinsRunDetail run={run} back={back}/>
  const running=['RUNNING','QUEUED'].includes(run.status),count=run.progress?.processed,total=run.progress?.total,remote=run.executor==='JENKINS',report=remote?(run.archive_build_url?run.archive_build_url+'artifact/output/runs/build-'+run.archive_build_url.replace(/\/$/,'').split('/').at(-1)+'/index.html':null):run.report_available?artifactUrl(id,'index.html'):null
  return <><Button variant="ghost" className="back-button" onClick={back}><ArrowLeft/>{t('Çalışmalara dön')}</Button><div className="run-heading"><div><h1>{run.spec?.profile.name||t('Karşılaştırma')}</h1><p className="muted">{remote?t('Jenkins Çalışması'):t('Yerel Çalışma')} - {new Date(run.created_at).toLocaleString(localeTag())}</p></div><div className="run-heading-actions"><Badge variant="secondary" className={`status-${run.status.toLowerCase()}`}>{running&&<LoaderCircle className="spin" size={13}/>} {statusLabel(run.status)}</Badge>{report&&<a href={report} target="_blank" rel="noreferrer"><Button variant="outline"><ArrowUpRight/>{t('HTML raporu')}</Button></a>}</div></div>
    {error&&<div className="error-banner" role="alert">{t(error)}</div>}{run.error_code&&<div className="error-banner" role="alert">{errorText(run.error_code)} {t('Sonuç alınamayan aşama tamamlanmış sayılmaz.')}</div>}
    <RunSummary run={run}/>
    {running?<div className="run-live-progress"><strong>{stageLabel(run.stage)}</strong>{total!==undefined&&total>0&&count!==undefined?<><Progress value={Math.min(100,count/total*100)}/><span>{count.toLocaleString(localeTag())} / {total.toLocaleString(localeTag())} {t('nesne')}</span></>:<span>{t('Aşama sürüyor. Toplam iş miktarı henüz bilinmiyor.')}</span>}</div>:null}
    <RunSchemaScope run={run}/>
    <ObjectResults key={`${run.id}-${run.status}`} runId={run.id} run={run} targets={resultTargets(run)}/>
    {!!run.events?.length&&<details className="run-stage-details"><summary>{t('Çalışma Aşamaları')}</summary>{run.events.map((event,i)=><div key={`${event.stage}-${i}`}><span>{stageLabel(event.stage)}</span><time>{new Date(event.at).toLocaleTimeString(localeTag())}</time></div>)}</details>}
  </>
}
