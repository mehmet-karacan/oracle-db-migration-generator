"""Oracle DB Migration Generator planındaki eksik DDL kanıtını açıklar.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

import re


def value(fields,name):
    field=fields.get(name)
    return field.value if field and field.state=='KNOWN' else None


def routine_inventory(obj):
    status=obj.properties.get('object_status');rows=obj.properties.get('dictionary.dependencies')
    state=status.value if status and status.state=='KNOWN' else 'Bilinmiyor'
    count=str(len(rows.value)) if rows and rows.state=='KNOWN' else 'Bilinmiyor'
    return (' Kaynak nesne durumu: '+str(state)+', yakalanan dictionary bağımlılığı: '+count+
        '. Bu kayıtlar tek başına tam statik çağrı/tip çözümleme kanıtı değildir.'+
        (' INVALID nesnenin bağımlılık kayıtları eksik veya eski olabilir.' if state=='INVALID' else ''))


def sequence_review(changes, has_proposal=False):
    names={'cache':'CACHE','min_value':'MINVALUE','max_value':'MAXVALUE','increment_by':'INCREMENT BY','cycle':'CYCLE','order':'ORDER'}
    settings=[];counter=False
    for diff in changes:
        field=diff.property_path.rsplit('/',1)[-1]
        if field=='start_with':counter=True;continue
        settings.append(names.get(field,field)+' ayarı hedefte '+str(diff.before.value)+', kaynakta '+str(diff.after.value))
    detail=(', '.join(settings)+'. ') if settings else ''
    outcome=('Ayarları değiştiren ALTER SEQUENCE önerisi ayrı dosyada hazırlandı. '
             if has_proposal else 'Bu ayarlar için güvenilir ALTER SEQUENCE önerisi hazırlanamadı. ')
    return (detail+outcome+
        ('START WITH farkı gözlenen sayaç durumudur. Sayaç değeri değiştirilmez.' if counter else 'Sayaç değeri değiştirilmez.'))


def sequence_alter_statement(name, changes):
    """Kaynak sequence ayarları için sayaç değerini değiştirmeyen ALTER üretir."""
    clauses={}
    for diff in changes:
        field=diff.property_path.rsplit('/',1)[-1]
        if field=='start_with' or diff.kind=='INFORMATIONAL':
            continue
        if diff.kind!='CHANGED' or diff.after.state!='KNOWN':
            return None
        value=diff.after.value
        if field in {'min_value','max_value','increment_by'}:
            if value is None and field!='increment_by':
                clauses[field]='NO'+field.split('_')[0].upper()+'VALUE'
            elif not re.fullmatch(r'[+-]?\d{1,38}',str(value)) or field=='increment_by' and int(value)==0:
                return None
            else:
                clauses[field]={'min_value':'MINVALUE','max_value':'MAXVALUE','increment_by':'INCREMENT BY'}[field]+' '+str(value)
        elif field=='cache':
            if not re.fullmatch(r'\d{1,9}',str(value)):
                return None
            amount=int(value)
            if amount==0:clauses[field]='NOCACHE'
            elif amount>=2:clauses[field]='CACHE '+str(amount)
            else:return None
        elif field in {'cycle','order'}:
            word=str(value).upper()
            if word not in {'TRUE','FALSE','CYCLE','NOCYCLE','ORDER','NOORDER'}:
                return None
            positive=word in {'TRUE','CYCLE','ORDER'}
            clauses[field]=('' if positive else 'NO')+field.upper()
        else:return None
    ordered=[clauses[field] for field in ('increment_by','min_value','max_value','cache','cycle','order') if field in clauses]
    return ('ALTER SEQUENCE '+name+' '+' '.join(ordered)+';').encode('utf-8') if ordered else None
