# Önceki 51 blok için teknik işler — 19 Ekim 2026

51 eski blok korundu: 8 eksik partition tablo, 3 mevcut partition yerleşimi, 24 parent bağımlı yorum, 13 parent bağımlı indeks, 2 indeks tanım/parent sorunu ve 1 namespace çakışması. Bunlar hedef INVALID durumundan kaynaklanmıyor. Desteği eksik dönüşümü uyarıya indirerek SQL üretmek doğru olmaz.

İş sırası: önce 8 partition CREATE desteği (37 bağımlı yorum/indeksin önünü açar); sonra expression index; ardından mevcut partition dönüşümü için ayrı destekli işlem sınırları. Eksik parent ve namespace çakışması kaynak/kapsam kararı ister. Mevcut satırları koruma şartı sürer.

Bu liste bir uygulama/backlog dökümüdür; yeni kapsam veya Oracle üzerinde işlem yetkisi değildir. Her sıra [teknik denetim JSON](../output/backend-review130-v2/blocker-technical-audit.json) kaydındaki nesne, reason_codes, references ve evidence_ids ile bağlıdır.

| # | Önceki blok | Somut eksik / çözüm koşulu |
|---:|---|---|
| 1 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.HEDEF_AKTARIM_DURUM | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 2 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.KAYIT_ID | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 3 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD7 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 4 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD1 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 5 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.KAYNAK_SISTEM | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 6 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD10 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 7 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD5 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 8 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.AKTARIM_ZAMANI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 9 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 10 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ISLEM_ZAMANI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 11 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ET_EXTRACTION_INTERFACE | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 12 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ISLEM_DEGERI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 13 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ID | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 14 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ET_EXTRACTION_ID | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 15 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD8 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 16 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.HEDEF_AKTARIM_ZAMANI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 17 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ET_MIGRATION_UNIT_ID | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 18 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD2 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 19 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.ISLEM_TIPI | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 20 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD6 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 21 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD3 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 22 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.KULLANICI_ID | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 23 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD4 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 24 | COMMENT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD9 | Eksik/bloke parent tablo: ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 25 | FUNCTION INNOVA_ODI.DENEME | Hedefte DENEME TABLE, kaynakta DENEME FUNCTION var; Oracle ortak namespace çakışıyor. Ürün hatası değildir. Silme/yeniden adlandırma için açık kapsam/isim kararı gerekir. |
| 26 | INDEX INNOVA_ODI.IDX_ET_CC_HA_DURUM | Eksik/bloke parent tablo: INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 27 | INDEX INNOVA_ODI.IDX_ET_CC_ISLEM_TIP | Eksik/bloke parent tablo: INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 28 | INDEX INNOVA_ODI.IDX_ET_CC_ISLEM_ZAMANI | TO_CHAR(ISLEM_ZAMANI,'YYYYMM') function index desteği eksik. Exact expression, NLS/function semantiği ve index özellikleri için kapalı kural/test gerekir; ET_CC_KULLANICI_ISLEMLERI parent engeli de çözülmeli. |
| 29 | INDEX INNOVA_ODI.IDX_ET_CC_KULL_ID | Eksik/bloke parent tablo: INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 30 | INDEX INNOVA_ODI.INX_ISLEM_ONC_ARS_BOLG_MI | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 31 | INDEX INNOVA_ODI.INX_ISLEM_ONC_ARS_ISLEM_TIPI | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 32 | INDEX INNOVA_ODI.INX_ISLEM_ONC_ARS_IS_EMRI_ID | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 33 | INDEX INNOVA_ODI.INX_ISLEM_ONC_ARS_MUS_ID | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 34 | INDEX INNOVA_ODI.INX_ISLEM_ONC_ARS_SIEB_MUS_ID | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 35 | INDEX INNOVA_ODI.I_ADDR_ID | Parent C$_0COPY_MTS_ADDR source ve target envanterinde yok. Doğru parent DDL veya kapsam kararı gerekli; sentetik parent oluşturulmaz. |
| 36 | INDEX INNOVA_ODI.NI_ISLEM_ONC_ARS_ABONE_ID | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 37 | INDEX INNOVA_ODI.NI_ISLEM_ONC_ARS_HIZMET_NO | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 38 | INDEX INNOVA_ODI.PK_ISLEM_ONCESI_ARSIV | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 39 | INDEX INNOVA_ODI.TH_BAYI_ISLEM_IDX | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 40 | INDEX INNOVA_ODI.UQ_IOA_DETAY_ID | Eksik/bloke parent tablo: INNOVA_ODI.ISLEM_ONCESI_ARSIV. Parent CREATE desteklendiğinde var olan COMMENT/INDEX kuralı dependency grafiği üzerinden tekrar planlanır; tek başına hazır yapılmaz. |
| 41 | TABLE INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 42 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT | Mevcut partition yerleşimi farklı. Veri taşımayan destekli dönüşüm ve doğrulanmış ara adımlar tanımlanmadan DROP/recreate, split/merge/exchange üretilmez. |
| 43 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT2 | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 44 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET | Mevcut partition yerleşimi farklı. Veri taşımayan destekli dönüşüm ve doğrulanmış ara adımlar tanımlanmadan DROP/recreate, split/merge/exchange üretilmez. |
| 45 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET23 | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 46 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET_REKLM | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 47 | TABLE INNOVA_ODI.ET_PRIM_ISLEM_ONCESI | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 48 | TABLE INNOVA_ODI.ET_PRIM_ISLEM_ONCESI_DETAY | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 49 | TABLE INNOVA_ODI.ET_TTNET_ELIF | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |
| 50 | TABLE INNOVA_ODI.ET_TT_SAYI_KONTROL | Mevcut partition yerleşimi farklı. Veri taşımayan destekli dönüşüm ve doğrulanmış ara adımlar tanımlanmadan DROP/recreate, split/merge/exchange üretilmez. |
| 51 | TABLE INNOVA_ODI.ISLEM_ONCESI_ARSIV | Eksik partition tablo için typed partition/interval AST, sınır/key/alt partition/depolama suffix kanıtı ve aynı kaynak metinden doğrulanan CREATE kuralı eksik. Kolon/constraint/backing-index grafiğiyle birlikte desteklenmeli. |

## Dependency envanteri düzeltmesiyle görünür olan dört blok

Bu kayıtlar önceki 130 inceleme içinde bulunuyordu. Toplam fark artmadı; gerekli önkoşulun doğrulanamadığı artık somut olarak görüldüğünden güncel BLOCKED sayısı 55 oldu.

| Nesne | Açık önkoşul |
|---|---|
| PCK_CALL_CENTER BODY | ET_CC_KULLANICI_ISLEMLERI oluşturma işlemi partition desteği nedeniyle bloke; ayrıca DUAL çözümü kanıt gerektiriyor. |
| PCK_COMPARE_FIELDS BODY | Değişen package spec incelemede; ALL_CONSTRAINTS/ALL_CONS_COLUMNS/ALL_TABLES/ALL_TAB_COLS çözümü mevcut envanterde doğrulanmıyor. |
| PCK_ISLEM_TIPI_AKTAR2 BODY | INNOVA_ODI.ISLEM_HESAP_DENEME3 ve TTBP.SEQ_ISLEM_HESAP_ID source/target/dış nesne kanıtında yok. |
| PCK_LOG_UTIL BODY | Birleşik dependency sidecar içindeki BIN$ recyclebin tablo referansı source/target kanıtında yok; düşürülmedi. |

## Doğrulama koşulları

Partition desteği çalışılırken önce gerçek snapshot biçimindeki küçük kırmızı test; ardından tek doğru CREATE, ham suffix/gövde koruması, key sırası ve bağımlı işlem sırası doğrulanmalı. Eksik key/boundary, LONG/LONG RAW, bilinmeyen expression ve mevcut veri taşıyan dönüşüm negatif testleri korunmalı. Mevcut dictionary okuması yeterli olmayan koşullar boş/uygun varsayılmaz.

Source/target salt okunur kaldı. Yeni canlı Oracle kabulü, SQL uygulaması ve Jenkins kurulumu **NOT_RUN**. Bu tur 51 engelin tamamı için somut iş kaydı çıkarıldı; partition desteği bu kapsamda uygulanmadı.
