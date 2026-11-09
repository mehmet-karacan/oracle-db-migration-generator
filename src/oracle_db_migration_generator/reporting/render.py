"""Oracle DB Migration Generator karşılaştırma raporlarını HTML olarak üretir.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from importlib.resources import files
from functools import partial
from jinja2 import Environment, StrictUndefined, PackageLoader
from .formatting import format_count,warning_text,difference_counts,human_text
from .labels import object_label, status_label, type_label, kind_label, operation_reason, target_reason, target_status
from .icons import report_icon, report_type_icon, metric_icon, icon_assets
from .web import ddl_distribution, environment_context, object_groups, sql_mappings, sql_view_path, render_sql_pages
from .comparison import comparison_catalog,attach_comparisons,render_comparisons,identity_key


def _environment():
    environment=Environment(autoescape=True,undefined=StrictUndefined,loader=PackageLoader(__package__,'templates'))
    environment.filters['count_tr']=format_count
    environment.globals.update(report_icon=report_icon,report_type_icon=report_type_icon,metric_icon=metric_icon)
    return environment


def _template(name):
    environment=_environment()
    return environment.from_string(files(__package__).joinpath('templates',name).read_text(encoding='utf-8'))


def _bounded(html):
    raw=html.encode('utf-8')
    if len(raw)>200*1024: raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
    return raw


def render_email(view,*,preview=False):
    """Özgün kurumsal logoyu değiştirmeden ayrı açık zeminle epostaya yerleştirir."""
    import base64
    logo='cid:innova-logo'
    if preview: logo='data:image/png;base64,'+base64.b64encode(files(__package__).joinpath('assets/innova-logo.png').read_bytes()).decode()
    logo_surface='data:image/png;base64,'+base64.b64encode(files(__package__).joinpath('assets/brand-surface-light.png').read_bytes()).decode()
    return _bounded(_template('email.html.j2').render(view=view,logo=logo,logo_surface=logo_surface))


def render_run_reports(view):
    result={};pages=max(1,(len(view['targets'])+49)//50)
    for page in range(pages):
        result['index.html' if page==0 else f'targets-{page+1:04d}.html']=_bounded(_template('run.html.j2').render(view=view,targets=view['targets'][page*50:(page+1)*50],pages=pages,page=page,
            report_icon=partial(report_icon,asset_prefix=''),report_type_icon=partial(report_type_icon,asset_prefix='')))
    for name in ('report.css','innova-logo.png'):
        result['assets/'+name]=files(__package__).joinpath('assets',name).read_bytes()
    result['report-email.html']=render_email(view)
    result['report-email.preview.html']=render_email(view,preview=True)
    result.update(icon_assets())
    return result


def preview(text):
    return '\n'.join(text.splitlines()[:30])[:2048]


def render_reports(document,sql_files,*,source_ddl_paths=None,proposal_paths=None,report_context=None):
    import json
    import re
    from .inventory import scan_scope_view
    summary=json.loads(sql_files['scan-summary.json']) if 'scan-summary.json' in sql_files else None
    target_id=document['target']['id']
    target_name=document['target'].get('name') or ''
    target_label='hedef ortam' if not target_name or re.fullmatch(r'[0-9a-fA-F]{32,}',target_name) else target_name
    differences={item['id']:item for item in document['differences']}
    def review_explanation(op):
        """Bölüm ve kolon farkını raporda nesneye özgü sözcüklerle açıklar."""
        codes=set(op['reason_codes'])
        if 'PARTITION_LAYOUT_REQUIRES_REVIEW' in codes:
            try:
                change=next(differences[key] for key in op['change_ids'] if differences[key]['property_path']=='/table_properties/partitioning')
                def partition_count(side):
                    tokens=json.loads(change[side]['value'])
                    count=sum(value=='PARTITION' and index+1<len(tokens) and tokens[index+1][1]!='BY'
                              for index,(_,value) in enumerate(tokens))
                    return count,any(value=='INTERVAL' for _,value in tokens),any(value=='MAXVALUE' for _,value in tokens)
                target_count,target_interval,_=partition_count('before')
                source_count,_,source_max=partition_count('after')
                if target_interval and source_max:
                    return (f'Kaynakta {source_count} bölümlü aralık düzeni ve MAXVALUE sınırı var. '
                            f'Hedefte {target_count} başlangıç bölümü ile interval düzeni bulunuyor. '
                            'Önerilen SQL interval düzenini kapatır, bölüm adlarını eşitler ve eksik bölümleri ekler.')
            except (KeyError,ValueError,TypeError,StopIteration,IndexError):
                pass
        if 'COLUMN_CHANGE_REQUIRES_REVIEW' in codes:
            try:
                change=differences[op['change_ids'][0]]
                if (change['property_path'].endswith('/collation') and change['after']['value'] is None
                        and change['before']['value']=='USING_NLS_COMP'):
                    return ('Kaynak kolonda açık kolasyon yok. Hedefte USING_NLS_COMP kayıtlı. '
                            'Eşdeğerlik doğrulanmadan ALTER komutu önerilmez.')
            except (KeyError,IndexError,TypeError):
                pass
        return human_text(operation_reason(op))
    scan_scope=scan_scope_view({target_id:document},{target_id:summary} if summary else {},[target_id])
    environment=_environment()
    template=environment.from_string(files(__package__).joinpath('templates/report.html.j2').read_text(encoding='utf-8'))
    source_ddl_paths,proposal_paths=sql_mappings(document,sql_files,source_ddl_paths,proposal_paths)
    context=environment_context(document,summary,target_label)
    if report_context is not None:
        if (set(report_context)!={'target_id','source_commit','run_href'}
                or report_context['target_id']!=target_id
                or report_context['source_commit']!=document['source']['commit_sha']
                or report_context['run_href']!='../../index.html'):
            raise ValueError('REPORT_DISPLAY_CONTEXT_MISMATCH')
        context['run_href']=report_context['run_href']
    ddl_types=ddl_distribution(document,set(proposal_paths))
    comparisons=comparison_catalog(document)
    viewer_paths={path for op in document['operations'] for path in
                  (op['sql']['path'] if op.get('sql') else None,source_ddl_paths.get(op['id']),proposal_paths.get(op['id']))
                  if path and path in sql_files}
    aggregate_path='migration.sql' if document['status']=='READY' else 'partial-ready.sql'
    if aggregate_path in sql_files: viewer_paths.add(aggregate_path)
    generated_count=document['counts']['ready_operations']+len(proposal_paths)
    action_count=sum(op['decision'] in {'READY','REVIEW_REQUIRED','BLOCKED'} for op in document['operations'])
    generation_complete=action_count>0 and generated_count==action_count
    ops=[{**op,'sql_view':sql_view_path(op['sql']['path']) if op.get('sql') and op['sql']['path'] in sql_files else None,
          'source_view':sql_view_path(source_ddl_paths[op['id']]) if source_ddl_paths.get(op['id']) in sql_files else None,
          'proposal_view':sql_view_path(proposal_paths[op['id']]) if proposal_paths.get(op['id']) in sql_files else None,
          'source_ddl_path':source_ddl_paths.get(op['id']),'proposal_path':proposal_paths.get(op['id']),'object_label':object_label(op['object']),'display_status':('DDL Üretildi' if op['decision'] in {'REVIEW_REQUIRED','BLOCKED'} and proposal_paths.get(op['id']) else status_label(op['decision'])),
          'type_label':type_label(op['object']['object_type']),'kind_label':kind_label(op['kind']),
          'summary_reason':('Kaynakta fonksiyon, hedefte aynı adlı tablo var.'
                            if proposal_paths.get(op['id']) and 'TARGET_NAMESPACE_CONFLICT' in op['reason_codes'] and op['object']['object_type']=='FUNCTION'
                            else 'Kaynak sequence ayarları için değişim DDL önerildi. Hedef sayaç değeri korunur.'
                            if proposal_paths.get(op['id']) and 'SEQUENCE_STATE_PRESERVED' in op['reason_codes']
                            else review_explanation(op)),
          'reason_tr':('Kaynakta fonksiyon, hedefte aynı adlı tablo var.'
                       if proposal_paths.get(op['id']) and 'TARGET_NAMESPACE_CONFLICT' in op['reason_codes'] and op['object']['object_type']=='FUNCTION'
                       else 'Kaynak sequence ayarları için değişim DDL önerildi. Hedef sayaç değeri korunur.'
                       if proposal_paths.get(op['id']) and 'SEQUENCE_STATE_PRESERVED' in op['reason_codes']
                       else human_text(op['reason_tr']))} for op in document['operations']]
    rank={'BLOCKED':0,'REVIEW_REQUIRED':1,'READY':2,'INFORMATIONAL':3}
    ops.sort(key=lambda op:(rank[op['decision']],op['object_label'],op['id']))
    important=sorted(ops,key=lambda op:(rank[op['decision']],op['id']))[:5]
    previews=[{'operation':op,'text':preview(sql_files.get(op['sql']['path'],b'').decode('utf-8')) if op['sql'] else ''} for op in important]
    result={}
    warning_sources=[value for value in document['warnings']
                     if not value.startswith(('TARGET_INVALID_DDL_REPORTED:','BACKING_INDEX_CREATED_BY_CONSTRAINT:'))]
    warnings=[warning_text(value) for value in warning_sources]
    from collections import Counter
    warning_codes=Counter(value.partition(': ')[0] for value in document['warnings']
                          if not value.startswith(('TARGET_INVALID_DDL_REPORTED:','BACKING_INDEX_CREATED_BY_CONSTRAINT:')))
    warning_labels={'TARGET_INVALID_OBJECT':'Derleme Sorunları',
                    'TARGET_INVALID_REFERENCE':'Dış Bağlantı Sorunları',
                    'PHYSICAL_STORAGE_PRESERVED':'Depolama Notları'}
    grouped_warnings=Counter()
    for code,count in warning_codes.items():grouped_warnings[warning_labels.get(code,'Diğer Uyarılar')]+=count
    warning_groups=[{'label':label,'count':count} for label,count in sorted(grouped_warnings.items(),key=lambda item:(-item[1],item[0]))]
    def operation_view(op,compact):
        row={**op,'reason_remaining':0,'field_previews':[]}
        if compact:
            row['reason_tr']=op['reason_tr'][:2048]
            row['reason_remaining']=len(op['reason_tr'])-len(row['reason_tr'])
        for key,label in (('depends_on','bağımlılık'),('reason_codes','neden kodu'),('evidence_ids','kanıt')):
            values=op[key];shown=values[:8] if compact else values
            clipped=[value[:64] for value in shown] if compact else shown
            row[key]=clipped
            row['field_previews'].append({'label':label,'remaining':len(values)-len(shown),
                                         'characters':sum(len(value)-len(text) for value,text in zip(shown,clipped))})
        return row
    def render(title,rows,prefix,show_previews,pages,current=1,compact=False,lean=False):
        # A bounded window keeps navigation independent of the operation count.
        links=list(range(1,pages+1)) if pages<=9 else sorted({1,pages,*range(max(1,current-2),min(pages,current+2)+1)})
        warning_rows=[{'text':text[:256] if compact else text,
                       'characters':max(0,len(source)-256) if compact else 0}
                      for text,source in zip(warnings[:20],warning_sources[:20])]
        prepared_rows=[operation_view(op,compact) for op in rows]
        groups=attach_comparisons(object_groups(prepared_rows),comparisons)
        return template.render(plan=document,target_label=context['target_label'],context=context,ddl_types=ddl_types,
                               has_comparisons=bool(comparisons),
                               missing_count=len({op['id'] for op in document['operations'] if op['decision'] in {'REVIEW_REQUIRED','BLOCKED'}}-set(proposal_paths)),groups=groups,compact_chrome=lean,
                               filter_types=sorted({(g['type'],g['type_label']) for g in groups}),
                               aggregate_view=sql_view_path(aggregate_path) if aggregate_path in viewer_paths else None,
                               current_page=current,difference_summary=difference_counts(document),
                               display_status='DDL Üretildi' if generation_complete else target_status(document),
                               status_reason=('Kaynak ve hedef farkları için DDL üretildi. Nesneye özgü notlar ilgili kayıtların altında yer alıyor.'
                                              if generation_complete and document['counts']['blocked_operations'] else target_reason(document)),
                               generated_count=generated_count,proposal_count=len(proposal_paths),generation_complete=generation_complete,title=title,
                               rows=prepared_rows,show_previews=show_previews,warning_groups=warning_groups,
                               prefix=prefix,pages=pages,page_links=links,
                               previews=previews if show_previews else [],warning_rows=warning_rows,
                               remaining_warnings=max(0,len(warnings)-20),scan_scope=scan_scope,
                               report_icon=partial(report_icon,asset_prefix=prefix),
                               report_type_icon=partial(report_type_icon,asset_prefix=prefix)).encode('utf-8')
    # Reserve 10 KiB for the final page count and navigation while partitioning.
    # Each successful prefix is consumed once, no operation is dropped or copied.
    groups=[(ops[start:start+100],False) for start in range(0,len(ops),100)] or [([],False)]
    if any(len(render(f'Nesneler - Sayfa {page}/{len(groups)}',rows,'../',False,len(groups),page))>200*1024
           for page,(rows,_) in enumerate(groups,1)):
        groups=[]
    offset=len(ops) if groups else 0;estimate=max(1,len(ops))
    while offset<len(ops):
        count=min(100,len(ops)-offset);compact=False
        while True:
            rows=ops[offset:offset+count]
            raw=render('Değişiklikler',rows,'../',False,estimate,len(groups)+1,compact)
            if len(raw)<=190*1024:break
            if count>1:count=max(1,count//2)
            elif not compact:compact=True
            else:raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
        groups.append((rows,compact));offset+=count
    if not groups:groups=[([],True)]
    pages=len(groups)
    summary=render('Hedef Ayrıntıları',important,'',True,pages)
    if len(summary)>200*1024:summary=render('Hedef Ayrıntıları',important,'',True,pages,lean=True)
    if len(summary)>200*1024:summary=render('Hedef Ayrıntıları',important,'',True,pages,compact=True,lean=True)
    result['index.html']=_bounded(summary.decode('utf-8'))
    for page,(rows,compact) in enumerate(groups,1):
        result[f'changes/page-{page:04d}.html']=_bounded(render(f'Nesneler - Sayfa {page}/{pages}',rows,'../',False,pages,page,compact).decode('utf-8'))
        for group in object_groups(rows):
            comparison=comparisons.get(identity_key(group['operations'][0]['object']))
            if comparison is not None:
                comparison.setdefault('operations_path',f'changes/page-{page:04d}.html#{group["id"]}')
    result.update(render_sql_pages(sql_files,viewer_paths,_template('sql.html.j2')))
    if comparisons:
        result.update(render_comparisons(comparisons,_template('comparison.html.j2'),
                                         _template('comparison_index.html.j2'),context))
    result['assets/report.css']=files(__package__).joinpath('assets/report.css').read_bytes()
    result['assets/innova-logo.png']=files(__package__).joinpath('assets/innova-logo.png').read_bytes()
    result.update(icon_assets())
    return result
