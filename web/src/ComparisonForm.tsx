import {ChoiceSelect} from './ChoiceSelect'
import {CaptureFilterFields} from './CaptureFilterFields'
import {translate as t,displayName} from './preferences'
import { useEffect,useRef,useState } from 'react'
import { ArrowRight, Database, GitBranch, Play, Save, SlidersHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { api, objectTypes, typeLabel,filterValues } from './api'
import type { Connection, Profile, Run, SchemaPair, SchemaMapping } from './api'

type Props = { localExecution?:boolean; projectId?:string; connections: Connection[]; profiles: Profile[]; mappings?:SchemaMapping[]; admin: boolean; onSaved: () => void; onStarted: (id: string) => void }
export function ComparisonForm({ localExecution=false,projectId,connections, profiles, mappings:catalog=[], admin, onSaved, onStarted }: Props) {
  const mounted=useRef(true)
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[])
  const [executor,setExecutor]=useState('JENKINS')
  const [selected, setSelected] = useState<Profile | null>(null)
  const [kind, setKind] = useState<'GIT' | 'ORACLE' | 'SNAPSHOT'>('GIT'), [source, setSource] = useState(''), [targets, setTargets] = useState<string[]>([])
  const [objectNames,setObjectNames]=useState(''),[dataTypes,setDataTypes]=useState(''),[related,setRelated]=useState(true)
  const [name, setName] = useState(''), [schemas, setSchemas] = useState(''), [ref, setRef] = useState('master'), [layout, setLayout] = useState<'by_object' | 'flat'>('by_object')
  const [types, setTypes] = useState(objectTypes.filter(t => t !== 'GRANT')), [technical, setTechnical] = useState(true), [physical, setPhysical] = useState(false)
  const [length, setLength] = useState('UNKNOWN'), [roots, setRoots] = useState(''), [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false)
  const [mappings,setMappings]=useState<Record<string,SchemaPair[]>>({})
  const sourceSchemas=[...new Set(schemas.split(',').map(s=>s.trim().toUpperCase()).filter(Boolean))]
  const [selectedMapping,setSelectedMapping]=useState<SchemaMapping|null>(null)
  const connectionName=(id:string)=>displayName(connections.find(c=>c.id===id)?.name||id)
  function captureScope(connectionId:string){
    const filter=connections.find(c=>c.id===connectionId)?.capture_summary?.filter
    setObjectNames(filter?.object_names?.join(', ')||'');setDataTypes(filter?.data_types?.join(', ')||'');setRelated(filter?.include_related!==false)
    if(filter?.object_types)setTypes(filter.object_types)
  }
  const chooseMapping=(id:string)=>{
    if(id==='profile'&&selected){
      setSelectedMapping(null);setError('');setNotice('');setKind(selected.source.kind);setSource(selected.source.connection_id)
      setSchemas(selected.source.schemas.join(', '));setTargets(selected.target_ids)
      setMappings(selected.target_mappings||Object.fromEntries(selected.target_ids.map(t=>[t,selected.source.schemas.map(s=>({source_schema:s,target_schema:s}))])))
      setRoots(Object.entries(selected.source.roots).map(([s,r])=>`${s}=${r}`).join(', '));setObjectNames(selected.capture_filter?.object_names?.join(', ')||'');setDataTypes(selected.capture_filter?.data_types?.join(', ')||'');setRelated(selected.capture_filter?.include_related!==false);return
    }
    const record=catalog.find(m=>m.id===id);setSelectedMapping(record||null);setError('');setNotice('')
    if(!record){setSource('');setSchemas('');setTargets([]);setMappings({});setObjectNames('');setDataTypes('');setRelated(true);return}
    setKind(record.source.kind);setSource(record.source.connection_id);setSchemas(record.source.schemas.join(', '));setTargets(record.target_ids);setMappings(record.target_mappings);setRoots('')
    captureScope(record.source.connection_id)
    if(localExecution&&(record.source.kind==='SNAPSHOT'||record.target_ids.some(id=>connections.find(c=>c.id===id)?.kind==='SNAPSHOT')))setExecutor('LOCAL')
    if(!name)setName(record.name)
  }
  const load = (id: string) => {
    const p = profiles.find(p => p.id === id); setSelected(p || null); setSelectedMapping(null); if (!p) {setSource('');setSchemas('');setTargets([]);setMappings({});setName('');setRoots('');setObjectNames('');setDataTypes('');setRelated(true);return}
    setName(p.name); setKind(p.source.kind); setSource(p.source.connection_id); setSchemas(p.source.schemas.join(', ')); setRef(p.source.ref); setLayout(p.source.layout)
    setTargets(p.target_ids); setTypes(p.object_types.filter(t => !p.excluded_object_types.includes(t))); setTechnical(p.exclude_system_generated); setPhysical(p.compare_physical_storage); setLength(p.source_length_semantics)
    setRoots(Object.entries(p.source.roots).map(([s,r]) => `${s}=${r}`).join(', ')); setError(''); setNotice('')
    setMappings(p.target_mappings||Object.fromEntries(p.target_ids.map(t=>[t,p.source.schemas.map(s=>({source_schema:s,target_schema:s}))])))
    setObjectNames(p.capture_filter?.object_names?.join(', ')||'');setDataTypes(p.capture_filter?.data_types?.join(', ')||'');setRelated(p.capture_filter?.include_related!==false)
    if(localExecution&&(p.source.kind==='SNAPSHOT'||p.target_ids.some(id=>connections.find(c=>c.id===id)?.kind==='SNAPSHOT')))setExecutor('LOCAL')
  }
  const submit = async (start: boolean) => {
    setError(''); setNotice('')
    if (!source) { setError(t("Şema eşleştirmesi seçin. Eşleştirmeleri Bağlantılar ekranından tanımlayabilirsiniz.")); return }
    if (!targets.length) { setError(t("En az bir hedef bağlantısı seçin.")); return }
    if (!sourceSchemas.length) { setError(t("Karşılaştırılacak kaynak şemalarını girin.")); return }
    for(const id of targets)if(!mappings[id]?.length){setError(t("{0} için şema eşleştirmesi seçin.",{0:(connections.find(c=>c.id===id)?.name||id)}));return}
    if (!types.length) { setError(t("En az bir nesne türü seçin.")); return }
    setBusy(true)
    try {
      let profile = selected
      if (admin) {
        const rootMap: Record<string,string> = {}
        if (roots.trim()) for (const value of roots.split(',')) { const [owner, path] = value.split('='); if (!owner || !path) throw new Error(t("Kökleri ŞEMA=klasör biçiminde girin.")); rootMap[owner.trim().toUpperCase()] = path.trim() }
        const captureFilter=objectNames.trim()||dataTypes.trim()||!related||kind==='SNAPSHOT'?{schemas:sourceSchemas,object_types:types,object_names:filterValues(objectNames),data_types:filterValues(dataTypes),include_related:related,exclude_system_generated:technical}:null
        profile = await api<Profile>('/profiles', { ...(selected ? {id:selected.id, revision:selected.revision}:{}), project_id:projectId, mapping_id:selectedMapping?.id||selected?.mapping_id||null, mapping_revision:selectedMapping?.revision||selected?.mapping_revision||null, name: name || t("Karşılaştırma profili"), source: {kind, connection_id:source, schemas:sourceSchemas, ref, layout, roots:rootMap}, target_ids:targets, target_mappings:Object.fromEntries(targets.map(id=>[id,mappings[id]])), object_types:types, excluded_object_types:objectTypes.filter(t => !types.includes(t)), exclude_system_generated:technical, compare_physical_storage:physical, source_length_semantics:length,capture_filter:captureFilter })
        if(mounted.current){setSelected(profile);onSaved()}
      }
      if(!mounted.current)return
      if (!profile) throw new Error(t("Yetkili olduğunuz kayıtlı bir profil seçin."))
      if (start) { const run = await api<Run>('/runs', {profile_id: profile.id,project_id:projectId,...(localExecution?{executor}:{})}); if(mounted.current)onStarted(run.id) }
      else setNotice(t("Profil kaydedildi. Bu ayarlar sonraki karşılaştırmada kullanılacak."))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <div className="comparison-form">
    <Card className="profile-setup"><CardContent className="two-fields">
      <div className="field"><Label htmlFor="saved-profile">{t('Karşılaştırma Seçimi')}</Label><ChoiceSelect id="saved-profile" aria-label={t('Kayıtlı profil')} value={selected?.id||''} onChange={load}><option value="">{t('Yeni karşılaştırma')}</option>{profiles.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</ChoiceSelect><small>{t('Kayıtlı bir karşılaştırmayı kullanın veya yeni ayarlar hazırlayın.')}</small></div>
      <div className="field"><Label htmlFor="profile-name">{t('Profil adı')}</Label><Input id="profile-name" value={name} disabled={!admin} onChange={e=>setName(e.target.value)} placeholder={t('Örn. TTBP geliştirme → üretim')}/><small>{t('Bu ayarları yeniden kullanmak için bir ad verin.')}</small></div>
      {localExecution&&<div className="field"><Label htmlFor="run-executor">{t('Çalıştırma Yeri')}</Label><ChoiceSelect id="run-executor" value={executor} onChange={setExecutor}><option value="JENKINS">Jenkins</option><option value="LOCAL">{t('Bu Bilgisayar')}</option></ChoiceSelect><small>{executor==='LOCAL'?t('SQL dosyaları bu bilgisayardaki özel çalışma klasöründe saklanır.'):t('Sonuçlar ve SQL dosyaları Jenkins arşivinde saklanır.')}</small></div>}
    </CardContent></Card>
    {error && <div role="alert" className="error-banner">{t(error)}</div>}{notice && <div role="status" className="success-banner">{t(notice)}</div>}
    <Card className="scope-picker"><CardContent className="field-stack"><div className="field"><Label htmlFor="comparison-mapping">{t("Şema eşleştirmesi") }</Label><ChoiceSelect id="comparison-mapping" value={selectedMapping?.id||(selected?'profile':'')} disabled={!admin} onChange={e=>chooseMapping(e)}><option value="">{t("Eşleştirme seçin") }</option>{selected&&<option value="profile">{t("Profilde kayıtlı eşleştirme") }</option>}{catalog.map(record=><option key={record.id} value={record.id}>{record.name} (v{record.revision})</option>)}</ChoiceSelect><small>{t("Kaynak ve hedef şemalarını Bağlantılar ekranındaki Şema eşleştirmeleri sekmesinden yönetin.") }</small></div></CardContent></Card>
    {source&&<div className="source-target-grid">
      <Card className="config-card"><CardHeader><div className="card-heading"><div className={`icon-tile tone-${kind==='GIT'?'git':'oracle'}`}>{kind==='GIT'?<GitBranch size={20}/>:<Database size={20}/>}</div><div><span className="eyebrow">{t("01 · İSTENEN YAPI") }</span><CardTitle>{t("Kaynak") }</CardTitle></div></div></CardHeader><CardContent className="field-stack">
        <div><small>{t("Kaynak bağlantısı") }</small><h3>{connectionName(source)}</h3><p className="micro-copy">{kind==='GIT'?t("Git deposu"):kind==='SNAPSHOT'?t('Metadata Dosyası'):t("Oracle bağlantısı")} / {sourceSchemas.join(', ')}</p></div>
        {kind==='GIT'&&<><div className="field"><Label htmlFor="git-ref">{t("Branch, tag veya commit") }</Label><Input id="git-ref" value={ref} disabled={!admin} onChange={e=>setRef(e.target.value)}/></div><div className="field"><Label htmlFor="layout">{t("Depo yerleşimi") }</Label><ChoiceSelect id="layout" value={layout} disabled={!admin} onChange={e=>setLayout(e as 'by_object'|'flat')}><option value="by_object">{t("Nesne klasörleri") }</option><option value="flat">{t("Tür klasörleri") }</option></ChoiceSelect></div></>}
        {kind==='ORACLE'&&<p className="micro-copy">{t("Kayıtlı hesapla oturum açılır. Seçilen kaynak şemalarının okuma yetkisi ayrıca doğrulanır.") }</p>}
        {kind==='SNAPSHOT'&&<p className="micro-copy">{t('İçe aktarılan metadata kullanılır. Bu kaynak için veri tabanı bağlantısı açılmaz.')}</p>}
      </CardContent></Card><div className="flow-arrow"><ArrowRight size={20}/></div>
      <Card className="config-card"><CardHeader><div className="card-heading"><div className="icon-tile tone-oracle"><Database size={20}/></div><div><span className="eyebrow">{t("02 · MEVCUT DURUM") }</span><CardTitle>{t("Hedefler") }</CardTitle></div></div></CardHeader><CardContent className="field-stack">
        {targets.map(id=><div className="selected-target-scope" key={id}><h3>{connectionName(id)}</h3>{mappings[id]?.map(pair=><p className="mapping-catalog-pair" key={pair.source_schema}><span>{t("Kaynak") }{' '}{pair.source_schema}{' '}{t("→ Hedef") }{' '}{pair.target_schema}</span></p>)}</div>)}
        <p className="micro-copy">{t("Her hedef için ayrı karşılaştırma ve DDL planı hazırlanır.") }</p>
      </CardContent></Card>
    </div>}
    <Card className="scope-card"><CardHeader><div className="card-heading"><SlidersHorizontal size={19}/><CardTitle>{t("Kapsam ve tercihler") }</CardTitle></div></CardHeader><CardContent>
      <div className="type-grid">{objectTypes.map(type => <label key={type}><Checkbox disabled={!admin||!!dataTypes.trim()&&!['TABLE','VIEW','MATERIALIZED_VIEW'].includes(type)} checked={types.includes(type)} onCheckedChange={v => setTypes(v ? [...types,type] : types.filter(t => t !== type))}/>{typeLabel(type)}</label>)}</div>
      <CaptureFilterFields prefix="comparison" names={objectNames} dataTypes={dataTypes} related={related} onNames={setObjectNames} onDataTypes={value=>{setDataTypes(value);if(value.trim())setTypes(previous=>previous.filter(type=>['TABLE','VIEW','MATERIALIZED_VIEW'].includes(type)))}} onRelated={setRelated} disabled={!admin}/>
      <div className="policy-row"><label><Switch disabled={!admin} checked={technical} onCheckedChange={setTechnical}/><span>{t("Teknik nesneleri kapsam dışında tut") }</span></label><label><Switch disabled={!admin} checked={physical} onCheckedChange={setPhysical}/><span>{t("Fiziksel depolama özelliklerini karşılaştır") }</span></label></div>
      {kind === 'GIT' && <details className="advanced"><summary>{t("Gelişmiş Git ayarları") }</summary><div className="two-fields"><div className="field"><Label htmlFor="roots">{t("Şema kökleri") }</Label><Input id="roots" value={roots} disabled={!admin} onChange={e=>setRoots(e.target.value)} placeholder="TTBP=ttbp, APP=app"/><small>{t("Boşsa küçük harfli şema adı kullanılır.") }</small></div><div className="field"><Label htmlFor="semantics">{t("Kaynak uzunluk semantiği") }</Label><ChoiceSelect id="semantics" value={length} disabled={!admin} onChange={e=>setLength(e)}><option value="UNKNOWN">{t("Doğrulanmamış") }</option><option value="BYTE">BYTE</option><option value="CHAR">CHAR</option></ChoiceSelect></div></div></details>}
    </CardContent></Card>
    <div className="form-footer"><div className="form-actions">{admin && <Button variant="outline" disabled={busy} onClick={()=>void submit(false)}><Save/>{' '}{t("Profili kaydet") }</Button>}<Button disabled={busy || (!admin && !selected)} onClick={()=>void submit(true)}><Play/>{busy ? t("Hazırlanıyor…") : t("Karşılaştırmayı başlat")}</Button></div></div>
  </div>
}
