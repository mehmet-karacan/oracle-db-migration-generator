"""Şema Karşılaştırma tür, işlem ve durum etiketlerini ortak başlık biçiminde sunar.

Kanonik nesne kimliği korunur ve bağlı nesne için yalnız kayıtlı bilgi kullanılır.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
import re


STATUSES = {'BLOCKED': 'DDL Üretilemedi', 'REVIEW_REQUIRED': 'İnceleme Gerekli',
            'READY': 'DDL Hazır', 'INFORMATIONAL': 'Bilgi', 'NO_ACTION': 'İşlem Gerekmiyor',
            'NO_CHANGE': 'Fark Yok', 'ERROR': 'Karşılaştırma Yapılamadı',
            'INCOMPLETE': 'Karşılaştırma Eksik', 'INCONSISTENT': 'Sonuçlar Tutarsız',
            'COMPLETE': 'Karşılaştırma Tamamlandı', 'PARTIAL': 'Karşılaştırma Kısmen Tamamlandı',
            'FAILED': 'Karşılaştırma Tamamlanamadı'}
TYPES = {'TABLE': 'Tablo', 'VIEW': 'Görünüm', 'MATERIALIZED_VIEW': 'Saklanan Görünüm',
         'INDEX': 'İndeks', 'COMMENT': 'Açıklama', 'GRANT': 'Yetki', 'FUNCTION': 'Fonksiyon',
         'PROCEDURE': 'Prosedür', 'PACKAGE_SPEC': 'Paket Tanımı', 'PACKAGE_BODY': 'Paket Gövdesi',
         'TYPE_SPEC': 'Veri Tipi', 'TYPE_BODY': 'Veri Tipi Gövdesi', 'SEQUENCE': 'Sıra Numarası',
         'SYNONYM': 'Nesne Takma Adı', 'TRIGGER': 'Tetikleyici'}
KINDS = {'CREATE': 'Oluşturma', 'REPLACE': 'Güncelleme', 'REVIEW': 'İnceleme',
         'COMMENT': 'Açıklama', 'GRANT': 'Yetki', 'CREATE_INDEX': 'İndeks Oluşturma',
         'ADD_COLUMN': 'Kolon Ekleme', 'ALTER_COLUMN': 'Kolon Güncelleme',
         'ADD_CONSTRAINT': 'Kural Ekleme', 'DROP_CONSTRAINT': 'Kural Kaldırma',
         'DROP': 'Kaldırma', 'ALTER': 'Güncelleme', 'NO_ACTION': 'İşlem Gerekmiyor'}


def status_label(value):
    return STATUSES.get(value, 'Sonuç Doğrulanamadı')


def type_label(value):
    return TYPES.get(value, 'Nesne')


def kind_label(value):
    return KINDS.get(value, 'Yapı Değişikliği')


def _plain_reason(text):
    text = re.sub(r' \[[A-Z_]+\]', '', text)
    text = re.sub(r'gerekli ([A-Z_]+) işlemi (BLOCKED|REVIEW_REQUIRED)',
                  lambda m: kind_label(m[1]).lower() + (' işlemi için DDL üretilemedi' if m[2]=='BLOCKED'
                                                       else ' işlemi inceleme bekliyor'), text)
    replacements = {'bağımlı nesnenin gerekli işlemi hazır değil:': 'bağlı nesnenin işlemi hazır değil:',
                    'hedefte bulunamadı ve oluşturulmasını sağlayan kaynak işlemi yok':
                    'hedefte bulunamadı, kaynakta oluşturma tanımı bulunmuyor',
                    'kaynak kolon karşılaştırmasındaki eksik metadata bu yapısal önkoşul için doğrulanamadı':
                    'kaynak kolon bilgileri eksik',
                    'metadata': 'tanım bilgisi', 'dictionary': 'veritabanı kayıtları',
                    'PRIMARY KEY/UNIQUE': 'birincil veya benzersiz anahtar',
                    'parent': 'bağlı', 'Index': 'İndeks'}
    for old, new in replacements.items(): text = text.replace(old, new)
    text = re.sub(r'REVIEW / (?:BLOCKED|REVIEW_REQUIRED)(?:, REVIEW / (?:BLOCKED|REVIEW_REQUIRED))*',
                  'inceleme bekliyor', text)
    for code, label in {**TYPES, **KINDS, **STATUSES}.items():
        text = re.sub(r'(?<![\w.])' + re.escape(code) + r'(?!\w|\.\w)', lambda _: label.lower(), text)
    return text


def operation_reason(op):
    """Summarize recorded evidence only; never infer absence from unknown facts."""
    reasons = {
        'OBJECT_METADATA_INCOMPLETE': 'Nesnenin tanımı veya hedefte bulunup bulunmadığı doğrulanamadı.',
        'UNKNOWN_SOURCE_SEMANTICS': 'Kaynak kolon tipi veya uzunluk birimi doğrulanamadı.',
        'COLUMN_METADATA_UNKNOWN': 'Kolon tanımındaki bazı bilgiler doğrulanamadı.',
        'INDEX_DEFINITION_UNVERIFIED': 'İndeksin türü, kolonları veya bağlı tablosu doğrulanamadı.',
        'RESERVED_INTERNAL_OBJECT': 'Oracle iç indeksinin bağlı olduğu anahtar doğrulanamadı.',
        'BLOCKED_UNSUPPORTED_FEATURE': 'Bu özel tablo yapısı için güvenli DDL üretimi desteklenmiyor.',
    }
    for code, message in reasons.items():
        if code in op['reason_codes']:
            if code=='UNKNOWN_SOURCE_SEMANTICS' and op['reason_tr'].startswith('Kaynak kolon bilgisi doğrulanamadı:'):
                return op['reason_tr'] if len(op['reason_tr'])<=240 else op['reason_tr'][:239]+'…'
            return message
    text = op['reason_tr']
    # The graph records the same prerequisite once for its held operation and
    # once for its underlying missing/unknown fact. Prefer that specific fact.
    pattern = r'(?:^|; )([^;]+?) \[[A-Z_]+\]: (.*?)(?=; [^;]+? \[[A-Z_]+\]: |$)'
    matches = list(re.finditer(pattern, text))
    if matches:
        grouped = {}
        for match in matches:
            name, detail = match.groups()
            old = grouped.get(name)
            if old is None or 'bağımlı nesnenin gerekli işlemi hazır değil:' in old:
                grouped[name] = detail
        parts = [name + ': ' + _plain_reason(detail).rstrip('.') for name, detail in grouped.items()]
        text = ', '.join(parts[:2]) + (f', ayrıca {len(parts)-2} bağlı nesne' if len(parts)>2 else '') + '.'
    else:
        text = _plain_reason(text)
    return text if len(text)<=240 else text[:239]+'…'


def mail_operation_reason(op):
    """Keep the mail cell brief; full evidence remains in the detailed report."""
    text = operation_reason(op)
    if 'Partition, LOB, IOT, external veya cluster' in op['reason_tr']:
        return ('Bağlı tablonun özel yapısı için DDL desteği gerekiyor.'
                if 'DEPENDENCY_UNVERIFIED' in op['reason_codes'] else
                'Tablonun özel yapısı için DDL desteği gerekiyor.')
    if len(text) <= 150:
        return text
    boundary = text.rfind(' ', 0, 149)
    return text[:boundary if boundary > 0 else 149].rstrip(' ;,.') + '…'


def target_reason(plan):
    if not plan: return 'Hedef bilgileri alınamadı, fark sonucu üretilemedi.'
    count = plan['counts']['blocked_operations']
    if count:
        return 'Bazı DDL’ler üretilemedi. Kayıtların altında nedenleri gösteriliyor.'
    if plan['counts']['review_operations']:
        return 'Bazı değişiklikler için uzman incelemesi gerekiyor.'
    return ''


def target_status(plan):
    if plan['counts']['blocked_operations'] and plan['counts']['ready_operations']:
        return 'DDL Kısmen Hazır'
    return status_label(plan['status'])


def object_label(obj):
    if obj['object_type'] in {'COMMENT','GRANT'}:
        name=obj.get('display_name')
        if not name:return type_label(obj['object_type'])+' (bağlı nesne doğrulanamadı)'
    else:name=obj['name']
    return obj['owner']+'.'+name
