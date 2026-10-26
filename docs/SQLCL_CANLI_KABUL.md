# SQLcl Canlı Eşdeğerlik Kabulü

25 Ekim 2026. Durum: **PASS**.

SQLcl 26.2 ile Oracle 19c INNOVA_ODI şemasından gerçek, salt okunur metadata
alındı. Dosya arayüzden SKY projesine aktarıldı ve arşiv SHA256 değeri doğrulandı.
Aynı sabit SKY kaynak snapshot'ı, gerçek PROD bağlantısından kaydedilen hedef
gözlemi ve SQLcl dosyası ile ayrı ayrı planlandı. Dosya kolunda Oracle bağlantısı
açılmadı. Kaynak profilinin ve kaynak snapshot kimliğinin aynı kaldığı denetlendi.

| Ölçüt | Canlı Hedef Gözlemi | SQLcl Dosyası |
| --- | ---: | ---: |
| Fark | 1743 | 1743 |
| Hazır SQL | 542 | 542 |
| İnceleme Gereken İşlem | 71 | 71 |
| Engelli İşlem | 5 | 5 |
| Bilgilendirme | 610 | 610 |

Farkların nesne/alan/değer bilgileri, kararlar, ön/son koşullar ve bağımlılık
kenarları eşit.542 SQL gövdesi byte düzeyinde aynı. Yalnız çalışma ve işlem
kimliğini taşıyan ilk iki yorum satırı karşılaştırmadan ayrıldı. Gerçek SQL'deki
boşluklar, çift tırnaklar ve gövde metni normalize edilmedi.

Son toplama565.530 sn (9 dk 26 sn),823 DDL kaydı,90 harici bağımlılık durum kaydı ve
24.661.019 bayt. Sorgu hatası yok, OWN envanteri başlangıç ve bitişte aynı.
Toplamalar arasında kaybolan tek C$_ teknik tablosu mevcut kapsam politikasında
zaten dışarıda. Bu nedenle işlevsel fark/DDL sonucu değişmedi.

Gerçek kaynak alımı335.543 sn, canlı hedef alımı211.278 sn. Son kayıtlı gözlem
planlaması89.624 sn, UI çalışma süresi1 dk 32 sn. Bu son süre yeni Oracle toplaması
içermez. UI kartları iki hedefin toplamını gösterir:3486 fark/1084 SQL. Bunlar iki
ayrı üretim ortamı anlamına gelmez, aynı PROD gözleminin canlı ve dosya yollarıdır.

Planlarda71 inceleme ve5 engel korunduğu için UI durumu Kısmen Tamamlandı.
Eşdeğerlik kabulünün PASS olması bütün DDL'nin uygulanabilir olduğu anlamına gelmez.

Canlı kabulde düzeltilenler:

- SQLcl metin bind sınırı için CLOB parametre aktarımı.
- SQLcl output tamponu için DBMS_OUTPUT.ENABLE(NULL), mevcut boyut bütçeleri korunur.
- Değişen ham envanterde ORA-20011 ile başarısız kapanış.
- DBMS_METADATA oturum dönüşümlerinin DEFAULT değerine alınması.
- CREATE TABLE SQL'inin parser tarafından doğrulanan kendi aralığıyla sınırlanması.
- NLS_CALENDAR ve mevcut ALL_DEPENDENCIES kayıtlarının harici nesne tür/durum kanıtı.
- Windows geçici paylaşım kilitlerinde sınırlı, üzerine yazmayan dizin rename tekrarları.

Eksik/eski dosyalarda takvim veya harici kanıt UNKNOWN kalır. Yeni harici referans,
synonym zinciri ve başka şemanın kolon/anahtar yapısı bu ek kayıtla doğrulanmış sayılmaz.

1135 birim testi PASS/105.98 sn. Gerçek UI import, başka projede dosyanın görünmemesi,
SQLcl hedefindeki görünümün hazır olması ve yerel SQL görüntüleyici PASS.
SQL*Plus canlı kabulü NOT_RUN. Jenkins kurulumu/değişikliği NOT_RUN. SMTP gönderimi,
Oracle DDL/DML/COMPILE, dış Git push ve commit yapılmadı.

Özet kanıt: output/portable-capture/live-acceptance-summary.json.
Ham SQL ve ayrıntılı kabul yalnız Git dışındaki .local arşivinde.
.local/portable-live-current.json ilgili dizini gösterir. Burada acceptance.json,
parity.json, unit-suite-final3.log, replay-provenance.json bağlantılı çalışma arşivi
ve acceptance-results.png bulunur. Önceki başarısız denemeler korunmuştur.
