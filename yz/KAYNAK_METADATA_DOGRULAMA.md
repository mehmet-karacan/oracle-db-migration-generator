# Kaynak kolon metadata doğrulaması - 19 Ekim 2026

Kullanıcı DDL Sync bağlantısına bakılmasını, ardından Jenkins'in açılmasını ve
kaynak Oracle erişimini açıkça yetkilendirdi. Bu yerel ek doğrulamada Git desired
DDL otoritesi olarak korundu. Canlı kaynak metadata okuması yeni bir DDL kaynak
sağlayıcısı veya kaynak SQL'ini çalıştırma akışı değildir.

## Erişim ve sınır

- Jenkins HTTP adresinden açıldı, mevcut mkaracan oturumu kullanıldı. HTTPS
  denemesi timeout oldu, sertifika kontrolü kapatılmadı, uyarı aşılmadı.
- Sky DDL Sync credential açıklamasından kaynak ortamı bulundu. Parola
  arayüzde Concealed kaldı, Change Password/Save kullanılmadı, decrypt veya
  script console çalıştırılmadı. Mevcut kullanıcı yetkili yerel INNOVA_ODI
  credential'ıyla tek Oracle bağlantısı başarılı oldu.
- Kaynak oturumunda SET TRANSACTION READ ONLY, SESSION_USER kontrolü,
  allowlist CAPTURE_INVENTORY ve CAPTURE_QUERIES['columns'] çalıştırıldı.
  Envanter önce/sonra aynı: 830 kayıt. 17.456 kolon metadata kaydı alındı.
- İş tablosu okunmadı, DDL/DML, Jenkins build/job değişikliği, push veya mail yok.
  Target'a yeni bağlantı açılmadı. Mevcut target capture yeniden kullanıldı.
- Endpoint/credentials/ham gözlem .local altında, git check-ignore doğrulandı.

## Git ile karşılık doğrulaması

Kaynak kaydı output/prepared-source-v6 üzerine yazılmadı. Yerel yardımcı,
kaynak capture tutarlılığını ve owner'ını doğruladı, her kaynak tabloda kolon
kümesi ve önceden bilinen tüm canonical kolon alanlarını canlı dictionary
karşılığıyla eşleştirdi. Fark varsa tamamlamayı durdurur. Bilinen tip, boy,
default, nullable, position, görünürlük, identity/virtual vb. değiştirilmedi.

- 405 tabloda 16.560 kaynak kolonunun bilinen alanları eşleşti.
- 10.088 örtük uzunluk semantiği BYTE olarak doğrulandı, açık CHAR/BYTE korundu.
- 10.379 eksik collation değeri kolon bazında tamamlandı.
- Global source_length_semantics profili UNKNOWN olarak kaldı, tek bir şema
  default'undan bütün geçmiş kolonlara değer atanmadı.
- Yeni snapshot output/prepared-source-v7/source-snapshot.json. Orijinal Git
  source-input.json ve nesne DDL hash'leri birebir korundu. Ek kanıt JSON'u
  metadata/source-column-semantics.json altında, hash ve gerçek SOURCE_SPAN
  aralığıyla snapshot evidence kaydına bağlandı. Bu yerel ek veri dosyasıdır,
  Git deposunun özgün dosyası olduğu iddia edilmez.
- Snapshot schema, DDL hash'leri, load_snapshot(require_ddl=True) roundtrip ve
  proof dosyası hash'i doğrulandı. Gözlem güncel metadata kanıtıdır, geçmiş SCN
  veya Git export anında atomik Oracle snapshot garantisi değildir.

## Karşılaştırma ve dar düzeltme

İlk ek metadata karşılaştırmasında kalan tek UNKNOWN, hedef VARCHAR2 iken
kaynak NUMBER olan VA_DIAMOND_EXTRACTION_DWH.SURE kolonunun collation alanıydı.
Kaynak NUMBER için collation uygulanamaz, karakter kaynaklarında eksik bilgi
koruması bu vakaya da uygulanıyordu. tests/unit/test_compare.py içindeki yeni
test önce bu nedenle kırmızı oldu. compare/snapshots.py koşulu yalnız karakter
veya tipi bilinmeyen kaynak için eksik collation'ı UNKNOWN yapacak şekilde
düzeltildi. Gerçek tip dönüşümü REVIEW_REQUIRED kalır, hazır SQL üretilmez.

Doğrulama: ilgili testler 15 passed / 4.14s, bağımsız dar inceleme 15 passed /
3.99s ve önemli bulgu yok. Tam kısa kapı 157 passed / 23.07s,
output/pytest-source-metadata.xml. Skip/failure yok.

Güncel comparison-only çıktı output/source-semantics-comparison-v2:
2.353 gözlenen fark, 545 MISSING, 1.048 EXTRA, 729 CHANGED, 31 INFORMATIONAL,
0 UNKNOWN. TARGET_DDL_PARTIAL nedeniyle genel sonuç PARTIAL ve tam fark sayısı
null. Mevcut target snapshot'taki beş INVALID/PLS hatalı kısmi tanım değişmedi.

Yeni SQL/HTML migration paketi bu adımda üretilmedi, local-report-v5 tarihsel
paketi korundu. Sonraki somut adım, ek metadata'nın CREATE/ADD üretiminde etkin
collation'ı da koruduğunu kısa testle doğrulamak ve yeni plan/raporu üretmek,
hedefteki INVALID tanımları açık diagnostic olarak korumaktır. Kullanıcıdan
yeniden kaynak bağlantı bilgisi istenmesine gerek yok.
