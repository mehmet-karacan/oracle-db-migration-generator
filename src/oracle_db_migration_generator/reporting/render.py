from importlib.resources import files
from jinja2 import Environment, StrictUndefined
from .formatting import format_count,warning_text
from .view import DISPLAY


def _template(name):
    environment=Environment(autoescape=True,undefined=StrictUndefined)
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
    environment=Environment(autoescape=True,undefined=StrictUndefined)
    environment.filters['count_tr']=format_count
    template=environment.from_string(files(__package__).joinpath('templates/report.html.j2').read_text(encoding='utf-8'))
    ops=[{**op,'display_status':DISPLAY.get(op['decision'],op['decision'])} for op in document['operations']];pages=max(1,(len(ops)+99)//100)
    rank={'BLOCKED':0,'REVIEW_REQUIRED':1,'READY':2,'INFORMATIONAL':3}
    important=sorted(ops,key=lambda op:(rank[op['decision']],op['id']))[:5]
    previews=[{'operation':op,'text':preview(sql_files.get(op['sql']['path'],b'').decode('utf-8')) if op['sql'] else ''} for op in important]
    result={}
    warnings=[warning_text(value) for value in document['warnings']
              if not value.startswith(('TARGET_INVALID_DDL_REPORTED:','BACKING_INDEX_CREATED_BY_CONSTRAINT:'))]
    def render(title,rows,prefix,show_previews):
        value=template.render(plan=document,title=title,rows=rows,prefix=prefix,pages=pages,
                              previews=previews if show_previews else [],warning_rows=warnings[:20],
                              remaining_warnings=max(0,len(warnings)-20))
        if len(value.encode())>200*1024: raise ValueError('HTML_SIZE_BUDGET_EXCEEDED')
        return value.encode()
    result['index.html']=render('Hedef Özeti',important,'',True)
    for page in range(pages):
        result[f'changes/page-{page+1:04d}.html']=render(f'Değişiklikler · {page+1}/{pages}',ops[page*100:(page+1)*100],'../',False)
    result['assets/report.css']=files(__package__).joinpath('assets/report.css').read_bytes()
    result['assets/innova-logo.png']=files(__package__).joinpath('assets/innova-logo.png').read_bytes()
    return result
