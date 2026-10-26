import {translate as t,displayName} from './preferences'
import type {Run} from './api'

export function RunSchemaScope({run}:{run:Run}) {
  const profile=run.spec?.profile,connections=run.spec?.connections
  if(!profile?.source.schemas?.length||!connections)return null
  const source=displayName(connections[profile.source.connection_id]?.name||t("Kaynak"))
  return <details className="run-schema-scope"><summary>{t("Karşılaştırılan şemalar") }</summary><table aria-label={t("Karşılaştırılan şemalar")}><thead><tr><th>{t("Kaynak bağlantı / şema") }</th><th>{t("Hedef bağlantı / şema") }</th></tr></thead><tbody>
    {profile.target_ids.flatMap(id=>(profile.target_mappings?.[id]||profile.source.schemas.map(s=>({source_schema:s,target_schema:s}))).map(pair=><tr key={`${id}-${pair.source_schema}`}><td>{source} / {pair.source_schema}</td><td>{displayName(connections[id]?.name||id)} / {pair.target_schema}</td></tr>))}
  </tbody></table></details>
}
