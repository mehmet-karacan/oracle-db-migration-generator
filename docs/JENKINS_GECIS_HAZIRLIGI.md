# Jenkins'e geçiş - yerel hazırlık

ODMG-RPT-UPDATE-001 yerel rapor/arşiv katmanı tamamlanınca Jenkins bağlantısı ayrı aşamadır.
Source ve target daima salt okunur. SQL üretimi uygulama yetkisi vermez.

Mevcut komutlar:

```powershell
oracle-db-migration-generator aggregate --run-root <run>
oracle-db-migration-generator verify-bundle --bundle <run>/targets/<target>
oracle-db-migration-generator archive-run --run-root <run> --store <artifact-checkout> --build-number <N>
```

Jenkins metadata'sı Python `aggregate_run(..., build_number=N)` arayüzüne geçirilebilir.
Koşu çıktısı index.html, report-email.html (CID), report-email.preview.html (gömülü logo),
run.json, README ve target paketlerini içerir. Mail yalnız dosyadır, SMTP gönderimi yoktur.
Her run Jenkins'te bütün dosya bağımlılıklarıyla arşivlenmeli, HTML tek başına taşınmamalı.

Artifact Git yayını CLI'nin varsayılan adımı değildir. `artifacts.publisher.publish_run`
opt-in API'si ayrı checkout + exact SSH remote/web_base + branch + host allowlist +
kurumsal storage onayı + açık push yetkisi ister. `ProviderHTTP` token'ı Jenkins Credentials'dan
bellekte alır, `private_check=http.private`, `url_check=http.reachable` enjekte edilir.
SQL içindeki sırlar dahil `secret_values` yayın öncesi tekrar taranır. Token argv/JSON'a yazılmaz.
Private kanıtı olmadan veya push/remote SHA/README erişimi doğrulanmadan başarılı URL verilmez.

Mail linki için `build_run_view(..., publication=receipt, url_check=http.reachable,
allowed_link_hosts=(...))` kullanılır. Allowlist varsayılanı boştur. Jenkins arşivi fallback'i
yalnız mevcut run.build_url altında sayısal build'e sabit ve erişilebilir dosya için kabul edilir.
Gözlem run.json publication alanı worker'ın ilk durumudur, gerçek yayın sonucu ayrı receipt'tir.

Jenkins aşamasında somut kalanlar:

1. Güvenilir Generator checkout/wheel ve Python bağımlılıklarını job/agent'a bağlamak.
2. Source sabit SHA, hedef registry ve read-only Credentials ID'lerini yapılandırmak.
3. Worker hedeflerini bağımsız koşturmak, ERROR/INCONSISTENT sonucunu UNKNOWN olarak korumak.
4. Aggregate, hash doğrulama ve run arşivini her hedef sonucu için tamamlamak.
5. Özel kurum artifact deposunu ve izinli hostları doğrulayıp ayrı yetkiyle opt-in yayını bağlamak.
6. Sabit son Git SHA receipt'iyle mail dosyası üretmek, gönderim kanalı/yetkisini ayrıca kurmak.
7. Jenkins HTML/CID/retention erişimini gerçek ortamda doğrulamak, CSP'yi gevşetmemek.

Beş kaynak/sözleşme koşulu yz/MOTOR_TAMAMLAMA.md içindedir. Bunlar karşılaştırmayı veya
rapor üretimini durdurmaz, yalnız ilgili işlemlerde BLOCKED kalır. Bağımsız hazır 559 SQL
partial-ready.sql içindedir. Bu aşamada gerçek Jenkins ayarı/push/SMTP/Oracle DDL kabulü NOT_RUN.
