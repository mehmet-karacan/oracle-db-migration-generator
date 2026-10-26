import {useEffect,useState} from 'react'
import {ArrowUpRight,FileCode2,LoaderCircle} from 'lucide-react'
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from '@/components/ui/dialog'
import {Button} from '@/components/ui/button'
import {translate as t} from './preferences'
import {projectHeaders} from './api'

export type SqlFile={title:string;url:string}
type Props={file:SqlFile;onClose:()=>void}
export function SqlViewer(props:Props){return <SqlDocument key={props.file.url} {...props}/>}
function SqlDocument({file,onClose}:Props){
  const [sql,setSql]=useState<string|null>(null),[error,setError]=useState('')
  let url:URL|null=null
  try{url=new URL(file.url,window.location.origin)}catch{/* Render a bounded invalid-link message. */}
  const valid=!!url&&['http:','https:'].includes(url.protocol)
  const local=valid&&url!.origin===window.location.origin&&url!.pathname.startsWith('/api/runs/')
  useEffect(()=>{
    if(!local)return
    const controller=new AbortController()
    void fetch(file.url,{credentials:'same-origin',cache:'no-store',signal:controller.signal,headers:projectHeaders()}).then(async response=>{
      if(!response.ok)throw new Error(t('SQL dosyası alınamadı. Çalışmayı ve dosya erişimini kontrol edin.'))
      const text=await response.text()
      if(!controller.signal.aborted)setSql(text)
    }).catch(e=>{if(!controller.signal.aborted)setError(e.message)})
    return()=>controller.abort()
  },[file.url,local])
  return <Dialog open onOpenChange={open=>{if(!open)onClose()}}><DialogContent className="sql-viewer">
    <DialogHeader><DialogTitle><FileCode2 size={22}/>{t('SQL Görüntüleyici')}</DialogTitle><DialogDescription>{file.title}</DialogDescription></DialogHeader>
    {!valid?<p role="alert">{t('SQL bağlantısı geçersiz.')}</p>:!local?<div className="sql-archive-note"><FileCode2 size={32}/><h3>{t('SQL dosyası Jenkins arşivinde')}</h3><p>{t('Bu çalışma Jenkins üzerinde çalıştırıldı. Yerel kopyası oluşturulmaz. Yerel çalıştırılan işlerin SQL dosyaları bu görüntüleyicide açılır.')}</p><a href={file.url} target="_blank" rel="noreferrer"><Button><ArrowUpRight/>{t('Jenkins Arşivinde Aç')}</Button></a></div>:error?<p role="alert" className="error-banner">{t(error)}</p>:sql===null?<div role="status" className="empty-inline"><LoaderCircle className="spin"/>{t('SQL yükleniyor…')}</div>:<pre className="sql-document"><code data-testid="sql-content">{sql}</code></pre>}
    <div className="sql-viewer-footer"><span>{t('Salt okunur. Kaynak biçimi ve çift tırnaklar korunur.')}</span><Button variant="outline" onClick={onClose}>{t('Kapat')}</Button></div>
  </DialogContent></Dialog>
}
