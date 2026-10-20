# Hedef INVALID yalnız uyarı — 19 Ekim 2026

Kullanıcı netleştirmesi: hedefte INVALID nesne bulunabilir; amaç raporlamaktır,
bu durum tek başına BLOCKED yapmamalıdır. AKTIF_GOREV ve kaynak/hedef sözleşmesine
bu kural eklendi. Oracle'a COMPILE/REPAIR/DDL uygulanmadı.

## Uygulama

- model/validity.py yalnız yakalanmış ham DDL, tam envanter/dictionary ve
  parser-only diagnostic taşıyan bilinen INVALID nesneyi tanır. Bu, tanımın
  bilindiği veya nesnenin geçerli olduğu iddiası değildir.
- compare/snapshots.py: bu nesne yalnız hedefteyse ve korunacaksa gövde parse
  sorunu karşılaştırma kapsamını eksiltmez. Varlığı EXTRA/INFORMATIONAL kalır;
  ham snapshot coverage değiştirilmez. Geçerli nesnenin parser hatası, izin
  hatası, eksik ham dosya veya karşılaştırılması gereken ortak tanımın UNKNOWN
  olması bu istisnaya girmez.
- planning/graph.py: metadata ile mevcut olduğu bilinen INVALID yerel/dış
  nesne, yalnız compile status nedeniyle eksik bağımlılık sayılmaz. Bloke veya
  inceleme gerektiren source prerequisite üzerinden geçiş yapılmaz.
- Dış ALL_OBJECTS kaydı yalnız varlık/status kanıtıdır. FK/kolon/key/index
  yapısını kanıtlamaz. Yapısal kanıt yoksa VALID/INVALID'den bağımsız blok sürer.
- planning/rules.py INVALID, ORA/PLS kodları, korunacak INVALID parse sorunu ve
  dış INVALID referansı uyarı olarak raporlar. Hata mesajındaki sırlar taşınmaz.
- HTML'de scope etiketi Karşılaştırma kapsamı oldu; ham capture tamlığıyla
  karıştırılmaz. Hedefin INVALID ve parse uyarıları görünür kalır.

## Kanıt

İlk kısa testte 4 kırmızı/3 yeşil ile eski global/bağımlılık blokları gösterildi.
Bağımsız incelemede dış FK için yalnız ALL_OBJECTS varlığının yapısal kanıt
sayılması bulundu; VALID ve INVALID için iki kırmızı regression eklendi ve
düzeltildi. Yerel FK guard'ı ve candidate-block propagation korundu.

Son dar kapı 11 passed / 4.19s; bağımsız teyit 11 passed / 10.15s. Tam kısa kapı
187 passed / 26.73s, output/pytest-invalid-target-final.xml. Skip/failure yok.
Wheel dist-v8 ve ayrı wheel-smoke-v8 import/config kontrolü geçti.

Bu değişiklikte source/target veya Jenkins bağlantısı açılmadı; kayıtlı
source-v8/target-reparsed-v7 kullanıldı. Target'taki beş parser sorunu olan
INVALID tanımın tamamı source'da yoktur ve korunur. Eski raporlar değiştirilmedi.

## Güncel paket

output/local-report-v8: comparison scope inventory/DDL/dictionary COMPLETE;
2353 farkın tamamı sayılabilir. Ham target DDL snapshot'ı PARTIAL kaldı. 15 INVALID
ve 5 target-only INVALID parse uyarısı görünür; TARGET_DDL_PARTIAL genel engeli yok.
447 READY, 119 REVIEW, 69 BLOCKED, 1020 INFORMATIONAL; plan BLOCKED/run PARTIAL
kalan gerçek bağımlılık ve destek sınırlarından kaynaklanır.

472 bundle/483 run dosyası VERIFIED; 19 HTML, max 93396 byte, 0 kırık link;
184 Git adayı/run dosyalarında 0 gerçek sır/endpoint eşleşmesi. Plan/kod/wheel
hash'i eşleşti. Kanıt output/local-report-v8-verification.json; arşiv aynı adlı
ZIP'te. Eski v6 ve ara v7 paketleri değiştirilmedi; v8 son düzeltme geçişini içerir.
