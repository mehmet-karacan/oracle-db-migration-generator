# Ortak UI: çalıştırma ve dağıtım

24 Ekim 2026 kullanıcı talimatının ilk uygulaması. React/TypeScript/Vite,
shadcn/ui (Radix), Tailwind ve TanStack Table, kontrol API'si Python FastAPI.
Mevcut motor/CLI korunur. Git/Oracle kaynak → birden çok Oracle hedef desteklenir.

## Yerel geliştirme

Bu tur Python 3.13/Windows doğrulandı. Mevcut venv ile:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -r requirements-ui.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
cd web
npm ci
npm test
npm run build
cd ..
.\.venv\Scripts\python.exe tools/ui_server.py --local-preview --password-login --port 8800
```

Adres `http://127.0.0.1:8800`. Yerel mod yalnız loopback'e bağlanır, açıkça
parolalı oturum açar, yerel worker mail göndermez. Gerçek SKY
bağlantıları kullanıcının açık talimatıyla şifreli vault’a aktarıldı. Canlı SKY
profili varsayılan Jenkins oturum devrine bağlıdır. 25 Ekim açık kullanıcı
talimatıyla Çalıştırma Yeri = Bu Bilgisayar seçilirse özel yerel worker kullanılır
ve SQL `.local/ui-state/runs/<run-id>/` altında kalır. Bu seçim yalnız
local-preview runtime yeteneğiyle sunulur. Varsayılan Jenkins korunur, sessiz
fallback yoktur. Jenkins çıktıları kendi arşivinde kalır. `.local/ui-state`
Git dışındadır. `requirements-ui.lock` yerel sürüm pinleridir, üretim platformuna
ait hash'li release lock ve agent kabulü NOT_RUN.

## Ekranlar ve çalışan ayarlar

24 Ekim ek sonuç ekranı: kendi `ObjectResults`/`ObjectComparisonPanel`
bileşenlerimizle nesne seçimi, kaydedilmiş kaynak–hedef alan farkları, işlem
gerekçeleri ve DDL linkleri. #55 yapısal metadata'sı mevcut arşivden bağlandı,
yeniden Oracle taraması yapılmadı. [Sözleşme ve aktarım](NESNE_SONUCLARI.md).

- Yeni karşılaştırma: kayıtlı profil, Git bağlantısı/ref/yerleşim/şema kökleri
  veya Oracle bağlantısı/şemalar, hedefler, nesne türleri, teknik filtre,
  fiziksel özellikler, uzunluk semantiği, kaydet/başlat.
  Bağlantılar ekranındaki Şema eşleştirmeleri sekmesinde kaynak bağlantısı,
  kaynak şemaları ve her hedefin çiftleri isimli kayıt olarak saklanır.
  Yeni karşılaştırmada kayıtlı eşleştirme seçilir ve kapsam özeti gösterilir.
  Git ref ve karşılaştırma tercihleri karşılaştırma ekranında kalır.
  Her hedef kaynağın bir alt kümesini seçebilir. Aynı şema adları desteklenir.
  Seçenekler girilen kaynak kapsamından gelir, canlı keşif listesi değildir.
  Eşleştirme düzenleyicisinde kaynak değişince geçersiz seçimler temizlenir.
- Bağlantılar: Git HTTPS ve Oracle host/port/service veya SID, Thin/Thick,
  yetkili katalog okuyucusu, ayrı süreçte salt okunur test.
  Git için kullanıcı adı ve kişisel HTTP erişim token'ı girilir. Bitbucket
  Profil → Manage account → HTTP access tokens → Create token yönergesi
  ekranda görünür, yalnız depo okuma yetkisi yeterlidir.
  Düzenlemede kullanıcı adı yetkili, no-store access-info yanıtından yüklenir,
  kayıtlı token/parola durumu gösterilir. Yükleme başarısızsa kaydet kapalıdır.
  Parola tekrar gösterilmez. Düzenlemede boş parola mevcut sırrı korur, parolanın
  baş/son boşlukları değiştirilmez. URL'ye gömülü kimlik bilgisi reddedilir.
  SSH bu UI sürümünde yoktur, CLI'nin mevcut SSH desteği korunur.
  Giriş hesabı ile karşılaştırılan şema farklı olabilir. Mevcut katalog
  okuyucusu belirtilmemişse farklı şemayı okurken giriş hesabı doğrulanır.
  Oturum kimliği, etkin SELECT_CATALOG_ROLE, şemanın varlığı ve DBA katalog
  erişimi kontrol edilir. Yalnız ALL_OBJECTS görünürlüğü tamlık kanıtı değildir.
  Yetki eksikliği boş veya eşit sonuç sayılmaz. Yetki verilmez, hesap değiştirilmez.
  Bağlantı ekranındaki şema alanı yalnız okuma testi içindir, profil kapsamı değildir.
- Çalışmalar: gerçek durum/aşama/nesne ilerlemesi, toplam ve kaynak hazırlama
  süresi, hedef sonuçları, sunucuda arama/tür filtresi ve kaydırarak nesne yükleme, gerekçe,
  SQL ve kanıt kimlikleri, mevcut HTML raporuna erişim.
- Ayarlar: Oracle connect/call/capture ve iş bütçesi, üç parser bütçesi,
  Git denemeleri/bekleme, eşzamanlı iş sınırı, prepared cache etkinliği/giriş ve
  boyut sınırı, Jenkins bildirim anahtarı. Alıcı yalnız mkaracan@innova.com.tr.
  Mevcut günlük TTBP 08:00 zamanlaması salt okunur gösterilir, değiştirilemez.

Kayıtlar sürümlüdür. Profil, bağlantı sürümleri ve etkin ayarlar iş başında
dondurulur, sırlar JSON'a konmaz. Çalışan/geçmiş iş, ayar düzenlemesiyle
yeniden yorumlanmaz. Sayfa filtreleri planı değiştirmez. Cache anahtarında
parser bütçeleri dahil etkin ayarlar vardır, Oracle kaynağı her işte yeniden
okunur. Kapasite ayarı var olan cache dosyalarını silmez.

Bağımsız eşleştirmeler SQLite records tablosunda schema_mapping türündedir.
Profil mapping_id ve mapping_revision ile birlikte gerçek kapsamın sabit
kopyasını taşır. Kayıtta sürüm ve kapsam aynı olmalıdır. Sonradan düzenleme
geçmiş profil veya çalışmayı değiştirmez. Güncel seçim yeniden seçilip kaydedilir.

Şema eşleştirmeleri profilin `target_mappings` alanında hedef kimliğiyle saklanır.
Çalışma kaydı bunların sabit kopyasını taşır, ayrıntıda karşılaştırılan çiftler
gösterilir. Eski profillerin örtük aynı-ad eşleştirmesi görünür olarak yüklenir.
Yeni API profil kayıtlarında her hedefin açık eşleştirmesi zorunludur.
Eski kayıtlar ve önceki run belgeleri değiştirilmez. Aynı kapsamın açık yazılması
Jenkins fingerprint'ini değiştirmez. Bir hedefin şema kapsamı gerçekten değişirse
eski Jenkins eşlemesi kullanılamaz. Mevcut job yeni seçimi sessizce yok sayamaz.

## Ortak ortamın kimliği ve sırları

Normal başlangıç `--local-preview` kullanmaz. En az 32 karakter
`ODMG_UI_PROXY_KEY` ve dış secret deposundan Fernet biçiminde
`ODMG_UI_VAULT_KEY` olmadan CLI başlamaz. Vault anahtarı Git/argv/log/artifact'e
yazılmaz. Anahtarın yedek/rotasyonu kurum sır yönetiminin parçasıdır.
Yerel `vault.key` geliştirme kolaylığıdır, ortak ortamda kullanılmaz.

Kurumsal SSO'yu tamamlayan güvenilir proxy gelen `X-ODMG-*` başlıklarını
silip aşağıdaki değerleri kendisi üretir:

```text
X-ODMG-User: kurumsal-kullanici
X-ODMG-Role: admin | operator | viewer
X-ODMG-Timestamp: Unix saniyesi
X-ODMG-Signature: hex(HMAC-SHA256(proxy_key, user + "\n" + role + "\n" + timestamp))
```

İmza 60 saniye toleransla doğrulanır, eksik/sahte kimlik 401 alır. Proxy
ve vault anahtarları ayrıdır. API'ye doğrudan istemci erişimi kapatılır,
HTTPS/kurumsal oturum/rol eşlemesi proxy'de kurulur. Proxy sağlayıcısı henüz
doğrulanmadı. `ODMG_UI_ALLOWED_ORIGINS` gerçek UI origin'iyle tanımlanır,
aynı origin dağıtımı kullanılır. Yetki API'de de denetlenir.

Varsayılan ortak çalışma modunda doğrulanmış bütün oturumlar aynı `shared`
yetkisini kullanır, kullanıcı/rol rozeti ve bağlantı kullanıcı listesi UI’de
bulunmaz. Herkes bağlantı/profil/ayar yönetir, karşılaştırma başlatır ve ortak
geçmişi görür. Bu, anonim ağ erişimi değildir: proxy imza kontrolü sürer.
Eski rol modu yalnız `create_app(shared_workspace=False)` ile açıkça seçilebilir.
Sırlar public JSON’a dönmez, SQLite vault Fernet ile şifrelenir. Ortak modda
audit aktörü `shared` olur. Kurum ACL/secret entegrasyonu NOT_RUN.

Yerel kalıcı kayıt dosyası `.local/ui-state/control.sqlite3` olur. Bağlantı,
profil, proje, ayar ve çalışma belgeleri SQLite tablolarında JSON metni olarak
saklanır, ayrı JSON dosyaları ana kayıt deposu değildir. `secrets` tablosu
kullanıcı adı + parola/token çiftini sürüm bazında Fernet ile şifreli tutar.
Yalnız düzenleme için `/api/connections/{id}/access-info?revision=N` kullanıcı
adını ve kayıtlı erişim bilgisi durumunu döndürür, token/parola hiçbir yanıtta
yer almaz. Bu okuma kayıt/frozen spec/binding hash'ini değiştirmez. Yerelde
anahtar `.local/ui-state/vault.key` içindedir, ortak ortam dış anahtar kullanır.

Üstte proje seçimi ve proje ekleme vardır. Bağlantı, profil ve çalışma kayıtları
proje kimliği taşır, eski kayıtlar SKY’ye atanır. Proje değiştirilince önceki
veriler/ayrıntı temizlenir. Farklı projenin bağlantısıyla profil/iş oluşturma
API’de reddedilir, mevcut kaydın projesi sonradan taşınamaz. Uygulama ayarları
globaldir. Proje ayrımı yetki duvarı değildir: ortak kullanıcı bütün projeleri
seçebilir.

## Servis hesabı olmadan mevcut Jenkins işine aktarım

Kullanıcı Jenkins servis hesabının henüz bulunmadığını bildirdi. Bu yüzden
mevcut SKY işi için server-owned `.local/ui-jenkins-bindings.json` kullanılır.
`ODMG_UI_JENKINS_BINDINGS` bu dosyanın mutlak yolunu gösterebilir. Kalıcı
varsayılan `state-root/jenkins-bindings.json` dosyasıdır, sunucu yeniden
başlatılınca da korunur. Bu modda eşleşmeyen hiçbir proje yerel worker’a
düşmez. Dosya yalnız
proje/profil kimliği, etkin spec hash’i, iş URL’si ve hedef eşlemesi içerir.
Bağlantı/credential sürümü veya kapsam/ayar değişince başlatma reddedilir,
mevcut Jenkins işi kullanıcının yeni seçimini sessizce yok sayamaz.

`tools/ui_import_connections.py --root .local/ui-state --manifest
.local/ui-import-connections.json --credentials-file .local/credentials.env`
endpoint ve credential alias’larını okur, sırları vault’a şifreli yazar. Aynı
girdide idempotenttir, kullanıcının değiştirdiği kaydı üzerine yazmaz. Gerçek
manifest/credential/binding Git dışında kalır.

UI’de Karşılaştırmayı başlat, `AWAITING_JENKINS` kaydı üretir, yerel kuyruğa
girmez. Jenkins’te başlat bağlantısı mevcut tarayıcı oturumunda parametre
formunu açar. Operatör kapsamı/COMPARE’ı doğrular ve Build’e basar. UI bu adımı
otomatik başlatılmış veya canlı izleniyormuş gibi göstermez.

Tamamlanan gerçek build’in `run.json` kaydı yetkili tarayıcıdan okunduktan
sonra `tools/ui_link_jenkins_run.py --root .local/ui-state --run-id <UI_ID>
--observed-run-json <KANIT_JSON> --observed-performance-json <OLCUM_JSON>` ile
bağlanır. Araç şema, zaman sırası/tazelik, build URL/numara, Git kaynağı,
hedefler ve ölçüm commit/süre uyumunu denetler. Bir build yalnız bir UI kaydına
tek transaction’da bağlanır, farklı sonuçla üzerine yazılamaz. Operatörün
kaynak kanıtını doğru işten okuması güven sınırıdır, `BROWSER_OBSERVED`
otomatik API doğrulaması değildir. SQL dosyaları yerel UI’ye kopyalanmaz,
sonuç/süre özeti ve Jenkins rapor bağlantısı gösterilir.

Bu yol yalnız eşleşen mevcut Git→PROD/TTBP işi içindir. Oracle kaynak veya
değiştirilmiş kapsamın otomatik Jenkins yürütülmesi aşağıdaki ayrı UI job ve
servis hesabı kurulumu tamamlanınca kullanılabilir. Ortak dağıtım/otomatik
başlatma ve sonuç takibi hâlâ NOT_RUN’dır.

## Jenkins çalıştırıcısı

`templates/jenkins-ui.groovy` ayrı manuel UI işi içindir, mevcut günlük işe
uygulanmaz, cron eklemez. Placeholder'lar gerçek agent/release/venv/Instant
Client/korunan state yolu/Jenkins Credentials kimliğiyle doldurulur.

API ortamı: `ODMG_UI_JENKINS_JOB_URL`, `ODMG_UI_JENKINS_USER`,
`ODMG_UI_JENKINS_TOKEN`, `ODMG_UI_PROXY_KEY`, `ODMG_UI_VAULT_KEY`,
`ODMG_UI_ALLOWED_ORIGINS`, thick için `ODMG_ORACLE_CLIENT_DIR`.
Sırlar ekrandan okunmaz. API Jenkins'e yalnız `RUN_ID` yollar, worker aynı
korunan state kökünden frozen kayıt/credential sürümlerini okur.

SQLite/PID kullanımı nedeniyle API ve worker **aynı makinede, yerel diskte ve
PID namespace'inde** çalıştırılır, çok hostlu NFS/SMB aktif-aktif kapsamda yoktur.
Ortak state Jenkins'in yönettiği özel alandadır, kullanıcı dosya erişimi yoktur.
Raw source/observations burada kalır, web artifact arşivine kopyalanmaz.
Arşiv yalnız Jenkins build `output/runs/build-N` alanına hazırlanır, Git/public
yayın yoktur. Özel state/log/cache retention da işletimce kurulmalıdır.

Yerel kuyruk kapasite/FIFO rezervasyonunu tek SQLite write transaction'da
yapar, scheduler son 200 kayda daraltılmaz. Worker global sınırı ve kendi
deadline'ını uygular, sayfa/API kapansa da sürer. Yerel API yeniden açılınca
ölmüş worker/yarım claim `WORKER_INTERRUPTED` olur. Üretimde agent/host kaybı
uzlaştırması ve servis restart kabulü ayrıca yapılmalıdır.

`tools/ui_jenkins_archive.py` mevcut renderer ile HTML maili/arşivi hazırlar,
repository/source/observations ve control/vault verisini yayımlamaz. Pipeline
frozen `notify_enabled` açıksa yalnız izinli alıcıya `emailext` gönderir.
Yerel araç SMTP çağırmaz. Kayıt `PREPARED_NOT_SENT` kalır, teslim iddiası yoktur.

Bir işte Oracle bağlantıları aynı Thin/Thick modunu kullanır, karışık mod
`MIXED_ORACLE_DRIVER_MODES` ile reddedilir. Testler ayrı process'tedir, driver
modu API'yi etkilemez. Ön test envanter erişimini, gerçek karşılaştırma ise
GET_DDL/dictionary tamlığını doğrular.

## Oracle kaynak kanıtı

`source/oracle_reader.py` kapalı salt okunur collector'ı kullanır. Envanter
değişirse bir tekrar sonrası `INCONSISTENT`, atomik SCN snapshot iddiası yoktur.
Oracle SOURCE commit taşımaz, `source_origin={kind:ORACLE,connection_id,
snapshot_id}` plan/run/SQL/HTML'e aktarılır. Git legacy sözleşmesi korunur.
Bütün kaynak kanıtları ve property/capability/context referansları ayrı ad
alanına taşınır. Raw DDL ve tam COMMENT/GRANT sidecar blobları hash'leriyle
özel source dizinine atomik kaydedilir. `load_snapshot(require_ddl=True)`
varlık/hash doğrular. Kaynak dictionary eksikse tam kapsam/NO_CHANGE sonucu
ve COMMENT/GRANT için kanıtsız yokluk üretilemez.

## Kabul durumu

Offline testler, gerçek yerel API form/worker hata akışı, sentetik Git →
gerçek parser/plan/SQL ve SQL çekmecesi doğrulandı. Jenkins archive helper
sentetik tamamlanmış işte SQL byte eşitliğiyle doğrulandı, mail gönderilmedi.
Komut/kanıt: `yz/DEVIR.md`.

**NOT_RUN:** gerçek Oracle→Oracle kabulü, kurumsal SSO, üretim hash'li/platform
lock, otomatik Jenkins UI job kurulumu/tetikleme, servis/ACL/retention/agent
kesinti kabulü. Günlük job değiştirilmedi. #55 mevcut Jenkins oturumuyla UI’den başlatıldı,
nihai canlı kanıt ve süre için yz/DEVIR.md kaydı esas alınır.

## Dil, görünüm ve okunabilirlik

Üst çubuktaki TR/EN ve tema düğmesi bütün ilk taraf ekranlarına uygulanır.
Tercihler odmg.ui.preferences.v1 anahtarında yalnız locale/theme olarak
saklanır. Tarayıcı depolaması kapalıysa seçim oturum belleğinde çalışır.
SQL, kullanıcı nesne adları ve arşivdeki özgün Türkçe gerekçeler çevrilmez.
İngilizce görünüm bu gerekçelerin özgün dilini belirtir.

Ana metin 16 px, yardımcı metin en az 13 px, kod/kanıt 14 px. Proje ve form
seçimleri ortak Radix menüsü kullanır. Menü/dialog ve durum renkleri iki temada
aynı anlamı korur. Bağlantı formunda Bağlantı Türü ilk, Bağlantı Adı ikinci.
Kayıtlı bağlantı adındaki orta nokta sunumda tire olur. Değiştirilmeden kaydedilen
adın özgün kayıt değeri korunur. Ayrıntılı kabul ve sınırlar ARAYUZ_STANDARTLARI.md.

## Parola girişi ve proje sınırı - 25 Ekim 2026

Uygulama adı Şema Karşılaştırma. mkaracan / Mehmet KARACAN tek ortak yetkili
hesaptır. Varsayılan parola yok. Loopback --local-preview --password-login
ilk açılışında kullanıcı en az 12 karakterlik parolasını belirler. Sonra giriş
yapar. Parola sohbet/argv/log içine yazılmaz. Salt ve scrypt hash'i özel control
SQLite içinde, oturum yalnız token hash'iyle tutulur. Cookie HttpOnly ve
SameSite strict, 8 saat süreli, çıkışta sunucu kaydı iptal edilir. Beş başarısız
deneme 15 dakika engellenir. Tarayıcı tercihlerine credential yazılmaz.

Ağ üzerinden --password-login servisinde ilk kurulum kapalıdır, ters proxy'nin
loopback peer olması bu sınırı değiştirmez. Önce aynı state diziniyle yerel
bootstrap yapılır, sonra servis yeniden ağ modunda açılır. Ağ password modunda
cookie Secure'dür. HTTPS/TLS ve dış vault anahtarı kurum dağıtımının kabulüdür,
bu tur NOT_RUN. Proxy kimlik modu alternatif olarak korunur. --local-preview
kurum ağına proxy edilmez. Yerel API'yi anonim açan create_app(mode='local')
yalnız sentetik test uyumluluğu içindir, normal yerel CLI parolalı açılır.

Her proje kendi bağlantı/eşleştirme/profil/ayar/çalışma kayıtlarına sahiptir.
UI X-ODMG-Project header'ını, dosya linkleri project_id query'sini taşır.
Header/query/payload çelişkisi reddedilir. Ayrıntı, test ve sonuç erişimi kayıt
sahipliğini kontrol eder. Scope verilmemiş legacy API yalnız SKY'dir. Başka
projenin ayarları SKY defaults değerlerini miras almaz. Run kendi proje ayar
kopyasıyla başlar. Proje geçişinde eski formlar ve geç gelen yanıtlar bırakılır.
Günlük TTBP takvimi yalnız SKY'de gösterilir, diğer projeye kopyalanmaz.

Çalışma Özeti kartları /api/runs/{id}/summary üzerinden SQL içermeyen kayıtlardan
üretilir. Bulunan Fark doğrulanmış farktır, UNKNOWN ayrı gösterilir. Envanter yoksa
sayı Bilinmiyor, PARTIAL ise alt sınır notu görünür. COMMENT/GRANT toplam nesneye
katılmaz. scan_views arşiv metadata'sını plan/kapsam/manifest hash'iyle değişmez
saklar, import_scan yalnız yerel operatör sınırıdır, HTTP yükleme endpoint'i yoktur.

## Hedef bağlantısı seçimi

Şema Eşleştirmeleri düzenleyicisinde hedef bağlantıları dropdown satırlarıdır.
Hedef Ekle ile en fazla8 farklı Oracle bağlantısı seçilir, her satırın şema çiftleri
ayrıdır. Bağlantı değişirse veya satır kaldırılırsa eski çiftler temizlenir. Boş
hedefle kayıt yapılmaz. Kaynak değişimi eski çiftleri de geçersiz kılar.

Yerel IZOLASYON_TEST projesi kullanıcı talimatıyla ayrılık kabulü için eklendi.
TEST bağlantıları example.invalid/oracle-test.invalid sentetik tanımlarıdır.
Gerçek hesap bilgileri taşımaz, çalışma başlatılmadı. SKY verileri değişmedi.


25 Ekim nesne inceleme teslimi: çalışma ekranı fark türü filtresi, tam kolon/
anahtar grupları, kısa nesne özeti, bağlantı/şema bağlamı ve change_ids üzerinden
ilgili SQL akışını kullanır. Özgün yerel snapshot tanımları ayrı yetkili,
no-store endpoint'ten okunabilir. Jenkins özgün tanımlarının aktarılmış olmadığı
mevcut#55 gibi kayıtlarda satır farkı yerine arşiv durumu gösterilir. Tam kayıt
sözleşmesi docs/NESNE_SONUCLARI.md, tasarım docs/SONUC_INCELEME_TASARIMI.md.
