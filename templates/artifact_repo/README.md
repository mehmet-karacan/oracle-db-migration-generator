# Oracle DB Migration Artifacts

Bu depo, Oracle DB Migration Generator tarafından otomatik üretilen hedef bazlı migration planı ve SQL dosyalarını saklar. Çalıştırılabilir ürün kodu deposu değildir. Dosyalar elle düzenlenmez.

## Okuma Sırası

AGENTS.md → catalog.json → plans/<source-profile-id>/<target-id>/<plan-id>/plan.json → seçilen operation'ın SQL ve evidence dosyası. Her planın README ve HTML raporu vardır. latest/ işaretçisi kolaylık içindir, denetim için değiştirilemez plan ID kullanılır.

SQL dosyaları **üretilmiştir, uygulanmamıştır**. READY, bir kuralın üretime izin verdiğini belirtir, deployment/DBA onayı değildir. REVIEW/BLOCKED işlemler otomatik çalıştırılabilir paket dışında tutulur.

Source Git durumunun bütün hedeflere aynı SQL olarak gönderilmesi yoktur. Her hedefin actual durumu ayrı değerlendirilir. before=target, after=source.

## Gizlilik

Bu depo kurumsal DDL/metadata içerebilir. Yalnız onaylı private alanda tutulur. Bağlantı sırları bu depoda yer almaz. Dış model/servise veri aktarımı için ayrıca kurum izinleri gerekir.
