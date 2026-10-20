# Teknik Mimari

## 1. Amaç Ve Sınır

Geliştirici mevcut Oracle çalışma biçimini korur. Sync DDL'yi Git'e gönderir. Generator seçilmiş kaynak revision'ını N ayrı hedefin mevcut durumuyla karşılaştırır. Manuel changeset/changelog veya SQL hazırlama yoktur. Üretilen SQL'i uygulama işi bu ürünün ilk kapsamı dışındadır.

Kaynak repository bir Oracle bağlantısı değildir. Kaynak SQL hiçbir ara veritabanında çalıştırılmadan analiz edilir. Boş hedef, erişilebilir fakat uygulama nesnesi olmayan **şema** demektir; instance/PDB/user/tablespace oluşturulmaz. Tablo verisi veya referans veri aktarılmaz.

## 2. Kesin Teknoloji Kararı

Python CLI + kütüphane. Geliştirme/varsayılan runtime Python 3.12; destek hedefi 3.11–3.13. `python-oracledb`, mevcut ANTLR PL/SQL parser'ı, Jinja2 ve jsonschema kullanılır. İlk üretim lock adayı: ANTLR runtime 4.13.2, oracledb 26.0.1, Jinja2 3.1.6, jsonschema 4.26.0; bunlar referans paketlerde görülmüştür. Transitif paketler kontrollü çözülüp hash'li lock'a alınır; sistemdeki sürümün rastgele kullanılması yoktur. Yüklenen 26.0.1 wheel'i cp310/Linux içindir; Python 3.12/Windows için aynısını kullanma. Uygun platform wheel'lerini ayrı üret/doğrula.

Spring Boot, Maven, Next.js, PostgreSQL veya Liquibase runtime'ı eklenmez. Schema Compare Platform'un Java kodları karşılaştırma kapsamı/kuralları için referanstır; web uygulaması yeni CLI'ye taşınmaz. `DBMS_METADATA_DIFF` varsayılan motor değildir: girdi Git SQL'idir ve Oracle nesnesine/SXML'e dönüştürmek için ek çalışma alanı/lisans varsayımı kurulmaz. LLM, embedding veya AI servis çağrısı yoktur.

## 3. Veri Akışı

1. Jenkins kaynak ref'i **bir kez SHA'ya** çözer ve içerik listesini sabitler.
2. Git kaynak okuyucusu, `by_object` veya eski `flat` yerleşiminden ham SQL + sidecar'ları okur.
3. Kaynak parser/adaptörü ortak `SchemaSnapshot` üretir; her alanın biliniyor/bilinmiyor/uygulanamaz durumu korunur.
4. Her hedef için ayrı worker, yetkili salt-okuma bağlantısıyla envanter, DDL ve gerekli dictionary alanlarını çıkarır.
5. Target DDL aynı parser'dan geçer; dictionary bilgisi eksik semantiği tamamlar, çelişki varsa gizlenmez.
6. `compare_snapshots(desired=source, actual=target)` hedef bazlı fark üretir.
7. Kural motoru farkları `READY`, `REVIEW_REQUIRED`, `BLOCKED` veya `INFORMATIONAL` işlemlere dönüştürür.
8. Bağımlılık grafı gerekli işlemleri sıralar; engellenmiş önkoşula bağlı işlemleri de engeller.
9. Aynı kanonik plandan SQL, JSON, HTML, nesne açıklaması ve manifest üretilir.
10. Jenkins çıktı arşivler; yetkilendirilmişse ayrı artifact Git deposuna içerik bazlı yayımlar.

Analyzer raporu isteğe bağlı ilişki/link bilgisi olabilir; doğruluk kaynağı veya çalıştırma tetikleyicisi şartı değildir. Kaynak/hedef bağımsız sürüm farkları her zaman tam durumdan hesaplanır; son Git commit diff'i migration planı değildir.

## 4. Modül Sınırları

| Paket | Sorumluluk |
|---|---|
| `config` | Kaynak profili, hedef kayıtları, politika doğrulaması; sır taşımaz. |
| `source` | Güvenli Git okuma, yerleşim, sidecar birleştirme, SHA/kanıt. |
| `oracle` | Sabit sorgular, metadata çıkarımı, sürüm/yetenek/eksiklik tespiti. |
| `model` | Snapshot, identity, completeness, evidence, difference, operation, plan. |
| `parsing` | Mevcut lexer/parser adaptörleri ve ek statement sınıflandırması. |
| `compare` | Semantik durum farkı; eski=hedef, yeni=kaynak yönü. |
| `planning` | Güvenlik politikası, işlem kuralları, graf ve bağımlılık kapanışı. |
| `sql` | DDL emission, SQLPlus giriş dosyası, offline doğrulama. |
| `reporting` | Aynı HTML ailesinden web raporu ve sınırlı önizleme. |
| `artifacts` | Atomik bundle, dosya hash'leri, katalog, Git publisher. |
| `runtime` | Target izolasyonu, timeout, tekrar başlatma, aggregate durum. |
| `_vendor` | İzlenebilir ve daraltılmış mevcut Python kaynak adaptasyonları. |

Dosya ve fonksiyon sözleşmeleri `CODEX_ARAYUZLERI.md` içindedir. Genel provider SPI geliştirip başka veritabanı ürünü ekleme; Oracle kapsamına odaklan.

## 5. Hedef Ve Şema Ayrımı

Bir target, kullanıcının verdiği ID/ad ile bir Oracle servisinin mantıksal ortamıdır. İçinde birden fazla schema mapping olabilir. Örneğin aynı target'ta `TTBP→TTBP`, `INNOVA_ODI→INNOVA_ODI` eşleşmeleri ayrı credential ID kullanabilir. Target sayısı bağlantı tanımlarından gelir; yeni target için kod değişmez.

İlk sürümde owner adı aynı olan eşleşme desteklenir. Farklı owner eşleşmesi yapılandırmada görülebilir fakat `SCHEMA_REMAP_NOT_SUPPORTED` ile engellenir. SQL gövdesinde `replace('DEV','PROD')` gibi global dönüşüm kesinlikle yoktur. Böylece cross-schema PL/SQL/dynamic SQL metinlerine yanlış müdahale edilmez. Farklı schema adlarına taşıma ayrı açık kapsam değişikliğidir.

## 6. Doğruluk Modeli

Her target ve nesne için üç ayrı kavram tutulur: **gözlenen fark**, **SQL üretilebilirliği**, **doğrulama düzeyi**. İzin eksikliği 'hedef boş'; parse hatası 'aynı'; SQL dosyası oluşturulması 'deploy edildi' demek değildir.

Source Git içeriğinin tam taranması yalnız seçili repo kapsamının tamlığını kanıtlar. Kaynak canlı Oracle'ın eksiksiz/fresh export edildiğini kendiliğinden kanıtlamaz. `_manifest.json` sayıları yardımcı kontroldür; Oracle snapshot veya SCN garantisi değildir.

Hedef envanteri çıkarım öncesi/sonrası kontrol edilir. Farklılık varsa en çok bir yeniden deneme; kararsızsa hedef `INCONSISTENT` olur. Bu kontrol SCN tabanlı atomik snapshot iddiası değildir. Karşılaştırma sonrası hedef değişebilir; deployment öncesi yeniden doğrulama gereği raporda belirtilir.

## 7. Kaynakları Koruyan Yeniden Kullanım

Mevcut Python kaynakları yalnız gereken import kapanışıyla yeni projenin `_vendor` alanına kontrollü uyarlanır; kopya kaynağı/hash/lisans kaydı tutulur. Jenkins runtime, kullanıcının `C:\` klasörlerinden import etmez; iki eski ürünü pip ile bütünüyle kurup AI servislerini de taşımaz.

Ortak beşinci repo/servis yaratılmaz. Sonraki sürümde ortak kütüphane çıkarma kararı ayrı alınabilir. Burada yeniden kullanılabilir parser/diff birimleri korunur; farklı amaçtaki analiz sonuç modeli migration yetkilendirmesi gibi kullanılmaz.

## 8. Çalıştırma Ve Kapasite

Jenkins worker başına bir target, schema'lar sırayla. Varsayılan en çok 2 target eşzamanlı; parametreyle 1–8. Her target worker bağımsız süreç olduğundan oracledb Thin/Thick modu izolasyonu mümkündür. Bir worker içinde mod değiştirilemez. Nested Oracle extraction parallelism ilk sürümde 1; 2×4×N oturum patlaması yoktur.

Tek hedef bağlantı hatası diğerlerini iptal etmez. Kaynak snapshot bir kez hazırlanır; target işleri salt-okunur kaynağı paylaşır. Target geçici dosyaları ayrı dizindedir. Runtime checkpoint'leri `output/.work/` altında; bunlar Git artifact bundle'ına girmez.
