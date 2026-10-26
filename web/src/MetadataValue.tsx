import {useState} from 'react'
import {Button} from '@/components/ui/button'
import {translate as t} from './preferences'
import {fieldTitle,metadataValueText} from './resultApi'
import type {ResultValue} from './resultApi'

function StructuredValue({value,path,depth}:{value:object;path:string;depth:number}){
 const [limit,setLimit]=useState(20),[expanded,setExpanded]=useState(depth<3)
 const entries=Object.entries(value),array=Array.isArray(value)
 if(!expanded)return <Button size="sm" variant="ghost" onClick={()=>setExpanded(true)}>{t('İç İçe Değeri Aç')}</Button>
 return <div className="metadata-structure">{entries.slice(0,limit).map(([key,child])=><div key={key} className={array?'metadata-list-item':'metadata-property'}>{!array&&<span>{fieldTitle('/'+key).label}</span>}<MetadataValue value={{state:'KNOWN',value:child}} path={path+'/'+key} depth={depth+1}/></div>)}{entries.length>limit&&<Button variant="ghost" size="sm" onClick={()=>setLimit(n=>n+20)}>{t('Diğer Değerleri Göster')}</Button>}{!entries.length&&<span>{t(array?'Boş Liste':'Boş Yapı')}</span>}</div>
}
export function MetadataValue({value,path,depth=0}:{value:ResultValue;path:string;depth?:number}){
 const field=path.split('/').at(-1),presence=field==='exists'||field==='presence'
 let text=metadataValueText(value)
 if(value.state==='ABSENT')text=t(presence?'Nesne Yok':'Alan Bulunmuyor')
 if(value.state==='KNOWN'&&!value.omitted&&typeof value.value==='boolean'){
  if(presence)text=t(value.value?'Nesne Var':'Nesne Yok')
  else if(field==='nullable')text=t(value.value?'NULL Kabul Eder':'NULL Kabul Etmez')
  else if(field==='enabled')text=t(value.value?'Etkin':'Etkin Değil')
 }
 if(value.state==='KNOWN'&&!value.omitted&&value.value!==null&&typeof value.value==='object'&&text===JSON.stringify(value.value))return <StructuredValue value={value.value} path={path} depth={depth}/>
 return <span className={`result-value value-${value.state.toLowerCase()}${value.omitted?' value-omitted':''}`}>{text}</span>
}
