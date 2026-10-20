## Güncel kapsam: yalnız PROD / TTBP — 20 Ekim 2026

Son kullanıcı talimatı: günlük varsayılan yalnız TTBP; INNOVA_ODI ancak manuel
SCHEMA_SCOPE seçimiyle. Jenkins 08:00 Europe/Istanbul korunur. tools/jenkins_scope.py
build'e özel dört config kapsamını birlikte daraltır; immutable iki şemalı registry
değişmez. Source/target READ ONLY, Oracle DDL/DML/COMPILE NOT_RUN. Hedef adı PROD;
TTBP şema olarak görünür, iç LOCAL-TTBP kimliği ve arşiv yolları korunur.

Gerçek 64-hex / S_64-hex teknik nesneler ile bağlı INDEX/COMMENT/GRANT policy
filtresine dahil edildi. Ham inventory ve scope-exclusions kanıtı korunur.
Sentetik COMMENT/GRANT hash kimlikleri silinmez: bilinen bağlı nesne/kolon,
optional object.display_name ile HTML/mail/README'de gösterilir. Belirsiz bağlı
nesne açık etiketlenir. Planı olmayan hedefte sahte ad/şema yok; UNKNOWN ve
bilinen hata kodu gösterilir. İç object/operation ID, dosya yolu ve SQL gövdesi
korunur; plan ID ve SQL header hash değişebilir. Bağımsız son inceleme P1/P2 yok.

Git paket bütünlüğü: eski unanchored artifacts/ ignore kuralı uygulamanın altı
artifacts Python modülünü de Git dışında bırakmıştı. /artifacts/ olarak düzeltildi;
6 gerçek kaynak modülü private kod yayınına alınır. Üretilen çıktı/.local/SQL
arşivleri yine Git dışıdır. Wheel içindeki 123 kaynak/asset dosyası workspace ile
byte eşitliği üzerinden doğrulandı. Kurumsal sırlar/yapılandırmalar yayımlanmaz.

Doğrulama: check_contracts 7 schema / 8 example VERIFIED. Son tam koşu 636 testte
630 passed, 6 Windows os.rename WinError5 (assertion/ürün kararı hatası değil),
skip0. İki dar tekrarın her biri 5 passed / 1 aynı Windows erişim hatası verdi;
başarılı tekrarların birleşimi aynı altı testin tamamını kapsıyor. Tek koşuda
tam yeşil iddia edilmez; aralıklı Windows filesystem kilidi açık ortam sınırlamasıdır.
JUnit: pytest-ttbp-prod-windows-failures.xml, pytest-ttbp-prod-windows-rerun.xml,
pytest-ttbp-prod-windows-rerun2.xml. Yeni scope 3, hash 22 ve yan kayıt/hata etiket
23 testleri odak doğrulamalarda geçti. Testler için güvenlik/antivirüs değiştirilmedi.

v11 release SHA f00a4c805204b9faa379266f9ce10c8740b47bbac8b6b590322edecc83842d9a;
wheel afcd482dfc165429b08ca1c2fb4d86caf3df310ad34ce7b6cbd4a6c7d8d4071b.
Jenkins normal v11 script UI'dan byte normalize exact-match doğrulandı;
SCHEMA_SCOPE ilk TTBP/ikinci INNOVA_ODI, RUN_MODE ilk COMPARE, cron 08:00.
Kanıt release-proof-v11.json ve v11-normal-job-proof.json. #23 seçili TTBP
ENVIRONMENT_CHECK SUCCESS, Oracle/Git source checkout/mail0.
#24 TAMAMLANDI: yalnız PROD / TTBP, Jenkins UNSTABLE / run PARTIAL. 43.343 gözlenen
satır; 1.170 READY SQL / 368 inceleme / 2.355 engel / 966 bilgi. Kısmi envanter/DDL
ve 37.419 UNKNOWN nedeniyle kesin difference_count=null; dictionary COMPLETE.
Target error_code=null. Manifest 7.241 dosya VERIFIED; 1.170 SQL / 616.700 byte.
Plan 98b88b50c2cc256a8272c6df67947d60cf5b001b7ae4de51bdc64aace1e96571.
Run 45bd3e14-2453-4043-b856-329290b4f6a3; kaynak ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a.
#18 yakalaması yeniden kullanıldı, fresh_capture=false / source_build=18 /
Oracle connection_attempts=0 / NOT_EXECUTED. Rapor süresi 7 dk 31 sn, tüm build
8 dk 2 sn. PROD/TTBP ve gerçek COMMENT tablo/kolon etiketleri HTML/mail'de görüldü;
görünür LOCAL-ID / S_64hex bulunmadığı DOM metninden doğrulandı. Eski ve yeni
sayımın aynı kalması beklenen durum: sentetik yan kayıtlar korunur, gerçek hash
teknik nesneler policy kapsamında dışlanır. Ham inventory/scope-exclusions korunur.

#24 mail açıklamasında yerel tek seferlik helper'ın varsayılan Windows encoding
ile okunması kaynaklı mojibake görüldü; normal ürün notification helper'ı doğru
UTF-8'dir. #25 #24 doğrulanmış paketin rapor özetini yeniledi: UTF-8 note doğrulandı,
targets_equal ve bundle_manifest_unchanged=true; plan ID ve 1.170 SQL değişmedi.
comparison_rerun=false / sql_regenerated=false / database_connections=0 /
NOT_EXECUTED, credential binding yok. #25 TAMAMLANDI: 53 sn build, rapor yenileme
33 sn; Jenkins UNSTABLE / PARTIAL, yeni run 8cff1abe-997a-4c55-92f2-714b63bdcd36.
Arşiv/fingerprint ve mail yalnız onaylı tek alıcıya Jenkins logunda doğrulandı;
attachment/log yok. Son mail DOM metninde PROD/TTBP, gerçek tablo/kolonlar ve temiz
Türkçe not görüldü; görünür LOCAL-ID/S_64hex/mojibake yok. Son hedef raporu açık
bırakıldı. Kanıt ttbp-prod-final-presentation-build-25.json,
ttbp-prod-presentation-build-25.log ve ttbp-prod-mail-build-25.png (output/jenkins-setup).
Normal günlük taze source/target okuyan v11'e geri döndü ve UI exact-match/08:00
bir kez daha doğrulandı (v11-normal-job-proof-final.json). Özel kod yayını ayrıca
output/github-code-ttbp-scope-prod-publication-receipt.json ile kanıtlanır;
üretim SQL'i/raporlar/yerel sırlar bu commit/push kapsamına girmez. Sonraki bakım
adımı TTBP kısmi kaynak/parse kapsamını nesne bazında azaltmaktır. Mevcut kapsam,
etiket ve Jenkins-only rapor/DDL teslimi tamamlandı. Artifact Git push NOT_RUN.
Canlı Oracle compile/iş verisi kabulü NOT_RUN; Oracle'a DDL/DML/COMPILE uygulanmadı.

# Jenkins arşivi ve PARTIAL kaynak devamı — 20 Ekim 2026

## TTBP raporu ve DDL — 20 Ekim 2026 son çalışma

ORA-04088 bağlantı nedeni: TTBP logon guard. Oracle güvenliği değiştirilmeden,
mevcut yetkili INNOVA_ODI katalog okuyucusu kullanıldı. #18 gerçek TTBP capture:
5.321 inventory / 24.508 metadata nesnesi, CAPTURED, capability_errors ve
dictionary_errors boş, READ ONLY. Süre 33 dk 22 sn. Kaydedilen snapshot 84,82 MiB.
#18 daha sonra çevrimdışı HTML_SIZE_BUDGET_EXCEEDED nedeniyle tamamlanamadı.
#20 kayıtlı verilerle hatayı kesin ayırdı: 43.343 gözlenen fark; 1.170 READY,
368 inceleme, 2.355 engel, 966 bilgi; tüm 1.170 SQL grammar/identity kontrolünden
geçti, yalnız HTML render boyut sınırı bundle yazılmasını durdurdu. Bu sayılar
kısmi kaynak kapsamı ve UNKNOWN içerebilir; kesin toplam karşılaştırma değildir.

Düzeltmeler: planning/context.py indexed lookup ve bağlam başına lazy sequence
consumer index; object_rules.py aynı mevcut tüketici güvenlik kararını korur.
graph.py son kuyruk heap ile aynı deterministik sıra/döngü gerekçesini üretir.
reporting/render.py + report.html.j2 200 KiB sınırını artırmadan değişken sayfalama,
tek büyük kayıtta sınırlı önizleme/kalan sayısı ve tam JSON bağlantısı kullanır.
Kanonik JSON/SQL/kararlar değişmez; hiçbir işlem atılmaz. Yeni test dosyaları:
test_planning_lookup_cache.py, test_graph_queue.py, test_report_size_budget.py.
Bağımsız çapraz incelemelerde açık P1/P2 yok. Tam son test: 615 passed / 90,89 sn /
skip0; output/jenkins-setup/pytest-ttbp-report-final.xml. İlk Windows Temp koşuları
os.rename WinError5 verdi; kanıt korunup unique workspace basetemp ile tekrarlandı.
Önceki performans seti de ayrı workspace içinde 610 passed / 99,96 sn idi.

Yeni immutable v10 release SHA 53a7edc145446301c7ea5c4e7ab19818a705a5c4483c7790996129508399aca4;
wheel 7e333734e07b95f7aa60703a8d8536e297046da6b0f781e715ac1b4d18f8a0c1.
Normal günlük v10 script LF normalize edilerek birebir UI doğrulandı; cron
TZ=Europe/Istanbul / 0 8 * * *, iki parametre ve Jenkins-only/son20 politikası var.
Kanıt release-proof-v10.json ve v10-normal-job-proof.json. #21 yalnız takvim ve
parametre geri yükleme, Oracle/Git/SMTP yok. #19 tanı süreci SIGSEGV, sonuç yok;
#20 başarılı kök neden tanısı; bunlar canlı karşılaştırma başarısı sayılmaz.

#22 TAMAMLANDI: Jenkins UNSTABLE / run PARTIAL, hedef error_code ikisinde de
null. Arşivde gerçek iki plan/HTML/manifest/nesne SQL dosyaları doğrulandı.
INNOVA_ODI: 1.857 fark / 559 DDL / 56 inceleme / 4 engel; kapsam COMPLETE.
TTBP: 43.343 gözlenen satır / 1.170 DDL / 368 inceleme / 2.355 engel / 966 bilgi.
TTBP fark türleri: MISSING 2.618, CHANGED 2.617, INFORMATIONAL 689, UNKNOWN 37.419.
TTBP kapsamı PARTIAL (SOURCE_INVENTORY_PARTIAL, SOURCE_DDL_PARTIAL,
TARGET_DDL_PARTIAL); dictionary COMPLETE. UNKNOWN nedeniyle kesin toplam fark
null kalır; güvenli hazır alt küme üretilmiştir. Hedef bağlantı ERROR durumu yok.

TTBP manifesti 7.241 dosya VERIFIED, 1.170 nesne SQL toplam 616.700 byte;
ODI 1.666 dosya VERIFIED, 559 nesne SQL toplam 571.756 byte. İki target plan_id
ve snapshot SHA-256'ları output/jenkins-setup/ttbp-replay-verified-build-22.json
arşivden okunup kaydedildi. Run 710e2cee-b185-46b7-86f0-249ac5f5d83b;
source ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a. Çevrimdışı yeniden üretim
10 dk 0 sn; fresh_capture=false, source_build=18, Oracle connection attempts=0,
execution_status=NOT_EXECUTED. Normal günlük kaynak/hedefi yeniden okuyacak v10
scriptine döndü; 08:00 exact UI kanıtı var. Tüm taze kaynak+capture akışının 09:00
öncesi biteceği henüz ölçülüp garanti edilmedi; saat kendiliğinden değiştirilmez.

#22 post-action archive/fingerprint tamam; yalnız onaylı tek adrese genel HTML
mail gönderimi Jenkins logunda doğrulandı. Attachment/log yok. TTBP arşiv HTML
ve genel iki hedef raporu UI'da açıldı; sayılar, binlik ayraç, logo, kapsam ve DDL
bağlantıları görüldü. Screenshot output/jenkins-setup/ttbp-report-build-22.png.
Kanonik 73 MiB plan JSON'u tarayıcıda açmak yerine küçük replay receipt kullanılır.
Kalan kapsam eksikleri rapordadır; gerçek Oracle syntax/compile/iş verisi kabulü
NOT_RUN. Oracle DDL/DML/COMPILE NOT_RUN; gerçek DDL Git push NOT_RUN.
Kod yayını kanıtı output/github-code-ttbp-completion-publication-receipt.json
ile ayrıca tutulur; çıktı/SQL/yerel sırlar yalnız Git dışındadır.
Sonraki bakım adımı TTBP parser/kapsam eksiklerini nesne bazında azaltmaktır;
mevcut görevin TTBP rapor/DDL/Jenkins arşiv teslimi tamamlanmıştır.

TTBP ORA-04088 düzeltmesi uygulanıyor (son kullanıcı görevi): #15 salt okunur
tanı CONNECT aşamasında SYS.BLOCK_TOOLS_TTBP / ORA-00604 / ORA-20983 zincirini
gösterdi. Trigger/Oracle güvenliği değiştirilmedi. #16 mevcut INNOVA_ODI hesabında
etkin SELECT_CATALOG_ROLE, SELECT_TTBP ve katalog okuma yetkileri ile TTBP GET_DDL
erişimi doğrulandı. #17 yeni kapalı katalog okuyucusuyla READ ONLY transaction,
gerçek session identity, etkin rol, DBA_USERS owner varlığı, 5.321 nesne, 20 tam
dictionary grubu ve TABLE/PACKAGE/TRIGGER GET_DDL erişimi 13,71 sn'de doğrulandı.
ALL_OBJECTS 4.864 görünür alt küme; bu modda DBA kataloğu esas alınır.

Kod: config/models+loader ve iki targets schema dosyası optional metadata_reader
ve 30–7.200 sn bounded capture_timeout_seconds (default900) içerir. Yeni
oracle/catalog_reader.py yalnız tam eşleşen sabit metadata SELECT listesiyle
DBA görünümüne geçer; bind değerleri korunur. collector/preflight explicit
reader kimliği+rol+mevcut owner/katalog erişimini önce doğrular. Varsayılan kendi
hesabı yolu değişmez; owner remap veya boşluk varsayımı yapılmaz. Reader kanıtı
metadata_access capability/evidence kaydına girer. TTBP target credential mevcut
ODI hesabı, source TTBP metadata credential kendi hesabıdır; Pipeline'da ayrı
TTBP_TARGET_CREDENTIAL placeholder vardır. Kaynak DDL yine sabit Git SHA'sıdır.

Offline son: PYTHONPATH=src; .venv/Scripts/python.exe -m pytest -q --tb=short
--junitxml=output/jenkins-setup/pytest-catalog-owner-final.xml → 587 passed /
82,89 sn / skip0. check_contracts VERIFIED. Bağımsız review P2 (olmayan owner'ı
boş şema sanma) DBA_USERS kapalı kontrolü ve negatif testlerle kapatıldı;
son tekrar incelemede açık P1/P2 yok. Yeni wheel/release v9 hash/manifests
output/jenkins-setup/release-proof-v9.json; eski release cache'lerine yazılmadı.

Jenkins #18 v9 ile başlatıldı: #14 source snapshot dış SHA-256 + sabit Git ref
ve tüm raw input kanıtları doğrulanarak yeniden kullanılacak, hedefler fresh
okunacak. TTBP capture bütçesi gerçek 5.321 katalog nesnesi için açık 3.600 sn.
Normal günlük v9 hemen geri yüklendi: cron Europe/Istanbul 08:00, script exact,
mevcut yetkili okuyucu ve Jenkins-only arşiv açıklaması UI'dan yeniden doğrulandı.
Kanıt v9-normal-job-proof.json. Source/target READ ONLY, Oracle DDL/DML/COMPILE
NOT_RUN, gerçek SQL Git push NOT_RUN. Canlı #18 karşılaştırma henüz bitmedi.
Sonraki somut adım #18 TTBP plan/DDL/arşiv ve mail kanıtını inceleyip gerçek
gözlenen farklar/kapsam sınırlamalarını raporlamak; kodu private depoya push etmek.

Güncel takvim: kullanıcının son yanıtıyla her gün Europe/Istanbul 08:00.
Canlı Schedule ve declarative Pipeline cron birlikte güncellendi; kayıt sonrası
cron, script byte eşitliği ve açıklama UI'dan doğrulandı. Sonraki planlı başlangıç
21 Ekim 2026 08:00 Türkiye saati. Yeni build/mail/Oracle bağlantısı açılmadı.
Kanıt: output/mail-layout/schedule-0800-proof.json ve schedule-0800.png;
güncel yerel job kopyası output/jenkins-setup/Jenkinsfile.normal-v8-0800.groovy.
Bu yalnız geri alınabilir takvim değişikliği olduğundan uygulama testleri yeniden
çalıştırılmadı; son kod doğrulaması 489 passed. Aşağıdaki 08:40 kayıtları tarihseldir.
Son canlı durum önceki turda doğrulandı: #14 tamamlandı, UNSTABLE/PARTIAL;
INNOVA_ODI 1.857 fark/559 DDL; TTBP ERROR/ORA-04088, fark sayısı bilinmiyor,
TTBP plan/DDL üretilmedi. Sıradaki teknik adım TTBP okuma hatasını yalnız
salt okunur kanıtlarla teşhis etmektir; invalid nesneler bu bağlantı hatasıyla
karıştırılmaz. Çıktılar yalnız Jenkins'te, Oracle yazma NOT_RUN.

Son ek: Jenkins-only kodu normal push ile private Generator main üzerinde
97d3992e79dd67f310cf5956af40051555acaf6a olarak exact remote/API doğrulandı.
#13 source reuse REUSED_VERIFIED; ODI kaynak metadata 405 tablo eşleşti, 0 red.
TTBP kaynak metadata DPY-3015 verdi; eski Sync'in aynı hesap için kullandığı
Oracle Instant Client 19.28 Linux dosyaları salt okunur referanstan yeni v8
release'e hash/provenance ve orijinal lisansıyla kopyalandı; eski Sync değişmedi.
Jenkins runner tüm seçili hedefler explicit thick ise istemciyi ilk Oracle
bağlantısından önce bir kez yükler. Karışık mod, eksik/yüklenmeyen client ve
mode mismatch güvenli kodla durur. Thin hedeflerde native load yapılmaz.
Kaynak metadata oturumu da ilgili hedefin yapılandırılmış modunu kullanır.
DB kullanıcı/parola/verifier değişikliği ve DDL/DML yapılmadı.

Son doğrulama: 489 passed / 84,19 sn / skip 0;
output/mail-layout/pytest-jenkins-thick-final.xml. Bağımsız dar incelemede açık
P1/P2 yok. check_contracts VERIFIED; references 36 match / 7 bilinen drift /
0 missing (önceden inceleme/provenance kaydı var, yeni referans değişikliği yok).
v8 release SHA 1940221e92f8ecf74670cf64416a18d9eeb9ec64684e7afbd5c02f86ea13ad38;
aynı v7 wheel kullanılır, yalnız trusted helper/config/native client değişti.
Normal günlük v8 script kaydedildi ve birebir UI doğrulandı; publication stage
ve credential yok, 08:40 Europe/Istanbul. Kanıt jenkins-only-v8-proof.json/png.
#14 v8 COMPARE paketi yüklenip kuyruğa alındı; #13 bitmesini bekliyor.
#14 normal fresh-source akışıdır, kaynak hazırlığını yeniden yapar. #13/#14 için
canlı iki-şema tamamlandı iddiası yok; sıradaki adım gerçek iki sonuç ve son
rapor/mail/arşiv kanıtını kontrol etmektir. Çıktılar yalnız Jenkins'te kalır.

Son kullanıcı kararı önceki artifact Git yayınını iptal etti. DDL/JSON/HTML
yalnız Jenkins build artifact arşivinde tutulur; yerel artifact push yapılmaz.
Canlı Pipeline ve templates/jenkins-generator.groovy publication stage ve GitHub
credential içermez. Mail ilgili Jenkins raporuna gider. Son 20 build/artifact
saklama sınırı ve Europe/Istanbul 08:40 takvimi korunur. Kod Git push yetkisi sürer.
Önceki proxy sorusu rapor akışı için artık beklenen bir girdi değildir.

#12 hedef okumaya ulaşmadan FAILED: kaynak 9.773 nesne ile PARTIAL kaydedildi,
CLI çıkış kodu 10 runner tarafından hatalı fatal sayıldı. tools/jenkins_run.py
0/10'u kabul eder, diğer kodlarda güvenilir sonuç uydurmaz. Tek seferlik resume
önceki snapshot'ın dışarıdan sabit dosya SHA-256'sını, model semantic digest'ini,
kapalı profile/input/manifest ve tüm ham dosyaları yeni sabit Git SHA'sıyla doğrular.
Eski build'e yazılmaz; yeni build source-snapshots alanına kopyalanır. Günlük
normal akış her defasında fresh source hazırlar; otomatik cache fallback yoktur.

Yeni model/source_scope.py seçili owner için kanıtlı türetilmiş görünüm oluşturur.
Ham iki-owner PARTIAL kaydı değişmez. Atanabilen TTBP parser sorunları temiz
INNOVA_ODI kapsamını bozmaz; açıklanamayan/seçili owner eksiği PARTIAL kalır.
Güvenilir kolon metadata span'ı özgün DDL kanıtı yerine geçmez. Her hedefin kanıtı
source-scopes.json; filtrelerin kanıtı scope-exclusions.json. INVALID hedef uyarısı
genel cümle yerine gerçek nesne, tür ve parser diagnostic kodunu taşır.

Offline: PYTHONPATH=src ile .venv/Scripts/python.exe -m pytest -q --tb=short
--junitxml=output/mail-layout/pytest-jenkins-only-final.xml → 483 passed / 71,90 sn,
skip 0. Bağımsız son kod incelemesinde açık P1/P2 yok. v7 wheel/release manifest
doğrulandı; release-proof-v7.json. Jenkins #13 aynı sabit kaynak SHA'sı ve dış
snapshot hash piniyle başlatıldı; canlı sonuç henüz tamamlandı iddiası değildir.
Normal v7 job hemen geri yüklendi; exact script/cron/no-artifact-credential UI
doğrulaması output/mail-layout/jenkins-only-v7-proof.json ve jenkins-only-v7.png.
Oracle DDL/DML/COMPILE NOT_RUN; bütün oturumlar salt okunur. Sonraki somut adım:
#13 iki hedef sonucu, gerçek rapor/mail ve arşiv kanıtlarını incele; kodu private
depoya normal push et. Gerçek SQL hiçbir Git deposuna gönderilmez.

---

# SKY raporu, filtreler ve TTBP — 20 Ekim 2026 (önceki durum)

Kullanıcı kapsamı güncelledi: konu SKY; geniş Nesne / Fark sütunu (%60/12/12/16),
logo açık 156×30 (orijinal PNG byte'ları değişmez), öncelikli ilk 5 nesne,
gerçek started_at/finished_at farkından çalışma süresi. Günlük Europe/Istanbul
08:40 takvimi UI'dan doğrulandı; sonraki tetikleme 21 Ekim 08:40.

Kod private GitHub Generator deposuna normal push ile yayımlandı.
Son SKY/TTBP/filtre commit'i f4560bdcb158a7fe727febe064e04b8ad66baa65;
uzak branch SHA ve GitHub commit API yanıtı birebir doğrulandı.
Artifact deposu da private/yazılabilir doğrulandı; iki depo ayrıdır.

Jenkins #9 aynı #8 planını, yeni Oracle bağlantısı açmadan yeniden sundu.
Logo düzeltmesi var; artifact push doğrulanamadı. #10/#11 salt ortam tanıları
0 Oracle bağlantısıyla tamamlandı: agent'ta Git var, GitHub API HTTPS bağlantısı
ConnectionResetError ile kesiliyor, proxy tanımlı değil; sistem CA dosyasıyla
deneme de aynı. Credential doğrulamasına ulaşılamadı; TLS bypass yapılmadı.
Mevcut kurumsal proxy bilgisi kullanıcıya soruldu, yanıt bekleniyor. Yerel GitHub
erişimi çalışıyor; son rapor yerelden yetkili private artifact deposuna gönderilebilir.
Bu ağ durumu Oracle karşılaştırmasını engellemez; hatalı Git URL sunulmaz.

Scope: DDL Sync'in 14 teknik ad öneki iki taraf için aynı; meşru APP$TABLE ve
gerçek MATERIALIZED_VIEW_LOG korunur. GRANT politika ile kapsam dışı; S_hash bir
gerçek tablo adı değil teknik grant kimliğiydi. Verified parent ilişkisiyle
teknik nesnenin index/COMMENT/GRANT ekleri de dışlanır. Raw snapshot/UNKNOWN ve
business nesnelerin bağımlılık güvenliği korunur. scope-exclusions.json run kanıtıdır.

INNOVA_ODI + TTBP runner uygulanıp test edildi: tek source SHA, iki ayrı
source owner metadata kanıtı, iki ayrı target/credential; her oturum owner kontrolü,
salt okunur transaction, iki envanter ve rollback. Metadata yetersizliği UNKNOWN
kalır; bir target hatası diğerinin raporunu durdurmaz. Source Git DDL değişmez.

Entegre offline: 414 passed / 40,89 sn, skip 0; output/mail-layout/pytest-integrated.xml.
Bağımsız çapraz incelemede önemli açık bulgu yok. Wheel SHA
2f8b387328b54baa959e9f74035515bfb0cc94263be91a8fe62a0ef466f41ed6;
release v6 SHA 4c979ca1bc112b35e4e2a4b8f0cab76657486578c55557e4bea92044d0cfafc4.
Jenkins #12 bu release ile gerçek iki-owner salt okunur karşılaştırmasını yapıyor.
Oracle DDL/DML/COMPILE NOT_RUN. Mail yalnız mkaracan@innova.com.tr.

Değişenler: reporting/view ve email/run şablonları; aggregate build_url;
config Policy/loader + iki profile schema; compare/scope.py ve snapshots.py;
tools/jenkins_run.py, source_semantics.py, notification.py, publication.py;
Jenkins şablonu; ilgili unit testleri. Ayrıntılı Git diff mevcut. Sır, bağlantı
config'i, SQL artifact/ZIP ve .local/.env/output code Git'e girmez.

Sıradaki somut adım: #12 bitişini ve iki capture receipt'ini doğrula; filtre
sayıları/ilk5/logo/süre/SKY maili kontrol et. Son raporu private artifact deposuna
yerelden normal push ile koy; Jenkins otomatik push ağ koşulu ayrıca açık kalır.
Son code/handoff değişikliklerini private Generator repo'ya normal push et.
Referans filtresi provenance kaydı docs/YENIDEN_KULLANIM.md içine eklendi:
güncel Sync dosyası SHA'sı kaydedildi, eski lock'taki önceden mevcut drift gizlenmedi.
Referans audit sonucu 36 eşleşen / 7 önceden mevcut drift / 0 eksik.

---

# Rapor gerekçeleri ve işlem hücresi — tamamlandı, 20 Ekim 2026

Kullanıcı düzeltmesi: genel mailin nesne satırlarındaki `işlem / hedef` sayısı
kaldırıldı. Bağımlılık/ad alanı/index parent gerekçeleri şema, gerçek nesne, tür
ve eksik koşulu gösterir. Belirsiz görünürlük yokluk olarak sunulmaz; hazır
ADD_COLUMN bulunan örnekte yanlış yokluk iddiası regresyon testiyle kapatıldı.

Değişen ürün dosyaları: reporting/templates/email.html.j2,
planning/graph.py, planning/object_rules.py. CI: tools/jenkins_notification.py
(yenileme bağlam notu), tools/jenkins_report_refresh.py (tek seferlik bağlantısız
yenileme). tests/unit/test_report_reasons.py ve test_report_refresh.py eklendi;
docs/HTML_STANDARDI.md güncellendi. Karar kuralları/SQL gövdeleri değişmedi.

Doğrulama: `.venv/Scripts/python.exe -m pytest -q --junitxml=output/report-reasons/pytest-final.xml`
→ 341 passed / 31,51 sn, skip 0. Son helper düzeltmesi sonrası ilgili 9 test
4,76 sn geçti; bağımsız incelemede önemli açık bulgu yok. Ürün wheel SHA
3eab77217087a0b4e2230c258352683c027d11965db51007946ff7863742760e.

Jenkins #7, #6'nın aynı source/target snapshotlarından üretildi. Yeni Oracle
bağlantısı 0; 559 SQL gövdesi birebir aynı; farklar ve karar/bağımlılık listeleri
aynı. 2.352 fark / 559 READY / 123 REVIEW / 5 BLOCKED / 1.037 INFO; UNKNOWN 0,
kapsam COMPLETE. Önceki build ve artifact'ler korundu. Yeni plan
1cbc9648a1a3677c339d6d5dbdb68a4af2ed4e32c195d5d983c7102278162dcb;
run a5a1d580-536d-4023-b7bb-c7e857a98c35. Source SHA değişmedi.

Somut örnekler: I_ADDR_ID → INNOVA_ODI.C$_0COPY_MTS_ADDR [TABLE] kaynak/hedefte
yok; PCK_ISLEM_TIPI_AKTAR2 → INNOVA_ODI.ISLEM_HESAP_DENEME3 hedefte yok,
oluşturma işlemi yok; DENEME → hedef TABLE / kaynak FUNCTION ad alanı çakışması.
Diğer iki paket de gerçek bağımlılık adlarıyla açıklanır. Genel belirsiz cümle
güncel plan ve mailde bulunmuyor. `işlem /` satırı gerçek mailde yok.

Mail yalnız mkaracan@innova.com.tr; konu GPU | Oracle DB Migration Generator |
UNSTABLE | Build #7. Gövde doğrudan HTML, ek yok. Güncel rapor:
Jenkins #7 → artifact/output/runs/build-7/index.html (tam adres yalnız Git dışı kanıtta).
Normal Jenkins v3 akışı geri yüklendi ve UI'dan birebir doğrulandı; tek seferlik
refresh kalıcı build modu değildir. Release SHA
aacc6d65248ad0949f7d14d5cbddd40a45b367683883175969547ad6646f6bec.

Kanıt output/report-reasons/ altında console, plan özeti, mail DOM/kanıt ve
mail-body-build-7.png. Offline=PASSED; Jenkins=VERIFIED; yeni canlı Oracle
capture=NOT_RUN (önceki salt okunur snapshot kullanıldı); Oracle DDL/DML=NOT_RUN;
Git push=NOT_RUN. Açık düzeltme engeli yok; sonraki COMPARE normal salt okunur
capture yapar. Aşağıdaki #6 ve önceki kayıtlar tarihseldir.

---

# Jenkins ve genel HTML mail — tamamlandı, 20 Ekim 2026

ODMG-JENKINS-001 kuruldu ve canlı doğrulandı. Ayrı sky/oracle-db-migration-generator işi; yalnız INNOVA_ODI. Son #6 UNSTABLE: karşılaştırma tam, 2.352 fark/559READY/123REVIEW/5BLOCKED/1.037INFO; UNKNOWN0. Envanter/DDL/dictionary COMPLETE. Beş gerçek koşul DENEME ad alanı çakışması, I_ADDR_ID parent yokluğu ve PCK_COMPARE_FIELDS/PCK_ISLEM_TIPI_AKTAR2/PCK_LOG_UTIL bağımlılıklarıdır; INVALID hedef nesneler yalnız rapor uyarısıdır. BLOCKED/UNSTABLE bu gerçek plan koşullarını korur, task çalışmasını bloke etmez.

Source Git SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a. Kaynak metadata405tablo/0reject canlı eşleşti; yalnız örtük BYTE/CHAR/collation tamamlandı, Git DDL byte/hash'i değişmedi. Target ilk capture sırasında821→820nesne değiştiği için ikinci read-only capture ile tutarlı snapshot alındı. Ürün veya ajan Oracle DDL/DML uygulamadı. TTBP ve mevcut Sync işi değişmedi.

Kullanıcı talimatındaki genel mail doğrudan HTML gövdesindedir; rapor eki yok. Yalnız mkaracan@innova.com.tr adresine gönderildi. Konu GPU | Oracle DB Migration Generator | UNSTABLE | Build #6. Genel özet, sayılar, hedef ve önemli nesneler ilk bakışta görünür; ayrıntı linki gerçek build6 arşivini açtı. Repo yayını yapılmadı; olmayan repo linki sunulmadı. Gövde önizlemesi output/jenkins-mail-preview/index.html; ekran kanıtı output/jenkins-setup/mail-body-build-6.png.

Doğrulama: .venv/Scripts/python.exe -m pytest -q --junitxml=output/jenkins-setup/pytest-final.xml →332passed/35.61s/skip0. 7schema/8örnek VERIFIED. Son19CI testi ve bağımsız inceleme başarılı; rawcolumnset/duplicate ve timestamp→planid regresyonları kapalı. BootstrapPython3.10syntax geçerli; JenkinsCPython3.12.15 offlinehashlock ile kuruldu. Ürün wheelSHA97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3 değişmedi. ReleaseSHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

PlanID51f8f3c711d26d78c8ed42c3379d291edef3cfe4e4f32d64932b1f0f4f9a4146. Kanıt output/jenkins-setup/live-verification.json; job/build/report URL'leri, sayaçlar, konu/alıcı ve dosya hash'leri bu Git dışı kayıttadır. Raw source/target observations ve bağlantı yapılandırmaları normal Jenkins arşivine girmez. Otomatik tetikleme yok; manuel COMPARE çalışır, sonraki build'de release dosyası boş bırakılabilir. Yerel Git hâlâ unborn/untracked; commit/push yapılmadı. Referans36match/7öncedenmevcutdrift/0missing.

Kapanış: offline_verification=PASSED; oracle_integration=READ_ONLY_CAPTURE_VERIFIED; oracle_ddl_acceptance=NOT_RUN; jenkins_installation=INSTALLED_VERIFIED; notification=SENT_HTML_BODY_SINGLE_AUTHORIZED_RECIPIENT; external_git_publication=NOT_RUN. Aktif görev kapsamında açık kurulum engeli yok. Sonraki somut adım kullanıcı yeni hedef/otomatik tetikleme veya Git yayın kapsamı verirse ayrı değerlendirmedir; mevcut5gerçekplan koşulu silinmez. Aşağıdaki kayıtlar tarihsel aşamalardır.

---

# Jenkins kurulumu — 20 Ekim 2026

ODMG-JENKINS-001 kullanıcı talimatıyla ayrı sky/oracle-db-migration-generator Pipeline olarak kuruldu. Scope yalnız INNOVA_ODI; mevcut Sync işi değişmedi. Source/target daima READ ONLY; gerçek Oracle DDL/DML ve dış Git push NOT_RUN. Kullanıcı mail alıcısını yalnız mkaracan@innova.com.tr olarak belirledi.

Test edilmiş ürün wheel'i değişmedi. Yeni dosyalar tools/jenkins_bootstrap.py, tools/jenkins_run.py, templates/jenkins-generator.groovy, tests/unit/test_jenkins_runtime.py ve docs/JENKINS_ILK_KURULUM.md. Bootstrap resmi SHA'lı CPython3.12 arşivini ve hash kilitli offline wheel'leri iş workspace'ine kurar. Boş file parametresi retained ZIP'e gider, archive path/link/hash sınırı korunur, bytecode yazımı kapalıdır. Gzip linkleri regular dosya kopyalarıyla çözülür; kaynak/target SQL uygulanmaz. Arşiv ham observations/** içermez.

Offline: 324 passed /83.03s, skip0; output/jenkins-setup/pytest-final.xml. 7 schema/8 örnek VERIFIED. Referans audit36match/7öncedenmevcutdrift/0missing; diğer projelerde değişiklik yok. Yeni 11 Jenkins testi ve bağımsız son inceleme başarılı. Python3.10 bootstrap syntax doğrulandı. Yerel env dosyası ve output Git dışında.

Canlı: #1 resmi tar göreli link/Python3.10 filter hatası; #2 boş file parametresi; #3 yavaş gzip geri seek nedeniyle yalnız ENV aşamasında güvenle ABORTED. Düzeltmeler kırmızı→yeşil. #4 ENVIRONMENT_CHECK SUCCESS (Python3.12.15, DB bağlantısı0). #5 ardışık runtime bütünlüğü ve SKY JGit checkout başarılı, sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a; canlı karşılaştırma sürüyor.

Job/build/private release kanıtı output/jenkins-setup altında. ReleaseZIP SHA c6a17a6751ce6892ca5ed92b0c5695cf8d3834e9f941922bd39f0bd298eee589. GitHub depolarının private/boş olduğu yalnız okuma API'si ile doğrulandı; token yazdırılmadı veya Jenkins'e yeni credential kaydı eklenmedi. Otomatik tetikleme kapalı.

Sıradaki somut adım: #5 bitişini, Oracle metadata receipt'ini, arşiv raporunu ve yalnız izinli alıcıya e-postayı doğrula. Başarısızlığı gizleme; INVALID hedef nesneler rapordur. Oracle DDL kabulü daima NOT_RUN. Geniş çoklu target/TTBP/yayın ayarı bu kapsam dışındadır.

---

# Rapor/artifact güncellemesi — 20 Ekim 2026

ODMG-RPT-UPDATE-001 yerel uygulaması tamamlandı. Onaylı ZIP'in iki tasarımı gerçek
Run → Target → Plan → Object modeline bağlandı. Source ve target daima salt okunur;
bu aşamada Oracle bağlantısı dahi açılmadı. Parser/compare/karar motoru değiştirilmedi.

2.353 fark; 559 hazır DDL; 123 inceleme; 5 kaynak/sözleşme koşulu; 1.038 bilgi.
559 SQL gövdesi önceki tamamlanmış motor paketiyle byte karşılaştırmasında aynı;
yalnız plan kimliği header'ı ve dosya yolları yeni rapor build'iyle değişti.
Birleşik SQL sıra/hash kontrolü ve eski flat bundle doğrulaması başarılı.
Beş gerçek koşul yz/MOTOR_TAMAMLAMA.md içinde; rapor üretimi için engel değiller.

313 passed / 51,22 sn; skip 0. 7 şema / 8 örnek VERIFIED.
İki farklı run aynı tek immutable planı kullanıyor. 14.346 statik bağlantı doğrulandı.
En büyük HTML 115.129 byte (<200 KiB). Web/target/email 390/820/1.440 px olmak üzere
9 browser kontrolü, yatay taşma 0. Onaylı logo SHA'sı iki ZIP referansıyla birebir aynı.
Mail 5 kritik target / 10 benzersiz nesne, CID ve ayrı gömülü preview; SQL body mailde yok.
Nesne README/review kanıtları, binlik ayraçlar ve gerçek dosya yolları tamamlandı.

Arşiv sahiplik/kilit/atomik yazma/rollback/dedup ve integrity conflict kontrolleri var.
Opt-in publisher private kurum deposu, izinli host/SSH remote, storage ve push yetkisi,
literal generated pathspec, bütün payload sır taraması ve doğrulanmış sabit son SHA linki ister.
Başarısız push/404/retention/yanlış run/yanlış Jenkins build için olmayan link çizilmez.
Bağımsız incelemedeki 3 bulgu kırmızı→yeşil kapandı; yeniden incelemede yeni önemli bulgu yok.

Plan: `1c5950cc93efb9d9420bbf94743ef8e9112038bef627cdb130775d503f8e078f`
Generator: `4912b9ea900f5670551106003b9983500232a4a9ca1d8be1b9c6b7bdeed932d1`
Source SHA: `3b028ebaa8c0c0b15d3095810f6a5e4f910c939f`
Wheel SHA: `97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3`

Kanıt: output/report-update-final-verification.json. Rapor: output/report-update-final/run/index.html.
Mail: output/report-update-final/run/report-email.preview.html.
Arşiv: output/report-update-final/store/README.md; her run ayrı, plan tek kopya.
Teslim ZIP'leri: output/report-update-final-run.zip ve output/report-update-final-store.zip.
Test: output/pytest-report-update-final.xml. Patch: output/report-update-code.patch.
Reference hash değişimi 0; eski 7 drift korunuyor. Git adaylarında sır/endpoint eşleşmesi 0.
Kod repo unborn/untracked olduğu için git diff boş; önceki dosya baseline'ından patch/hash listesi üretildi.

Offline uygulama: VERIFIED. Wheel build/ayrı dizine kurulum/installed import + archive smoke: VERIFIED.
Canlı Oracle DDL/compile kabulü: NOT_RUN. Gerçek artifact push/SMTP/Jenkins: NOT_RUN.
Eski belgede adı geçen tools/check_release.py mevcut değil: NOT_AVAILABLE; uygulanmış kapı sayılmadı.
Sonraki somut iş Jenkins geçişidir: docs/JENKINS_GECIS_HAZIRLIGI.md.
Önceki backend kanıtları ve ZIP görev orijinalleri korunuyor; v1/v2 rapor çıktıları ara kanıttır,
son teslim output/report-update-final'dır. Otomatik code commit/push yapılmadı.

---

# Motor tamamlama — 20 Ekim 2026

Son motor aşaması tamamlandı. 2.353 fark; 559 READY, 123 REVIEW_REQUIRED,
5 BLOCKED, 1.038 INFORMATIONAL. Kapsam inventory/DDL/dictionary COMPLETE;
UNKNOWN 0. Eski 55 blok: 47 READY, 2 INFORMATIONAL, 1 REVIEW, 5 BLOCKED.
Sekiz RANGE/INTERVAL CREATE, ayrılan 10 constraint ve bağlı indeks/yorum SQL,
tarih function index, typed partition karşılaştırması, private/PUBLIC synonym
metadata çözümü uygulandı. Büyük DDL parser bütçesi 30/120 sn; UNKNOWN routine
metadata doğru sınıflanır. Uyumlu mevcut sequence API tüketicisi ayar incelemesine
gereksiz bağlanmaz; sequence ayarı REVIEW ve sayaç/reset yasağı aynı.

Beş gerçek koşul: DENEME FUNCTION/TABLE namespace çakışması; I_ADDR_ID için
eksik C$_0COPY_MTS_ADDR parent; PCK_COMPARE_FIELDS spec/tablo sözleşmesi incelemesi;
PCK_ISLEM_TIPI_AKTAR2 eksik relation/sequence; PCK_LOG_UTIL kaynak BIN$ dependency.
Bunlar giderilmiş gibi gösterilmedi. Tam 55 satır: yz/MOTOR_TAMAMLAMA.md.

282 passed/57,99s, skip yok; output/pytest-backend-completion-final.xml.
6 schema/7 örnek VERIFIED. Reference 36 matched/7 önceden mevcut drift/0 missing;
actual hash değişimi 0. Bağımsız inceleme ve yeni canlı capture bulguları kırmızı→yeşil
kapandı. Son inceleme sequence negatifleri/yeni sequence çakışma korumasını doğruladı.

Source/target her zaman salt okunur. Ön metadata 90 ve yeni tam target capture
954 sabit allowlist sorgusu, toplam 2 target bağlantısı. Source DB bağlantısı 0;
DDL/DML/COMPILE, iş verisi, gerçek push/SMTP/Jenkins değişikliği yok.
Target yeni capture 1.417 nesne: output/target-capture-backend-v1. Aynı raw bloblar
30/120 sn sınırlı parser ile yeniden yorumlandı: output/target-reparsed-backend-v2.
Üç VALID büyük paket COMPLETE; kalan beş target-only INVALID parse bulgusu
uyarıdır. Ham coverage PARTIAL gerçeği, karşılaştırma COMPLETE ayrımı korunur.
Source output/prepared-source-review130-v2; Git SHA ve 917 raw DDL değişmedi.

Teslim: output/backend-completion-v2 ve ZIP. 559 SQL grammar/identity/hash,
566 dosya manifest, dependency sırası, ZIP byte roundtrip, sır/endpoint scan
VERIFIED. HTML/schema 18 dosya bu aşamada değişmedi. Makbuz:
output/backend-completion-final-verification.json.
Plan ID: 75f547faa72f2f424446ba81cf9f86162fbdd405309bf99b8dd45281ec5c1bdb
Generator SHA: b602b46c62e6780a6ed2ba2e86398ccf8d925e5d11d4798f66c993fc540dcff1
ZIP SHA: aa43d0bff686ea1d6bc4d7acc2cd19ea7a01a567f93f091f107703a3f2a0b756
Wheel: output/dist-backend-completion-v2; kurulu import/hash smoke VERIFIED.
İlk no-isolation build setuptools eksikliğinden başarısızdı; isolated build başarılı.

v1 backend-completion paketi ilk capture timeoutlarından dolayı PARTIAL kapsamlı
ara adaydır; teslim değildir. v2 gerekli bloblar yeniden ayrıştırıldıktan sonra
üretilmiştir. Eski output paketleri silinmedi/üzerine yazılmadı. partial-ready.sql
tam migration veya uygulama onayı değildir; gerçek SQL uygulanmadı.

Değişen ürün dosyaları: parsing/{adapter,dependencies}.py; model/plan.py (yalnız
internal unqualified reference bilgisi); planning/{partition_rules,index_rules,policy,
table_rules,object_rules,graph}.py; oracle/{queries,reference_metadata,collector}.py.
Tests: yeni test_backend_completion.py (49 test), test_rules.py/test_blocker_audit.py
artık desteklenen partition beklentisi; test_collector.py SELECT newline uyumu.
Docs: DDL_KURALLARI.md, plan ve durum/devir/doğrulama. Referans repolar salt okunur.
Unborn repo nedeniyle git diff tek başına kanıt değildir; output altında eski
backend baseline ve final patch tutulur. Commit/push yok.

implementation_status: COMPLETE_SUPPORTED_LOCAL_SCOPE
offline_verification: VERIFIED
oracle_integration: READ_ONLY_METADATA_CAPTURED; DDL_ACCEPTANCE_NOT_RUN
jenkins_installation: NOT_RUN
artifact_publication: NOT_REQUESTED
remaining_environment_requirements: Beş kaynak/sözleşme koşulu ve 123 veri/policy
incelemesi; bunlar HTML/Jenkins kodu beklediğinden kalmıyor.

Sonraki kullanıcı görevi: Downloads/oracle-migration-yalnizca-guncelleme.zip,
SHA-256 ac8ca4161fe5f40966fac992d58188bffb7ee16c075e16f0c928b1cd244f61f6.
AKTIF_GOREV değişiklik yönergesi ve iki onaylı HTML referansı içerir; rapor/e-posta,
Run→Target→Plan→Object saklama ve immutable link/dedup güncellemesi. Mevcut
motor kapatıldıktan sonra bu görev uygulanır. Gerçek push/Jenkins için ayrıca
kullanıcı yetkisi şartı sürer. Source/target read-only tüm sonraki işlerde de bağlayıcı.

## Önceki aşamaların tarihsel kaydı

# 130 inceleme kaydı — motor çalışması, 19 Ekim 2026

Kullanıcı HTML tasarımını ayrı yürütürken motor tarafındaki 130 REVIEW_REQUIRED
kaydın tamamı incelendi. 3 READY (PCK_HYPERION BODY ve iki sequence trigger),
1 INFORMATIONAL (PK_COMPARE_FIELDS_LOG), 4 somut dependency BLOCKED,
122 REVIEW_REQUIRED. Aynı 2.353 mantıksal fark korunur. Güncel motor planı:
502 READY · 122 REVIEW · 55 BLOCKED · 1.036 INFORMATIONAL; UNKNOWN 0;
inventory/DDL/dictionary karşılaştırma kapsamı COMPLETE, plan BLOCKED.

Eski 51 blok korunur. Dört ek blok yeni fark değil, önceki genel inceleme
gerekçesinin somut dependency kanıtına dönüşmesidir: PCK_CALL_CENTER parent
partition tablo; PCK_COMPARE_FIELDS değişen spec/katalog referansları;
PCK_ISLEM_TIPI_AKTAR2 eksik ISLEM_HESAP_DENEME3/dış sequence;
PCK_LOG_UTIL recyclebin dependency. Hedef INVALID bu kararların nedeni değildir.

Source/target her zaman salt okunur. Bu tur yalnız yerel snapshot okundu;
Oracle/Jenkins bağlantısı 0, SQL NOT_EXECUTED, iş verisi/COMPILE/REPAIR yok.
HTML/CSS/renderer ve JSON schema sözleşmeleri değişmedi (18 dosya hash'i aynı).
Referans projelerde bu tur hash değişikliği 0. .local sırları Git dışında;
commit/push yok. Kullanıcının eşzamanlı HTML çalışmasına müdahale edilmedi.

## Değişen motor dosyaları

- source/sidecars.py: exporter PACKAGE/TYPE spec+body union; owner/conflict
  koruması, kanıt tekilleştirme ve mevcut DDL span sırasını koruma.
- parsing/dependencies.py ve planning/object_rules.py: EXECUTE IMMEDIATE,
  dynamic OPEN ve quoted DBMS_SQL için dependency inceleme kapısı.
- planning/backing_index.py: mevcut enabled/validated PK/UK + VALID normal
  UNIQUE index yalnız tam dictionary/AST ve kolon sırası kanıtıyla korunur.
- Yeni planning/trigger_rules.py: yeni boş tablo, NUMBER kolon ve yalnız
  sequence NEXTVAL ataması. FOLLOWS/PRECEDES ve ek etkiler kapalı.
- tests/unit/test_review130.py: 32 regresyon/sınır testi.
- yz/INCELEME_130.md: tüm 130 kararın nesne/kolon/grantee bazlı dökümü.
- yz/TEKNIK_EKSIKLER_51.md: tüm 51 engelin somut teknik işi ve dört ek kayıt.

## Doğrulama ve çıktı

`.\.venv\Scripts\python.exe -m pytest -q --tb=short --junitxml=output/pytest-review130-final.xml`
→ 233 passed / 31,59 sn; skip/failure yok. Kırmızı→yeşil kanıtları
output/pytest-review130-*.xml içinde. Bağımsız kod incelemesinin quoted
DBMS_SQL ve FOLLOWS bulguları önce 3 fail/29 pass ile üretildi, sonra kapatıldı.

`tools/check_contracts.py` → 6 schema/7 örnek VERIFIED.
`tools/verify_references.py --report output/reference-review130-final.json`
→ 36 matched/7 önceden mevcut drift/0 missing (exit 1); önceki audit69 ile
actual hash'ler birebir aynı. Bu 7 kayıt yeni hata veya bu turda değişiklik değildir.

`.\.venv\Scripts\python.exe output/verify-review130-final.py` → VERIFIED.
502 SQL grammar/nesne kimliği; tüm fark kapsama/evidence/dependency sırası;
509 bundle dosyası/hash ve ZIP byte roundtrip; sır/özel endpoint eşleşmesi 0.
233 test XML'i ve 130+51 belge satırı/linkleri kontrol edildi.

Yeni çıktı **output/backend-review130-v2** ve aynı adlı ZIP. JSON/SQL-only;
HTML render çağrılmadı. plan.json/evidence.json/objects/*.sql/partial-ready.sql
mevcut JSON sözleşmesindedir. migration.sql yok; partial-ready.sql tam migration
veya uygulama onayı değildir. 130 audit ve 51+4 teknik audit JSON pakettedir.
Makbuz: output/review130-final-verification.json.

Plan ID: 81bb901a0c8356c7125c02f80bcec474119c7195ad850231cbe6e2abba6403b9
Generator hash: 7c21ca22422d9e3845fe8fabdb133de4fe42bbf78748251ace138ab0f246a72b
ZIP SHA-256: 170e829968e43107c7e5bb2b315963c9a6f5676b990a4b33910a827439af4204

Kaynak: output/prepared-source-review130-v2/source-snapshot.json; v8'den
aynı 55 sidecar hash'iyle dependency yeniden bağlandı, 917 nesnenin raw DDL'i
birebir aynı, roundtrip doğrulandı. Git SHA değişmedi:
3b028ebaa8c0c0b15d3095810f6a5e4f910c939f.
Target: output/target-reparsed-v7/target-snapshot.json, önceki capture aynı.
Ham target DDL PARTIAL; korunan target-only INVALID parse sorunları ve uyarılar
aynı kuralla raporlanır. Bu tur canlı snapshot/capture yenilenmedi.

output/prepared-source-review130-v1 tarihsel başarısız ara denemedir;
span kanıt sırası nedeniyle yeniden yüklemeye uygun değildir, kullanılmaz.
output/backend-review130-v1 ara adayıdır; teslim v2'dir. Eski v11 HTML raporu
ve önceki output paketleri üzerine yazılmadı. Wheel bu tur yeniden üretilmedi.

## Sonraki somut adım

HTML çalışması yeni backend-review130-v2 plan/evidence/SQL verilerini mevcut
sözleşmeyle kullanabilir; v11 HTML eski 499/130/51 sayılarını taşır. UI değişimi
sonrası yeni plan üretilirse generator fingerprint ve plan ID yeniden hesaplanır;
doğrulanmış v2 paket yerinde değiştirilmez.

Motor için en yüksek etkili sonraki iş: 8 eksik partition CREATE desteği;
37 parent bağımlı yorum/indeks buna bağlı. Ayrıntılı sınırlar TEKNIK_EKSIKLER_51.md.
Grant allowlist, NUMBER/CHAR-BYTE/NOT NULL, sequence sayaç ve gerçek eksik
metadata koşulları varsayımla gevşetilmedi. Yeni ürün kapsamı eklenmedi.

Offline motor uygulama/doğrulaması: VERIFIED. Yeni canlı Oracle DDL kabulü:
NOT_RUN. TTBP geçişi/Jenkins kurulumu/yayın: NOT_RUN, sonraya bırakıldı.

## Önceki aşamaların tarihsel kaydı

# Oturum Devri — 19 Ekim 2026

Son görev: kalan 69 BLOCKED kaydı tek tek incelendi. 18 yanlış/toplu engel
kaldırıldı; 51 gerçek destek/önkoşul engeli korundu. Nesne bazlı sonuçlar
BLOK_INCELEME_69.md ve output/local-report-v11/blocker-audit69.json içindedir.
Önceki kayıttaki “69 bloğun tamamı gerçektir” değerlendirmesi düzeltildi.

Source ve target her zaman salt okunur. Bu turda Oracle/Jenkins bağlantısı
AÇILMADI; aynı source-v8/target-v7 yerel snapshot'ları kullanıldı. Gerçek SQL
uygulanmadı, iş verisi okunmadı, COMPILE/REPAIR yapılmadı. Referans projeler
ve kaynak DDL/Git geçmişi değiştirilmedi. Credentials .local altında, Git dışı;
.env.local korunuyor. Commit/push yok. Tek aktif görev AKTIF_GOREV.md.

## Güncel sonuç

- 2.353 fark; 499 READY, 130 REVIEW_REQUIRED, 51 BLOCKED, 1.035 INFORMATIONAL.
  UNKNOWN 0; karşılaştırma inventory/DDL/dictionary COMPLETE. Plan BLOCKED,
  run PARTIAL. partial-ready.sql yalnız 499 bağımsız hazır işlemi içerir.
- Eski 69 kayıttan 8'i READY, 2'si REVIEW, 7'si yalnız uyarı/bilgi oldu;
  1 tablo kolon/depolama/constraint işlemlerine ayrıldı, artık bloklu değil.
- Kalan 51: 24 yorum + 13 indeks eksik parent tabloya bağlı; 8 eksik partition
  tablo; 3 partition yerleşimi farkı; 2 indeks kuralı/eksik parent;
  1 FUNCTION/TABLE DENEME ortak ad alanı çakışması.
- CTE alias kapsamı ve DB link ayrımı; spec/body ortak dependency envanterinin
  yalnız builtin ve defaultsuz imzadan oluşan spec için sınırlandırılması;
  implicit anonymous PK/UK backing index tekilleştirmesi düzeltildi.
- Mevcut LOB depolaması uyarıya ayrıldı. Partition tablo bağımsız DEFAULT ve
  metadata ile kanıtlı widening işlemleri ayrı. Layout dönüşümü kapalı,
  partition LONG/LONG RAW ADD kapalı. Eksik source projection'ı eski AST ile
  kanıt sayılmaz; desired/actual COMPLETE + KNOWN zorunlu.
- COMMENT/normal INDEX mevcut kolon veya READY ADD_COLUMN önkoşuluna bağlanır.
  Table-only/kolon eksikliği, spec değişimi ve dış FK yapı korumaları sürüyor.
- HTML'de 2.353 biçimi kullanılır; JSON sayıları/SQL değişmez. İç parser/dedup
  açıklamaları banner'dan çıkarıldı; teknik kodlar details altında.
  INVALID ve LOB depolama bulguları görünür. Rapor tarihi capture zamanı değildir.

## Kanıt ve yeniden üretim

Source: output/prepared-source-v8/source-snapshot.json (917 kayıt, COMPLETE).
Target: output/target-reparsed-v7/target-snapshot.json (1417 kayıt, ham DDL PARTIAL).
Beş target-only INVALID parser sorunu karşılaştırmayı bloklamaz; 15 INVALID
uyarısı korunur. Target capture 17:01:57–17:14:47 UTC gözlemidir, bu tur yenilenmedi.
Source etkin BYTE/collation ek kanıtı ve değişmeyen Git SHA/DDL hash'i korunur.

201 test / 29.43s; output/pytest-audit69-delivery.xml. 14 audit regresyonu
kırmızı→yeşil ve bağımsız inceleme bulgularının sınır testleri dahil, skip yok.
check_contracts: 6 schema/7 örnek VERIFIED. Referans audit: 36 match/7 mevcut
drift/0 missing; vendor adaptasyonlarına dokunulmadı.

Güncel çıktı output/local-report-v11; v8–v10 tarihsel çıktılar, üstüne yazılmaz.
Wheel output/dist-v11; ayrı kurulu import output/wheel-smoke-v11.
Paket son bütünlük/sır/link kanıtı output/local-report-v11-verification.json
VERIFIED; güncel teslim kanıtıdır.

## Sonraki somut iş

Kalan engeller desteklenmeyen partition CREATE/layout dönüşümü, expression
index ve gerçek eksik parent/ad çakışmasıdır; yalnız etiket değiştirerek kaldırma.
130 inceleme satırı veri/default/constraint/unique koşullarını ayrı korur.
İlk INNOVA_ODI kabulü bitmeden TTBP/Jenkins/yayın kapılarına geçme.
Bu kullanıcı isteği 69 incelemesidir; mimari/kapsamı yeniden açma.

Kapanış alanları: implementation_status=IMPLEMENTED_WITH_EXPLICIT_LIMITS;
offline_verification=PASSED; oracle_integration=PREVIOUS_READ_ONLY_CAPTURE;
oracle_ddl_acceptance=NOT_RUN; jenkins_installation=DEFERRED_NOT_RUN;
artifact_publication=DISABLED_NOT_RUN. Hiçbir SQL uygulanmadı.

Goal sayacı eski BLOCKED kaydında; araç resume/active sunmuyor. İş sürdürüldü;
sayaç çalışıyor veya geniş hedef tümüyle tamamlandı iddiası yapılmadı.

Plan ID: `93664a750b696bac0024ca0ed3bb9c41e443d1bda7e7ad6cbe9781edbaf48da3`. Generator hash: `29f08bba4a9eb823b4297ab77000090e8791097b2e2abd807a51b10750c8ae30`.

## Son teslim doğrulaması

v11 paket VERIFIED: 525 bundle / 538 run dosyası;
21 HTML, en büyük 93223 byte; 945 yerel bağlantı doğrulandı,
0 kırık bağlantı, 0 gerçek sır/endpoint eşleşmesi. 187 Git adayında
0 gerçek yerel sır eşleşmesi. Kod/wheel kurulu import hash'i planla aynı.
201 passed / 29.43s; 6 schema/7 örnek VERIFIED; Oracle/Jenkins/DDL kabulü ayrımı korunur.

ZIP SHA256: `e2eaab489238433d2bed460a32bcd642ba477aa6feef5fee50a1f37ebe38879b`.
Wheel SHA256: `c0597eb640799adcff005b47a34aa5c8b9b55199b2ccf4db86ae4469cf0f41e5`.
Yerel rapor: http://127.0.0.1:8574/targets/LOCAL-ODI/index.html
69 satırlı çizelge: http://127.0.0.1:8574/blocker-audit69.html
Tarayıcıda 2.353 sayı biçimi, 499/130/51 sonuçları, yalnız somut INVALID/LOB
uyarıları ve nesne bazlı çizelge doğrulandı. Static server exec session 54719;
yalnız 127.0.0.1 rapor servisi. Eski server'lar tarihsel yerel çıktılardır.

## Jenkins #6 ve genel mail düzeltmesi — devam

Kullanıcı ilk mailin gövdede genel HTML özeti olmasını ve konu biçimini Sync örneğiyle aynı düzende istedi. Ek dosyalı ilk bildirim bu beklentiyi karşılamadığı için post adımı text/html + readFile(report-email.jenkins.html), attachmentsPattern boş olarak değişti. Konu: GPU | Oracle DB Migration Generator | DURUM | Build #N. Alıcı yalnız mkaracan@innova.com.tr. Sabit Jenkins build arşivi bağlantısı job_url+build_number tam eşleşmesiyle üretilir. Repo yayını henüz yok; olmayan repo linki çizilmez.

#5 stable target gözlemiyle plan üretti, SMTP gönderdi ve UNSTABLE bitti; 7.508 gözlenen fark/95READY/103REVIEW/2.932BLOCKED kaynak BYTE/collation eksikliği yüzündendi. Yereldeki kaynak column correspondence CI'ye eksik taşınmıştı. tools/jenkins_source_semantics.py kapalı SELECT'ler ve iki readonly transaction ile yalnız kaynak kolon metadata'sını okur. Kolon adı kümesi ve duplicate kontrolü, bütün bilinen alan eşitliği ve değişmeyen Git DDL hash'i koşuluyla yalnız eksik BYTE/CHAR/collation tamamlanır. Gözlem saati/capture hash'i run receipt; plan kanıtı zamandan bağımsız. Ham gözlem normal arşiv dışında.

Bağımsız incelemede column set fallback ve saat→plan ID bulguları kırmızı→yeşil kapandı; son19 scopedtest geçti ve açık önemli bulgu yok. Tam paket332passed/35.61s/skip0. Ürün wheel'i hâlâ aynı97d09db...; yeni CI helper'ları ayrı SHA'lı release içinde. Yeni releaseZIP SHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

#6 sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a okundu; canlı kaynak405table/0reject, source/target readonly. Şu anda target821nesne capture sürüyor. Bitişte yeni bodyHTML/mail ve targetplan kapsamı doğrulanacak; bu paragraf nihai başarı kaydı değildir.
