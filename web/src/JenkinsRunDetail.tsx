import {RunSummary} from './RunSummary'
import {translate as t,localeTag,displayName} from './preferences'
import { ArrowLeft,ArrowUpRight,Clock3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card,CardContent } from '@/components/ui/card'
import { duration,statusLabel } from './api'
import type { Run } from './api'
import {ObjectResults} from './ObjectResults'
import {resultTargets} from './resultApi'
import {RunSchemaScope} from './RunSchemaScope'

export function JenkinsRunDetail({run,back}:{run:Run;back:()=>void}) {
  const external=run.external!,pending=run.status==='AWAITING_JENKINS'
  const summary=<>
<div className="run-overview"><Card><CardContent><span className="eyebrow">{t("KARŞILAŞTIRMA SÜRESİ") }</span><strong className="metric-value">{duration(run.started_at,run.finished_at)}</strong><small>{pending?t("Jenkins sonucu bekleniyor"):t("Gerçek başlangıç ve bitişten")}</small></CardContent></Card><Card><CardContent><span className="eyebrow">{t("KAYNAK HAZIRLAMA") }</span><strong className="metric-value">{run.source_performance?t("{0} sn",{0:(run.source_performance.seconds.toFixed(1))}):t("Bekleniyor")}</strong><small>{run.source_performance?.cache_status==='HIT_VERIFIED'?t("Doğrulanmış önbellek"):t("Kaynak ölçümü")}</small></CardContent></Card><Card><CardContent><span className="eyebrow">{t("BİLDİRİM ALICISI") }</span><strong className="metric-value" style={{fontSize:17}}>mkaracan@innova.com.tr</strong><small>{t("Tek alıcı · Jenkins bildirimi") }</small></CardContent></Card></div>
    {pending?<Card className="progress-card"><CardContent><div className="progress-heading"><div><span className="eyebrow">{t("JENKINS OTURUMU") }</span><h3>{t("Karşılaştırmayı Jenkins’te başlatın") }</h3></div><Clock3/></div><p>{t("Bu iş mevcut Jenkins oturumunuzla çalıştırılır. Açılan sayfada") }{' '}<strong>{external.schema_scope}</strong>{' '}{t("ve") }{' '}<strong>COMPARE</strong>{' '}{t("seçimini doğrulayıp Başlat’a basın.") }</p><p className="muted">{t("Servis hesabı henüz tanımlanmadığından başlatma ve sonuç aktarımı otomatik değildir. Sonuç doğrulanıp bağlanana kadar bu kayıt beklemede kalır.") }</p><a href={external.launch_url} target="_blank" rel="noreferrer"><Button><ArrowUpRight/>{t("Jenkins’te başlat") }</Button></a></CardContent></Card>:<Card className="progress-card"><CardContent><h3>{t("Jenkins sonucu bağlandı") }</h3><p className="muted">{t("Tamamlanan çalışmanın kimliği, hedefi ve zamanları doğrulandı. Rapor ve DDL dosyaları Jenkins arşivindedir.") }</p>{run.targets.map(targetItem=><div className="target-summary" key={targetItem.id}><span>{displayName(run.spec?.connections[Object.keys(external.target_map||{}).find(key=>external.target_map?.[key]===targetItem.id)||'']?.name||targetItem.id)}</span><strong>{targetItem.status==='BLOCKED'&&targetItem.plan_id?t("DDL kısmen hazır"):statusLabel(targetItem.status)}</strong><span>{targetItem.difference_count===null?t("Toplam fark kesinleşmedi"):t('{0} fark',{0:targetItem.difference_count.toLocaleString(localeTag())})}</span></div>)}<a href={external.report_url} target="_blank" rel="noreferrer"><Button><ArrowUpRight/>{t("Karşılaştırma raporunu aç") }</Button></a></CardContent></Card>}
  </>
  return <><Button variant="ghost" className="back-button" onClick={back}><ArrowLeft/>{t("Çalışmalara dön") }</Button>
    <div className="run-heading"><div><span className="eyebrow">{run.project_name} - {external.build_number?`JENKINS #${external.build_number}`:t("YENİ ÇALIŞMA")}</span><h1>{run.profile_name}</h1><p className="muted">{t("Git Kaynağı") }{' '}{external.schema_scope}</p></div><div className="run-heading-actions"><Badge variant="secondary" className={`status-${run.status.toLowerCase()}`}>{statusLabel(run.status)}</Badge>{!pending&&<a href={external.report_url} target="_blank" rel="noreferrer"><Button variant="outline"><ArrowUpRight/>{t('Karşılaştırma raporunu aç')}</Button></a>}</div></div>
    {pending?summary:<RunSummary run={run}/>}
    <RunSchemaScope run={run}/>
    {!pending&&<ObjectResults key={run.id} runId={run.id} run={run} targets={resultTargets(run)}/>}
  </>
}
