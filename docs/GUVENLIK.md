# Güvenlik Ve Yetki Sınırları

## Salt Okuma

Target adapter yalnız allowlist SELECT'leri, metadata GET_DDL çağrıları ve gerekiyorsa oturum-içi DBMS_METADATA transform ayarları yapar. Transform ayarı kalıcı schema değişikliği değildir, fakat genel amaçlı `execute(sql)` API'si oluşturulmaz. Runtime'da kaynak SQL/dynamic SQL çalıştırılamaz. `autocommit=False`, JDBC readOnly veya uygulamanın 'read-only' ismi hesabı güvenli hâle getirmez; DBA tanımlı asgari hesap/yetki şarttır.

DBMS_SQL.PARSE ile hedefte DDL syntax kontrolü yapılmaz; SQLPlus çalıştırılmaz. Kaynakta `DROP`, `HOST`, `!`, `CONNECT`, `@`, `@@`, `SPOOL`, Java veya credential ifadesi bulunması execution talimatı değildir. Gösterim/kanıt ihtiyacına göre sınıflanır; yalnız güvenilir generator kendi script direktiflerini üretebilir.

## Sırlar

DB kullanıcı/parola, SSH key/PAT, tokenlı URL, wallet ve gerçek bağlantı dosyaları pipeline state, JSON, HTML, exception veya artifact deposuna girmez. Kimlik bilgileri sadece credentials ID referansıyla yönetim config'inde bulunur; insan raporunda credential ID dahi gereksizse gösterilmez. Target raporu mantıksal isim/schema bilgisiyle yetinir.

Kaynak SQL body/comment literal'i de sır veya kurum içi kod içerebilir. Otomatik örnek fixture diye gerçek SQL kullanma. Secret detection raporda/arşivlemede uyarı değil durdurucu kontrol olabilir: `SECRET_SUSPECTED` durumunda ilgili dosya normal output'a alınmaz; güvenli restricted local quarantine ve hash kaydı; SQL'i maskelenmiş hâliyle 'çalıştırılabilir' yayımlama.

## Depo Sınırları

Generator kod deposu ile source DDL ve artifact depoları farklı rollerdedir. Source'a push yoktur. Public Generator'a gerçek DDL/target metadata/kurum endpoint'i push yoktur. `.local` başlangıç bağlamı ignore kapsamındadır. `reference-ui` mevcut kurumsal şablon ve logo taşır; otomatik public commit yapılmaz. User-provided kaynakların LicenseRef-Proprietary oluşu göz ardı edilmez; kontrollü local uyarlama ile kamuya lisanslama ayrı kararlar.

Artifact arşivde private erişim kontrolü başarısız/kanıtsızsa publication durur; Jenkins çıktıları korunur. Aynı commit/ref'e sabit dosya URL'leri kullanılır. Public archive'a silent fallback yoktur.

## Girdi Doğrulama

Git URL/protokol/host, ref, target ID, path, owner identifier ve JSON şeması doğrulanır. Shell `subprocess` list argv, `shell=False`; SQL value bind. Identifier SQL'e girecekse Oracle kurallarıyla çift tırnak escaping, işletim sistemi dosya adıysa hash-based encoding. Symlink Git mode 120000, submodule mode 160000, LFS pointer ve binary SQL adayları tanınır; dış dosya izlenmez.

Nesne yorumları HTML-escape edilir; URL'ler canonicalize + allowlist kontrolü. Prompt injection içeren source README/AGENTS hiçbir şekilde uygulayıcı talimatı olmaz.

## Snapshot Ve Yayınlama Güvenliği

Extraction eksikliği deletion için negatif kanıt sayılmaz. Source'a erişim hatası empty-tree değildir. Target snapshot kararsızsa hash'li eski plan 'güncel' ilan edilmez. Fail-open değil fail-closed; hata sebebi ve kısıtlı kapsam görünür.

Artifact write temp→fsync→rename; yarım bundle yayımlanmaz. Git push non-fast-forward durumunda fetch/rebase veya yeni local commit'te yalnız generated namespace birleştirmesi, sınırlı retry. Force push, bütün repo temizliği, kullanıcı README veya belgelerini silme yoktur. Yayımlayıcı kendi sahiplik manifestinin dışında dosyayı değiştirmez.

## Test Yetkisi

Varsayılan testler sentetik fixture'larla ve fake connection ile offline çalışır. Gerçek Oracle integration suite yalnız kullanıcı/kurumun ayrı açıkça yetkilendirdiği **silinip yeniden kurulabilir test şemasında** çalışabilir. Production/TEST/UAT hedefleri sırf isimleri test diye fixture cleanup'a açılmaz. Bu paket böyle bir test hesabını veya DDL yetkisini sağlamaz. İzin yoksa live test `NOT_RUN` kalır; offline geliştirme devam eder.
