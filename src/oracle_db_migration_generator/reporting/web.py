"""Şema Karşılaştırma web raporunun nesne dizinini ve SQL sayfalarını hazırlar.

Yalnız kayıtlı dosyalar görüntülenir. SQL çalıştırılmaz ve girdi değiştirilmez.
İş ortam adları rapor sunumuna eklenir, nesne kimliklerine uygulanmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import PurePosixPath

from .labels import type_label


def ddl_type_label(op):
    if op['kind'] in {'ADD_COLUMN','ALTER_COLUMN','MODIFY_COLUMN','DROP_COLUMN'}:
        return 'Kolon'
    if op['kind'] in {'ADD_CONSTRAINT','ALTER_CONSTRAINT','DROP_CONSTRAINT'}:
        return 'Kural'
    return type_label(op['object']['object_type'])


def ddl_distribution(document, proposed):
    rows=Counter(ddl_type_label(op) for op in document['operations']
                 if op['decision']=='READY' or op['id'] in proposed)
    total=document['counts']['ready_operations']+len(proposed)
    return {'total':total,'verified':sum(rows.values())==total,
            'rows':[{'label':label,'count':count} for label,count in sorted(rows.items())]
                   if sum(rows.values())==total else []}


def sql_view_path(path):
    if (not path or path.startswith('/') or '\\' in path or ':' in path
            or any(part in {'','.','..'} for part in path.split('/'))
            or any(ord(char)<32 for char in path)):
        raise ValueError('REPORT_SQL_PATH_UNSAFE')
    return 'sql/'+hashlib.sha256(path.encode('utf-8')).hexdigest()[:24]+'-0001.html'


def sql_mappings(document,payload,source_paths,proposal_paths):
    """Yeni paket veya eski arşivdeki mevcut SQL dosyalarını işlem kimliğine bağlar."""
    operations={op['id'] for op in document['operations']}
    source=dict(source_paths or {})
    proposals=dict(proposal_paths or {})
    if not source and 'source-ddl/index.json' in payload:
        index=json.loads(payload['source-ddl/index.json'])
        if index['plan_id']!=document['plan_id']:
            raise ValueError('REPORT_SOURCE_DDL_PLAN_MISMATCH')
        source={op:path for item in index['objects'] if (path:=item.get('path')) in payload
                for op in item['operation_ids'] if op in operations}
    if not proposals:
        proposals={PurePosixPath(path).stem:path for path in payload
                   if path.startswith('proposals/') and path.endswith('.sql')
                   and PurePosixPath(path).stem in operations}
    return source,proposals


def environment_context(document,summary,target_label):
    source=os.environ.get('GENERATOR_REPORT_SOURCE_ENVIRONMENT')
    target=os.environ.get('GENERATOR_REPORT_TARGET_ENVIRONMENT')
    if (source is None)!=(target is None):
        raise ValueError('REPORT_ENVIRONMENT_CONFIGURATION_INCOMPLETE')
    for value in (source,target):
        if value is not None and (not value.strip() or len(value)>40 or any(ord(c)<32 for c in value)):
            raise ValueError('REPORT_DISPLAY_CONTEXT_MISMATCH')
    schemas=sorted(summary['source']['by_schema']) if summary else []
    # Çalışma bağlantısı render_reports içindeki doğrulanmış bağlamdan gelir.
    # Ortam değişkeni aynı planın arşiv dosyalarını koşular arasında değiştiremez.
    return {'run_href':None,'source_label':', '.join(schema+(' - '+source.strip() if source else '') for schema in schemas)
                            or 'Kaynak Şema Bilgisi Yok',
            'target_label':', '.join(schema+' - '+target.strip() for schema in document['target']['schemas'])
                           if target else target_label,
            'source_schemas':schemas}


def object_groups(rows):
    """Aynı nesnenin bu sayfadaki işlemlerini tek dizin satırında birleştirir."""
    groups={}
    for row in rows:
        obj=row['object']
        key=tuple(obj.get(k) for k in ('owner','object_type','name','parent_key'))
        identifier='object-'+hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()[:16]
        group=groups.setdefault(key,{'id':identifier,'label':row['object_label'],'type':obj['object_type'],
            'type_label':row['type_label'],'operations':[],'has_ddl':False,'missing':False})
        group['operations'].append(row)
        present=bool(row.get('sql') or row.get('proposal_path'))
        group['has_ddl']|=present
        group['missing']|=row['decision'] in {'READY','REVIEW_REQUIRED','BLOCKED'} and not present
    return list(groups.values())


def render_sql_pages(payload,paths,template):
    """Uzun SQL metninin tamamını boyut sınırını aşmayan HTML sayfalarına ayırır."""
    result={}
    for path in sorted(set(paths)):
        if path not in payload:
            continue
        text=payload[path].decode('utf-8',errors='replace')
        chunks=[text[i:i+24000] for i in range(0,len(text),24000)] or ['']
        base=sql_view_path(path).removesuffix('-0001.html')
        for index,chunk in enumerate(chunks,1):
            html=template.render(sql_text=chunk,download_path='../'+path,file_name=PurePosixPath(path).name,
                page=index,pages=len(chunks),previous=f'{base.rsplit("/",1)[-1]}-{index-1:04d}.html' if index>1 else None,
                following=f'{base.rsplit("/",1)[-1]}-{index+1:04d}.html' if index<len(chunks) else None).encode('utf-8')
            if len(html)>200*1024:
                raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
            result[f'{base}-{index:04d}.html']=html
    return result
