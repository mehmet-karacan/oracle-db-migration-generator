# Yerel başlangıç — 19 Ekim 2026

Kullanıcının son talimatı uygulama sırasını belirler: önce yerel INNOVA_ODI →
INNOVA_ODI, başarıdan sonra TTBP, ardından Jenkins. Source Git ve target Oracle
her zaman salt okunur. Eski projelerde değişiklik, otomatik commit/push yok.

Yerel akış: sabit Git SHA → izole ANTLR parse ve sidecar → salt okunur target
metadata → semantic compare → kural/bağımlılık → SQL/JSON/HTML paketi.
Eksik metadata başarısızlığı boş şema veya başarılı migration sayılmaz.

## Çalışan yerel komutlar

```powershell
.\.venv\Scripts\python.exe -m oracle_db_migration_generator prepare-source --repo .local/source.git --ref <sabit-SHA> --source-profile .local/source-profile.sky.json --output output/prepared-source
.\.venv\Scripts\python.exe -m oracle_db_migration_generator plan-target --source-snapshot output/prepared-source/source-snapshot.json --targets .local/targets.json --target-id <yerel-hedef-id> --credentials-file .local/credentials.env --output output/local-run
.\.venv\Scripts\python.exe -m oracle_db_migration_generator plan-offline --source-snapshot output/prepared-source/source-snapshot.json --target-snapshot output/local-run/observations/<yerel-hedef-id>/target-snapshot.json --source-profile .local/source-profile.sky.json --output output/offline-plan
.\.venv\Scripts\python.exe -m oracle_db_migration_generator verify-bundle --bundle output/offline-plan
.\.venv\Scripts\python.exe -m oracle_db_migration_generator aggregate --run-root output/local-run
```

`prepare-source` yeni dizin ister, var olan bundle'ın üzerine yazmaz. Hedef
kimliği `.local/targets.json` içinden seçilir. Parolalar argv'ye girmez.
`plan-target` yalnız metadata okur; her schema credential'ı ayrı bağlantıdadır.
Başlangıç/bitiş envanteri değişirse bir kez yeniden okur; hâlâ değişiyorsa
`INCONSISTENT`, fark sayısı null ve `target-error.json` üretir.

Target paketi `targets/<id>/`, ham metadata yerel `observations/<id>/` altında;
`index.html` koşu girişidir. Ham metadata da Git dışında tutulmalıdır.
Plan tamamı READY ise `migration.sql`; aksi halde yalnız hazır işlemler varsa
`partial-ready.sql` çıkar. Sıfır hazır işlemde boş deployment dosyası üretilmez.
Review/blocked kararları SQL aggregate'e alınmaz. `OFFLINE_VALIDATED` gerçek
Oracle syntax/compile veya veri doğrulaması anlamına gelmez.

Exit kodları: 0 hazır/no-change/no-action veya doğrulandı; 10 kısmi/inceleme/blok;
20 hedef erişim/tutarlılık hatası; 30 geçersiz girdi/paket. Ürün son sürüm
kabulü, Jenkins ve yayın kapıları aşağıdaki sırada ertelidir.

## Uygulama sırası

1. A00: paketi manifest ile doğrula, mevcut dosyaları koru; referansların
   hash ve Git durumunu okumayla kaydet. Farklı sürümü eşleşmiş gibi gösterme.
2. A01: `load_source_profile(Path)` ve `load_targets(Path, selected)`;
   JSON Schema + semantik doğrulama, immutable modeller, sır içermeyen hatalar.
   `validate-config` bağlantı açmadan çalışır; geçersiz girdide exit 30.
3. Yerel ön kontrol: `preflight --settings .local/session-context.json`;
   source için yalnız SSH veya HTTPS askpass ile `ls-remote`, target için salt okunur transaction içinde
   sabit kimlik/envanter/dictionary sorguları ve örnek GET_DDL. Source SQL
   çalıştırılmaz. Hata halinde fark sayısı null, comparison_status NOT_RUN.
4. Kısa testler: root/referans koruma, registry sınırları, secret gizleme,
   UNKNOWN ayrımı ve Oracle sorgu sınırı. Önce kırmızı, sonra yeşil kanıt.
5. CLI kurulumunu ve canlı ön kontrolü doğrula; durum/devir dosyalarını güncelle.

## Sona taşınan işler

- A11: Jenkins job/pipeline entegrasyonu; yerel karşılaştırma doğrulanınca.
- A12: artifact Git yayını; varsayılan kapalı ve ayrıca yetkilendirilir.
- A13: üç hedefli geniş kabul, wheelhouse/offline kurulum matrisi ve uzun
  senaryolar; desteklenen karşılaştırma/SQL akışı tamamlanınca.
- Oracle'a fixture kuran veya üretilen SQL'i uygulayan testler bu hedefte
  çalıştırılmayacak. Source/target salt okunurluk kuralı süreklidir.

Güvenlik/yön/metadata doğruluğu testleri kaldırılmaz. Başlangıçta var olmayan
uzun testler oluşturulmaz; geçilmemiş aşamalar tamamlandı sayılmaz.
