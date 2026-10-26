import {translate as t,displayName,localeTag} from './preferences'
import type {Run} from './api'

export type ResultTarget={id:string;name:string}
export type ResultValue={state:'KNOWN'|'ABSENT'|'UNKNOWN'|'NOT_APPLICABLE';value:unknown;omitted?:boolean}
export type FieldDifference={id:string;property_path:string;kind:string;source:ResultValue;target:ResultValue;evidence_ids?:string[]}
export type ResultObject={key:string;owner:string;name:string;display_name?:string|null;object_type:string;difference_count:number;operation_count:number;decisions:string[];difference_kinds?:string[]}
export type ObjectPage={available:boolean;total:number|null;total_objects?:number;unknown_count?:number;observed_difference_count?:number;rows:ResultObject[];counts?:Record<string,number>;scope?:Record<string,string>}
export type ResultGroup={id:string;name:string;entity_type:string;section:string;status:string;unknown_count:number;difference_count:number;operation_ids:string[];rows:FieldDifference[]}
export type StructureSummary={group_count:number;unknown_count:number;object_presence:string|null;items:{entity_type:string;status:string;count:number}[]}
export type ObjectDetail={groups?:ResultGroup[];group_total?:number;group_sections?:Record<string,number>;summary?:StructureSummary;object_operation_total?:number;key:string;owner:string;name:string;display_name?:string|null;object_type:string;total:number;rows:FieldDifference[];sections:Record<string,number>;operations:{id:string;kind:string;decision:string;reason_tr:string;change_ids:string[];depends_on:string[];evidence_ids:string[];sql_url:string|null}[];operation_total:number;operation_page:number;recorded_differences_only:boolean}

export function resultTargets(run:Run):ResultTarget[]{return (run.spec?.profile.target_ids||[]).map(id=>({id,name:displayName(run.spec?.connections[id]?.name||id)}))}
export function valueText(value:ResultValue){
  if(value.state==='UNKNOWN')return t('Bilinmiyor')
  if(value.state==='ABSENT')return t('Yok')
  if(value.state==='NOT_APPLICABLE')return t('Uygulanamaz')
  if(value.omitted)return t('Tanım arşivde')
  if(value.value===null)return 'NULL'
  if(value.value==='')return t('Boş metin')
  if(typeof value.value==='boolean')return value.value?t('Evet'):t('Hayır')
  return typeof value.value==='object'?JSON.stringify(value.value):String(value.value)
}
export function metadataValueText(value:ResultValue){
  if(value.state!=='KNOWN'||value.omitted)return valueText(value)
  let tokens:unknown=value.value
  if(typeof tokens==='string'&&tokens.startsWith('[['))try{tokens=JSON.parse(tokens)}catch{return valueText(value)}
  if(!Array.isArray(tokens)||!tokens.length||!tokens.every(item=>Array.isArray(item)&&item.length===2&&['code','quoted','literal','hint'].includes(item[0])&&typeof item[1]==='string'))return valueText(value)
  return (tokens as [string,string][]).reduce((text,[tag,token],index,all)=>{
    const previous=all[index-1],close=tag==='code'&&['.',',',')',';'].includes(token),afterOpen=previous?.[0]==='code'&&['.','('].includes(previous[1])
    const displayed=tag==='quoted'?'"'+token.replaceAll('"','""')+'"':token
    return text+(index&&!close&&!afterOpen?' ':'')+displayed
  },'')
}
export const differenceLabel=(kind:string)=>t({CHANGED:'Farklı',MISSING:'Hedefte Eksik',EXTRA:'Hedefte Fazla',UNKNOWN:'Doğrulanamadı',INFORMATIONAL:'Bilgi'}[kind]||kind)
const fieldNames:Record<string,string>={data_type:'Veri tipi',length:'Uzunluk',precision:'Hassasiyet',scale:'Ölçek',nullable:'NULL izni',default:'Varsayılan değer',length_semantics:'Uzunluk semantiği',fractional_precision:'Saniye hassasiyeti',collation:'Karşılaştırma düzeni',identity:'Kimlik kolonu',virtual:'Sanal kolon',hidden:'Gizli kolon',position:'Kolon sırası',exists:'Varlık',presence:'Nesne varlığı',kind:'Tür',columns:'Kolonlar',condition:'Koşul',enabled:'Etkinlik',validation:'Doğrulama',deferrable:'Ertelenebilirlik',initially:'Başlangıç durumu',delete_rule:'Silme kuralı',unique:'Benzersizlik',keys:'İndeks kolonları',visibility:'Görünürlük',availability:'Kullanılabilirlik',target:'Bağlı tablo',definition:'Nesne tanımı',ddl:'DDL kapsamı',increment_by:'Artış',cache:'Önbellek',min_value:'En küçük değer',max_value:'En büyük değer',start_with:'Başlangıç',directions:'Sıralama yönleri',default_on_null:'NULL için varsayılan',virtual_expression:'Sanal kolon ifadesi',reference:'Referans',index_association:'İndeks ilişkisi',rely:'Güven durumu',partitioning:'Bölümleme',partition_key:'Bölüm anahtarı',compression:'Sıkıştırma',tablespace:'Tablo alanı',logging:'Loglama',parallel:'Paralellik'}
export function fieldTitle(path:string){const parts=path.split('/').filter(Boolean).map(p=>p.replaceAll('~1','/').replaceAll('~0','~'));const label=t(fieldNames[parts.at(-1)||'']||parts.at(-1)||path);return {name:['columns','constraints'].includes(parts[0])?parts[1]:label,label}}

export function objectName(obj:{owner:string;name:string;display_name?:string|null}){return obj.display_name||`${obj.owner?obj.owner+'.':''}${obj.name}`}

export const entityLabel=(entity:string)=>t({COLUMN:'Kolon',FOREIGN_KEY:'Yabancı Anahtar',PRIMARY_KEY:'Birincil Anahtar',UNIQUE_KEY:'Benzersiz Anahtar',CHECK_CONSTRAINT:'Kontrol Kısıtı',CONSTRAINT:'Kısıt',INDEX:'İndeks',SEQUENCE:'Sıra Numarası',OBJECT_PROPERTY:'Nesne Özellikleri'}[entity]||entity)
export const structureStatus=(status:string)=>t({MISSING:'Hedefte Eksik',EXTRA:'Hedefte Fazla',CHANGED:'Özellikleri Farklı',UNKNOWN:'Doğrulanamadı',INFORMATIONAL:'Bilgi'}[status]||status)
export function legacyGroups(rows:FieldDifference[]):ResultGroup[]{
 const groups=new Map<string,ResultGroup>()
 for(const row of rows){const parts=row.property_path.split('/').filter(Boolean);const child=['columns','constraints'].includes(parts[0])&&parts.length>=3;const id='/'+parts.slice(0,child?2:1).join('/')
  if(!groups.has(id))groups.set(id,{id,name:child?parts[1].replaceAll('~1','/').replaceAll('~0','~'):'',entity_type:parts[0]==='columns'?'COLUMN':parts[0]==='constraints'?'CONSTRAINT':'OBJECT_PROPERTY',section:parts[0],status:'CHANGED',unknown_count:0,difference_count:0,operation_ids:[],rows:[]})
  const group=groups.get(id)!;group.rows.push(row);group.difference_count++;if(row.kind==='UNKNOWN'){group.unknown_count++;group.status='UNKNOWN'}
 }
 return [...groups.values()]
}

export function entityCountLabel(entity:string,count:number){
 if(localeTag()==='en-GB'&&count!==1)return ({COLUMN:'Columns',FOREIGN_KEY:'Foreign Keys',PRIMARY_KEY:'Primary Keys',UNIQUE_KEY:'Unique Keys',CHECK_CONSTRAINT:'Check Constraints',CONSTRAINT:'Constraints',INDEX:'Indexes',SEQUENCE:'Sequences',OBJECT_PROPERTY:'Object Property Groups'} as Record<string,string>)[entity]||entityLabel(entity)
 return entityLabel(entity)
}
