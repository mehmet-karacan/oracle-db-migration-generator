"""Şema Karşılaştırma planındaki kaynak ve hedef alanlarını yan yana sunar.

Yeni fark veya SQL kararı üretmez. After kaynak, before hedeftir.
Kayıtlı bütün farklar korunur. Uzun değerler sınırlı HTML sayfalarına bölünür.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import hashlib
import json
import re
from math import ceil

from .labels import object_label,type_label


FIELD_LABELS={
    'data_type':'Veri Tipi','length':'Uzunluk','precision':'Hassasiyet','scale':'Ölçek',
    'nullable':'NULL İzni','default':'Varsayılan Değer','length_semantics':'Uzunluk Semantiği',
    'fractional_precision':'Saniye Hassasiyeti','collation':'Karşılaştırma Düzeni',
    'identity':'Kimlik Kolonu','virtual':'Sanal Kolon','hidden':'Gizli Kolon','position':'Kolon Sırası',
    'exists':'Varlık','presence':'Nesne Varlığı','kind':'Tür','columns':'Kolonlar','condition':'Koşul',
    'enabled':'Etkinlik','validation':'Doğrulama','deferrable':'Ertelenebilirlik',
    'initially':'Başlangıç Durumu','delete_rule':'Silme Kuralı','unique':'Benzersizlik',
    'keys':'İndeks Kolonları','visibility':'Görünürlük','availability':'Kullanılabilirlik',
    'target':'Bağlı Tablo','definition':'Nesne Tanımı','ddl':'DDL Kapsamı','body':'Gövde',
    'increment_by':'Artış','cache':'Önbellek','min_value':'En Küçük Değer','max_value':'En Büyük Değer',
    'start_with':'Başlangıç','directions':'Sıralama Yönleri','default_on_null':'NULL İçin Varsayılan',
    'virtual_expression':'Sanal Kolon İfadesi','reference':'Referans','index_association':'İndeks İlişkisi',
    'rely':'Güven Durumu','partitioning':'Bölümleme','partition_key':'Bölüm Anahtarı',
    'compression':'Sıkıştırma','tablespace':'Tablo Alanı','logging':'Loglama','parallel':'Paralellik',
    'cycle':'Döngü','order':'Sıralama','editionable':'Sürüm Desteği','coverage':'Bilgi Kapsamı',
    'text':'Açıklama Metni','privileges':'Yetkiler','name':'Ad','status':'Durum','query':'Sorgu',
}
KINDS={'CHANGED':'Özellikleri Farklı','MISSING':'Hedefte Eksik','EXTRA':'Hedefte Fazla',
       'UNKNOWN':'Doğrulanamadı','INFORMATIONAL':'Bilgi'}
COLUMN_TOKEN_FIELDS={'data_type','default','identity','virtual_expression'}


def identity_key(identity):
    """Planın kanonik nesne anahtarını ad veya şema tahmini yapmadan hesaplar."""
    values=[identity.get(k) for k in ('profile_id','owner','object_type','name','parent_key')]
    return hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def path_parts(path):
    return [p.replace('~1','/').replace('~0','~') for p in path.strip('/').split('/')]


def token_value_path(path):
    """Yalnız canonical_fields tarafından SQL tokenı olarak üretilen yolları seçer."""
    parts=path_parts(path)
    return (parts==['definition'] or parts[0] in {'constraints','table_properties','index'}
            or parts[0]=='columns' and len(parts)>=3 and parts[-1] in COLUMN_TOKEN_FIELDS)


def field_context(path):
    parts=path_parts(path)
    root=parts[0]
    group=('Kolon '+parts[1] if root=='columns' and len(parts)>=3
           else 'Kısıt '+parts[1] if root=='constraints' and len(parts)>=3
           else {'index':'İndeks Özellikleri','sequence':'Sıra Numarası Özellikleri',
                 'table_properties':'Tablo Özellikleri','trigger':'Tetikleyici Özellikleri'}.get(root,'Nesne Özellikleri'))
    return group,FIELD_LABELS.get(parts[-1],parts[-1].replace('_',' ') or 'Nesne')


def metadata_text(item,path):
    """Durumları ve SQL token metadata değerini kaybetmeden okunabilir metne çevirir."""
    state=item['state']
    if state!='KNOWN':
        return {'UNKNOWN':'Bilgi Doğrulanamadı','ABSENT':'Nesne Bulunmuyor' if path_parts(path)[-1] in {'exists','presence'} else 'Alan Bulunmuyor',
                'NOT_APPLICABLE':'Uygulanamaz'}.get(state,'Bilgi Doğrulanamadı')
    value=item.get('value')
    if value is None:return 'NULL'
    if value=='':return 'Boş Metin'
    if isinstance(value,bool):
        field=path_parts(path)[-1]
        if field in {'exists','presence'}:return 'Nesne Var' if value else 'Nesne Bulunmuyor'
        if field=='nullable':return 'NULL Kabul Eder' if value else 'NULL Kabul Etmez'
        if field=='enabled':return 'Etkin' if value else 'Etkin Değil'
        return 'Evet' if value else 'Hayır'
    tokens=value
    tokenized=token_value_path(path)
    if isinstance(value,str) and value.startswith('[[') and tokenized:
        try:tokens=json.loads(value)
        except ValueError:pass
    if tokenized and isinstance(tokens,list) and tokens and all(isinstance(t,(tuple,list)) and len(t)==2
            and t[0] in {'code','quoted','literal','hint'} and isinstance(t[1],str) for t in tokens):
        result=''
        for index,(tag,token) in enumerate(tokens):
            previous=tokens[index-1] if index else None
            close=tag=='code' and token in {'.',',',')',';'}
            after_open=previous and previous[0]=='code' and previous[1] in {'.','('}
            displayed='"'+token.replace('"','""')+'"' if tag=='quoted' else token
            result+=(' ' if index and not close and not after_open else '')+displayed
        return result
    if isinstance(value,(dict,list)):
        def readable(child):
            if isinstance(child,str) and child.startswith('[[') and tokenized:
                return metadata_text({'state':'KNOWN','value':child},path)
            if isinstance(child,list):return [readable(item) for item in child]
            if isinstance(child,dict):return {key:readable(item) for key,item in child.items()}
            return child
        return json.dumps(readable(value),ensure_ascii=False,indent=2)
    return str(value)


def comparison_catalog(document):
    """Farkları kanonik kimlik ve açık change_ids bağlantılarıyla nesneye bağlar."""
    objects={}
    by_id={row['id']:row for row in document['differences']}
    def get(key,identity=None):
        if not isinstance(key,str) or not re.fullmatch(r'[a-f0-9]{64}',key):
            raise ValueError('REPORT_COMPARISON_KEY_INVALID')
        return objects.setdefault(key,{'key':key,'label':object_label(identity) if identity else 'Kimliği Kayıtlı Olmayan Nesne '+key[:12],
            'type':identity['object_type'] if identity else 'UNKNOWN',
            'type_label':type_label(identity['object_type']) if identity else 'Nesne','changes':{}})
    for op in document['operations']:get(identity_key(op['object']),op['object'])
    for row in document['differences']:get(row['object_key'])['changes'][row['id']]=row
    for op in document['operations']:
        obj=get(identity_key(op['object']),op['object'])
        for change in op['change_ids']:
            if change in by_id:obj['changes'][change]=by_id[change]
    result={}
    for key,obj in objects.items():
        if not obj['changes']:continue
        rows=[]
        for row in sorted(obj['changes'].values(),key=lambda r:(r['property_path'],r['id'])):
            group,field=field_context(row['property_path'])
            rows.append({'id':row['id'],'path':row['property_path'],'group':group,'field':field,
                         'kind':row['kind'],'kind_label':KINDS[row['kind']],
                         'source':metadata_text(row['after'],row['property_path']),
                         'target':metadata_text(row['before'],row['property_path']),
                         'source_state':row['after']['state'],'target_state':row['before']['state']})
        preview=[{**row,'source':row['source'][:180],'target':row['target'][:180],
                  'clipped':len(row['source'])>180 or len(row['target'])>180,'part':1,'parts':1} for row in rows[:3]]
        result[key]={k:v for k,v in obj.items() if k!='changes'}|{
            'rows':rows,'preview':preview,'total':len(rows),'path':f'comparison/{key}-0001.html'}
    return result


def attach_comparisons(groups,catalog):
    for group in groups:
        comparison=catalog.get(identity_key(group['operations'][0]['object']))
        group['comparison']=comparison
    return groups


def _chunks(rows):
    for row in rows:
        parts=max(1,ceil(max(len(row['source']),len(row['target']))/2000))
        for part in range(parts):
            yield {**row,'source':row['source'][part*2000:(part+1)*2000],
                   'target':row['target'][part*2000:(part+1)*2000],
                   'part':part+1,'parts':parts,'clipped':False}


def page_numbers(page,total):
    return sorted({1,total,*range(max(1,page-2),min(total,page+2)+1)})


def render_comparisons(catalog,template,index_template,context):
    """Bütün fark değerlerini 200 KiB sınırını aşmadan statik HTML olarak üretir."""
    result={}
    for obj in catalog.values():
        rows=list(_chunks(obj['rows']))
        batches=[]
        offset=0
        def render(batch,page,total):
            return template.render(obj=obj,rows=batch,prefix='../',context=context,
                back_href='../index.html',back_label='Hedef Ayrıntılarına Dön',
                page=page,pages=total,page_links=page_numbers(page,total)).encode()
        while offset<len(rows):
            count=min(30,len(rows)-offset)
            while len(render(rows[offset:offset+count],len(batches)+1,len(rows)))>190*1024:
                if count==1:raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
                count=max(1,count//2)
            batches.append(rows[offset:offset+count]);offset+=count
        for page,batch in enumerate(batches,1):
            raw=render(batch,page,len(batches))
            if len(raw)>200*1024:raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
            result[f'comparison/{obj["key"]}-{page:04d}.html']=raw
    objects=sorted(catalog.values(),key=lambda obj:(obj['label'],obj['type'],obj['key']))
    total=max(1,ceil(len(objects)/50))
    for page in range(1,total+1):
        raw=index_template.render(objects=objects[(page-1)*50:page*50],total=len(objects),
            prefix='../',context=context,back_href='../index.html',back_label='Hedef Ayrıntılarına Dön',
            page=page,pages=total,page_links=page_numbers(page,total)).encode()
        if len(raw)>200*1024:raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
        result[f'comparison/index-{page:04d}.html']=raw
    return result
