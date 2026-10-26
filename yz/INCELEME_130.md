# 130 inceleme kaydı - 19 Ekim 2026

130 eski REVIEW_REQUIRED işlem tek tek kaynak/hedef snapshot ve kanıtlarıyla değerlendirildi. 3 işlem READY, 1 INFORMATIONAL, 4 somut bağımlılık nedeniyle BLOCKED, 122 REVIEW_REQUIRED oldu. 2.353 mantıksal farkın tamamı korunuyor, eski/yeni change ID eşlemesi denetim JSON dosyasında.

Güncel motor sonucu: **502 READY · 122 REVIEW_REQUIRED · 55 BLOCKED · 1.036 INFORMATIONAL**. Dört yeni blok, eski genel inceleme gerekçelerinin dependency çözümlemesiyle somutlaşmasıdır. Hedef INVALID durumu engel sayılmadı.

Bu tur yalnız mevcut yerel snapshot kullanıldı. Oracle/Jenkins bağlantısı ve SQL uygulaması yok. HTML/CSS/renderer ve JSON schema sözleşmeleri değiştirilmedi. Bu belge motor denetimidir, kullanıcı tarafından yürütülen HTML tasarımı ayrıdır.

Önce target, sonra source değeri gösterilir. Her satır numarası [tam denetim JSON kaydındaki](../output/backend-review130-v2/review130-audit.json) `number` ile aynıdır. Bu kayıtta eski/yeni operation ID, tüm farklar, before/after değerleri ve evidence ID listesi bulunur. PL/SQL gövdeleri bu belgeye kopyalanmaz, orijinal yerel snapshot ve denetim kanıtında korunur.

| # | Nesne / değişiklik | Son karar | Tekil değerlendirme |
|---:|---|---|---|
| 1 | INDEX INNOVA_ODI.PK_COMPARE_FIELDS | REVIEW_REQUIRED | Mevcut tablodaki yeni UNIQUE anahtar için veri tekilliği kanıtı yok, otomatik CREATE açılmadı. |
| 2 | INDEX INNOVA_ODI.PK_COMPARE_FIELDS_LOG | INFORMATIONAL | Hedef PK ID ve bağlı VALID/UNIQUE/NORMAL indeks dictionary ile doğrulandı. Aynı anahtar için ikinci indeks üretilmiyor, constraint ad farkı ayrı incelemede. |
| 3 | FUNCTION INNOVA_ODI.F_ODI_NIGHT_CHECK_AND_LOG | REVIEW_REQUIRED | Açık dependency envanteri yok. DUAL ve builtin çağrıların çözümü boş dependency varsayımıyla onaylanmıyor. |
| 4 | GRANT INNOVA_ODI.SKY_INTERFACE_NAME_ISLEM / INSERT / TTBP | REVIEW_REQUIRED | SKY_INTERFACE_NAME_ISLEM: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 5 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / INSERT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 6 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / REFERENCES / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: REFERENCES → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 7 | GRANT INNOVA_ODI.P_ET_EXCHANGE_PARTITION / DEBUG / TTBP | REVIEW_REQUIRED | P_ET_EXCHANGE_PARTITION: DEBUG → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 8 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / UPDATE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 9 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / ON COMMIT REFRESH / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: ON COMMIT REFRESH → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 10 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET23 / UPDATE / TTBP | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET23: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 11 | GRANT INNOVA_ODI.TARIFE_DAKIKA_TEMP / INSERT / TTBP | REVIEW_REQUIRED | TARIFE_DAKIKA_TEMP: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 12 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / DELETE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 13 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / QUERY REWRITE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: QUERY REWRITE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 14 | GRANT INNOVA_ODI.SKY_INTERFACE_NAME_ISLEM / UPDATE / TTBP | REVIEW_REQUIRED | SKY_INTERFACE_NAME_ISLEM: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 15 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / QUERY REWRITE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: QUERY REWRITE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 16 | GRANT INNOVA_ODI.F_BK_ASK_PR_TEK_HGO_MBL / SELECT / TTBP | REVIEW_REQUIRED | F_BK_ASK_PR_TEK_HGO_MBL: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 17 | GRANT INNOVA_ODI.SKY_INTERFACE_NAME_ISLEM / SELECT / TTBP | REVIEW_REQUIRED | SKY_INTERFACE_NAME_ISLEM: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 18 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / DEBUG / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: DEBUG → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 19 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_SEQ / SELECT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_SEQ: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 20 | GRANT INNOVA_ODI.SKY_MODEL_SISTEM / DELETE / TTBP | REVIEW_REQUIRED | SKY_MODEL_SISTEM: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 21 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_SEQ / ALTER / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_SEQ: ALTER → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 22 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / INDEX / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: INDEX → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 23 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / DELETE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 24 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TT2 / UPDATE / TTBP | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TT2: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 25 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / FLASHBACK / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: FLASHBACK → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 26 | GRANT INNOVA_ODI.SKY_MODEL_SISTEM / INSERT / TTBP | REVIEW_REQUIRED | SKY_MODEL_SISTEM: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 27 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / INDEX / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: INDEX → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 28 | GRANT INNOVA_ODI.TARIFE_DAKIKA_TEMP / SELECT / TTBP | REVIEW_REQUIRED | TARIFE_DAKIKA_TEMP: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 29 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / DEBUG / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: DEBUG → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 30 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / DELETE / EUS_OTHER | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET: DELETE → EUS_OTHER. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 31 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET23 / SELECT / TTBP | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET23: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 32 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / INSERT / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 33 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / FLASHBACK / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: FLASHBACK → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 34 | GRANT INNOVA_ODI.SKY_INTERFACE_NAME_ISLEM / DELETE / TTBP | REVIEW_REQUIRED | SKY_INTERFACE_NAME_ISLEM: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 35 | GRANT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI / SELECT / TTBP | REVIEW_REQUIRED | ET_CC_KULLANICI_ISLEMLERI: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 36 | GRANT INNOVA_ODI.SKY_MODEL_SISTEM / UPDATE / TTBP | REVIEW_REQUIRED | SKY_MODEL_SISTEM: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 37 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / READ / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: READ → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 38 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / INSERT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: INSERT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 39 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / DELETE / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 40 | GRANT INNOVA_ODI.SKY_MODEL_SISTEM / SELECT / TTBP | REVIEW_REQUIRED | SKY_MODEL_SISTEM: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 41 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / SELECT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 42 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / ON COMMIT REFRESH / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: ON COMMIT REFRESH → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 43 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / ALTER / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: ALTER → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 44 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / REFERENCES / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: REFERENCES → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 45 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / DEBUG / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: DEBUG → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 46 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / UPDATE / EUS_OTHER | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET: UPDATE → EUS_OTHER. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 47 | GRANT INNOVA_ODI.SKY_TABLO_ALAN_ODI / SELECT / TTBP | REVIEW_REQUIRED | SKY_TABLO_ALAN_ODI: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 48 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI_SEQ / SELECT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI_SEQ: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 49 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TT2 / SELECT / TTBP | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TT2: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 50 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / SELECT / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 51 | GRANT INNOVA_ODI.F_BK_ASK_PR_CHZ_RES_DTL / SELECT / TTBP | REVIEW_REQUIRED | F_BK_ASK_PR_CHZ_RES_DTL: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 52 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / FLASHBACK / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: FLASHBACK → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 53 | GRANT INNOVA_ODI.F_ODI_NIGHT_CHECK_AND_LOG / DEBUG / TTBP | REVIEW_REQUIRED | F_ODI_NIGHT_CHECK_AND_LOG: DEBUG → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 54 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / SELECT / EUS_OTHER | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET: SELECT → EUS_OTHER. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 55 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / UPDATE / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 56 | GRANT INNOVA_ODI.P_ET_EXCHANGE_PARTITION / EXECUTE / TTBP | REVIEW_REQUIRED | P_ET_EXCHANGE_PARTITION: EXECUTE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 57 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / ALTER / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: ALTER → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 58 | GRANT INNOVA_ODI.TARIFE_DAKIKA_TEMP / DELETE / TTBP | REVIEW_REQUIRED | TARIFE_DAKIKA_TEMP: DELETE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 59 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / ON COMMIT REFRESH / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: ON COMMIT REFRESH → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 60 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / ALTER / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: ALTER → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 61 | GRANT INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / INSERT / EUS_OTHER | REVIEW_REQUIRED | ET_PRIM_ISLEMLERI_TTNET: INSERT → EUS_OTHER. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 62 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI_SEQ / ALTER / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI_SEQ: ALTER → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 63 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / REFERENCES / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: REFERENCES → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 64 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC / SELECT / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC: SELECT → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 65 | GRANT INNOVA_ODI.TARIFE_DAKIKA_TEMP / UPDATE / TTBP | REVIEW_REQUIRED | TARIFE_DAKIKA_TEMP: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 66 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / INDEX / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: INDEX → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 67 | GRANT INNOVA_ODI.F_ODI_NIGHT_CHECK_AND_LOG / EXECUTE / TTBP | REVIEW_REQUIRED | F_ODI_NIGHT_CHECK_AND_LOG: EXECUTE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 68 | GRANT INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI / UPDATE / TTBP | REVIEW_REQUIRED | ET_CC_EF_BELIRTEC_ILISKI: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 69 | GRANT INNOVA_ODI.MUSTERI_SEGMENT_UPDATE_LOG / QUERY REWRITE / TTBP | REVIEW_REQUIRED | MUSTERI_SEGMENT_UPDATE_LOG: QUERY REWRITE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Ayrıca bu ayrıcalık için üretim kuralı kapalı. |
| 70 | GRANT INNOVA_ODI.ET_CC_KULLANICI_ISLEMLERI / UPDATE / TTBP | REVIEW_REQUIRED | ET_CC_KULLANICI_ISLEMLERI: UPDATE → TTBP. Alıcı metadata ile mevcut, grant allowlist boş. Standart desteklenen ayrıcalık. |
| 71 | INDEX INNOVA_ODI.IX_PUSULA_01 | REVIEW_REQUIRED | Kaynak indeks açıkça UNUSABLE istiyor, kullanılabilir indeks üretmek kaynak niyetini değiştirir. İşletim kararı gerekli. |
| 72 | INDEX INNOVA_ODI.IX_PUSULA_02 | REVIEW_REQUIRED | Kaynak indeks açıkça UNUSABLE istiyor, kullanılabilir indeks üretmek kaynak niyetini değiştirir. İşletim kararı gerekli. |
| 73 | PACKAGE_BODY INNOVA_ODI.PCK_CALL_CENTER | BLOCKED | ET_CC_KULLANICI_ISLEMLERI oluşturma işlemi partition desteği nedeniyle bloke, ayrıca DUAL çözümü kanıt gerektiriyor. |
| 74 | PACKAGE_BODY INNOVA_ODI.PCK_COMPARE_FIELDS | BLOCKED | Değişen package spec incelemede, ALL_CONSTRAINTS/ALL_CONS_COLUMNS/ALL_TABLES/ALL_TAB_COLS çözümü mevcut envanterde doğrulanmıyor. |
| 75 | PACKAGE_BODY INNOVA_ODI.PCK_HYPERION | READY | Exporter PACKAGE+BODY birleşik sidecar gövdeye de bağlandı, gerekli spec/dış nesneler mevcut kanıtla doğrulandı. Ham gövde korunarak REPLACE SQL üretildi. |
| 76 | PACKAGE_BODY INNOVA_ODI.PCK_ISLEM_TIPI_AKTAR2 | BLOCKED | INNOVA_ODI.ISLEM_HESAP_DENEME3 ve TTBP.SEQ_ISLEM_HESAP_ID source/target/dış nesne kanıtında yok. |
| 77 | PACKAGE_BODY INNOVA_ODI.PCK_LOG_UTIL | BLOCKED | Birleşik dependency sidecar içindeki BIN$ recyclebin tablo referansı source/target kanıtında yok, düşürülmedi. |
| 78 | PACKAGE_BODY INNOVA_ODI.PCK_VA_KUTUPHANE | REVIEW_REQUIRED | Dinamik SQL var, dictionary listesi çalışma anında oluşan hedefleri kanıtlamaz. SQL üretimi incelemede. |
| 79 | PACKAGE_SPEC INNOVA_ODI.PCK_COMPARE_FIELDS | REVIEW_REQUIRED | Dışa açık package spec değişiyor, çağıranların sözleşme uyumu otomatik kanıtlanmıyor. Gövde kararı ayrı tutuldu. |
| 80 | PACKAGE_SPEC INNOVA_ODI.PCK_ISLEM_DAGITIM | REVIEW_REQUIRED | Dışa açık package spec değişiyor, çağıranların sözleşme uyumu otomatik kanıtlanmıyor. Gövde kararı ayrı tutuldu. |
| 81 | PROCEDURE INNOVA_ODI.FILLDML | REVIEW_REQUIRED | Açık dependency envanteri eksik, INNOVA_ODI.tableName ifadesi parametreyle tablo seçildiği varsayımıyla çözülemez. |
| 82 | PROCEDURE INNOVA_ODI.P_ET_EXCHANGE_PARTITION | REVIEW_REQUIRED | Dinamik SQL var, dictionary listesi çalışma anında oluşan hedefleri kanıtlamaz. SQL üretimi incelemede. |
| 83 | PROCEDURE INNOVA_ODI.P_REV_CREATE_PARTITION | REVIEW_REQUIRED | Dinamik SQL var, dictionary listesi çalışma anında oluşan hedefleri kanıtlamaz. SQL üretimi incelemede. |
| 84 | SEQUENCE INNOVA_ODI.AKTARIMLOG_SEQ | REVIEW_REQUIRED | Canlı sayaç korunur, START WITH yeniden uygulanmaz. Ayar farkı ayrı inceleme: max_value: 99999999 → 9999999999999999999999999999. |
| 85 | SEQUENCE INNOVA_ODI.SEQ_COMPARE_FIELDS_LOG_ID | REVIEW_REQUIRED | Canlı sayaç korunur, START WITH yeniden uygulanmaz. Ayar farkı ayrı inceleme: cache: 20 → 0. |
| 86 | SEQUENCE INNOVA_ODI.SEQ_ET_EXTRACTION_ID | REVIEW_REQUIRED | Canlı sayaç korunur, START WITH yeniden uygulanmaz. Ayar farkı ayrı inceleme: cache: 0 → 20, min_value: 0 → 1. |
| 87 | SEQUENCE INNOVA_ODI.SEQ_ET_PRIM_ISLEMLERI_ID | REVIEW_REQUIRED | Canlı sayaç korunur, START WITH yeniden uygulanmaz. Ayar farkı ayrı inceleme: cache: 1000 → 20, max_value: 999999999999999999999999999 → 9999999999999999999999999999. |
| 88 | TABLE INNOVA_ODI.COMPARE_FIELDS / TABLE_NAME/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 89 | TABLE INNOVA_ODI.COMPARE_FIELDS / OWNER/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 90 | TABLE INNOVA_ODI.COMPARE_FIELDS / COLUMN_NAME/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 91 | TABLE INNOVA_ODI.COMPARE_FIELDS | REVIEW_REQUIRED | Yeni birleşik PK için NULL/tekillik ve constraint etkisi bilinmiyor. |
| 92 | TABLE INNOVA_ODI.COMPARE_FIELDS_LOG | REVIEW_REQUIRED | Mevcut anonymous PK ile source named PK ad/yapı farkı var. Mevcut key/index korunuyor, DROP/yeniden oluşturma üretilmiyor. |
| 93 | TABLE INNOVA_ODI.COMPARE_FIELDS_LOG | REVIEW_REQUIRED | ISLEM_TARIHI DATE nullable, DEFAULT SYSDATE ile yeni kolon. Mevcut satır/default etkisi için sabit politika inceleme gerektiriyor. |
| 94 | TABLE INNOVA_ODI.ET202204 / HEDEF_AKTARIM_DURUM/precision: 5 → NULL/tanımsız, HEDEF_AKTARIM_DURUM/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 95 | TABLE INNOVA_ODI.ET202204 / KULLANICI_ID/precision: 11 → NULL/tanımsız, KULLANICI_ID/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 96 | TABLE INNOVA_ODI.ET202204 / SIEBEL_MUSTERI_ID/precision: 19 → NULL/tanımsız, SIEBEL_MUSTERI_ID/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 97 | TABLE INNOVA_ODI.ET202204 / ABONELIK_TIPI/precision: 4 → NULL/tanımsız, ABONELIK_TIPI/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 98 | TABLE INNOVA_ODI.ET202204 / ACIKLAMA/length: 255 → 500, ACIKLAMA/length_semantics: CHAR → BYTE | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 99 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT / KULLANICI_ID/precision: 11 → NULL/tanımsız, KULLANICI_ID/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 100 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT / ACIKLAMA/length: 255 → 500, ACIKLAMA/length_semantics: CHAR → BYTE | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 101 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT / ABONELIK_TIPI/precision: 4 → NULL/tanımsız, ABONELIK_TIPI/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 102 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT / HEDEF_AKTARIM_DURUM/precision: 5 → NULL/tanımsız, HEDEF_AKTARIM_DURUM/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 103 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TT / SIEBEL_MUSTERI_ID/precision: 19 → NULL/tanımsız, SIEBEL_MUSTERI_ID/scale: 0 → NULL/tanımsız | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 104 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / EXTRA_FIELD8/length: 500 → 255 | REVIEW_REQUIRED | Kolon uzunluğu daralıyor, mevcut veri uzunluğu kanıtı yok. |
| 105 | TABLE INNOVA_ODI.ET_PRIM_ISLEMLERI_TTNET / HIZMET_NO/length: 150 → 20 | REVIEW_REQUIRED | Kolon uzunluğu daralıyor, mevcut veri uzunluğu kanıtı yok. |
| 106 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / DURUM/precision: NULL/tanımsız → 10, DURUM/scale: NULL/tanımsız → 0 | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 107 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / SATIS_KANALI_ID/precision: NULL/tanımsız → 19, SATIS_KANALI_ID/scale: NULL/tanımsız → 0 | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 108 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / ACIKLAMA/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 109 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / YETKILI_E_MAIL/length: 500 → 255, YETKILI_E_MAIL/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 110 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / ID/precision: NULL/tanımsız → 19, ID/scale: NULL/tanımsız → 0 | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 111 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / ACIKLAMA/nullable: hayır → evet | REVIEW_REQUIRED | NOT NULL gevşiyor, şema sözleşmesi değişimi mevcut politika gereği incelemede. |
| 112 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / DURUM/nullable: hayır → evet | REVIEW_REQUIRED | NOT NULL gevşiyor, şema sözleşmesi değişimi mevcut politika gereği incelemede. |
| 113 | TABLE INNOVA_ODI.HAKEDIS_TIPI_O / GECMIS_KAYITLAR_HAKEDISE_DAHIL/nullable: hayır → evet | REVIEW_REQUIRED | NOT NULL gevşiyor, şema sözleşmesi değişimi mevcut politika gereği incelemede. |
| 114 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / DURUM/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 115 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / ACIKLAMA/length: 250 → 255, ACIKLAMA/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 116 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / BELIRTEC/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 117 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / ETKILESIM_KODU/length: 50 → 255, ETKILESIM_KODU/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 118 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / ID/nullable: evet → hayır | REVIEW_REQUIRED | NOT NULL sıkılaşıyor, mevcut NULL bulunmadığı kanıtlanmadı. |
| 119 | TABLE INNOVA_ODI.ISLEM_ONCESI_TIPI_O / BELIRTEC/length: 100 → 255, BELIRTEC/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 120 | TABLE INNOVA_ODI.SATIS_KANALI_O / FLOW/length: 50 → 255, FLOW/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 121 | TABLE INNOVA_ODI.SATIS_KANALI_O / ID/precision: NULL/tanımsız → 19, ID/scale: NULL/tanımsız → 0 | REVIEW_REQUIRED | NUMBER hassasiyet/scale kapsamı değişiyor, mevcut sabit dönüşüm matrisi otomatik SQL açmıyor. |
| 122 | TABLE INNOVA_ODI.SATIS_KANALI_O / ACIKLAMA/length: 64 → 255, ACIKLAMA/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 123 | TABLE INNOVA_ODI.SATIS_KANALI_O / IMAGE_NAME/length: 50 → 255, IMAGE_NAME/length_semantics: BYTE → CHAR | REVIEW_REQUIRED | BYTE/CHAR semantiği değişiyor, sayı büyümesi tek başına güvenli kapasite artışı kanıtı değil. |
| 124 | TABLE INNOVA_ODI.SATIS_KANALI_O / ACIKLAMA/nullable: hayır → evet | REVIEW_REQUIRED | NOT NULL gevşiyor, şema sözleşmesi değişimi mevcut politika gereği incelemede. |
| 125 | TABLE INNOVA_ODI.VA_DIAMOND_EXTRACTION_DWH / SURE/data_type: VARCHAR2 → NUMBER, SURE/length: 10 → NULL/tanımsız, SURE/length_semantics: BYTE → NULL/tanımsız | REVIEW_REQUIRED | VARCHAR2 → NUMBER dönüşümü, mevcut değerlerin çevrilebilirliği bilinmiyor. |
| 126 | TABLE INNOVA_ODI.VA_DIAMOND_EXTRACTION_DWH / SURE/collation: USING_NLS_COMP → NULL/tanımsız | REVIEW_REQUIRED | SURE kolonunun VARCHAR2 → NUMBER dönüşümündeki collation farkı, tip dönüşümünden bağımsız uygulanmıyor. |
| 127 | TABLE INNOVA_ODI.VA_DIAMOND_EXTRACTION_DWH / DURUM/length: 100 → 50 | REVIEW_REQUIRED | Kolon uzunluğu daralıyor, mevcut veri uzunluğu kanıtı yok. |
| 128 | TABLE INNOVA_ODI.VW_DT_HAK_COMMON_APPROVE / PRM_TYPE/length: 50 → 5 | REVIEW_REQUIRED | Kolon uzunluğu daralıyor, mevcut veri uzunluğu kanıtı yok. |
| 129 | TRIGGER INNOVA_ODI.ET_CC_EF_BELIRTEC_ILISKI_TRG | READY | Yeni boş tablo + mevcut/READY sequence + NUMBER kolon + yalnız :NEW kolonuna NEXTVAL ataması kanıtlandı. Ek DML/çağrı veya sıralama clause kabul edilmez. |
| 130 | TRIGGER INNOVA_ODI.ET_CC_EF_BELIRTEC_TRG | READY | Yeni boş tablo + mevcut/READY sequence + NUMBER kolon + yalnız :NEW kolonuna NEXTVAL ataması kanıtlandı. Ek DML/çağrı veya sıralama clause kabul edilmez. |

## Kod ve doğrulama

- PACKAGE/TYPE union sidecar spec ve body kimliklerine bağlanır, owner/conflict kontrolleri ve DDL span sırası korunur.
- Dinamik SQL kapısı quoted DBMS_SQL ve dynamic ref cursor açılışını da kapsar.
- Mevcut PK/UK backing index yalnız tam dictionary + AST kanıtı ve implicit source association ile tekilleştirilir.
- Yeni boş tablo için tek sequence atamalı trigger dar kuralı eklendi, FOLLOWS/PRECEDES kapalıdır.
- 233 test geçti (31,59 sn), skip yok. 6 JSON schema ve 7 örnek doğrulandı.
- 502 SQL için mevcut grammar/nesne kimliği, fark kapsama, bağımlılık sırası ve SHA-256 denetimi yapıldı. Oracle syntax/compile kabulü NOT_RUN.

[Motor paketi](../output/backend-review130-v2/README.md) · [Plan](../output/backend-review130-v2/plan.json) · [51 teknik iş](TEKNIK_EKSIKLER_51.md) · [Test kanıtı](../output/pytest-review130-final.xml)
