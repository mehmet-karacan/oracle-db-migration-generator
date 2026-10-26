import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Switch} from '@/components/ui/switch'
import {translate as t} from './preferences'

export function CaptureFilterFields({names,dataTypes,related,onNames,onDataTypes,onRelated,disabled=false,prefix='capture'}:{names:string;dataTypes:string;related:boolean;onNames:(v:string)=>void;onDataTypes:(v:string)=>void;onRelated:(v:boolean)=>void;disabled?:boolean;prefix?:string}){
  return <div className="capture-filter-fields field-stack"><div className="two-fields">
    <div className="field"><Label htmlFor={`${prefix}-names`}>{t('Nesne Adları')}</Label><Input id={`${prefix}-names`} value={names} onChange={e=>onNames(e.target.value)} disabled={disabled} placeholder="ORDERS, CUSTOMERS"/><small>{t('Boşsa tüm adlar. Virgülle ayırın, tam ad eşleşmesi kullanılır.')}</small></div>
    <div className="field"><Label htmlFor={`${prefix}-data-types`}>{t('Kolon Veri Tipleri')}</Label><Input id={`${prefix}-data-types`} value={dataTypes} onChange={e=>onDataTypes(e.target.value)} disabled={disabled} placeholder="NUMBER, VARCHAR2"/><small>{t('Tablo ve görünümler içindir. Eşleşen nesnenin tüm kolonları korunur.')}</small></div>
    </div><label className="capture-related"><Switch checked={related} onCheckedChange={onRelated} disabled={disabled}/><span>{t('İlgili İndeks, Tetikleyici ve Açıklamaları Dahil Et')}</span></label>
    <p className="micro-copy">{t('Filtreler birlikte uygulanır. Veri tipi seçimi kaynakta yapılır, hedefteki farklı veri tipi karşılaştırmada kalır.')}</p>
  </div>
}
