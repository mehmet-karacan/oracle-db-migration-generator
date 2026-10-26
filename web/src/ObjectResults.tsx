import {ChoiceSelect} from './ChoiceSelect'
import {translate as t,localeTag,displayName} from './preferences'
import {useEffect,useRef,useState} from 'react'
import {Database,LoaderCircle,RefreshCw,Search,ChevronRight} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {Input} from '@/components/ui/input'
import {api,objectTypes,statusLabel,typeLabel,type Run} from './api'
import type {ObjectPage,ResultTarget} from './resultApi'
import {objectName,differenceLabel} from './resultApi'
import {ObjectComparisonPanel} from './ObjectComparisonPanel'

type Snapshot={key:string;page:number;data?:ObjectPage;error?:string}
export function ObjectResults({runId,targets,run}:{runId:string;targets:ResultTarget[];run?:Run}){
  const [target,setTarget]=useState(targets[0]?.id||''),[kind,setKind]=useState('TABLE'),[search,setSearch]=useState(''),[page,setPage]=useState(1),[revision,setRevision]=useState(0),[retry,setRetry]=useState(0),[difference,setDifference]=useState('')
  const [selected,setSelected]=useState(''),[result,setResult]=useState<Snapshot|null>(null)
  const scrollLock=useRef(false),query=`${runId}|${target}|${kind}|${search}|${difference}|${revision}`
  useEffect(()=>{if(!target)return;let active=true
    scrollLock.current=true
    const timer=setTimeout(()=>{void api<ObjectPage>(`/runs/${runId}/results/objects?target_id=${encodeURIComponent(target)}&object_type=${kind}&search=${encodeURIComponent(search)}&difference_kind=${difference}&page=${page}&size=25`).then(data=>{
      if(active)setResult(previous=>{
        const rows=page>1&&previous?.key===query?[...(previous.data?.rows||[]),...data.rows]:data.rows
        return {key:query,page,data:{...data,rows:Array.from(new Map(rows.map(row=>[row.key,row])).values())}}
      })
    }).catch(e=>{if(active)setResult(previous=>({...(previous?.key===query?previous:{key:query,page:0}),error:(e as Error).message}))}).finally(()=>{if(active)scrollLock.current=false})},200)
    return()=>{active=false;clearTimeout(timer)}
  },[runId,target,kind,search,difference,page,query,retry])
  const current=result?.key===query?result:null,data=current?.data,targetName=targets.find(item=>item.id===target)?.name||t('Hedef')
  const loading=!current||(!current.error&&current.page!==page)
  const activeObject=data?.available?(data.rows.find(o=>o.key===selected)||data.rows[0]):undefined
  function reset(){setPage(1);setSelected('')}
  return <section className="object-results" aria-label={t('Nesne bazlı sonuçlar')}>
    <div className="section-toolbar"><div><h2>{t('Nesneler ve Farklar')}</h2><p className="muted">{t('Soldan nesne seçin. Kaynak ve hedef farklarını sağda inceleyin.')}</p></div><div className="workspace-actions"><ChoiceSelect aria-label={t('İncelenecek hedef')} value={target} onChange={value=>{setTarget(value);reset()}}>{targets.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</ChoiceSelect><Button variant="outline" size="sm" onClick={()=>{reset();setRevision(n=>n+1)}}><RefreshCw size={16}/>{t('Yenile')}</Button></div></div>
    <div className="results-workspace">
      <section className="object-navigation" aria-label={t('Nesne listesi')}><header><strong>{t('Nesneler')}</strong><span className="object-loaded-count">{data?.total==null?t('Bekleniyor'):t('{0} / {1} nesne',{0:data.rows.length.toLocaleString(localeTag()),1:data.total.toLocaleString(localeTag())})}</span></header>
        <div className="object-navigation-filters"><div className="search-box"><Search size={19}/><Input aria-label={t('Nesne ara')} placeholder={t('Nesne adı ara…')} value={search} onChange={e=>{setSearch(e.target.value);reset()}}/></div><ChoiceSelect aria-label={t('Nesne türü')} value={kind} onChange={value=>{setKind(value);reset()}}><option value="">{t('Tüm nesneler')}</option>{objectTypes.filter(item=>item!=='GRANT').map(item=><option key={item} value={item}>{typeLabel(item)}</option>)}</ChoiceSelect><ChoiceSelect aria-label={t('Fark Türü')} value={difference} onChange={value=>{setDifference(value);reset()}}><option value="">{t('Tüm Fark Türleri')}</option>{['MISSING','EXTRA','CHANGED','UNKNOWN','INFORMATIONAL'].map(value=><option key={value} value={value}>{differenceLabel(value)}</option>)}</ChoiceSelect></div>
        <div className="object-navigation-items" data-testid="object-scroll" tabIndex={0} aria-label={t('Nesne Listesini Kaydır')} aria-busy={loading} onScroll={event=>{const list=event.currentTarget;if(list.scrollHeight-list.scrollTop-list.clientHeight<180&&!scrollLock.current&&!loading&&!current?.error&&data?.total&&current?.page===page&&page*25<data.total){scrollLock.current=true;setPage(n=>n+1)}}}>
          {data?.available&&data.rows.map(obj=>{const decision=['BLOCKED','REVIEW_REQUIRED','READY','INFORMATIONAL'].find(d=>obj.decisions.includes(d));return <button key={obj.key} className={`object-navigation-item ${activeObject?.key===obj.key?'selected':''}`} aria-label={t('{0} ayrıntıları',{0:objectName(obj)})} aria-pressed={activeObject?.key===obj.key} onClick={()=>setSelected(obj.key)}><Database size={18}/><span><strong>{objectName(obj)}</strong><small>{typeLabel(obj.object_type)} - {obj.difference_count} {t('alan kaydı')}</small><span className="object-difference-status">{t('Fark')}: {obj.difference_kinds?.length?obj.difference_kinds.map(differenceLabel).join(', '):t('Kayıtlı Alan Farkları')}</span>{decision&&<span className="object-decision">DDL: {t(({READY:'Hazır',REVIEW_REQUIRED:'İnceleme Gerekli',BLOCKED:'Üretilemedi',INFORMATIONAL:'Bilgi'} as Record<string,string>)[decision]||statusLabel(decision))}</span>}</span><ChevronRight size={16}/></button>})}
          {loading&&target&&<div className="empty-inline" role="status"><LoaderCircle className="spin"/>{t('Sonuçlar yükleniyor…')}</div>}
          {current?.error&&<div className="object-load-error"><p role="alert">{t(current.error)}</p><Button variant="outline" size="sm" onClick={()=>{setResult(previous=>previous?{...previous,error:undefined}:previous);setRetry(n=>n+1)}}>{t('Tekrar Dene')}</Button></div>}
          {data?.available&&!data.rows.length&&!loading&&<div className="empty-inline"><Database/><strong>{t('Bu filtreye uygun nesne yok')}</strong><p>{t('Nesne türünü veya arama metnini değiştirin.')}</p></div>}
          {data&&!data.available&&<div className="empty-inline"><Database/><strong>{t('Nesne ayrıntıları henüz aktarılmadı')}</strong></div>}
        </div>
      </section>
      {activeObject?<ObjectComparisonPanel key={`${runId}-${target}-${activeObject.key}`} runId={runId} targetId={target} targetName={targetName} sourceName={displayName(run?.spec?.connections[run.spec.profile.source.connection_id]?.name||t('Kaynak'))} targetSchema={run?.spec?.profile.target_mappings?.[target]?.find(pair=>pair.source_schema===activeObject.owner)?.target_schema||activeObject.owner} objectKey={activeObject.key}/>:<section className="object-comparison-empty" aria-label={t('Seçili nesne karşılaştırması')}><Database size={30}/><h3>{loading?t('Sonuçlar yükleniyor'):t('İncelenecek nesne seçin')}</h3><p>{t('Seçtiğiniz nesnenin kaynak ve hedef değerleri burada gösterilir.')}</p></section>}
    </div>
  </section>
}
