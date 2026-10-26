# INNOVA_ODI PL/SQL bağımlılık incelemesi

26 Ekim 2026 tarihli bu inceleme, önceki 59 `REVIEW_REQUIRED` işlemini temel alır. Kaynak ve hedefteki ilgili program birimleri için Oracle sözlüğü yalnız salt okunur işlem içinde sorgulandı. İş verisi okunmadı; DDL, DML ve `COMPILE` çalıştırılmadı. Toplanan kanıt, eski kaynak ve hedef snapshot'larına ek olarak bağlandı. İlk snapshot ve ham DDL korunarak aynı kaydedilmiş gözlem iki hedef yolunda tekrar planlandı.

| Hedef başına | Önce | Sonra |
| --- | ---: | ---: |
| Gözlenen fark | 1743 | 1743 |
| Hazır işlem ve SQL | 559 | 567 |
| İnceleme | 59 | 51 |
| Engel | 1 | 1 |
| Bilgilendirme | 610 | 610 |

59 önceki incelemenin tamamı yeni işleme bağlandı. Aşağıdaki sekiz statik PL/SQL biriminin kaynak gövdesi, güncel `VALID` durumu, derleme hatası, bağımlılık listesi, hedef nesne/kolon ve etkin çağrı imzası, synonym çözümü ve gerekli doğrudan yetkiler doğrulandı. Kanıt tam kaynak ve hedef bağlantı gözlemine bağlandı; hedef kök birimin sonradan oluşması veya değişmesi de kontrol edildi. Bu birimler için kaynak tanımını koruyan SQL üretildi:

- `FUNCTION F_ODI_NIGHT_CHECK_AND_LOG`
- `FUNCTION F_VA_AKTARIM_BASLA`
- `PACKAGE BODY PCK_CALL_CENTER`
- `PROCEDURE ADDTOTABLELOGGPP`
- `PROCEDURE LOGGPPBASLANGICBITISGUNCELLE`
- `PROCEDURE P_GPP_ODENEN_ADETLER`
- `PROCEDURE P_VA_AKTARIM_BITIR`
- `PROCEDURE WITH_DENEME`

Önceki 559 SQL gövdesi bayt düzeyinde aynı kaldı. Kaynak ve hedef ham DDL hash'leri ile 1743 fark değişmedi. Canlı bağlantı gözlemi ve SQLcl dosya hedefi aynı kararları, bağımlılıkları ve SQL gövdelerini verdi. İki hedefin her birinde 567 hazır işlem vardır; bu sayı iki hedefin toplamı değildir. `DENEME` ad çakışması tek engel olarak kaldı. Hedef `DENEME` tablosuna dokunulmadı ve ilgili fonksiyon için SQL üretilmedi.

## Açık 51 inceleme

| Neden | Adet | Kalan kanıt veya karar |
| --- | ---: | --- |
| Veri tipi dönüşümü | 20 | Mevcut değerlerin yeni türe kayıpsız uyumu |
| Kolon değişikliği | 7 | Kolon/veri etkisinin ayrı değerlendirilmesi |
| Derlenmiş PL/SQL bağımlılığı | 7 | Güncel `INVALID` kaynak veya değişen hedef kolon imzası |
| Sequence durumu | 4 | Çalışma zamanı değerinin korunması |
| Dinamik SQL | 3 | Statik sözlük bağımlılığıyla kanıtlanamayan çalışma zamanı referansı |
| Index kullanılabilirliği | 2 | Kaynak `UNUSABLE` durumu |
| Tablo bileşeni | 2 | PK ve tablo bağımlılığı |
| Trigger etkisi | 2 | Çalışma zamanı/veri etkisi |
| Yeni kolon veri etkisi | 1 | Mevcut satırlarla uyum |
| Partition yerleşimi | 1 | Veri/yerleşim değişikliği |
| Public package sözleşmesi | 1 | Dış tüketici etkisi |
| Unique index | 1 | Mevcut satırlarda tekillik |

Yedi PL/SQL kaydı özellikle açık kaldı: `PCK_COMPARE_FIELDS` ve `GECICI` bağlı tablo kolon imzaları değiştiği için; `PCK_HYPERION` dış `TTBP.F_CMS_RESULT` imzası değiştiği için; `PCK_ISLEM_TIPI_AKTAR2`, `PCK_LOG_UTIL`, `PCK_ISLEM_DAGITIM` ve `FILLDML` kaynakta `INVALID` olduğu için hazır sayılmadı. Üç dinamik SQL kaydı da otomatik üretime açılmadı.

## Kanıt ve sınır

- Kaynakta 762, hedefte 786, toplam 1548 metadata çağrısı yapıldı. Ürün sorguları sabit ve parametreli; hata veya görünmeyen kayıt `UNKNOWN` olarak tutulur.
- [Oracle ALL_DEPENDENCIES](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_DEPENDENCIES.html) derlenmiş statik bağımlılıklar içindir. Dinamik SQL için tam referans kanıtı sağlamaz; bu kayıtlar incelemede kalır.
- [AUTHID davranışı](https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/invokers-rights-and-definers-rights-authid-property.html) nedeniyle invoker rights birimler bu dar otomatik yolun dışındadır.
- Özel arşivde `.local/plsql-audit-current.json` işaretçisinin gösterdiği dizinde `verification.json` ve 59 satırlık `remaining-59-audit.csv` bulunur. Son yerel UI koşusu `c0f45c8ca18848988968bafd90943e5c` durum olarak `PARTIAL` kaldı; bütün farkların güvenle uygulanabilir olduğu anlamına gelmez.
- Bu çalışma yeni metadata ile **yeniden planlama** kabulüdür. Gerçek hedefte DDL uygulanması ve Jenkins kabulü `NOT_RUN` durumundadır. Yeni zamanlanmış koşulara kanıt toplamanın otomatik bağlandığı iddia edilmez.

26 Ekim devamında ek metadata toplayıcısı normal Oracle kaynak/hedef worker akışına bağlandı; 1213 birim testi geçti. Ağ erişimi geri geldiğinde yeni gerçek Oracle kaynak/hedef koşusu 7 dk 59 sn sürdü. 567 SQL gövdesi ve karar sayıları önceki kayıtla aynı; iki sequence sayaç değeri ile geçici hedef nesneleri değişmiş olduğundan tam snapshot eşitliği iddia edilmez. Kalan 51 işlemin tekil eylem sınıflandırması [ayrı planda](INNOVA_ODI_KALAN_51_PLANI.md) bulunur. Toplu veri ölçümü adayları `READY` kararı değildir. Kaynakta `INVALID` kalan dört birim şema sahibinin düzeltmesi olmadan `READY` yapılmaz.

Sonraki çevrimdışı kural düzeltmesi, hedef package body için sözlükte birlikte
görünen spec/body satırlarını doğru ayırır ve iki tarafın spec DDL hash'lerini
kontrol eder. `PCK_COMPARE_FIELDS` ve `PCK_HYPERION` artık gerçek bağımlı kolon
imzası gerekçeleriyle REVIEW kalır. Bu yeni kodla gerçek Oracle'a tekrar
bağlanılmadı; kayıtlı canlı snapshot yeniden planlandı. 567 hazır SQL gövdesi,
51 REVIEW ve `DENEME` engeli aynı kaldı. 1219 birim testi geçti.
