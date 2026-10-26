# INNOVA_ODI kalan 51 inceleme

26 Ekim 2026. Kaydedilmiş gerçek hedef planındaki 51 `REVIEW_REQUIRED` işlem,
karar nedeni ve ilgili farklar üzerinden tek tek sınıflandırıldı. Bu çalışma
yalnız mevcut özel arşivi okudu. İş verisi, `DENEME` tablosu ve yeni Oracle
bağlantısı kullanılmadı. DDL, DML veya `COMPILE` çalıştırılmadı.

Sayım **hedef başınadır**. Aynı işlemin SQLcl dosya hedefindeki kopyası ikinci
bir iş sayılmaz. Tam 51 satırlık, işlem kimliğine bağlı eylem kaydı
`.local/plsql-audit-current.json` işaretçisinin gösterdiği özel dizinde
`remaining-51-actions.json` ve `remaining-51-actions.csv` olarak bulunur.

| Grup | Adet | Sonraki kanıt veya karar |
| --- | ---: | --- |
| `NUMBER(p,0)` → sınırsız `NUMBER` | 8 | Tipin ölçek ve uygulama sözleşmesi incelenir. Yalnız sayısal aralık uyumu bu değişimi güvenli yapmaz. |
| Sınırsız `NUMBER` → `NUMBER(p,0)` | 4 | Toplu aralık ve kesirli değer sayımı; bağlı nesne denetimi. |
| `VARCHAR2` uzunluk/semantik değişimi | 7 | Toplu karakter ve bayt uzunluğu aşımı; BYTE/CHAR ve bağımlılık denetimi. |
| `VARCHAR2` → `NUMBER` | 1 | Dönüşüm/NLS ve uygulama sözleşmesi; otomatik karar yok. |
| `NOT NULL` sıkılaştırma | 6 | Hedefte toplu NULL sayımı, constraint ve varsayılan değer etkisi. |
| Kolasyon değişimi | 1 | Karşılaştırma, sıralama ve indeks sözleşmesi. |
| Kaynak `INVALID` veya hedef etkin imza sapması olan PL/SQL | 7 | Dört kaynak `INVALID` nesne sahibi tarafından düzeltilmeli; üç hedef şekli tekrar doğrulanmalı. |
| Sequence durumu | 4 | Sayaç/tüketici etkisi için operasyon kararı; `NEXTVAL` okunmaz. |
| Dinamik SQL | 3 | Çalışma zamanı referansı statik bağımlılık kanıtı sayılmaz. |
| Kullanılamaz indeks | 2 | Kaynak `UNUSABLE` durumunun kasıtlılığı DBA tarafından belirlenir. |
| PK/tablo bileşeni | 2 | Toplu duplicate/NULL ve bağımlı FK denetimi. |
| Trigger etkisi | 2 | Çalışma zamanı ve veri yan etkisi incelemesi. |
| Mevcut tabloya yeni tarih kolonu | 1 | Satır sayısı, `SYSDATE` varsayılanı ve constraint etkisi. |
| Bölüm yerleşimi | 1 | Veri taşıma ve bakım kararı. |
| Public package sözleşmesi | 1 | Dış tüketicinin çağrı imzası. |
| Unique index | 1 | Toplu duplicate/NULL denetimi. |
| **Toplam** | **51** | |

## 26 Ekim çevrimdışı karar güncellemesi

Kayıtlı canlı kaynak ve hedef snapshot'ları yeni kural ile yeniden planlandı.
Kaynakta `UNUSABLE` olan `IX_PUSULA_01` ve `IX_PUSULA_02`, hedefte bulunmayan
`PUSULA_OLD` heap tablosuna bağlı normal, nonunique ve bölümsüz indekslerdir.
Kaynak sözlüğü ve DDL birlikte doğrulandığında tek `CREATE INDEX ... UNUSABLE`
SQL'i üretildi. İndeksler kullanılabilir duruma geçirilmedi. Bu iki işlem
`REVIEW_REQUIRED` durumundan `READY` durumuna geçti: güncel sonuç 569 hazır SQL,
49 inceleme, 1 engel, 610 bilgilendirme ve 1743 farktır. Önceki 567 SQL
gövdesinin tamamı değişmedi. `DENEME` engeli ve SQL'siz durumu korundu.

Bu, yukarıdaki 51 satırlık tarihsel canlı sayımı değiştirmez. Güncel çevrimdışı
kanıt `.local/unusable-index-proof-current.json` işaretçisinin gösterdiği
`verification.json` ve doğrulanmış bundle içindedir. Yeni canlı Oracle
karşılaştırması, Oracle DDL/DML, SMTP ve Jenkins işlemi yapılmadı. Dört büyük
PROD uzunluk taraması kullanıcının talimatıyla `NOT_RUN` kalır.

İlk salt okunur veri ölçüm adayları 4 `NUMBER` daraltma, 7 `VARCHAR2`
değişimi, 6 `NOT NULL`, 1 unique index ve 2 PK işlemidir: toplam 20 işlem.
Ölçüm SQL'i oluşturulursa yalnız bu işlem/kolonların adları doğrulanmış
metadata'dan seçilir, sonuçlar toplu sayı olarak tutulur; örnek satır, ham
değer veya gizli veri arşivlenmez. Ölçümün başarılı olması `READY` için tek
başına yeterli değildir: Oracle sözdizimi, bağımlı nesneler, kilit ve uygulama
sözleşmesi ayrıca geçmelidir. Yeni tarih kolonu için satır sayımı da olasıdır,
ancak `SYSDATE` davranışı ayrı karardır.

`DENEME` fonksiyonu ile hedef tablonun Oracle ad alanı çakışması bu 51'in
dışındaki tek `BLOCKED` işlemdir. Hedef tablo korunur ve bu fonksiyon için SQL
üretilmez.

Normal Oracle kaynak/hedef worker'ına otomatik PL/SQL metadata toplama kodu
eklendi ve birim testleri geçti. Ağ erişimi açıldıktan sonra gerçek Oracle
kaynak ve hedefte canlı kabul tamamlandı: 1743 fark, 567 hazır SQL, 51 inceleme,
1 engel. Önceki 567 SQL gövdesi aynı kaldı. İki sequence sayaç gözlemi ve
`C$_/I$_` adlı nesnelerdeki değişim ayrıca kayıtlıdır; tam snapshot eşitliği
iddia edilmez. Toplam süre 7 dk 59 sn, kaynak hazırlama 2 dk 56 sn.
Kanıt `.local/auto-capture-live-verification.json`. Sonraki adım yukarıdaki
ölçümleri sınırlı salt okunur oturumda tasarlamak ve doğrulamaktır. Oracle DDL
uygulaması, Jenkins kurulumu ve SQL*Plus kabulü ayrı `NOT_RUN` durumundadır.

## PROD hedefte sınırlı toplu ölçüm

Canlı koşudan sonra hedef `ALL_TABLES` istatistikleri salt okunur alındı.
`ET_PRIM_ISLEMLERI_TT` yaklaşık 162,8 milyon satır/13,8 milyon blok,
`ET_PRIM_ISLEMLERI_TTNET` yaklaşık 99,9 milyon satır/27,4 milyon blok gösteriyor.
Bu iki tablo için tam veri taraması yapılmadı. `ET202204` yaklaşık 594 bin
satır/50,6 bin blok; bu tablo da küçük tablo sınırına alınmadı. İstatistikler
yaklaşık ve son analiz tarihlerine bağlıdır. Özel kayıt
`.local/remaining-51-target-stats.json`.

En çok 50 bin tahmini satırlı yedi hedef tabloda, her sorguya 10 saniyelik
çağrı sınırı konarak gerçek `SELECT` toplu ölçümleri yapıldı. Sonuç:

| Kanıt grubu | İncelenen işlem | Uyum ihlali |
| --- | ---: | ---: |
| Mevcut kolonlarda `NOT NULL` | 6 | 0 NULL |
| `NUMBER(p,0)` daraltma | 4 | 0 aralık/kesir ihlali |
| `VARCHAR2` uzunluk/semantik | 3 | 0 uzunluk ihlali |
| Unique index | 1 | 0 yinelenen anahtar grubu |
| İki PK | 2 | 0 NULL, 0 yinelenen anahtar grubu |
| **Toplam** | **16** | |

`COMPARE_FIELDS` 34.509, `COMPARE_FIELDS_LOG` 998, `HAKEDIS_TIPI_O` 32,
`ISLEM_ONCESI_TIPI_O` 795, `SATIS_KANALI_O` 12,
`VA_DIAMOND_EXTRACTION_DWH` 15 ve `VW_DT_HAK_COMMON_APPROVE` 0 gerçek satır
gösterdi. Son tablonun boş olması güncel ölçümdür; diğerlerinin sıfır ihlali
iş verisi dışa aktarımı değildir. Yeni tarih kolonunun mevcut 998 satırla
etkileşimi ayrıca uygulama/varsayılan değer kararı gerektirir.

Özel `.local/remaining-51-small-aggregates.json` dosyasında yalnız toplu
sayılar, sorgu hash'leri ve süreler vardır; örnek satır veya ham değer yoktur.
Kalan dört uzunluk ölçümü büyük tablolardadır: `ET202204.ACIKLAMA`,
`ET_PRIM_ISLEMLERI_TT.ACIKLAMA`, `ET_PRIM_ISLEMLERI_TTNET.HIZMET_NO` ve
`ET_PRIM_ISLEMLERI_TTNET.EXTRA_FIELD8`. Bu dört işlem için veri uyumu
`NOT_RUN`; 16 ölçümün başarılı olması DDL sözdizimi, gelecekteki veri girişi,
bağımlılık, kilit veya uygulama sözleşmesini kanıtlamaz. Bu yüzden kararlar
51 REVIEW olarak korunur.

## Kalan teknik kanıtın ayrıştırılması

VPN erişimi yeniden açıldıktan sonra dört büyük kolon için indeks ve bölüm
metadata'sı okundu. Bu kolonların hiçbirinde doğrudan kolon indeksi görülmedi.
`ET202204` bölümsüz, `ET_PRIM_ISLEMLERI_TT` 119 bölüm,
`ET_PRIM_ISLEMLERI_TTNET` 115 bölüm içeriyor. Bu metadata, tüm satırlar için
kesin uzunluk uyumu yerine geçmez. Kanıt
`.local/remaining-51-access-paths.json`; iş satırı okunmadı. Büyük tabloların
geniş veri taraması yapılmadı.

Kayıtlı canlı snapshot ile çevrimdışı yeniden planlama, package body için ayrı
bir sözlük kuralı hatasını gösterdi: hedef `ALL_OBJECTS` aynı adla hem package
spec hem body satırı döndürüyor. Düzeltme yalnız doğru body satırını seçiyor ve
kaynak/hedef spec DDL hash'lerini ayrıca bağlıyor. `PCK_COMPARE_FIELDS` artık
gerçek nedeni olan `COMPARE_FIELDS` ile `COMPARE_FIELDS_LOG` kolon imzası
farklarıyla; `PCK_HYPERION` ise `TTBP.F_CMS_RESULT` harici kolon imzası
farkıyla REVIEW kalıyor. 567 eski SQL gövdesi, 51 REVIEW ve 1 `DENEME` engeli
değişmedi. Özel yeniden planlama kanıtı `.local/package-body-proof-current.json`
işaretçisinin gösterdiği `verification.json` dosyasındadır.

51 işlemin her birindeki ölçüm durumu ve düzeltilmiş gerekçe
`.local/plsql-audit-current.json` işaretçisinin gösterdiği
`remaining-51-evidence.json/.csv` kayıtlarında bulunur: 16 sonradan ölçülen
uyum, 4 büyük tabloda yapılmayan ölçüm, 1 satır sayısı bilinen fakat varsayılan
değer etkisi açık kalan kolon, 1 sınırlı sayı dönüşümü ölçümü ve 29 teknik/iş
sahibi incelemesi. Ölçüm işlemi
canlı karşılaştırmanın kaynak/hedef snapshot işlemiyle aynı transaction değildir;
bu kanıtla otomatik READY kararı verilmez.

Kullanıcı, PROD büyük tablolarındaki dört tam uzunluk taramasını şimdilik
erteledi. Bu kolonlar için örnekleme veya eski istatistik sıfır ihlal kanıtı
olarak kullanılmaz; durumları `NOT_RUN` kalır.

Küçük `VA_DIAMOND_EXTRACTION_DWH` tablosundaki `SURE` kolonunun `VARCHAR2`
→ `NUMBER` dönüşümü için yalnız toplu `VALIDATE_CONVERSION` ölçüldü.
15 satırda oturum `NLS_NUMERIC_CHARACTERS='.,'` altında dönüşemeyen dolu değer
sayısı 0. [Oracle'ın işlev tanımı](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/VALIDATE_CONVERSION.html)
bu ölçümün verilen ifade ve oturum/biçim kuralları için olduğunu açıklar.
Hedef uygulamanın NLS/dönüşüm sözleşmesi, gelecekteki yazmalar ve ALTER
davranışı kanıtlanmadığından işlem REVIEW kalır. Ham değer dışa aktarılmadı;
özel sayı kanıtı `.local/remaining-51-sure-conversion.json`.
