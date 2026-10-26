from importlib.resources import files
from jinja2 import Environment, StrictUndefined, PackageLoader
from .formatting import format_count,warning_text,difference_counts
from .labels import object_label, status_label, type_label, kind_label, operation_reason, target_reason, target_status


def _template(name):
    environment=Environment(autoescape=True,undefined=StrictUndefined,loader=PackageLoader(__package__,'templates'))
    environment.filters['count_tr']=format_count
    return environment.from_string(files(__package__).joinpath('templates',name).read_text(encoding='utf-8'))


def _bounded(html):
    raw=html.encode('utf-8')
    if len(raw)>200*1024: raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
    return raw


def render_email(view,*,preview=False):
    import base64
    logo='cid:innova-logo'
    if preview: logo='data:image/png;base64,'+base64.b64encode(files(__package__).joinpath('assets/innova-logo.png').read_bytes()).decode()
    return _bounded(_template('email.html.j2').render(view=view,logo=logo))


def render_run_reports(view):
    result={};pages=max(1,(len(view['targets'])+49)//50)
    for page in range(pages):
        result['index.html' if page==0 else f'targets-{page+1:04d}.html']=_bounded(_template('run.html.j2').render(view=view,targets=view['targets'][page*50:(page+1)*50],pages=pages,page=page))
    for name in ('report.css','innova-logo.png'):
        result['assets/'+name]=files(__package__).joinpath('assets',name).read_bytes()
    result['report-email.html']=render_email(view)
    result['report-email.preview.html']=render_email(view,preview=True)
    return result


def preview(text):
    return '\n'.join(text.splitlines()[:30])[:2048]


def render_reports(document,sql_files):
    import json
    from .inventory import scan_scope_view
    summary=json.loads(sql_files['scan-summary.json']) if 'scan-summary.json' in sql_files else None
    target_id=document['target']['id']
    scan_scope=scan_scope_view({target_id:document},{target_id:summary} if summary else {},[target_id])
    environment=Environment(autoescape=True,undefined=StrictUndefined,loader=PackageLoader(__package__,'templates'))
    environment.filters['count_tr']=format_count
    template=environment.from_string(files(__package__).joinpath('templates/report.html.j2').read_text(encoding='utf-8'))
    ops=[{**op,'object_label':object_label(op['object']),'display_status':status_label(op['decision']),
          'type_label':type_label(op['object']['object_type']),'kind_label':kind_label(op['kind']),
          'summary_reason':operation_reason(op)} for op in document['operations']]
    rank={'BLOCKED':0,'REVIEW_REQUIRED':1,'READY':2,'INFORMATIONAL':3}
    important=sorted(ops,key=lambda op:(rank[op['decision']],op['id']))[:5]
    previews=[{'operation':op,'text':preview(sql_files.get(op['sql']['path'],b'').decode('utf-8')) if op['sql'] else ''} for op in important]
    result={}
    warnings=[warning_text(value) for value in document['warnings']
              if not value.startswith(('TARGET_INVALID_DDL_REPORTED:','BACKING_INDEX_CREATED_BY_CONSTRAINT:'))]
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
    def render(title,rows,prefix,show_previews,pages,current=1,compact=False):
        # A bounded window keeps navigation independent of the operation count.
        links=list(range(1,pages+1)) if pages<=9 else sorted({1,pages,*range(max(1,current-2),min(pages,current+2)+1)})
        warning_rows=[{'text':text[:256] if compact else text,
                       'characters':max(0,len(text)-256) if compact else 0} for text in warnings[:20]]
        return template.render(plan=document,difference_summary=difference_counts(document),display_status=target_status(document),status_reason=target_reason(document),title=title,rows=[operation_view(op,compact) for op in rows],
                               prefix=prefix,pages=pages,page_links=links,
                               previews=previews if show_previews else [],warning_rows=warning_rows,
                               remaining_warnings=max(0,len(warnings)-20),scan_scope=scan_scope).encode('utf-8')
    # Reserve 10 KiB for the final page count and navigation while partitioning.
    # Each successful prefix is consumed once, no operation is dropped or copied.
    groups=[(ops[start:start+100],False) for start in range(0,len(ops),100)] or [([],False)]
    if any(len(render(f'Değişiklikler · {page}/{len(groups)}',rows,'../',False,len(groups),page))>200*1024
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
    summary=render('Hedef Özeti',important,'',True,pages)
    if len(summary)>200*1024:summary=render('Hedef Özeti',important,'',True,pages,compact=True)
    result['index.html']=_bounded(summary.decode('utf-8'))
    for page,(rows,compact) in enumerate(groups,1):
        result[f'changes/page-{page:04d}.html']=_bounded(render(f'Değişiklikler · {page}/{pages}',rows,'../',False,pages,page,compact).decode('utf-8'))
    result['assets/report.css']=files(__package__).joinpath('assets/report.css').read_bytes()
    result['assets/innova-logo.png']=files(__package__).joinpath('assets/innova-logo.png').read_bytes()
    return result
