"""Concrete review explanations from facts already captured in the plan."""


def value(fields,name):
    field=fields.get(name)
    return field.value if field and field.state=='KNOWN' else None


def datatype(fields):
    kind=value(fields,'data_type') or 'Bilinmiyor'
    if kind in {'VARCHAR2','CHAR','NVARCHAR2','NCHAR','RAW'}:
        length=value(fields,'length');semantics=value(fields,'length_semantics')
        return str(kind)+'('+str(length)+((' '+str(semantics)) if semantics else '')+')'
    if kind=='NUMBER' and value(fields,'precision') is not None:
        return 'NUMBER('+str(value(fields,'precision'))+','+str(value(fields,'scale'))+')'
    return str(kind)


def type_review(name,before,after):
    prefix=name+': hedef '+datatype(before)+', kaynak '+datatype(after)+'. '
    if value(before,'data_type')!=value(after,'data_type'):
        return prefix+'Mevcut değerlerin yeni veri tipine kayıpsız dönüştürülebildiği doğrulanmalı.'
    if value(after,'data_type')=='NUMBER':
        return prefix+'Precision veya scale sınırı değişiyor. Sınırsız NUMBER ile sınırlı NUMBER otomatik eşdeğer sayılmaz, değer ve yuvarlama etkisi doğrulanmalı.'
    return prefix+'Karakter ve bayt kapasitesinin birlikte daralmadığı kanıtlanamadı. Mevcut değerlerin yeni sınıra uyumu doğrulanmalı.'


def routine_inventory(obj):
    status=obj.properties.get('object_status');rows=obj.properties.get('dictionary.dependencies')
    state=status.value if status and status.state=='KNOWN' else 'Bilinmiyor'
    count=str(len(rows.value)) if rows and rows.state=='KNOWN' else 'Bilinmiyor'
    return (' Kaynak nesne durumu: '+str(state)+', yakalanan dictionary bağımlılığı: '+count+
        '. Bu kayıtlar tek başına tam statik çağrı/tip çözümleme kanıtı değildir.'+
        (' INVALID nesnenin bağımlılık kayıtları eksik veya eski olabilir.' if state=='INVALID' else ''))


def sequence_review(changes):
    names={'cache':'CACHE','min_value':'MINVALUE','max_value':'MAXVALUE','increment_by':'INCREMENT BY','cycle':'CYCLE','order':'ORDER'}
    settings=[];counter=False
    for diff in changes:
        field=diff.property_path.rsplit('/',1)[-1]
        if field=='start_with':counter=True;continue
        settings.append(names.get(field,field)+': '+str(diff.before.value)+' -> '+str(diff.after.value))
    return ('Mevcut sequence ayarları değişiyor: '+', '.join(settings)+'. Operasyon ve tüketici etkisi incelemesi gerekiyor.'+
        (' START WITH farkı gözlenen sayaç durumudur, reset SQL üretilmez.' if counter else ' Sayaç resetlenmez.'))
