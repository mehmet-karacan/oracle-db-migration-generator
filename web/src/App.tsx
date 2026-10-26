import {BrandLogo} from './BrandLogo'
import {usePreferences,translate as t,localeTag} from './preferences'
import { lazy,Suspense,useCallback,useEffect,useRef,useState } from 'react'
import { ArrowRight,Database,GitBranch,LayoutDashboard,Settings2,History,Plus,LogOut,LoaderCircle,ShieldCheck,Activity,FileJson } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card,CardContent } from '@/components/ui/card'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Table,TableHeader,TableBody,TableHead,TableRow,TableCell } from '@/components/ui/table'
import { ComparisonForm } from './ComparisonForm'
import { ConnectionWorkspace } from './ConnectionWorkspace'
import { SettingsPage } from './SettingsPage'
import {AuthGate} from './AuthGate'
import {UiPreferences} from './UiPreferences'
import { ProjectSwitcher } from './ProjectSwitcher'
import { api,duration,statusLabel,stageLabel,setProjectScope } from './api'
import type { Connection,Profile,Run,Session,Settings,Project,SchemaMapping } from './api'

type Page='new'|'history'|'connections'|'settings'|'run'
const RunDetail=lazy(()=>import('./RunDetail').then(module=>({default:module.RunDetail})))
const titles:Record<Page,[string,string]>={new:['Yeni karşılaştırma','Kaynak yapıyı seçin, hedefleri karşılaştırın ve DDL planını inceleyin.'],history:['Çalışmalar','Başlatılan karşılaştırmalar, aşamalar ve üretilen sonuçlar.'],connections:['Bağlantılar','Git depoları, Oracle bağlantıları ve metadata dosyaları tek yerde.'],settings:['Uygulama ayarları','Yeni çalışmaların varsayılanlarını ve işletim sınırlarını yönetin.'],run:['Çalışma ayrıntısı','']}

function Workspace({onLogout}:{onLogout:()=>void}) {
  usePreferences()
  const [page,setPage]=useState<Page>('new'),[runId,setRunId]=useState(''),[session,setSession]=useState<Session|null>(null),[error,setError]=useState('')
  const [connections,setConnections]=useState<Connection[]>([]),[profiles,setProfiles]=useState<Profile[]>([]),[runs,setRuns]=useState<Run[]>([]),[settings,setSettings]=useState<Settings|null>(null)
  const [projects,setProjects]=useState<Project[]>([]),[projectId,setProjectId]=useState(''),[refreshVersion,setRefreshVersion]=useState(0)
  const [mappings,setMappings]=useState<SchemaMapping[]>([])
  const projectEpoch=useRef(0)
  const refresh=useCallback(()=>setRefreshVersion(n=>n+1),[])
  useEffect(()=>{let active=true;let loading=false;const epoch=projectEpoch.current
    async function load(){if(loading)return;loading=true;try{
      const [who,available]=await Promise.all([api<Session>('/session'),api<Project[]>('/projects')]);if(!active||epoch!==projectEpoch.current)return
      setSession(who);setProjects(available)
      const chosen=available.find(p=>p.id===projectId)?.id||available[0]?.id||''
      setProjectScope(chosen)
      if(chosen!==projectId){setProjectId(chosen);return}if(!chosen)return
      const suffix=`?project_id=${encodeURIComponent(chosen)}`
      const [c,p,r,s,m]=await Promise.all([api<Connection[]>('/connections'+suffix),api<Profile[]>('/profiles'+suffix),api<Run[]>('/runs'+suffix),['admin','shared'].includes(who.role)?api<Settings>('/settings'):Promise.resolve(null),api<SchemaMapping[]>('/schema-mappings'+suffix)])
      if(active&&epoch===projectEpoch.current){setConnections(c);setProfiles(p);setRuns(r);setSettings(s);setMappings(m);setError('')}
    }catch(e){if(active&&epoch===projectEpoch.current)setError((e as Error).message)}finally{loading=false}}
    void load();const timer=setInterval(()=>void load(),5000);return()=>{active=false;clearInterval(timer)}
  },[projectId,refreshVersion])
  const chooseProject=(id:string)=>{projectEpoch.current++;setProjectScope(id);setConnections([]);setProfiles([]);setRuns([]);setMappings([]);setSettings(null);setError('');setRunId('');setPage('new');setProjectId(id)}
  const canEdit=!!session&&['admin','shared'].includes(session.role)
  const openRun=(id:string)=>{setRunId(id);setPage('run');void refresh()}
  const active=runs.filter(r=>['RUNNING','QUEUED'].includes(r.status)).length
  const menu=[{id:'new' as Page,label:t("Yeni karşılaştırma"),icon:LayoutDashboard},{id:'history' as Page,label:t("Çalışmalar"),icon:History},{id:'connections' as Page,label:t("Bağlantılar"),icon:Database},...(canEdit?[{id:'settings' as Page,label:t('Ayarlar'),icon:Settings2}]:[])]
  return <TooltipProvider><div className="app-shell"><aside className="sidebar"><div className="brand"><BrandLogo/><span>{t('Şema Karşılaştırma')}</span></div><nav aria-label={t("Ana menü")}>{menu.map(item=><button key={item.id} aria-label={item.label} title={item.label} onClick={()=>setPage(item.id)} className={(page===item.id||(page==='run'&&item.id==='history'))?'active':''}><item.icon size={18}/><span>{item.label}</span>{item.id==='history'&&active>0&&<span className="nav-count">{active}</span>}</button>)}</nav><div className="sidebar-bottom"><ShieldCheck size={17}/><div><strong>{t("Salt okunur karşılaştırma") }</strong><small>{t("DDL üretir, veri tabanına uygulamaz.") }</small></div></div></aside>
    <div className="app-body"><header className="topbar"><div className="topbar-location"><ProjectSwitcher projects={projects} selected={projectId} onSelect={chooseProject} onCreated={p=>{setProjects(items=>[...items,p]);chooseProject(p.id);refresh()}}/></div><div className="topbar-right"><UiPreferences/><span className="api-status"><span className={error?'offline':'online'}/>{session?t("Sunucuya bağlı"):t("Bağlanıyor")}</span>{session?.display_name&&<span className="signed-in-user">{session.display_name}</span>}{session?.mode==='password'&&<Button variant="ghost" size="icon" aria-label={t('Çıkış Yap')} title={t('Çıkış Yap')} onClick={onLogout}><LogOut/></Button>}</div></header>
      <main><div className="page-inner">{page!=='run'&&<div className="page-heading"><div><h1>{t(titles[page][0])}</h1><p>{t(titles[page][1])}</p></div>{page==='history'&&<Button onClick={()=>setPage('new')}><Plus/>{t("Yeni karşılaştırma") }</Button>}</div>}
      {error&&<div role="alert" className="error-banner">{t(error)}<Button variant="ghost" size="sm" onClick={()=>void refresh()}>{t("Yeniden dene") }</Button></div>}
      {!session&&!error&&<div className="empty-state"><LoaderCircle className="spin"/><p>{t("Uygulamaya bağlanılıyor…") }</p></div>}
      {session&&page==='new'&&<><div className="overview-strip"><div className="overview-git"><GitBranch/><span>{t("Git deposu") }<strong>{connections.filter(c=>c.kind==='GIT').length}</strong></span></div><div className="overview-oracle"><Database/><span>{t("Oracle bağlantısı") }<strong>{connections.filter(c=>c.kind==='ORACLE').length}</strong></span></div><div className="overview-active"><Activity/><span>{t("Devam eden iş") }<strong>{active}</strong></span></div><div className="overview-hint">{connections.some(c=>c.kind==='SNAPSHOT')?<><FileJson/><span>{t('Metadata Dosyası')}<strong>{connections.filter(c=>c.kind==='SNAPSHOT').length}</strong></span></>:<><ShieldCheck/><p>{t("Bir kaynak,") }<br/>{t("bir veya birden çok hedef.") }</p></>}</div></div><ComparisonForm localExecution={session.local_execution_available} key={projectId} projectId={projectId} connections={connections} profiles={profiles} mappings={mappings} admin={canEdit} onSaved={()=>void refresh()} onStarted={openRun}/></>}
      {session&&page==='connections'&&<ConnectionWorkspace key={projectId} projectId={projectId} connections={connections} mappings={mappings} admin={canEdit} refresh={()=>void refresh()}/>}
      {session&&page==='settings'&&settings&&<SettingsPage key={projectId} projectId={projectId} initial={settings} hasSchedule={projects.find(p=>p.id===projectId)?.code==='SKY'} local={session.artifact_mode==='LOCAL_DEVELOPMENT'} onSaved={()=>void refresh()}/>}
      {session&&page==='run'&&<Suspense fallback={<div role="status">{t('Sonuçlar yükleniyor…')}</div>}><RunDetail key={runId} id={runId} back={()=>setPage('history')}/></Suspense>}
      {session&&page==='history'&&<><div className="history-summary"><Badge variant="secondary">{runs.length} {t('çalışma')}</Badge><span>{active}{' '}{t("devam eden iş") }</span></div><Card className="history-card">{runs.length?<Table><TableHeader><TableRow><TableHead>{t("Çalışma") }</TableHead><TableHead>{t("Durum") }</TableHead><TableHead>{t("Aşama") }</TableHead><TableHead>{t("Süre") }</TableHead><TableHead/></TableRow></TableHeader><TableBody>{runs.map(run=><TableRow key={run.id} className="click-row" onClick={()=>openRun(run.id)}><TableCell><div className="object-cell"><strong>{run.profile_name||`#${run.id.slice(0,8)}`}</strong><small>{new Date(run.created_at).toLocaleString(localeTag())}</small></div></TableCell><TableCell><Badge variant="secondary" className={`status-${run.status.toLowerCase()}`}>{statusLabel(run.status)}</Badge></TableCell><TableCell>{stageLabel(run.stage)}</TableCell><TableCell>{duration(run.started_at,run.finished_at)}</TableCell><TableCell><Button variant="ghost" size="icon" aria-label={t("Çalışmayı aç")} onClick={e=>{e.stopPropagation();openRun(run.id)}}><ArrowRight/></Button></TableCell></TableRow>)}</TableBody></Table>:<CardContent><div className="empty-state"><History/><h3>{t("Henüz karşılaştırma başlatılmadı") }</h3><p>{t("Kaynak ve hedeflerinizi seçtikten sonra ilk çalışmayı burada takip edebilirsiniz.") }</p><Button variant="outline" onClick={()=>setPage('new')}>{t("Yeni karşılaştırma") }</Button></div></CardContent>}</Card></>}
      </div></main><footer className="company-footer">{t('© 2026 İnnova Bilişim Çözümleri A.Ş.')}</footer>
    </div></div></TooltipProvider>
}

export default function App(){return <AuthGate>{logout=><Workspace onLogout={logout}/>}</AuthGate>}
