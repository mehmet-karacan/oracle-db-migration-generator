import {useEffect,useMemo,useState} from 'react'
import {ArrowUpRight,FileCode2,LoaderCircle} from 'lucide-react'
import {api} from './api'
import {translate as t} from './preferences'
import {alignLines} from './lineDiff'

type Definition={state:'AVAILABLE'|'ABSENT'|'UNAVAILABLE'|'ARCHIVED'|'TOO_LARGE'|'INTEGRITY_ERROR';text?:string}
type Definitions={source:Definition;target:Definition;archive_url?:string}
const stateLabel=(state:string)=>t({ABSENT:'Nesne Bu Tarafta Bulunmuyor',UNAVAILABLE:'Özgün Tanım Kaydedilmemiş',TOO_LARGE:'Tanım Görüntüleme Sınırını Aşıyor',INTEGRITY_ERROR:'Tanım Bütünlüğü Doğrulanamadı',ARCHIVED:'Özgün Tanım Arşivde'}[state]||'Özgün Tanım Kaydedilmemiş')
export function DefinitionComparison(props:{runId:string;targetId:string;objectKey:string;sourceName:string;targetName:string}){
 return <DefinitionDocument key={`${props.runId}-${props.targetId}-${props.objectKey}`} {...props}/>
}
function DefinitionDocument({runId,targetId,objectKey,sourceName,targetName}:{runId:string;targetId:string;objectKey:string;sourceName:string;targetName:string}){
 const [data,setData]=useState<Definitions|null>(null),[error,setError]=useState(''),[firstLine,setFirstLine]=useState(0)
 useEffect(()=>{let active=true;void api<Definitions>(`/runs/${runId}/results/objects/${objectKey}/definitions?target_id=${encodeURIComponent(targetId)}`).then(value=>{if(active)setData(value)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[runId,targetId,objectKey])
 const aligned=useMemo(()=>data?.source.state==='AVAILABLE'&&data.target.state==='AVAILABLE'?alignLines(data.source.text!,data.target.text!):null,[data])
 if(error)return <p role="alert" className="error-banner">{t(error)}</p>
 if(!data)return <div role="status" className="empty-inline"><LoaderCircle className="spin"/>{t('Özgün Tanımlar Yükleniyor…')}</div>
 if(data.source.state==='ARCHIVED'||data.target.state==='ARCHIVED')return <div className="definition-unavailable"><FileCode2 size={28}/><h4>{t('Özgün Tanımlar Jenkins Arşivinde')}</h4><p>{t('Bu çalışmanın yerel kaydı yapısal farkları içerir. İki tarafın özgün DDL metni bu uygulamaya aktarılmadığı için satır karşılaştırması gösterilemiyor.')}</p>{data.archive_url&&<a className="definition-archive-link" href={data.archive_url} target="_blank" rel="noreferrer"><ArrowUpRight size={17}/>{t('Jenkins Arşivinde Aç')}</a>}</div>
 if(!aligned)return <div className="definition-availability">{([['source',sourceName],['target',targetName]] as const).map(([side,label])=><section key={side}><h4>{label}</h4>{data[side].state==='AVAILABLE'?<><p>{t('Özgün Tanım Mevcut')}</p><pre className="single-definition">{data[side].text}</pre></>:<p>{stateLabel(data[side].state)}</p>}</section>)}<p className="definition-completeness-note">{t('İki özgün tanım birlikte bulunmadığından satır karşılaştırması yapılmadı. Bu durum eşitlik anlamına gelmez.')}</p></div>
 const changed=aligned.rows.filter(row=>row.kind!=='equal').length
 return <div className="definition-comparison"><div className="definition-comparison-status"><strong>{changed?t('{0} satırda metin farkı',{0:changed}):t('Özgün Tanım Metinleri Aynı')}</strong><span>{t('Yalnız metin karşılaştırması. Yapısal fark ve DDL kararları değişmez.')}</span></div>{aligned.coarse&&<p className="micro-copy">{t('Uzun tanımın değişen bölümü blok olarak gösteriliyor.')}</p>}
 <div className="sql-compare-scroll" tabIndex={0} aria-label={t('Özgün Tanım Satırları')} onScroll={event=>{const next=Math.max(0,Math.floor((event.currentTarget.scrollTop-62)/32)-10);setFirstLine(Math.min(next,Math.max(0,aligned.rows.length-300)))}}><table className="sql-compare-table"><colgroup><col className="line-number-col"/><col/><col className="line-number-col"/><col/></colgroup><thead><tr><th colSpan={2}>{t('Kaynak')} - {sourceName}<small>{t('İstenen Yapı')}</small></th><th colSpan={2}>{t('Hedef')} - {targetName}<small>{t('Mevcut Yapı')}</small></th></tr></thead><tbody>{firstLine>0&&<tr aria-hidden="true" className="line-spacer"><td colSpan={4} style={{height:firstLine*32}}/></tr>}{aligned.rows.slice(firstLine,firstLine+300).map((row,i)=><tr key={firstLine+i} className={'line-'+row.kind}><td className="line-number">{row.source?.number}</td><td className="line-source"><code>{row.source?.text??''}</code></td><td className="line-number">{row.target?.number}</td><td className="line-target"><code>{row.target?.text??''}</code></td></tr>)}{firstLine+300<aligned.rows.length&&<tr aria-hidden="true" className="line-spacer"><td colSpan={4} style={{height:(aligned.rows.length-firstLine-300)*32}}/></tr>}</tbody></table></div></div>
}
