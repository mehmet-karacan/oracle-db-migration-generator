# Jenkins Çalışma Sözleşmesi

20 Ekim son kullanıcı kararı: mevcut SKY işi rapor/SQL'i yalnız Jenkins
artifact arşivinde saklar; artifact Git publication aşaması/credential binding
yoktur. Mail Jenkins build raporunu açar. Aşağıdaki yayın parametreleri mevcut
işte etkin değildir; yeni açık yetki olmadan kullanılamaz.

**Durum:** 20 Ekim 2026 kullanıcı talimatıyla ilk INNOVA_ODI işi kuruldu.
İlk kurulum ve çalışma kanıtı `docs/JENKINS_ILK_KURULUM.md` içindedir.
Aşağıdaki geniş parametre sözleşmesi sonraki çoklu hedef/yayın düzenidir;
ilk işte yalnız RUN_MODE ve sabit SHA doğrulamalı GENERATOR_RELEASE görünür.

## Parametreler

| Ad | Tip / Varsayılan | Anlam |
|---|---|---|
| SOURCE_REPO_URL | string, job kurulurken girilir | Kaynak DDL Git URL'si; kodda kurum adresi sabitlenmez. |
| SOURCE_REF | string | SKY ilk kurulum adayı master; gerçek ref doğrulanır. |
| SOURCE_GIT_CREDENTIAL_ID | string | Salt okunur Git SSH credential. |
| SOURCE_PROFILE_FILE_ID | string | Managed JSON kaynak profilinin ID'si. |
| TARGETS_FILE_ID | string | Managed JSON target registry. |
| TARGET_IDS | string = ALL | Tüm enabled target'lar veya virgüllü ID listesi. |
| MAX_PARALLEL_TARGETS | string = 2 | 1–8 tam sayı, sınırlı batch paralelliği. |
| ORACLE_DRIVER_MODE | choice = thin | thin/thick; target özel override olabilir, worker izolasyonu şart. |
| ORACLE_CLIENT_LIB_DIR | string, boş | Thick için agent'a kurulmuş dizin; dosya indirme yoktur. |
| PUBLISH_ARTIFACTS | boolean = false | İzinli arşiv Git push'u. |
| ARTIFACT_REPO_URL | string, boş | Özel çıktı deposu; Source ve Generator URL'lerinden farklı. |
| ARTIFACT_REF | string = main | Artifact branch'i; mevcut default/kurum kuralı kurulumda doğrulanır. |
| ARTIFACT_GIT_CREDENTIAL_ID | string, boş | Yalnız artifact repo'ya yazma yetkisi. |
| ARTIFACT_DESTINATION_APPROVED | boolean = false | Kurumsal verinin bu hedefe aktarımı için job yöneticisi tarafından verilen izin; key sahibi olmak tek başına izin değildir. |

Normal build kullanıcılarının repo URL/credential kombinasyonunu keyfi host'a çevirebildiği güvensiz iş kurulmaz. Güvenilir job kurulumunda `allowedSourceHosts` ve `allowedArtifactRepositories` allowlist'leri tanımlanır; build parametresiyle değiştirilemez. Bu değerler source-profile JSON'unun alanı değildir. Örnek/test job'da yalnız `.invalid` ve geçici yerel Git fixture'ları yetkilidir. Registry yönetimi güvenilir Jenkins yöneticisine aittir. `PUBLISH_ARTIFACTS=true` tek başına allowlist/private erişim politikasını atlayamaz.

## Target Registry

`schemas/targets.schema.json` ve `examples/targets.example.json` esas alınır. Her tanım id/name/enabled, Oracle endpoint, driver mode ve schema mapping/credential ID içerir. Port pozitif, service_name ile sid tam biri, ID benzersiz, schema mapping duplicate yok; enabled hedef bulunmaması INPUT_ERROR. Yeni enabled tanım eklendiğinde `ALL` otomatik kapsar.

Bir target birden fazla schema taşır; schema başına ayrı credential olabilir. Kullanıcı adı/şifre registry'de değil Credentials içindedir. Python'a hedefin gerçek DSN/user/password'u yalnız worker process environment veya izinleri sınırlandırılmış geçici dosya ile verilir. Dosya/console/manifest içine serialize edilmez. Credentials binding'in log maskelemesi bir güvenlik sınırı değildir; Groovy string interpolation'da sır kullanma (K03).

## Pipeline Aşamaları

1. Güvenilir Generator kodunu checkout, dependency lock/wheelhouse kontrolü.
2. Managed file ve parametreleri doğrula; endpoint/credential/publisher allowlist kontrolü.
3. Source ref'i sabitle ve güvenli checkout/blob okuyucu ile source snapshot oluştur.
4. Aktif/seçili target listesini hazırla; bilinmeyen ID'de fail, sessiz ALL yok.
5. Target'ları en fazla MAX_PARALLEL_TARGETS büyüklüğünde batch'lere ayır. Her target closure yalnız kendi immutable config kopyasını kullansın.
6. Branch içinde target ve schema credential scope'u, tek worker, timeout. `env.TARGET_*` ortak global değişkeniyle paralel branch'leri birbirine karıştırma.
7. Worker sonucu ne olursa olsun diagnostic/result JSON'u atomik yaz. `failFast=false`; ayrı target'lar sürsün.
8. Aggregate JSON/HTML hazırla, hash ve link kontrolü; ham sırlar ve gerçek bağlantı yapılandırmaları arşivlenmez.
9. `post/always` içinde rapor/dosyaları arşivle. HTML Publisher varsa publish; yoksa normal artifact linkleri. Hata çıkan koşuda da diagnostic kaybolmasın.
10. Yetkili publication ayrı aşama: payload doğrula, private/kurum allowlist kontrolü, commit/push retry. Yayınlama başarısı ve plan durumu ayrı.

İlk ürün GitHub Actions iş akışı eklemez; mevcut kurumsal Jenkins esas alınır. Eklenti eksikliği varsa core pipeline testleri devam eder, canlı kurulum `ENVIRONMENT_BLOCKED` raporlanır. Config File Provider kurumsal managed JSON için seçilmiştir; `readJSON`/`configFileProvider`/`withCredentials`/Git step gereksinimleri kurulum kontrol listesine yazılır. Dinamik target UI için Active Choices gibi ilave eklenti şartı yoktur.

## Exit Code Ve Build Durumu

| Code | Anlam | Jenkins |
|---|---|---|
| 0 | Seçili tüm target'lar tam karşılaştırılmış; READY, NO_CHANGE veya yalnız INFORMATIONAL farklardan oluşan NO_ACTION, blocking/review yok | SUCCESS |
| 10 | Farklar var; review/unsupported/policy-held işlem nedeniyle tam migration üretilemedi | UNSTABLE |
| 20 | En az bir target error/inconsistent/incomplete; diğer sonuçlar korunur | UNSTABLE |
| 30 | Geçersiz config/source scope/ref/parse-global sorun; plan güvenilir değil | FAILURE |
| 40 | Artifact integrity/security ihlali veya zorunlu publication başarısız | FAILURE |

Öncelik 40 > 30 > 20 > 10 > 0. Başarı/no-change sadece gerçek sonuçlardan türetilir. Connection başarısız target'ı try/catch sonrası 0'a çevirmek yoktur.

## Güvenli Erişim

SSH için doğrulanmış known_hosts; `StrictHostKeyChecking=no` yoktur. HTTPS Git kullanımında key URL'ye gömülmez; provider credential binding/askpass kullanılır. Credentials job trusted code dışında PR build'lerine açılmaz. Hedef profilinde yazma yetkili user kullanıldığını saptarsan otomatik hak düşürme/grant yapma; DBA kurulum koşulu olarak raporla.

Private GitHub kullanımı kullanıcı tarafından belirtilmiştir; bu, kurumun dışa veri aktarım iznini kanıtlamaz. Varsayılan publication kapalı ve Jenkins arşivi açıktır. Artifact Git adresi daha sonra Bitbucket'a değiştirilebilir; kod hosta sabitlenmez. Key veya token hiçbir belge/sohbette istenmez.
