# INNOVA_ODI Engel ve İnceleme Analizi

26 Ekim 2026. Durum: **Offline doğrulama PASS**.

25 Ekimde kaydedilmiş gerçek kaynak ve iki hedef gözlemi değiştirilmeden tekrar
planlandı. Yeni Oracle bağlantısı açılmadı, iş verisi okunmadı, DDL uygulanmadı.
76 başlangıç kaydı tekil operasyon kimliğiyle son karara eşlendi. Hiçbir kayıt
rapordan silinmedi veya sayıyı düşürmek için Bilgi durumuna taşınmadı.

| Hedef Başına | Önce | Sonra |
| --- | ---: | ---: |
| Hazır SQL | 542 | 559 |
| İnceleme Gereken İşlem | 71 | 59 |
| Engelli İşlem | 5 | 1 |
| Kaydedilen Fark | 1743 | 1743 |

16 başlangıç kaydı otomatik üretime açıldı: 5 yeni BASICFILE LOB tablosu,
7 kapasitesi kanıtlanan VARCHAR2 BYTE -> CHAR genişlemesi, 4 NOT NULL gevşetme.
Yeni bir tablonun kısıtı da ayrı üretildiği için toplam 17 yeni SQL oluştu.
Eski 542 hazır SQL'in gövdeleri byte düzeyinde aynı. Canlı gözlem ve SQLcl dosyası
aynı 559 SQL, aynı kararlar ve bağımlılıkları üretiyor.

BASICFILE desteği yalnız doğrulanmış yeni, boş ve partition içermeyen heap tablo
ve CLOB/BLOB/NCLOB kolonları içindir. Kolon/storage eşleşmesi, açık BASICFILE,
hedef sürüm, parametre tekilliği ve izin verilen seçenekler doğrulanır. Kaynak
LOB clause metni korunur. SECUREFILE, adlandırılmış segment, şifreleme/sıkıştırma,
partition LOB ve kanıtlanmayan seçenekler bu genişlemeyle desteklenmiş sayılmaz.

BYTE -> CHAR yalnız yeni karakter sınırı eski bayt sınırından küçük değilse,
hedef karakter genişliği ve bayt sınırı biliniyorsa, partition/domain index engeli
yoksa üretilir. CHAR -> BYTE veya olası daraltmalar otomatik üretilmez.

NULL gevşetme açık NOT NULL, PK dışı tam kısıt/kolon kanıtı ve iki tarafta bilinen
DEFAULT ON NULL=false koşuluyla üretilir. Veri güncellenmez. NOT NULL sıkılaştırma,
identity/virtual, DEFAULT ON NULL ve eksik/çelişkili kanıtlar incelemede kalır.

Kalan gerçek engel INNOVA_ODI.DENEME adıdır: kaynak fonksiyon, hedef aynı adla
tablo içeriyor. Oracle ortak ad alanında ikisini oluşturamaz. Mevcut tabloyu
silme veya yeniden adlandırma SQL'i üretilmedi. Bu durum önce genel bağımlılık
incelemesi altında kalıyordu, artık gerçek ad çakışması olarak gösteriliyor.

Kalan 59 inceleme kaydı:

| Neden | Adet | Gerekli Koşul |
| --- | ---: | --- |
| Tip/uzunluk/NUMBER sınırı | 20 | Değer uyumu, yuvarlama ve karakter/bayt kapasitesi |
| Kolon koşulları | 7 | 6 NOT NULL sıkılaştırma,1 tip değişimine bağlı collation kontrolü |
| Nitelikli PL/SQL referansı | 13 | Tam statik çağrı/tip çözümleme ve hedef kanıtı |
| SQL içeren routine | 2 | Tam bağımlılık çözümleme |
| Dinamik SQL | 3 | Çalışma zamanı nesne ve etki incelemesi |
| Public paket sözleşmesi | 1 | Çağıranların uyumu |
| Sequence ayarları | 4 | CACHE/MIN/MAX ve tüketici etkisi, sayaç reseti yok |
| Kaynakta UNUSABLE indeks | 2 | İstenen kullanılabilirlik davranışı, sessiz REBUILD yok |
| PK/UNIQUE | 3 | Mevcut değerlerin doluluk/benzersizlik uyumu |
| Yeni trigger | 2 | Parent/enabled durumu ve sonraki DML etkisi |
| Varsayılanı olan yeni kolon | 1 | Mevcut satırlar üzerindeki varsayılan etkisi |
| Mevcut partition yapısı | 1 | Interval/bölüm sınırları ve veri taşıma etkisi |

Program birimlerinden 5 tanesinin kaynak durumu INVALID. Yakalanmış dictionary
bağımlılıkları tek başına tam exporter/AST kanıtı sayılmadı. Böyle varsayan salt
okunur offline deneme 14 ek çözümleme/ad alanı engeli çıkardı. Bu kapı gevşetilmedi,
INVALID veya eksik statik çözümleme için başarılı derleme iddiası kurulmadı.

Doğrulama: 1163 birim testi PASS /161.46 sn. Son bağımsız incelemedeki DEFAULT ON
NULL ve yinelenen/çelişkili LOB seçeneği bulguları önce kırmızı testle üretildi,
sonra giderildi. Yeni rapor ve yerel LOB SQL görüntüleyici UI'de doğrulandı.
SQL gövdesi karşılaştırmasında yalnız ilk iki generator kimlik yorum satırı ayrıldı.
Oracle üzerinde DDL parse, COMPILE veya uygulama testi yapılmadı. Jenkins, SMTP,
commit ve push bu görevde çalıştırılmadı.

Özel ayrıntılı 76 kayıt: .local/held-audit-current.json ile bulunan dizinde
operation-audit.md, operation-audit.csv, operation-audit.json, verification.json,
unit-final.log ve UI görüntüleri. Yeni rapor run 13a6dbe5c2aa4b03be417f10763a02a2.
Eski run 5a6cf3bb20cb4e72be7557ed35c76edd ve ham gözlemleri korunur. UI kartları iki
hedef yolunun toplamını gösterir, tablodaki değerler hedef başınadır. 2 dk 1 sn yeni
Oracle toplaması değil, kaydedilmiş gözlemlerin yeniden planlama süresidir.

Oracle dayanakları: [CREATE TABLE LOB özellikleri](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-TABLE.html),
[ALTER TABLE uzunluk semantiği](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/ALTER-TABLE.html),
[DEFAULT ON NULL ve ORA-30667](https://docs.oracle.com/en/error-help/db/ora-30667/).
