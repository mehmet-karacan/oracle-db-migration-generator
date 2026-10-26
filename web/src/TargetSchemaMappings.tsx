import {translate as t} from './preferences'
import { Checkbox } from '@/components/ui/checkbox'
import type { SchemaPair } from './api'

export function TargetSchemaMappings({name,schemas,value,disabled,onChange}:{name:string;schemas:string[];value:SchemaPair[];disabled:boolean;onChange:(pairs:SchemaPair[])=>void}) {
  return <fieldset className="schema-mappings"><legend>{name}{' '}{t("şema eşleştirmeleri") }</legend>
    {!schemas.length?<p className="micro-copy">{t("Önce kaynak şemalarını girin.") }</p>:<>
      <div className="schema-pair-heading"><span>{t("Kaynak şema") }</span><span>{t("Hedef şema") }</span></div>
      {schemas.map(schema=><label key={schema} className="schema-pair"><Checkbox disabled={disabled} aria-label={`${name}: ${schema} → ${schema}`} checked={value.some(m=>m.source_schema===schema&&m.target_schema===schema)} onCheckedChange={checked=>onChange(checked?[...value,{source_schema:schema,target_schema:schema}]:value.filter(m=>m.source_schema!==schema))}/><span>{schema}</span><span aria-hidden="true">→</span><span>{schema}</span></label>)}
      <p className="micro-copy">{t("Karşılaştırılacak çiftleri seçin. Farklı şema adları arasında dönüşüm desteklenmiyor.") }</p>
    </>}
  </fieldset>
}
