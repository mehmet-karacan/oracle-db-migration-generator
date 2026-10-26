import {useEffect,useRef,useState} from 'react'
import {Download,Upload,FileJson,Package,LoaderCircle} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {Card,CardContent,CardHeader,CardTitle} from '@/components/ui/card'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Checkbox} from '@/components/ui/checkbox'
import {Badge} from '@/components/ui/badge'
import {ChoiceSelect} from './ChoiceSelect'
import {CaptureFilterFields} from './CaptureFilterFields'
import {captureRequest,typeLabel,objectTypes,filterValues} from './api'
import type {Connection} from './api'
import {translate as t,localeTag,displayName} from './preferences'

const ddlTypes=objectTypes.filter(type=>!['COMMENT','GRANT','MATERIALIZED_VIEW_LOG'].includes(type))
export function PortableCapture({projectId='',connections=[],admin,refresh}:{projectId?:string;connections?:Connection[];admin:boolean;refresh:()=>void}){
  const mounted=useRef(true),fileInput=useRef<HTMLInputElement>(null)
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[])
  const [schemas,setSchemas]=useState(''),[types,setTypes]=useState(ddlTypes),[names,setNames]=useState(''),[dataTypes,setDataTypes]=useState(''),[related,setRelated]=useState(true)
  const [filterSide,setFilterSide]=useState('SOURCE')
  const [environment,setEnvironment]=useState(''),[reader,setReader]=useState('AUTO'),[seconds,setSeconds]=useState('900'),[limit,setLimit]=useState('10000')
  const [name,setName]=useState(''),[file,setFile]=useState<File|null>(null),[busy,setBusy]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState('')
  function changeDataTypes(value:string){setDataTypes(value);if(value.trim())setTypes(previous=>previous.filter(type=>['TABLE','VIEW','MATERIALIZED_VIEW'].includes(type)))}
  async function download(){
    setError('');setNotice('');if(!types.length){setError(t('En az bir nesne türü seçin.'));return}setBusy('export')
    try{
      const body={schemas:filterValues(schemas),object_types:types,object_names:filterValues(names),data_types:filterValues(dataTypes),include_related:related,environment,filter_side:filterSide,reader_mode:reader,timeout_seconds:Number(seconds),max_objects:Number(limit)}
      const response=await captureRequest('package',JSON.stringify(body),'application/json',projectId)
      const blob=await response.blob();if(!mounted.current)return
      const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='oracle-capture.zip';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
      setNotice(t('Paket hazırlandı. Çalıştırma adımları ve parametreler paketteki README dosyasındadır.'))
    }catch(e){if(mounted.current)setError((e as Error).message)}finally{if(mounted.current)setBusy('')}
  }
  async function upload(){
    setError('');setNotice('')
    if(!file||!name.trim()){setError(t('Dosya adı girin ve metadata dosyasını seçin.'));return}
    if(file.size>64*1024*1024){setError(t('Metadata dosyası en fazla 64 MiB olabilir.'));return}
    setBusy('import')
    try{
      await captureRequest('import?name='+encodeURIComponent(name.trim()),file,'application/octet-stream',projectId)
      if(mounted.current){refresh();setNotice(t('Dosya projeye eklendi. Şema Eşleştirmeleri sekmesinde kaynak veya hedef olarak seçebilirsiniz.'));setName('');setFile(null);if(fileInput.current)fileInput.current.value=''}
    }catch(e){if(mounted.current)setError((e as Error).message)}finally{if(mounted.current)setBusy('')}
  }
  return <div className="portable-workspace field-stack">
    <div><h2>{t('Taşınabilir Toplama')}</h2><p className="muted">{t('Ortamda metadata toplayın, dosyayı bu projeye aktarın ve bağlantı açmadan karşılaştırın.')}</p></div>
    {error&&<div role="alert" className="error-banner">{t(error)}</div>}{notice&&<div role="status" className="success-banner">{t(notice)}</div>}
    {admin&&<div className="portable-grid"><Card><CardHeader><CardTitle className="card-heading"><Package/>{t('1. Toplama Paketini Hazırlayın')}</CardTitle></CardHeader><CardContent className="field-stack">
      <p className="micro-copy">{t('Mevcut SQL*Plus veya SQLcl ile çalışır. Üretim ortamına Python veya uygulama kurulmaz. Parola pakete yazılmaz.')}</p>
      <div className="field"><Label htmlFor="capture-side">{t('Toplama Amacı')}</Label><ChoiceSelect id="capture-side" value={filterSide} onChange={setFilterSide}><option value="SOURCE">{t('Kaynak Yapı')}</option><option value="TARGET">{t('Hedef Yapı')}</option></ChoiceSelect><small>{t('Hedef seçildiğinde veri tipi DDL okumayı daraltmaz. Hedefte tipi değişmiş nesneler korunur.')}</small></div><div className="two-fields"><div className="field"><Label htmlFor="capture-schemas">{t('Şemalar')}</Label><Input id="capture-schemas" value={schemas} onChange={e=>setSchemas(e.target.value)} placeholder="APP, TTBP"/><small>{t('Boşsa bağlanılan hesabın şeması kullanılır.')}</small></div><div className="field"><Label htmlFor="capture-environment">{t('Ortam Etiketi')}</Label><Input id="capture-environment" value={environment} onChange={e=>setEnvironment(e.target.value)} placeholder="PROD"/></div></div>
      <fieldset className="capture-types"><legend>{t('Nesne Türleri')}</legend><div className="type-grid">{ddlTypes.map(type=><label key={type}><Checkbox checked={types.includes(type)} disabled={!!dataTypes.trim()&&!['TABLE','VIEW','MATERIALIZED_VIEW'].includes(type)} onCheckedChange={checked=>setTypes(previous=>checked?[...previous,type]:previous.filter(v=>v!==type))}/>{typeLabel(type)}</label>)}</div></fieldset>
      <CaptureFilterFields names={names} dataTypes={dataTypes} related={related} onNames={setNames} onDataTypes={changeDataTypes} onRelated={setRelated}/>
      <details className="advanced"><summary>{t('Toplama Sınırları ve Yetki')}</summary><div className="field-stack"><div className="field"><Label htmlFor="capture-reader">{t('Metadata Okuma Kapsamı')}</Label><ChoiceSelect id="capture-reader" value={reader} onChange={setReader}><option value="AUTO">{t('Otomatik Doğrula')}</option><option value="OWN">{t('Hesabın Kendi Şeması')}</option><option value="CATALOG">{t('Yetkili Katalog')}</option><option value="VISIBLE">{t('Görünen Nesneler (Kısmi)')}</option></ChoiceSelect></div><div className="two-fields"><div className="field"><Label htmlFor="capture-seconds">{t('Süre Bütçesi (sn)')}</Label><Input type="number" id="capture-seconds" min="30" max="7200" value={seconds} onChange={e=>setSeconds(e.target.value)}/></div><div className="field"><Label htmlFor="capture-limit">{t('Nesne Sınırı')}</Label><Input type="number" id="capture-limit" min="1" max="100000" value={limit} onChange={e=>setLimit(e.target.value)}/></div></div></div></details>
      <Button disabled={!!busy} onClick={()=>void download()}>{busy==='export'?<LoaderCircle className="spin"/>:<Download/>}{t('Toplama Paketini İndir')}</Button>
    </CardContent></Card><Card><CardHeader><CardTitle className="card-heading"><Upload/>{t('2. Metadata Dosyasını İçe Aktarın')}</CardTitle></CardHeader><CardContent className="field-stack">
      <p className="micro-copy">{t('Paketi ayrı bir SQL oturumunda çalıştırın. Oluşan capture.odmg.jsonl dosyasını seçin. Dosya yalnız bu projede kullanılabilir.')}</p>
      <div className="field"><Label htmlFor="capture-name">{t('Dosya Adı')}</Label><Input id="capture-name" value={name} onChange={e=>setName(e.target.value)} placeholder={t('Örn. Üretim - 25 Ekim')}/></div>
      <div className="field"><Label htmlFor="capture-file">{t('Metadata Dosyası')}</Label><Input ref={fileInput} id="capture-file" type="file" accept=".jsonl,.json" onChange={e=>setFile(e.target.files?.[0]||null)}/><small>{t('En fazla 64 MiB. Sıra, bütünlük ve kapsam kontrol edilir. Dosyadaki SQL çalıştırılmaz.')}</small></div>
      <Button variant="outline" disabled={!!busy||!file||!name.trim()} onClick={()=>void upload()}>{busy==='import'?<LoaderCircle className="spin"/>:<Upload/>}{t('Dosyayı İçe Aktar')}</Button>
      <div className="capture-note"><FileJson/><p>{t('Eksik yetki veya okunamayan DDL, nesnenin yok olduğu anlamına gelmez. Bu kayıtlar karşılaştırmada belirsiz olarak gösterilir.')}</p></div>
    </CardContent></Card></div>}
    <div><h2>{t('Bu Projedeki Metadata Dosyaları')}</h2><div className="connection-grid">{connections.filter(c=>c.kind==='SNAPSHOT').map(c=><Card key={c.id}><CardContent className="field-stack"><div className="section-toolbar"><h3><FileJson size={19}/> {displayName(c.name)}</h3><Badge variant="secondary">{c.capture_summary?.inventory_complete?t('Tam Envanter'):t('Kısmi Görünürlük')}</Badge></div><p>{c.capture_schemas?.join(', ')}</p><p className="micro-copy">{c.capture_summary?.environment} - {c.capture_summary&&new Date(c.capture_summary.captured_at).toLocaleString(localeTag())}</p><small>{t('{0} nesne için DDL toplandı.',{0:c.capture_summary?.selected_objects||0})}</small></CardContent></Card>)}</div>{!connections.some(c=>c.kind==='SNAPSHOT')&&<p className="muted">{t('Henüz metadata dosyası eklenmedi.')}</p>}</div>
  </div>
}
