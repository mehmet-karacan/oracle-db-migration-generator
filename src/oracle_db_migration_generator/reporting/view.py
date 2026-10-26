"""Bounded presentation derived from canonical plans; no comparison decisions here."""
import re
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from .formatting import format_count, difference_counts
from .labels import object_label, status_label, type_label, kind_label, operation_reason, mail_operation_reason, target_reason, target_status

RANK={'ERROR':0,'INCONSISTENT':1,'INCOMPLETE':2,'BLOCKED':3,'REVIEW_REQUIRED':4,'READY':5,'NO_ACTION':6,'NO_CHANGE':7}
OP_RANK={'BLOCKED':0,'REVIEW_REQUIRED':1,'READY':2,'INFORMATIONAL':3}
DISPLAY={'READY':'DDL hazır','INFORMATIONAL':'Bilgi','BLOCKED':'DDL üretilemedi','REVIEW_REQUIRED':'İnceleme gerekli'}


def short(value,limit=500):
    text=str(value)
    return text if len(text)<=limit else text[:limit]+'…'


def _duration_label(run):
    try:
        started=datetime.fromisoformat(run.get('started_at','').replace('Z','+00:00'))
        finished=datetime.fromisoformat(run.get('finished_at','').replace('Z','+00:00'))
        elapsed=(finished-started).total_seconds()
        if elapsed<0:return 'Bilinmiyor'
    except (AttributeError,TypeError,ValueError):
        return 'Bilinmiyor'
    hours,remainder=divmod(int(elapsed),3600)
    minutes,seconds=divmod(remainder,60)
    return (f'{hours} sa ' if hours else '')+f'{minutes} dk {seconds} sn'


def _timing_view(run,comparison_timing):
    def parsed(value):
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
        if result.tzinfo is None:raise ValueError('TIMING_TIMEZONE_MISSING')
        return result
    def minutes(data):
        try:
            elapsed=(parsed(data.get('finished_at',''))-parsed(data.get('started_at',''))).total_seconds()
            if elapsed<0:raise ValueError('TIMING_NEGATIVE')
            count,seconds=divmod(int(elapsed+0.5),60)
            return f'{count} dk {seconds} sn'
        except (AttributeError,TypeError,ValueError):return 'Ölçülemedi'
    def date(data,key):
        try:return parsed(data.get(key,'')).astimezone(timezone(timedelta(hours=3))).strftime('%d.%m.%Y %H:%M:%S')
        except (AttributeError,TypeError,ValueError):return 'Kaydedilmedi'
    origin=comparison_timing if comparison_timing is not None else run
    return {'comparison_duration_label':minutes(origin),
            'report_duration_label':minutes(run) if comparison_timing is not None else None,
            'comparison_started_label':date(origin,'started_at'),
            'comparison_finished_label':date(origin,'finished_at')}


def build_run_view(run,plans,*,publication=None,url_check=None,fallback=None,allowed_link_hosts=(),comparison_timing=None,scan_summaries=None):
    targets=[];unique={};counts={'ready_operations':0,'review_operations':0,'blocked_operations':0}
    for target in run['targets']:
        plan=plans.get(target['id'])
        facts=difference_counts(plan) if plan else None
        item={**target,'name':short(plan['target']['name']) if plan else 'Hedef adı doğrulanamadı',
              'schemas':list(plan['target']['schemas']) if plan else [],
              'confirmed_difference_count':target['difference_count'] if target['difference_count'] is not None else facts['confirmed'] if facts else None,
              'unverified_difference_count':facts['unverified'] if facts else None,
              'display_status':target_status(plan) if plan else status_label(target['status']), 'status_reason':target_reason(plan),
              'counts':plan['counts'] if plan else None,'report_path':None,'aggregate_path':None,
              'aggregate_view_path':None,'download_path':None,'manifest_path':None,'objects_path':None}
        if plan:
            base=str(PurePosixPath(target['plan_path']).parent)
            item.update(report_path=base+'/index.html',manifest_path=base+'/bundle-manifest.json',objects_path=base+'/README.md')
            if plan['counts']['ready_operations']:
                item['aggregate_path']=base+('/migration.sql' if plan['status']=='READY' else '/partial-ready.sql')
            for key in counts: counts[key]+=plan['counts'][key]
            for op in plan['operations']:
                obj=op['object'];key=tuple(obj[k] for k in ('owner','object_type','name','parent_key'))
                row=unique.setdefault(key,{'object':obj,'object_label':object_label(obj),'type_label':type_label(obj['object_type']),'evidence_path':target['plan_path'],
                                          'decision':op['decision'],'reason':operation_reason(op),'mail_reason':mail_operation_reason(op), 'targets':set(),'kinds':set(),'operation_count':0})
                row['targets'].add(target['id']);row['kinds'].add(op['kind']);row['operation_count']+=1
                if OP_RANK[op['decision']]<OP_RANK[row['decision']]: row.update(decision=op['decision'],reason=operation_reason(op),mail_reason=mail_operation_reason(op))
        targets.append(item)
    important=sorted(unique.values(),key=lambda r:(OP_RANK[r['decision']],r['object']['owner'],r['object']['object_type'],r['object']['name']))[:5]
    target_labels={item['id']:item['name']+(' ('+', '.join(item['schemas'])+')' if item['schemas'] else '') for item in targets}
    for row in important:
        row['targets']=sorted(row['targets']);row['kinds']=[kind_label(kind) for kind in sorted(row['kinds'])];row['display_status']=status_label(row['decision'])
        row['target_label']=', '.join(target_labels[target] for target in row['targets'][:5])+ (f" + {format_count(len(row['targets'])-5)} hedef" if len(row['targets'])>5 else '')
    unknown=sum(t['difference_count'] is None for t in targets)
    known_values=[t['confirmed_difference_count'] for t in targets if t['confirmed_difference_count'] is not None]
    known=sum(known_values) if known_values or not targets else None
    unverified=sum(t['unverified_difference_count'] or 0 for t in targets)
    missing=sum(t['counts'] is None for t in targets)
    notes=[]
    if unverified:notes.append(f'{format_count(unverified)} kayıt, bilgisi eksik olduğu için karşılaştırılamadı.')
    if unknown>missing:notes.append('Kapsam eksik; ek farklar bulunabilir.')
    if missing:notes.append(f'{format_count(missing)} hedeften sonuç alınamadı.')
    metrics=[{'label':'Hedef','value':format_count(len(targets))},{'label':'Bulunan fark','value':format_count(known) if known is not None else 'Sonuç alınamadı'},
             {'label':'Üretilen DDL','value':format_count(counts['ready_operations'])},
             {'label':'İnceleme','value':format_count(counts['review_operations'])},{'label':'Üretilemeyen DDL','value':format_count(counts['blocked_operations'])}]
    link=None;note='Git yayını yapılmadı veya bağlantı doğrulanmadı. Dosyalar yerel çalışma arşivinde.'
    if publication and publication.status=='PUBLISHED' and publication.url and publication.commit_sha and url_check:
        p=urlsplit(publication.url);sha=publication.commit_sha
        path=p.path
        immutable=bool(re.fullmatch('[a-f0-9]{40}',sha) and (f'/blob/{sha}/runs/' in path or ('/browse/runs/' in path and p.query=='at='+sha)))
        current=bool(re.search(r'/build-[A-Za-z0-9-]*-'+re.escape(run['run_id'])+r'/README\.md$',path))
        from .links import safe_https
        try: safe_https(publication.url,allowed_link_hosts);allowed=True
        except ValueError: allowed=False
        if allowed and immutable and current and url_check(publication.url) is True:
            link=publication.url;note='Bu çalışmanın sabit Git commit kaydı. Erişim yetkisi gereklidir.'
    if link is None and fallback and url_check and run.get('build_url'):
        from .links import verified_archive
        checked=verified_archive(fallback.url,allowed_link_hosts,url_check,build_url=run['build_url'])
        if checked: link=checked.url;note=checked.note
    from .inventory import scan_scope_view
    return {'scan_scope':scan_scope_view(plans,scan_summaries or {},[target['id'] for target in targets]),
            'run':run,'display_status':status_label(run.get('status')),'duration_label':_duration_label(run),**_timing_view(run,comparison_timing),'targets':targets,'critical_targets':sorted(targets,key=lambda t:(RANK[t['status']],t['id']))[:5],
            'metrics':metrics,'important_objects':important,'unique_objects':len(unique),'unknown_targets':unknown,
            'confirmed_differences':known,'unverified_differences':unverified,'difference_note':' '.join(notes),
            'counts':counts,'link':link,'link_note':note}
