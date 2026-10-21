"""Presentation-only formatting; numeric contracts and SQL stay untouched."""


def format_count(value):
    return format(value,',d').replace(',','.')


def difference_counts(plan):
    unverified=sum(item['kind']=='UNKNOWN' for item in plan['differences'])
    return {'confirmed':len(plan['differences'])-unverified,'unverified':unverified}


def warning_text(value):
    code,separator,detail=value.partition(': ')
    labels={'TARGET_INVALID_OBJECT':'INVALID nesne','TARGET_INVALID_REFERENCE':'INVALID dış referans',
            'PHYSICAL_STORAGE_PRESERVED':'Depolama uyarısı',
            'BACKING_INDEX_CREATED_BY_CONSTRAINT':'PK/UK indeksi'}
    return labels.get(code,code)+separator+detail
