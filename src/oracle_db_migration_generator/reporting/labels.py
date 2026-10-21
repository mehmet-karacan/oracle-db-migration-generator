"""Human labels preserve canonical identity and use only recorded parent facts."""
import re


STATUSES = {'BLOCKED': 'DDL üretilemedi', 'REVIEW_REQUIRED': 'İnceleme gerekli',
            'READY': 'DDL hazır', 'INFORMATIONAL': 'Bilgi', 'NO_ACTION': 'İşlem gerekmiyor',
            'NO_CHANGE': 'Fark yok', 'ERROR': 'Karşılaştırma yapılamadı',
            'INCOMPLETE': 'Karşılaştırma eksik', 'INCONSISTENT': 'Sonuçlar tutarsız',
            'COMPLETE': 'Karşılaştırma tamamlandı', 'PARTIAL': 'Karşılaştırma kısmen tamamlandı',
            'FAILED': 'Karşılaştırma tamamlanamadı'}
TYPES = {'TABLE': 'Tablo', 'VIEW': 'Görünüm', 'MATERIALIZED_VIEW': 'Saklanan görünüm',
         'INDEX': 'İndeks', 'COMMENT': 'Açıklama', 'GRANT': 'Yetki', 'FUNCTION': 'Fonksiyon',
         'PROCEDURE': 'Prosedür', 'PACKAGE_SPEC': 'Paket tanımı', 'PACKAGE_BODY': 'Paket gövdesi',
         'TYPE_SPEC': 'Veri tipi', 'TYPE_BODY': 'Veri tipi gövdesi', 'SEQUENCE': 'Sıra numarası',
         'SYNONYM': 'Nesne takma adı', 'TRIGGER': 'Tetikleyici'}
KINDS = {'CREATE': 'Oluşturma', 'REPLACE': 'Güncelleme', 'REVIEW': 'İnceleme',
         'COMMENT': 'Açıklama', 'GRANT': 'Yetki', 'CREATE_INDEX': 'İndeks oluşturma',
         'ADD_COLUMN': 'Kolon ekleme', 'ALTER_COLUMN': 'Kolon güncelleme',
         'ADD_CONSTRAINT': 'Kural ekleme', 'DROP_CONSTRAINT': 'Kural kaldırma',
         'DROP': 'Kaldırma', 'ALTER': 'Güncelleme', 'NO_ACTION': 'İşlem gerekmiyor'}


def status_label(value):
    return STATUSES.get(value, 'Sonuç doğrulanamadı')


def type_label(value):
    return TYPES.get(value, 'Nesne')


def kind_label(value):
    return KINDS.get(value, 'Yapı değişikliği')


def _plain_reason(text):
    text = re.sub(r' \[[A-Z_]+\]', '', text)
    text = re.sub(r'gerekli ([A-Z_]+) işlemi (BLOCKED|REVIEW_REQUIRED)',
                  lambda m: kind_label(m[1]).lower() + (' işlemi için DDL üretilemedi' if m[2]=='BLOCKED'
                                                       else ' işlemi inceleme bekliyor'), text)
    replacements = {'bağımlı nesnenin gerekli işlemi hazır değil:': 'bağlı nesnenin işlemi hazır değil:',
                    'hedefte bulunamadı ve oluşturulmasını sağlayan kaynak işlemi yok':
                    'hedefte bulunamadı; kaynakta oluşturma tanımı bulunmuyor',
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
        text = '; '.join(parts[:2]) + (f'; ayrıca {len(parts)-2} bağlı nesne' if len(parts)>2 else '') + '.'
    else:
        text = _plain_reason(text)
    return text if len(text)<=240 else text[:239]+'…'


def target_reason(plan):
    if not plan: return 'Hedef bilgileri alınamadı; fark sonucu üretilemedi.'
    count = plan['counts']['blocked_operations']
    if count:
        return 'Bazı DDL’ler üretilemedi. Kayıtların altında nedenleri gösteriliyor.'
    if plan['counts']['review_operations']:
        return 'Bazı değişiklikler için uzman incelemesi gerekiyor.'
    return ''


def target_status(plan):
    if plan['counts']['blocked_operations'] and plan['counts']['ready_operations']:
        return 'DDL kısmen hazır'
    return status_label(plan['status'])


def object_label(obj):
    if obj['object_type'] in {'COMMENT','GRANT'}:
        name=obj.get('display_name')
        if not name:return type_label(obj['object_type'])+' (bağlı nesne doğrulanamadı)'
    else:name=obj['name']
    return obj['owner']+'.'+name
