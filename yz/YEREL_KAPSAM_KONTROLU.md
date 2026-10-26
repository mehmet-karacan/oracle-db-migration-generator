# Yerel kapsam kontrolü - 19 Ekim 2026

Güncel kullanıcı kuralı: hedef INVALID yalnız rapor uyarısıdır, onarım veya VALID
hale getirme ilk kabul koşulu değildir. Korunacak beş target-only INVALID parse
sorunu karşılaştırmayı bloklamaz. Ham target snapshot DDL PARTIAL korunurken
karşılaştırma kapsamı COMPLETE ve difference_count=2353'tür. Kalan 69 blok gerçek
bağımlılık/yapısal veya destek koşullarındandır. Ayrıntı INVALID_HEDEF_UYGULAMA.md.
Bu değişiklikte yeni Oracle/Jenkins bağlantısı açılmadı.

Aktif kapsam AKTIF_GOREV.md. INNOVA_ODI → INNOVA_ODI yerel başlangıcı, TTBP,
Jenkins kurulumu, yayın ve uzun kabul matrisi sonrada. Kaynak metadata için
Jenkins'in yalnız okunmasına ayrıca izin verildi, Generator Jenkins'e kurulmadı.

| Gereklilik | Güncel kanıt | Sonuç |
|---|---|---|
| Source/target salt okuma | READ ONLY + fixed metadata sorguları, execution CLI yok | Korundu, DDL/DML yok |
| Sırlar yerel/Git dışında | .local/output ignored, 184 aday/483 run dosyası tarandı | 0 gerçek endpoint/parola eşleşmesi |
| A00 referans koruma | Önceki 36 match/7 drift/0 missing, vendor 24 | Eski projelere yazılmadı |
| A01 config/kimlik | Kısa testler, 6 schema/7 örnek | Offline doğrulandı |
| A02–A03 kaynak/parse | source-v8: 917 kayıt, sabit Git DDL/hash korundu | Inventory/DDL COMPLETE |
| Kaynak örtük semantik | 405 tablo/16560 kolonun bilinen alanları canlı kaynakla eşleşti | 10088 BYTE, 10379 collation tamamlandı |
| A04 target metadata | target-reparsed-v7: eski DDL capture + yeni capability | Inventory/dictionary COMPLETE, 5 INVALID tanım PARTIAL |
| A05 compare | before=target/after=source, 2353 olgu | 0 UNKNOWN, tam sayı 2353 |
| A06–A08 SQL/sıra | 447 READY, BYTE/collation korunumu, graph/grammar | İnceleme ve bloklar korunur |
| A09 paket | local-report-v8, plan/evidence/hash | 472 bundle dosyası VERIFIED |
| A10 rapor | 19 HTML, max 93396 byte, 0 kırık link | Tarayıcıda güncel sayılar doğrulandı |
| Kısa kapı | 187 passed / 26.73s, bağımsız collation teyidi | Skip/failure yok |
| Wheel | dist-v8 ve wheel-smoke-v8 | Kod hash'i planla aynı |
| İlk tam INNOVA_ODI kabulü | 69 yapısal/destek bloğu, 119 inceleme | Henüz tam kabul değil, SQL uygulanmadı |
| TTBP/Jenkins/yayın/A13 | Kullanıcı sırası ve salt okuma sınırı | DEFERRED / NOT_RUN |

Kaynak erişim/semantik engeli kapandı, kullanıcıdan tekrar bağlantı bilgisi
istenmez. Kalan bloklar bağımlılık kanıtı, kapsanmayan fiziksel özellikler,
Oracle iç nesneleri ve index tanımlarıdır. INVALID target tanımları burada
onarılmaz. partial-ready.sql tam migration veya çalıştırma onayı değildir.

Güncel uygulama/kanıt COLLATION_UYGULAMA.md, tarihsel kayıtlar DOGRULAMA_KAYDI.md.
