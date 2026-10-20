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

# Jenkins arşivi — 20 Ekim 2026 güncel durum

## TTBP — 20 Ekim 2026 güncel ek

Mevcut yetkili katalog hesabıyla #18 TTBP READ ONLY capture tamamlandı:
5.321 envanter, 24.508 metadata nesnesi; dictionary/capability hata yok.
#20 çevrimdışı kesin kök neden HTML_SIZE_BUDGET_EXCEEDED; 1.170 READY SQL'in
ayrıştırması başarılıydı. HTML boyutuna göre sayfalama ve JSON tam kanıt bağlantısı
uygulandı. Aynı bağımlılık analizi ve doğrusal lookup tekrarları azaltıldı;
heap sıralaması eski sıra/engel kararlarını korur. Üç yeni test dosyası dahil
615 passed / 90,89 sn / skip0; bağımsız incelemede açık P1/P2 yok.
V10 yeni immutable release + normal günlük 08:00 exact LF/UI doğrulandı.
#22 tamamlandı: UNSTABLE/PARTIAL, iki hedefte error_code null. INNOVA_ODI
1.857 fark/559 DDL; TTBP 43.343 gözlenen satır/1.170 DDL/368 inceleme/2.355 engel.
TTBP 37.419 UNKNOWN ve kısmi kapsam nedeniyle kesin toplam null; hazır alt küme
arşivlenmiştir. TTBP 7.241 manifest dosyası, 1.170 SQL/616.700 byte VERIFIED.
Genel HTML mail yalnız tek yetkili alıcıya gönderildi; gerçek iki hedef HTML'i
arşivde açıldı. #18 yakalamalarından çevrimdışı yeniden üretim10dk0sn,
Oracle bağlantı girişimi0, SQL NOT_EXECUTED. Normal günlük08:00 v10 geri yüklü.
Oracle yazma ve DDL Git push NOT_RUN. Kalan parser/kapsam eksikleri rapordadır.
Kanıtlar ve sonraki bakım adımı DEVIR.md başındaki ek bölümde.

Son görev TTBP ORA-04088: hedefte araç bağlantısını reddeden mevcut logon trigger
tanılandı. Güvenlik/Oracle kullanıcıları değiştirilmedi. Mevcut ODI katalog okuma
yetkisiyle explicit metadata_reader desteği tamamlandı; identity+role+owner varlığı
ve tam DBA metadata erişimi kapalı sorgularla doğrulanır. 587 test passed /
82,89 sn; bağımsız review P2 kapandı, açık P1/P2 yok. #17 salt okunur canlı erişim:
5.321 katalog nesnesi, 20 dictionary grubu ve üç DDL türü başarılı. #18 v9 gerçek
karşılaştırma sürüyor; henüz TTBP plan/DDL tamamlandı iddiası yok. Günlük normal
v9 script + 08:00 exact UI doğrulandı; yalnız Jenkins arşivi, SQL uygulanmaz.
Dosya/kanıt/sonraki adım yz/DEVIR.md başındadır.

Son kullanıcı saati: her gün Europe/Istanbul 08:00 (08:40 yerine). Canlı cron,
declarative trigger ve açıklama kaydedilip yeniden okunarak doğrulandı.
Sonraki planlı başlangıç 21 Ekim 08:00. Yeni build/mail/DB bağlantısı yok.
Kanıt schedule-0800-proof.json/png; uygulama kodu değişmedi, test tekrar edilmedi.
#14 son canlı sonuç: ODI 1.857 fark/559 DDL; TTBP ERROR/ORA-04088, plan/DDL yok.
Aşağıdaki kuyruk/08:40 bilgileri önceki durumdur; ayrıntılar yz/DEVIR.md başında.

Son ek: 489 passed / 84,19 sn / skip 0; son bağımsız inceleme P1/P2 yok.
Jenkins-only uygulama kodu 97d3992e79dd67f310cf5956af40051555acaf6a normal
push ile doğrulandı. #13 kaynak snapshot'ı hash piniyle doğruladı; ODI metadata
405 tablo eşleşti. TTBP DPY-3015 için mevcut Sync Oracle Instant Client 19.28
yeni v8 release'e lisans/hash/provenance ile alındı; iki owner explicit thick.
Yeni driver helper kırmızı→yeşil 6 test; thin native load yok, mixed/error
güvenli reddedilir. Oracle yazma/verifier değişikliği yoktur. v8 normal script
Jenkins'te birebir kaydedildi; Git publication yok. #14 paket yüklendi ve #13
ardında kuyruğa girdi. Canlı karşılaştırma sonuçları halen bekleniyor.

Kullanıcı artifact Git push'unu iptal etti. DDL/JSON/HTML yalnız Jenkins build
artifact arşivinde, son 20 build/artifact saklama ayarıyla tutulur. Mail doğrudan
Jenkins raporunu açar; 08:40 Europe/Istanbul değişmedi. Kod deposu push yetkisi sürer.
Canlı job ve template publication stage/credential içermez; v7 exact UI doğrulandı.

Offline 483 passed / 71,90 sn / skip 0; bağımsız son incelemede açık P1/P2 yok.
#12 PARTIAL prepare exit10 runner hatası giderildi; ham UNKNOWN korunur.
Yeni owner scope kapalı kanıtla doğrulanır; TTBP kaynağındaki parser eksikleri
temiz ODI envanterine taşınmaz. Dış dosya hash piniyle aynı SHA snapshot resume
doğrulanır; günlük normal akış fresh source hazırlar. #13 gerçek iki hedef
salt okunur çalışma sürüyor; live henüz tamamlandı sayılmaz. Oracle DDL/DML/COMPILE
NOT_RUN. Dosya, komut, sonraki somut adım yz/DEVIR.md başındadır.

---

# SKY, süre, ilk 5 ve iki şema — 20 Ekim 2026 (önceki durum)

Offline uygulama: 414 passed / 40,89 sn; bağımsız çapraz inceleme temiz.
SKY konu, %60 Nesne/Fark sütunu, 156×30 logo, süre ve öncelikli5nesne hazır.
Sync teknik nesne filtreleri + GRANT dışlama opt-in policy ile uygulanır;
ham envanter ve UNKNOWN/bağımlılık güvenliği korunur. INNOVA_ODI+TTBP için
ayrı credential/sessionowner doğrulamalı runner ve owner bazlı source kanıtı var.
scope-exclusions.json filtre kanıtını taşır. Dosyalar ve komutlar yz/DEVIR.md başında.

GitHub code son push doğrulandı (f4560bdcb158a7fe727febe064e04b8ad66baa65);
SKY/TTBP/filtre uygulaması bu commit'te. Jenkins günlük 08:40
Europe/Istanbul doğrulandı. #12 v6 release ile canlı salt okunur iki şema koşusu
sürüyor; henüz tamamlandı iddiası yok. Gerçek Oracle DDL/DML/COMPILE NOT_RUN.
Jenkins agent GitHub HTTPS ConnectionResetError; proxy kullanıcı yanıtı bekleniyor.
Bu yalnız otomatik artifact push'u etkiler; yerel GitHub erişimi ve karşılaştırma sürer.

---

# Rapor gerekçeleri ve işlem hücresi — tamamlandı, 20 Ekim 2026

Genel mailde nesne başına `işlem / hedef` satırı kaldırıldı. planning/graph.py
ve object_rules.py gerekçeleri gerçek şema/nesne/tür, kolon ve eksik koşulla
açıklar. Karar kuralları değişmedi. email.html.j2, jenkins_notification.py,
tek seferlik jenkins_report_refresh.py, iki regresyon test dosyası ve HTML
standardı güncellendi. Ayrıntılı dosya/kanıt kaydı yz/DEVIR.md başındadır.

341 test / 31,51 sn / skip 0; son helper düzeltmesi sonrası ilgili 9 test geçti.
Bağımsız incelemede açık önemli bulgu yok. Jenkins #7 UNSTABLE: #6 snapshotları
ile aynı 2.352 fark, 559 READY, 123 REVIEW, 5 BLOCKED, 1.037 INFO, UNKNOWN 0.
559 SQL gövdesi birebir aynı; yeni Oracle bağlantısı 0. Genel belirsiz gerekçe
ve gereksiz sayı satırı gerçek plan/mailde yok. Genel HTML mail yalnız izinli
tek alıcıya gönderildi; normal Jenkins v3 Pipeline geri yüklendi ve doğrulandı.

Kanıt output/report-reasons/; release SHA aacc6d65248ad0949f7d14d5cbddd40a45b367683883175969547ad6646f6bec.
Offline=PASSED; Jenkins=VERIFIED; yeni Oracle capture=NOT_RUN; Oracle DDL/DML ve
dış Git push=NOT_RUN. Açık düzeltme engeli yok; sonraki manuel COMPARE normal
salt okunur capture yapar. Önceki immutable raporlar korunur.

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

# 69 blok incelemesi — güncel durum, 19 Ekim 2026

Önceki 69 kaydın 18 yanlış/toplu engeli kaldırıldı; 51 gerçek engel korundu.
Nesne bazlı tam çizelge: [BLOK_INCELEME_69.md](BLOK_INCELEME_69.md).
Güncel v11: 2.353 fark, 499 READY, 130 REVIEW, 51 BLOCKED, 1.035 INFORMATIONAL;
UNKNOWN 0; karşılaştırma kapsamı COMPLETE, plan BLOCKED/run PARTIAL.

201 test / 29.43s (pytest-audit69-delivery.xml); 14 audit regresyonu dahil.
6 schema/7 örnek VERIFIED. Kod, test ve HTML sunumu uygulandı; source/target
salt okunur kaldı. Yeni Oracle/Jenkins bağlantısı veya Git push yapılmadı.
Canlı DDL kabulü NOT_RUN; TTBP/Jenkins/yayın ertelendi. Ayrıntılı güncel devir
DEVIR.md içindedir. v8–v10 ara/tarihsel çıktıları korunur.

Değişen dosyalar: planning/{table_rules,object_rules,rules,graph,builder}.py;
model/plan.py (yalnız internal intent kolon kanıtı); parsing/dependencies.py;
reporting/{formatting,render}.py, templates/report.html.j2; runtime/aggregate.py;
tests/unit/test_blocker_audit.py; yz devir/durum/doğrulama/inceleme belgeleri.

## Önceki aşamaların tarihsel kaydı

# Geliştirme Durumu — 19 Ekim 2026

Güncel kullanıcı kuralı: hedef INVALID yalnız rapor uyarısıdır; onarım veya VALID
hale getirme ilk kabul koşulu değildir. Korunacak beş target-only INVALID parse
sorunu karşılaştırmayı bloklamaz. Ham target snapshot DDL PARTIAL korunurken
karşılaştırma kapsamı COMPLETE ve difference_count=2353'tür. Kalan 69 blok gerçek
bağımlılık/yapısal veya destek koşullarındandır. Ayrıntı INVALID_HEDEF_UYGULAMA.md.
Bu değişiklikte yeni Oracle/Jenkins bağlantısı açılmadı.

Yerel INNOVA_ODI → INNOVA_ODI plan/SQL/HTML akışı çalışıyor. Kaynak metadata
belirsizlikleri kapandı; güncel plan 69 güvenlik/özellik bloğu nedeniyle BLOCKED,
run PARTIAL. SQL Oracle'a uygulanmadı. TTBP ve Jenkins kurulumu sonrada.

| Alan | Durum | Güncel kanıt |
|---|---|---|
| A00 referans tabanı | DRIFT KAYITLI | 36 match/7 mevcut drift/0 missing; eski projelere yazılmadı |
| A01 config/domain | UYGULANDI | Kapalı schema, immutable kimlik/KnownValue/kanıt |
| A02 Git kaynak | UYGULANDI | Sabit SHA/blob; checkout/hook/push yok |
| A03 parser/sidecar | UYGULANDI, DESTEK SINIRLI | prepared-source-v8: 917 kayıt, inventory/DDL COMPLETE |
| Kaynak etkin kolon semantiği | DOĞRULANDI | 405 tablo/16560 kolon eşleşti; 10088 BYTE, 10379 collation tamamlandı |
| A04 target collector | UYGULANDI | READ ONLY + allowlist; opsiyonel capability hatası UNKNOWN, izin hatası boş şema değil |
| Gerçek target | DDL PARTIAL | target-reparsed-v7: 1417 kayıt; 5 INVALID/PLS hatalı kısmi tanım, toplam 15 INVALID uyarısı |
| A05 compare | UYGULANDI | before=target/after=source; 2353 olgu, 0 UNKNOWN; tam fark sayısı 2353 |
| A06–A08 SQL/graph | KAPSAMLI YEREL AKIŞ | 447 READY, 119 REVIEW, 69 BLOCKED, 1020 INFORMATIONAL |
| Etkin collation emission | OFFLINE DOĞRULANDI | CREATE/ADD, enabled/disabled/unknown; explicit LOB/noncharacter ve tablo default kapıları |
| A09 artifact | VERIFIED | 472 bundle/483 run dosyası; plan/evidence/SQL hash ve grammar |
| A10 HTML | DOĞRULANDI | 19 HTML, max 93396 byte, 0 kırık link; Innova görünümü tarayıcıda kontrol edildi |
| Kısa offline kapı | PASSED | 187 test / 26.73s; pytest-invalid-target-final.xml; skip/failure yok |
| Contract kapısı | VERIFIED | 6 schema, 7 örnek; ağsız |
| Wheel | PASSED | dist-v8, wheel-smoke-v8; kurulu kod hash'i planla aynı |
| Sır taraması | PASSED | Run dosyaları ve 184 Git adayında 0 gerçek endpoint/parola eşleşmesi |
| TTBP/Jenkins kurulumu/A13 | DEFERRED / NOT_RUN | İlk INNOVA_ODI tam kabulü kanıtlanmadı |
| Artifact publication | DISABLED / NOT_RUN | Commit/push yok |

Güncel rapor output/local-report-v8/index.html; arşiv output/local-report-v8.zip;
doğrulama output/local-report-v8-verification.json. Kaynak source-v8 ve target
reparsed-v7 kullanıldı. Target DDL eski capture-v2 gözlemidir; yalnız hedef
capability parametreleri yeni okundu. Kaynak inventory kontrolü ayrı READ ONLY
transaction'larla yenilendi. Ayrıntı COLLATION_UYGULAMA.md ve DEVIR.md.

## Açık sınırlar

49 bağımlılık, 14 kapsanmayan tablo özelliği, 4 Oracle iç nesnesi ve 2 index
tanımı bloke. Daraltma/tip değişimi, mevcut tablo constraint/data etkisi,
grants ve rutin dış bağımlılıkları otomatik READY yapılmaz. INVALID target
nesneleri salt okuma sınırında düzeltilmez. Kaynak bağlantı bilgisi beklenmiyor.

Yalnız READY alt küme partial-ready.sql içinde. Tam migration.sql yok; çıktı
çalıştırma onayı veya canlı syntax/compile testi değildir. Oracle üzerinde
DDL/DML veya iş verisi testleri NOT_RUN. TTBP/Jenkins/yayın için yeni adım yok.

| Kapanış alanı | Değer |
|---|---|
| implementation_status | LOCAL_COMPARISON_AND_ARTIFACT_FLOW_IMPLEMENTED_WITH_LIMITATIONS |
| offline_verification | PASSED_187_TESTS_CONTRACTS_WHEEL_BUNDLE |
| oracle_integration | READ_ONLY_METADATA_CAPTURED; COMPARISON_COMPLETE; INVALID_REPORTED; DDL_NOT_EXECUTED |
| jenkins_installation | DEFERRED_NOT_RUN; READ_ONLY_LOOKUP_AUTHORIZED |
| artifact_publication | DISABLED_NOT_RUN |
| remaining_environment_requirements | Dependency/unsupported-feature review; INVALID status is report-only |

Eski paket ve aşama kanıtları değiştirilmedi; DOGRULAMA_KAYDI.md tarihsel
kayıtları korur. Goal UI kaydı BLOCKED kaldı; resume aracı yokluğu kullanıcıya
bildirildi. Bu, source erişim engelinin sürdüğü veya çalışma durduğu anlamına gelmez.

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
