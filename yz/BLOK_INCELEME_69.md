# 69 Blok İncelemesi - 19 Ekim 2026

69 kaydın tamamı incelendi. 18 engel kaldırıldı, 51 engel korundu. Kaldırılanlar: 8 hazır, 2 inceleme, 7 yalnız uyarı/bilgi ve 1 kolon/depolama/constraint ayrıştırması. Kalan 51: 24 yorum ve 13 indeks eksik parent tabloya bağlı, 8 eksik partition tablo, 3 partition yerleşimi değişimi, 2 indeks kuralı/eksik parent ve 1 ad çakışması.

Source ve target salt okunur. Bu turda Oracle/Jenkins bağlantısı açılmadı, mevcut sabit snapshot’lar kullanıldı. SQL uygulanmadı.

Plan `93664a750b696bac0024ca0ed3bb9c41e443d1bda7e7ad6cbe9781edbaf48da3`. 2.353 fark, 499 READY, 130 REVIEW_REQUIRED, 51 BLOCKED, 1.035 INFORMATIONAL.

| No | Nesne | Yeni durum | İnceleme sonucu |
|---|---|---|---|
| 1 | ET_CC_KULLANICI_ISLEMLERI.HEDEF_AKTARIM_DURUM (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 2 | ET_CC_KULLANICI_ISLEMLERI.KAYIT_ID (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 3 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD7 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 4 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD1 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 5 | ET_CC_KULLANICI_ISLEMLERI.KAYNAK_SISTEM (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 6 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD10 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 7 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD5 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 8 | ET_CC_KULLANICI_ISLEMLERI.AKTARIM_ZAMANI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 9 | ET_CC_KULLANICI_ISLEMLERI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 10 | ET_CC_KULLANICI_ISLEMLERI.ISLEM_ZAMANI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 11 | COMPARE_FIELDS_LOG (COMMENT) | READY | Hedefte tablo mevcut. İlgisiz constraint incelemesi yorum işleminin önkoşulu değil. |
| 12 | ET_CC_KULLANICI_ISLEMLERI.ET_EXTRACTION_INTERFACE (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 13 | ET_CC_KULLANICI_ISLEMLERI.ISLEM_DEGERI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 14 | ET_CC_KULLANICI_ISLEMLERI.ID (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 15 | ET_CC_KULLANICI_ISLEMLERI.ET_EXTRACTION_ID (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 16 | COMPARE_FIELDS (COMMENT) | READY | Hedefte tablo mevcut. İlgisiz constraint incelemesi yorum işleminin önkoşulu değil. |
| 17 | COMPARE_FIELDS_LOG.KAYNAK_ALAN (COMMENT) | READY | Hedefte tablo ve KAYNAK_ALAN kolonu mevcut. İlgisiz constraint incelemesi yorum işleminin önkoşulu değil. |
| 18 | COMPARE_FIELDS_LOG.ACIKLAMA (COMMENT) | READY | Hedefte tablo ve ACIKLAMA kolonu mevcut. İlgisiz constraint incelemesi yorum işleminin önkoşulu değil. |
| 19 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD8 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 20 | ET_CC_KULLANICI_ISLEMLERI.HEDEF_AKTARIM_ZAMANI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 21 | ET_CC_KULLANICI_ISLEMLERI.ET_MIGRATION_UNIT_ID (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 22 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD2 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 23 | ET_CC_KULLANICI_ISLEMLERI.ISLEM_TIPI (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 24 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD6 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 25 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD3 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 26 | ET_CC_KULLANICI_ISLEMLERI.KULLANICI_ID (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 27 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD4 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 28 | ET_CC_KULLANICI_ISLEMLERI.EXTRA_FIELD9 (COMMENT) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI tablosu yok, partition tablo oluşturma desteği gerektiği için yorum bekliyor. |
| 29 | DENEME (FUNCTION) | BLOCKED | Hedefte aynı owner/ad ile TABLE DENEME mevcut. Oracle ortak nesne ad alanında FUNCTION DENEME oluşturulamaz, mevcut tablo korunuyor. |
| 30 | IDX_ET_CC_HA_DURUM (INDEX) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 31 | IDX_ET_CC_ISLEM_TIP (INDEX) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 32 | IDX_ET_CC_ISLEM_ZAMANI (INDEX) | BLOCKED | TO_CHAR ifade indeksi otomatik üretim kuralında desteklenmiyor, parent ET_CC_KULLANICI_ISLEMLERI da hedefte yok. |
| 33 | IDX_ET_CC_KULL_ID (INDEX) | BLOCKED | Hedefte ET_CC_KULLANICI_ISLEMLERI yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 34 | IDX_ISEMRI_TAMAMLANMA_ZAMANI_DBA (INDEX) | READY | ET_PRIM_ISLEMLERI_TTNET tablosu ve indeks kolonları hedef metadata’sında doğrulandı, partition yerleşimi değişikliği bu indeksi gerektirmiyor. |
| 35 | INX_ISLEM_ONC_ARS_BOLG_MI (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 36 | INX_ISLEM_ONC_ARS_ISLEM_TIPI (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 37 | INX_ISLEM_ONC_ARS_IS_EMRI_ID (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 38 | INX_ISLEM_ONC_ARS_MUS_ID (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 39 | INX_ISLEM_ONC_ARS_SIEB_MUS_ID (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 40 | I_ADDR_ID (INDEX) | BLOCKED | C$_0COPY_MTS_ADDR parent tablosu hem kaynak hem hedef envanterinde yok, CREATE INDEX için gerçek eksik önkoşul. |
| 41 | NI_ISLEM_ONC_ARS_ABONE_ID (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 42 | NI_ISLEM_ONC_ARS_HIZMET_NO (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 43 | PK_COMPARE_FIELDS (INDEX) | REVIEW_REQUIRED | Mevcut COMPARE_FIELDS tablosuna unique indeks eklenmesi veri uyumu incelemesi gerektiriyor, metadata engeli yok. |
| 44 | PK_COMPARE_FIELDS_LOG (INDEX) | REVIEW_REQUIRED | Mevcut COMPARE_FIELDS_LOG tablosuna unique indeks eklenmesi veri uyumu incelemesi gerektiriyor, metadata engeli yok. |
| 45 | PK_ET_CC_KULLANICI_ISLEMLERI (INDEX) | INFORMATIONAL | ET_CC_KULLANICI_ISLEMLERI tablosundaki eşleşen PK/UK indeksi oluşturur, bağımsız indeks üretimi gerekmiyor. |
| 46 | PK_ISLEM_ONCESI_ARSIV (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 47 | SYS_C0044099 (INDEX) | INFORMATIONAL | PRODUCT tablosundaki eşleşen PK/UK indeksi oluşturur, bağımsız indeks üretimi gerekmiyor. |
| 48 | SYS_C0049777 (INDEX) | INFORMATIONAL | RAPOR_ISTEK tablosundaki eşleşen PK/UK indeksi oluşturur, bağımsız indeks üretimi gerekmiyor. |
| 49 | SYS_C0062300 (INDEX) | INFORMATIONAL | KATALOG_FIYAT_AUDIT tablosundaki eşleşen PK/UK indeksi oluşturur, bağımsız indeks üretimi gerekmiyor. |
| 50 | SYS_C0062301 (INDEX) | INFORMATIONAL | KATALOG_FIYAT_AUDIT tablosundaki eşleşen PK/UK indeksi oluşturur, bağımsız indeks üretimi gerekmiyor. |
| 51 | TH_BAYI_ISLEM_IDX (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 52 | UQ_IOA_DETAY_ID (INDEX) | BLOCKED | Hedefte ISLEM_ONCESI_ARSIV yok. Parent partition tablonun CREATE işlemi bloklu, indeks önce üretilemez. |
| 53 | PCK_CALL_CENTER (PACKAGE_SPEC) | READY | Spec yalnız builtin VARCHAR2 parametreli prosedür imzası içeriyor. Ortak exporter kaydındaki body tablo bağımlılıkları spec’in önkoşulu değil. |
| 54 | GECICI (PROCEDURE) | READY | Tüm referans tablolar hedefte mevcut, kaynak kolonları aynı veri tipiyle hedefte doğrulandı. Ayrı partition/uzunluk değişiklikleri routine için önkoşul değil. |
| 55 | WITH_DENEME (PROCEDURE) | READY | ISIM, WITH sorgusunun yerel CTE adı. Gerçek tablo referansı VA_ET_EXTRACTION_TTNET hedefte mevcut, CTE kapsam hatası düzeltildi. |
| 56 | COMPARE_CONSTRAINTS (TABLE) | INFORMATIONAL | Yalnız mevcut LOB depolama ayarı farkı, fiziksel depolama karşılaştırması kapalı. Ayar korunarak uyarı raporlandı. |
| 57 | COMPARE_FIELDS_LOG (TABLE) | INFORMATIONAL, READY, REVIEW_REQUIRED | LOB depolaması uyarıya ayrıldı. Güvenli kolon genişletmesi hazır, yeni default’lu kolon ve PK/UK farkı ayrıca inceleme gerektiriyor. |
| 58 | ET_CC_KULLANICI_ISLEMLERI (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 59 | ET_PRIM_ISLEMLERI_TT (TABLE) | BLOCKED, READY, REVIEW_REQUIRED | Mevcut partition sınırları farklı. Yerleşim dönüşümü bloklu, varsa bağımsız güvenli kolon/default işlemleri ayrıldı. |
| 60 | ET_PRIM_ISLEMLERI_TT2 (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 61 | ET_PRIM_ISLEMLERI_TTNET (TABLE) | BLOCKED, READY, REVIEW_REQUIRED | Mevcut partition sınırları farklı. Yerleşim dönüşümü bloklu, varsa bağımsız güvenli kolon/default işlemleri ayrıldı. |
| 62 | ET_PRIM_ISLEMLERI_TTNET23 (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 63 | ET_PRIM_ISLEMLERI_TTNET_REKLM (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 64 | ET_PRIM_ISLEM_ONCESI (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 65 | ET_PRIM_ISLEM_ONCESI_DETAY (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 66 | ET_TTNET_ELIF (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 67 | ET_TT_SAYI_KONTROL (TABLE) | BLOCKED | Mevcut partition sınırları farklı. Yerleşim dönüşümü bloklu, varsa bağımsız güvenli kolon/default işlemleri ayrıldı. |
| 68 | ISLEM_ONCESI_ARSIV (TABLE) | BLOCKED | Hedefte bulunmayan partition tablo. Partition/interval sınırları korunmuş güvenli CREATE kuralı mevcut değil, heap’e dönüştürülmedi. |
| 69 | STG_CHRG_TRF_VER (TABLE) | INFORMATIONAL | Yalnız mevcut LOB depolama ayarı farkı, fiziksel depolama karşılaştırması kapalı. Ayar korunarak uyarı raporlandı. |

Makine kanıtı: `output/local-report-v11/blocker-audit69.json`, her kaydın önceki/yeni işlem, fark ve kanıt kimlikleri bulunur.

Test: 14 audit regresyonu ve tüm kısa kapı (son XML: output/pytest-audit69-delivery.xml). Geniş kabul/Jenkins/DDL uygulama NOT_RUN.

Doğrulama: 201 passed / 29.43s, 525 bundle/538 run dosyası, 0 kırık link veya gerçek sır eşleşmesi.
