import {ChoiceSelect} from './ChoiceSelect'
import {translate as t} from './preferences'
import { useState } from 'react'
import { FolderOpen, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from './api'
import type { Project } from './api'

export function ProjectSwitcher({projects,selected,onSelect,onCreated}:{projects:Project[];selected:string;onSelect:(id:string)=>void;onCreated:(project:Project)=>void}) {
  const [open,setOpen]=useState(false),[name,setName]=useState(''),[code,setCode]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  async function save(){setBusy(true);setError('');try{const project=await api<Project>('/projects',{name,code});onCreated(project);setOpen(false);setName('');setCode('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  return <div className="project-switcher"><FolderOpen size={16}/><ChoiceSelect aria-label={t("Proje")} value={selected} onChange={e=>onSelect(e)}>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</ChoiceSelect><Button variant="ghost" size="icon" aria-label={t("Proje ekle")} onClick={()=>setOpen(true)}><Plus size={15}/></Button>
    <Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogHeader><DialogTitle>{t("Yeni proje") }</DialogTitle><DialogDescription>{t("Bağlantılar, karşılaştırma profilleri ve çalışmalar bu projeye ait olacak.") }</DialogDescription></DialogHeader><div className="field-stack">{error&&<div role="alert" className="error-banner">{t(error)}</div>}<div className="field"><Label htmlFor="project-name">{t("Proje adı") }</Label><Input id="project-name" value={name} onChange={e=>setName(e.target.value)}/></div><div className="field"><Label htmlFor="project-code">{t("Proje kodu") }</Label><Input id="project-code" placeholder="SKY" value={code} onChange={e=>setCode(e.target.value.toUpperCase())}/><small>{t("Harf, rakam, alt çizgi veya tire kullanın.") }</small></div><Button disabled={busy||!name.trim()||!code.trim()} onClick={()=>void save()}>{busy?t('Kaydediliyor…'):t("Projeyi oluştur")}</Button></div></DialogContent></Dialog>
  </div>
}
