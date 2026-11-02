"""Oracle DB Migration Generator raporunda sayıları ve metinleri düzenler.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

import re


def format_count(value):
    return format(value,',d').replace(',','.')


def difference_counts(plan):
    unverified=sum(item['kind']=='UNKNOWN' for item in plan['differences'])
    return {'confirmed':len(plan['differences'])-unverified,'unverified':unverified}


def human_text(value):
    """Teknik ayrıntıyı değiştirmeden görünen açıklamadaki ayraçları sadeleştirir."""
    text=str(value).replace('→',' ile ').replace('—',', ').replace('–','-')
    text=text.replace('; ','. ').replace(';','.')
    text=re.sub(r':\s*',' ',text)
    return re.sub(r'\s+',' ',text).strip()


def warning_text(value):
    code,separator,detail=value.partition(': ')
    labels={'TARGET_INVALID_OBJECT':'Derleme hatası olan nesne',
            'TARGET_INVALID_REFERENCE':'Doğrulanamayan dış bağlantı',
            'PHYSICAL_STORAGE_PRESERVED':'Korunan depolama ayarı',
            'BACKING_INDEX_CREATED_BY_CONSTRAINT':'Anahtarla oluşan indeks'}
    return human_text(labels.get(code,code.replace('_',' ').capitalize())+' '+detail if separator else value)
