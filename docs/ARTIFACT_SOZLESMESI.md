# Artifact Ve Makine Okunabilirlik Sözleşmesi

## Tek Doğruluk Kaynağı

Target başına `plan.json` kanonik işlem planıdır. HTML kendi fark hesabını yapmaz, SQL renderer doğrudan diff metninden bağımsız işlem uydurmaz. Planın operation set'i ve dependency sırası SQL/HTML/özetlerde aynı olmalıdır. `schema_version` her belgede açık, uyumsuz major version reddedilir.

`source=desired`, `target=actual`, farkın `before=target`, `after=source` olduğu bütün sözleşmelerde aynıdır. Human-readable Türkçe alanlar kanıt kimlikleri ve reason code'larla ilişkilidir. Başka bir model SQL'i tahmin ederek değil, plan ve evidence referanslarını okuyarak açıklar.

## Runtime Çıktı Düzeni

Her run: `index.html`, `run.json`, `assets/`, `targets/<target-id>/`. Target altında `plan.json`, `evidence.json`, `README.md`, `index.html`, `changes/page-0001.html`, `objects/`, gerekirse `migration.sql` veya `partial-ready.sql`, `review/`, `checks/`, `bundle-manifest.json`.

`objects/` altındaki güvenli dosya adları operation ID içerir, her dosya tam statement veya PL/SQL birimi taşır. Önizleme kısaltması yalnız HTML'de yapılır. Review SQL'leri executable aggregate dışında ayrı klasördedir. Tarama/bağlantı hatasında `plan.json` yerine yanlış boş-plan üretme: `target-error.json` + `run.json` kayıtları yeterlidir, counts null kalır.

## Şemalar

- `schemas/targets.schema.json`: Jenkins'te sır içermeyen hedef tanımları.
- `schemas/source-profile.schema.json`: source roots, layout, parse/policy kapsamı.
- `schemas/snapshot.schema.json`: parser/dictionary birleşiminden kanonik snapshot.
- `schemas/plan.schema.json`: target işlem planı, evidence ve state ayrımı.
- `schemas/run.schema.json`: gözlem zamanı, build ve target durumları.
- `schemas/bundle-manifest.schema.json`: dosya yolu/byte/hash/env gizliliği.

Şemalar kapalı üst düzey alan seti (`additionalProperties=false`) kullanır. Serbest model properties yalnız tanımlı extension alanında, yeni production alan için şema/test değişikliği gerekir. Oracle precision/scale gibi metinsel literal hassasiyeti JSON float'a çevrilmez. Örnekler `synthetic=true` etiketlidir.

## Evidence Zinciri

Kaynak kanıtı: source commit SHA, repo-profile ID, göreli dosya yolu, blob/sha256, byte ve satır aralığı. Hedef kanıtı: target ID, snapshot digest, sorgu kimliği/metadata alanı, DDL blob sha256. Olmama kanıtı: tamlığı doğrulanmış envanter kapsamında yokluk. Sorgu hatası veya kaynakta dosya bulunmaması farklıdır.

Operation en az bir farkı (`change_ids`), before/after kanıtlarını ve rule ID'yi gösterir. `reason_codes` makine kodu, `reason_tr` kısa Türkçe açıklamadır. `depends_on` yalnız aynı plan operation ID'lerine veya ayrı doğrulanmış external dependency kanıtına gider. Döngü/dangling ID schema sonrası semantic validation ile yakalanır.

## Hash Ve Determinizm

SHA-256, UTF-8 ve sıralı JSON serialization standardı kullanılır. Semantic/plan digest hesabında byte formatı açıkça `sort_keys=True`, `ensure_ascii=False`, `separators=(',', ':')` olarak sabitlenir. Kaynak ham SQL byte hash'i orijinal LF/CRLF üzerinden hesaplanır, karşılaştırma canonical form hash'i ayrı alan olur.

`plan_id`: kaynak SHA + source DDL input digest + target canonical snapshot digest + seçili scope + source-profile/policy digest + generator/parser/rule/schema sürümleri + plan gövdesi, kendisi, observation timestamp, Jenkins URL/build ve çıktı hash'i dışarıda bırakılır. SQL dosyalarına plan ID girer, bu nedenle SQL hash'i plan ID öncesi hesap zincirine sokulmaz. Plan-core → plan ID → SQL bytes/hash → tamamlanmış plan → bundle manifest yönü korunur.

`run.json` gözlemsel alanları (run_id, source ref çözümleme zamanı, hedef capture zamanları, Jenkins build) taşır. Aynı kaynak SHA, aynı canonical target durumu, aynı scope/sürüm/politikada dosyalar byte-identical olmalıdır, yalnız saat değişti diye yeni Git commit oluşturulmaz.

`bundle-manifest.json` kendisini hash listesine dahil etmez. SHA dosyaları da kendi kendisini referanslamaz. Payload doğrulaması bütün listedeki dosyaları ve ayrıca beklenmeyen fazlalıkları kontrol eder.

## Artifact Repository

20 Ekim güncel kullanıcı kararı: üretilen DDL/JSON/HTML şimdilik yalnız Jenkins
build artifact arşivindedir, Git yayını kapalıdır. Aşağıdaki depo düzeni mevcut
SKY işinde kullanılmaz. Uygulama kodu ve gerçek çıktılar ayrı tutulur.

Kök başlangıç belgeleri `templates/artifact_repo/` içindedir. Önerilen yapı:

`plans/<source-profile-id>/<target-id>/<plan-id>/` değiştirilemez payload, `catalog.json` keşif indeksi, `latest/<profile>/<target>.json` son plan kimliği. Her yeni **benzersiz** payload için root katalog/pointer atomik güncellenir. Aynı plan tekrar üretildiyse payload yeniden yazılmaz, her build yeni küçük runs/YYYY/MM/DD/build-NNN-run-id kaydıyla mevcut plana bağlanır.

Var olan plan ID altında farklı bytes bulunursa overwrite değil `INTEGRITY_CONFLICT`. Artifact branch source DDL branch'i değildir. Yayımlayıcı kendi sahiplik alanı dışında dosyaları düzenlemez. Runtime raporları code repo'ya koymaz.

Bir target yayını başarısız olunca üretilmiş SQL silinmez. Publication `PUBLISHED/UNCHANGED/NOT_REQUESTED/FAILED` ile plan durumundan ayrı raporlanır. Non-fast-forward en çok 3 kontrollü retry, çakışma çözülmezse hata, force push yok.

## Modelin Okuma Sırası

Artifact repo `README.md` → `AGENTS.md` → `catalog.json` → ilgili `plan.json` → yalnız seçili operation'ın SQL/evidence dosyası. Her payload'ın README'si source/target yönü, niçin üretildiği, kısıtlar ve uygulanmadığı bilgisini içerir. Büyük body'leri topluca bağlama yükleme zorunluluğu yoktur.

SQL'in doğru üretildiğini anlatmak ile iş kuralının üretimde doğru çalışacağını iddia etmek farklıdır. Model yorumunun kanıt kapsamı plan/evidence ile sınırlanır, gerçek runtime veya iş verisi bilinmiyorsa bunu açıklar.

## Kanonik Plan Çekirdeğinin Kesin Hesabı

`input_fingerprint` profil/policy SHA-256, parser sürümü ve parser artifact SHA-256, canonicalizer sürümü, şema sözleşme sürümünü içerir. `differences` listesi operation `change_ids` için tek registry'dir. Condition ve evidence ID'leri semantic validation ile çözülür.

Plan ID hesabında tamamlanmış planın derin kopyası alınır, `plan_id` ve `validation` üst alanları çıkarılır, her operation'ın `sql` alanı null yapılır. Bu çekirdek yukarıdaki canonical JSON bytes kuralıyla SHA-256'ya çevrilir. Observation timestamp/build zaten planın hiçbir alanında bulunmaz. Generator/rule/input fingerprint'leri çekirdekte kalır. Bu düzen örnek plan ve paket doğrulayıcısında da kullanılmıştır.

Bağımsız Oracle sandbox doğrulama receipt'leri Jenkins koşusu içinde saklanır. Önceden yayımlanmış aynı planın validation metnini güncelleyip immutable payload'ı bozma. Target bundle HTML/README de capture time/build URL içermez, bunlar run-level giriş sayfasındadır. Böylece aynı planın arşiv tekrarında metinsel zaman farkından yeni commit oluşmaz.

**NO_ACTION:** Farklar vardır, hepsi açık policy nedeniyle INFORMATIONAL olarak korunur ve SQL üretimi gerekmez. Count'lar sıfırlanmaz, NO_CHANGE yazılmaz. **NO_CHANGE** yalnız sıfır gerçek fark + tam kapsam içindir. **READY** en az bir hazır operation ve sıfır REVIEW/BLOCKED içerir, **NO_ACTION** sıfır hazır/review/blocked ve en az bir informational fark içerir. ERROR/INCOMPLETE/INCONSISTENT target sonuçlarında nullable difference_count, güvenilir fark sayısı bilinmiyorsa null'dır.

## Yerel geliştirme build kimliği

Henüz yayımlanmamış 0.1.0 geliştirmesinde `generator_version`, paket kodu, schema, şablon, CSS ve asset byte hash'ini `+sha256.<digest>` suffix'iyle taşır. Renderer/kural değişip temel sürüm numarası aynı kaldığında farklı bytes aynı plan ID altında oluşmaz. Hash gözlem zamanı veya çıktı dizinini içermez.


## ODMG-RPT-UPDATE-001 yerel store ve yayın API'si

`archive-run --run-root DIR --store DIR --build-number N` yalnız yerel arşivdir, Git veya
Oracle çağırmaz. objects/schema/type/name/op-id.sql ve nesne README'leri, review/op-id.json
kanıtları bundle manifestine dahildir. Tehlikeli veya taşınabilir olmayan path bileşeni hash ile
kodlanır. Genel SQL plan sırasıyla birebir doğrulanır, eski flat bundle'lar okunabilir.

Store .artifact-store.json ile yalnız generated alanın byte sahipliğini doğrular. plans payload'ı
aynı ID altında farklıysa INTEGRITY_CONFLICT, kullanıcı dosyası üzerine yazılmaz. Kilit, fsync,
atomik dosya değişimi ve işlem hatasında kendi dosyalarını geri alma uygulanır. latest kolaylık
referansıdır, geçmiş run JSON/README bağlantıları yalnız immutable plan yollarını kullanır.
catalog/1.0 kapalı şema ve hafif run/plan listeleridir, SQL veya nesne detayını kopyalamaz.

Opt-in `publish_run` Python API'si ayrı artifact checkout, açık push yetkisi, kurum storage onayı,
izinli host/remote eşleşmesi ve provider'dan exact repo private kanıtı ister. GitCLI shell kullanmaz,
sadece owned literal pathspec'leri stage eder, hook/filter ve kullanıcı değişikliğini reddeder.
A commit'i plan payload'larını içerir, planlı bekleyen run JSON'larının artifact_git_sha'sı A olur.
B commit'i run/README/catalog/latest referanslarını içerir. Tek normal push sonrası remote SHA ve
run README erişimi doğrulanır. Mail linki B'ye sabittir. Plan yoksa (tam ERROR) yalnız run commit'i
oluşur, artifact_git_sha null, fark UNKNOWN kalır. Non-fast-forward fail-closed'dur, force yoktur.
Yayın sonucu receipt'tedir, run içindeki worker publication alanı ilk gözlem durumunu saklar.
Gerçek remote onayı/kurulumu yapılmadı, API offline Git/provider adaptör testleriyle doğrulandı.
