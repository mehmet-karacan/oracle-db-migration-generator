import {Database,GitCompareArrows,FileJson} from 'lucide-react'
import {translate as t} from './preferences'
import {Tabs,TabsList,TabsTrigger,TabsContent} from '@/components/ui/tabs'
import {Connections} from './Connections'
import {SchemaMappings} from './SchemaMappings'
import {PortableCapture} from './PortableCapture'
import type {Connection,SchemaMapping} from './api'

export function ConnectionWorkspace(props:{projectId?:string;connections:Connection[];mappings:SchemaMapping[];admin:boolean;refresh:()=>void}) {
  return <Tabs defaultValue="connections"><TabsList className="connection-workspace-tabs"><TabsTrigger value="connections"><Database size={18}/>{t("Bağlantılar") }<span className="tab-count" aria-hidden="true">{props.connections.filter(c=>c.kind!=='SNAPSHOT').length}</span></TabsTrigger><TabsTrigger value="mappings"><GitCompareArrows size={18}/>{t("Şema Eşleştirmeleri")}<span className="tab-count" aria-hidden="true">{props.mappings.length}</span></TabsTrigger><TabsTrigger value="portable"><FileJson size={18}/>{t("Taşınabilir Toplama")}<span className="tab-count" aria-hidden="true">{props.connections.filter(c=>c.kind==='SNAPSHOT').length}</span></TabsTrigger></TabsList>
    <TabsContent value="connections"><Connections {...props} connections={props.connections.filter(c=>c.kind!=='SNAPSHOT')}/></TabsContent>
    <TabsContent value="mappings"><SchemaMappings {...props}/></TabsContent>
    <TabsContent value="portable"><PortableCapture {...props}/></TabsContent>
  </Tabs>
}
