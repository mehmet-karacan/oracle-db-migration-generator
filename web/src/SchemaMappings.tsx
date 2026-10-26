import {ChoiceSelect} from './ChoiceSelect'
import {translate as t,displayName} from './preferences'
import {useEffect,useRef,useState} from 'react'
import {ArrowLeft,Plus,Save,Pencil,X} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Card,CardContent} from '@/components/ui/card'
import {TargetSchemaMappings} from './TargetSchemaMappings'
import {api} from './api'
import type {Connection,SchemaMapping,SchemaPair} from './api'

export function SchemaMappings({projectId,connections,mappings,admin,refresh}:{projectId?:string;connections:Connection[];mappings:SchemaMapping[];admin:boolean;refresh:()=>void}) {
  const mounted=useRef(true)
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[])
  const [open,setOpen]=useState(false),[editing,setEditing]=useState<SchemaMapping|null>(null)
  const [name,setName]=useState(''),[source,setSource]=useState(''),[schemas,setSchemas]=useState(''),[targets,setTargets]=useState<string[]>([])
  const [pairs,setPairs]=useState<Record<string,SchemaPair[]>>({}),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false)
  const sourceSchemas=[...new Set(schemas.split(',').map(s=>s.trim().toUpperCase()).filter(Boolean))]
  const connectionName=(id:string)=>displayName(connections.find(c=>c.id===id)?.name||id)
  function edit(record:SchemaMapping|null){setEditing(record);setName(record?.name||'');setSource(record?.source.connection_id||'');setSchemas(record?.source.schemas.join(', ')||'');setTargets(record?.target_ids||['']);setPairs(record?.target_mappings||{});setError('');setNotice('');setOpen(true)}
  function changeSchemas(value:string){setSchemas(value);const allowed=new Set(value.split(',').map(s=>s.trim().toUpperCase()));setPairs(previous=>Object.fromEntries(Object.entries(previous).map(([id,rows])=>[id,rows.filter(row=>allowed.has(row.source_schema))])))}
  function changeTarget(index:number,id:string){
    const prior=targets[index]
    setTargets(previous=>previous.map((value,i)=>i===index?id:value))
    setPairs(previous=>{const next={...previous};delete next[prior];return next})
  }
  function removeTarget(index:number){
    const prior=targets[index]
    setTargets(previous=>previous.length===1?['']:previous.filter((_,i)=>i!==index))
    setPairs(previous=>{const next={...previous};delete next[prior];return next})
  }
  async function save(){
    setError('');const selected=connections.find(c=>c.id===source)
    if(!selected){setError(t("Kaynak bağlantısı seçin."));return}
    if(!sourceSchemas.length){setError(t("Karşılaştırılacak kaynak şemalarını girin."));return}
    if(!targets.length||targets.some(id=>!id)){setError(t("En az bir hedef bağlantısı seçin."));return}
    for(const id of targets)if(!pairs[id]?.length){setError(t("{0} için şema eşleştirmesi seçin.",{0:(connectionName(id))}));return}
    if(!name.trim()){setError(t("Eşleştirme adı girin."));return}
    setBusy(true)
    try{
      await api<SchemaMapping>('/schema-mappings',{...(editing?{id:editing.id,revision:editing.revision}:{}),project_id:projectId,name,source:{kind:selected.kind,connection_id:source,schemas:sourceSchemas},target_ids:targets,target_mappings:Object.fromEntries(targets.map(id=>[id,pairs[id]]))})
      if(mounted.current){setOpen(false);setNotice(t("Eşleştirme kaydedildi. Yeni karşılaştırma ekranında seçebilirsiniz."));refresh()}
    }catch(e){if(mounted.current)setError((e as Error).message)}finally{if(mounted.current)setBusy(false)}
  }
  return <>
    <div className="section-toolbar"><p className="muted">{t("Kaynağı seçin, karşılaştırılacak hedef şemalarını eşleştirin.") }</p>{!open&&admin&&<Button onClick={()=>edit(null)}><Plus/>{t("Yeni eşleştirme") }</Button>}{open&&<Button variant="ghost" disabled={busy} onClick={()=>{setOpen(false);setError('')}}><ArrowLeft/>{t("Eşleştirmelere dön") }</Button>}</div>
    {error&&<div role="alert" className="error-banner">{t(error)}</div>}{notice&&<div role="status" className="success-banner">{t(notice)}</div>}
    {open?<Card><CardContent className="field-stack mapping-editor"><h2>{editing?t("Eşleştirmeyi düzenle"):t("Yeni şema eşleştirmesi")}</h2><div className="field"><Label htmlFor="mapping-name">{t("Eşleştirme adı") }</Label><Input id="mapping-name" value={name} onChange={e=>setName(e.target.value)} placeholder={t("Örn. UAT TTBP → PROD TTBP")}/></div>
      <div className="source-target-grid"><div className="field-stack"><h3>{t("Kaynak") }</h3><div className="field"><Label htmlFor="mapping-source">{t("Kaynak bağlantısı") }</Label><ChoiceSelect id="mapping-source" value={source} onChange={e=>{setSource(e);setSchemas('');setPairs({})}}><option value="">{t("Bağlantı seçin") }</option>{connections.map(c=><option key={c.id} value={c.id}>{displayName(c.name)} ({c.kind==='GIT'?'Git':c.kind==='SNAPSHOT'?t('Metadata Dosyası'):'Oracle'})</option>)}</ChoiceSelect></div>
      <div className="field"><Label htmlFor="mapping-schemas">{t("Kaynak şemaları") }</Label><Input id="mapping-schemas" value={schemas} onChange={e=>changeSchemas(e.target.value)} placeholder={t("Örn. TTBP, INNOVA_ODI")}/><small>{t("Şemaları virgülle ayırın. Bağlantı hesabının bu şemaları okuma yetkisi olmalıdır.") }</small></div></div><div className="flow-arrow">→</div>
      <div className="field-stack"><h3>{t('Hedefler')}</h3><p className="micro-copy">{t('Hedef bağlantısını seçin, ardından şemaları eşleştirin.')}</p>
        {targets.map((id,index)=><div className="target-mapping-row" key={index}>
          <div className="target-picker"><div className="field"><Label htmlFor={`mapping-target-${index}`}>{index===0?t('Hedef Bağlantısı'):t('Hedef Bağlantısı {0}',{0:index+1})}</Label>
            <ChoiceSelect id={`mapping-target-${index}`} value={id} disabled={busy} onChange={value=>changeTarget(index,value)}><option value="">{t('Bağlantı seçin')}</option>{connections.filter(c=>(c.kind==='ORACLE'||c.kind==='SNAPSHOT')&&(!targets.includes(c.id)||c.id===id)).map(c=><option key={c.id} value={c.id}>{displayName(c.name)}</option>)}</ChoiceSelect>
          </div>{(id||targets.length>1)&&<Button variant="ghost" size="icon" disabled={busy} aria-label={t('Hedefi Kaldır {0}',{0:index+1})} onClick={()=>removeTarget(index)}><X size={17}/></Button>}</div>
          {id&&<TargetSchemaMappings name={connectionName(id)} schemas={sourceSchemas} value={pairs[id]||[]} disabled={busy} onChange={rows=>setPairs(previous=>({...previous,[id]:rows}))}/>}
        </div>)}
        <Button variant="outline" className="add-target-button" disabled={busy||targets.length>=8||targets.includes('')||targets.length>=connections.filter(c=>(c.kind==='ORACLE'||c.kind==='SNAPSHOT')).length} onClick={()=>setTargets(previous=>[...previous,''])}><Plus size={16}/>{t('Hedef Ekle')}</Button>
      </div></div>
      <div className="dialog-actions"><Button disabled={busy} onClick={()=>void save()}><Save/>{busy?t('Kaydediliyor...'):t("Eşleştirmeyi kaydet")}</Button></div>
    </CardContent></Card>:<div className="mapping-catalog">{mappings.map(record=><Card key={record.id}><CardContent><div className="section-toolbar"><div><h3>{record.name}</h3><small>v{record.revision}</small></div>{admin&&<Button variant="outline" size="sm" onClick={()=>edit(record)} aria-label={t("{0} eşleştirmesini düzenle",{0:(record.name)})}><Pencil/>{t("Düzenle") }</Button>}</div><p className="micro-copy">{t("Kaynak:") }{' '}{connectionName(record.source.connection_id)}</p>{record.target_ids.map(id=><p key={id} className="mapping-catalog-pair">{record.target_mappings[id].map(pair=><span key={pair.source_schema}>{pair.source_schema} → {connectionName(id)} / {pair.target_schema}</span>)}</p>)}</CardContent></Card>)}{!mappings.length&&<div className="empty-state"><h3>{t("Henüz şema eşleştirmesi yok") }</h3><p>{t("Önce bağlantılarınızı tanımlayın, ardından Yeni eşleştirme ile kaynak ve hedef şemalarını seçin.") }</p></div>}</div>}
  </>
}
