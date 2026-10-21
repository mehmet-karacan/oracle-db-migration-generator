## 4.645 kayıt incelemesi ve statik performans — teslim, 21 Ekim 2026

Önceki ara devirlerin yerine bu son durum esas alınır. Kaynak ve hedef salt
okunur kaldı; bu incelemede yeni Oracle bağlantısı0, SQL/DML/COMPILE0.
Yeni canlı metadata capture ve Oracle üzerinde DDL kabulü NOT_RUN; doğrulanmış
#29 metadata'sı ve sabit kaynak commit'i yeniden karşılaştırıldı.

4.645/4.645 benzersiz kayıt ID'si JSON/CSV ve47 HTML sayfada incelendi.
Eski kayıtların sonucu:4.021 kaynakta olmayan hedef nesne/alanı,489 belirsiz,
53 bilgi,80 alan eşitliği,2 doğrulanmış fark. Yeni temsil edilen4 alanla
son planda toplam493 UNKNOWN bulunuyor. Sonuçta11.066 doğrulanmış fark,
1.382 READY,657 REVIEW,139 BLOCKED; kapsam PARTIAL kalır. UNKNOWN kayıtlar
bulunan fark toplamına eklenmedi. Hedefe özgü nesneler için DROP üretilmedi.

Düzeltmeler: kapalı kaynak header/context proof1.2, ayrı ALTER/DROP/SQLPlus
birimi için fail-closed kontrol; identity BY DEFAULT/ISEQ ve FLOAT126,
8 VIEW query wrapper'ı, stored unit içindeki TRG identifier lexer çakışması,
hedef DDL/katalog identity çelişkisinin UNKNOWN kalması ve gerçek kök nedenin
bağımlı açıklamaya taşınması.6 timeout body'nin yalnız kimliği doğrulandı;
DDL/semantik bilgisi UNKNOWN kaldı. Kaynak global kapsamı COMPLETE yapılmadı.
BAREM_TANIM CREATE ve OLUSTURMA_TARIHI açıklaması dahil11 SQL hazırdır;
KULLANICI bağımlılığı olan2 foreign key ayrı gerekçeyle tutulur. İzole tablo
kanıtındaki13 READY, bütün bağımlılık grafiğinin sonucu gibi sunulmaz.

Eski489 belirsiz kaydın435'inde kaynak yokluğunu kapalı kapsamla kanıtlama
sınırı,32'sinde kaynak kolon semantiği,7'sinde eksik partition index status,
6'sında IN(WITH) grammar desteği,4'ünde nested routine analizi,3'ünde büyük
package/timeout,2'sinde çok ifadeli TYPE evolution desteği bulunur. Bunlar
tekil nedenleriyle raporlandı; başarılı veya eşit diye gizlenmedi.

Karşılaştırma Python/ANTLR ile statiktir; LLM/AI servisi çağrılmaz.
Scope parent index, metadata row index ve sidecar decode tekrarları azaltıldı.
Başarılı parser cevabı tam byte/hash/şema/flag/artifact anahtarıyla sınırlı
cache'e alınır; hata/timeout ve bozuk payload cache hit sayılmaz. Canlı Oracle
metadata'sı her koşuda yeniden okunur. Collector aşama zamanları receipt'e
ayrıldı. Mail/web süre alanı başlık altında tek kompakt kutuda gösterilir.
Windows/Linux Path sıralamasından doğan artifact fingerprint farkı2 kırmızı
testle kanıtlandı ve göreli POSIX ad sırasıyla düzeltildi; hash kontrolü atlanmadı.

Son doğrulama:
- `.venv/Scripts/python.exe -m pytest -q --junitxml=output/unknown-audit/tests-release-portable-final.xml`:886 PASS/159.92sn; skip/error/failure0.
- `tools/check_contracts.py`:7 schema/8 örnek VERIFIED; `git diff --check`0.
- Gerçek son replay toplam326.51sn; raporda clock farkı5dk23sn. Bu yalnız
  frozen metadata yeniden hesaplama süresidir. Son plan e723ce96…669d31,
 5355file bundle VERIFIED;101 HTML/2507 yerel bağlantı/0 kırık link.
- v19 wheel127 package dosyasıyla byte-eşit; Linux release SHA
  f404a21f0d9b7fe3451ebecab6f5917eb770cd6890a9d5845473cd5acadff9f6.
- Jenkins#36 bağlantısız runtime kurulumu SUCCESS. #37 frozen paket aktarımı,
  Windows/Linux Path hash sırası farkıyla güvenli biçimde durdu; bu hata
  giderilip #38 Linux üzerindeki aynı wheel+parser kimliğiyle VERIFIED oldu.
- Jenkins#38 UNSTABLE:5355 bundle dosyası,47 inceleme sayfası,CSV/JSON,
  hazır SQL ve gerekçeler arşivde. Genel HTML maili yalnız izinli alıcıya gitti.
  Yeni Oracle bağlantısı0; özgün capture#29. Gerçek canlı performans NOT_MEASURED.
- Normal v19 Pipeline hash14306490…d6019 tam geri okundu; günlük
  Europe/Istanbul08:00, varsayılanTTBP/PROD, parser cache açık, geçici
  VERIFIED_REPORT parametresi kaldırıldı. Artifact Git push kapalı.
- Kanıtlar `output/unknown-audit/`, `output/jenkins-setup/release-proof-v19.json`.
  `jenkins-38-archived-receipt.json` ve `jenkins-normal-v19-readback.json`
  gerçek Jenkins UI'den tekrar okunmuştur. SQL/ham metadata/sırlar Git'e girmez.


Değişen dosyalar: compare/projection_adapter,scope,snapshots; oracle/collector,
enrichment; parsing/adapter,client,fingerprint,grammar_compat,inventory,
projections,response_cache,worker; planning/graph,table_rules; reporting
labels/CSS/mail/run şablonları; source/sidecars; source semantics aracı;
Jenkins şablonu, ilgili regresyon testleri, HTML/Jenkins belgeleri ve devirler.

Sonraki ölçüm: normal08:00 PROD/TTBP koşusunda yeni collector fazlarını ve
ilk dolum/sıcak cache sürelerini değerlendir. Yerel frozen replay süresi75dk
canlı sürenin yeni karşılığı değildir. Kalan parser/metadata destek sınırları
kayıt bazında görünür; source/target yazma yetkisi yoktur.

## 4.645 belirsiz kayıt, BAREM ve süre incelemesi — devam, 21 Ekim 2026

Aktif kullanıcı isteği: #29 PROD/TTBP verisindeki her UNKNOWN kaydını incele,
kod hatalarını düzelt, gerçek bilgi eksikliğini koru; source/target her zaman
salt okunur. Ayrıca süre sunumu ve 75 dakikalık statik işlem iyileştiriliyor.
Bu kayıt ara devirdir; bütün işin tamamlandığı anlamına gelmez.

43 yeni payload ve 29.050 yeniden kullanılan DDL blobu SHA256 ile doğrulandı.
4645/4645 benzersiz ID çizelgesi output/unknown-audit/coverage/ altında:
3666 yerel alan yokluğuna sızan global envanter belirsizliği, 845 kaynak
nesne yokluğu kanıtsız, 89 kolon semantiği, 45 parser/metadata alanı.
Yerel _absence düzeltildi. Identity BY DEFAULT ve FLOAT126 kanonik okumaları
düzeltildi; kaynak correspondence 1235→1266 tablo, 35→4 gerçek red.
BAREM_TANIM CREATE+3constraint+9COMMENT çevrimdışı READY kanıtlandı.
Bağımlılık gerekçesi artık gerçek kolon/kök nedeni taşıyor.

İlk bütün frozen replay: UNKNOWN4645→922, READY1266→1381,
BLOCKED251→142; gerçek metadata #29 olarak kaldı, Oracle bağlantısı0.
Replay süresi239.02sn: validatedload35.48, correspondence5.66,
compare10.25, plan46.61, bundle112.43. Bu canlı75dk yerine ölçülmüş
bir süre değildir; eski metadata yeniden hesaplandı. Yeni view/header
inventory/cache iyileştirmeleri henüz bu replay sonucuna dahil değil.
İlk replay: output/unknown-audit/fixed-replay/ (5359file VERIFIED).

Süre kökeni: kaynak hazırlık/setup2224.06sn; kaynak catalog6.80sn;
correspondence/setup15.54sn; target capture+parse1913.26sn;
son karşılaştırma/plan/arşiv349.21sn. LLM/AI çağrısı yok; statik Python/ANTLR.
Scope indeks ve metadata satır indeksleri byte-eşit sonuçla iyileştirildi.
Sidecar parent index/single decode:46scopedtest PASS.
Süre alanı mevcut HTML ailesinde kompakt özet alanına taşındı.

Jenkins #32 ve #33 yalnız frozen workspace dosyalarını aktardı; SQL/Git/SMTP
ve Oracle bağlantısı0. Normal v17/08:00 pipeline her seferinde geri yüklendi.
Eksik353SQLinput blobu için ek frozen export gerekebilir. Şu anda üç alt
çalışma: guarded inventoryproof, geçerli VIEW/TRG parser uyumluluğu,
exact-byte+parser-hash bounded parser cache. Final fullsuite, bağımsız
inceleme, yeni wheel/release, Jenkins replay/arşiv/mail ve private code
push HENÜZ YAPILMADI. Sonuçlar tamamlanınca bu ara durum güncellenecek.

## Rapor süresi ve doğrulanan fark sayısı — tamamlandı, 21 Ekim 2026

Mailin ana başlığında gerçek karşılaştırma süresi dakika/saniye olarak görünür.
Son özgün #29 karşılaştırması 08:00:00–09:15:09 TSİ, 75 dk 9 sn sürdü.
Rapor yenileme süresi ayrı adla yazılır. comparison-timing.json özgün clock'u
ve source SHA'sını korur; run.json'un gerçek yenileme zamanları değişmez.
Tekrarlanan yenilemeler de eski receipt zincirinden aynı karşılaştırmayı bulur.

Fark kartındaki Bilinmiyor kaldırıldı. Güncel PROD /TTBP: 6936 doğrulanmış
bulunan fark; 4645 kayıt eksik bilgi nedeniyle karşılaştırılamadı.
Kanonik observed_differences=11581 bu iki grubun toplamıdır;
UNKNOWN kayıtlar kesin fark sayısına eklenmez. Kapsam eksikliği ve ek fark
bulunabileceği görünür. Kanonik difference_count=null değeri değiştirilmedi.
1266 hazır DDL /633 inceleme /251 üretilemeyen DDL kararları ve SQL aynıdır.

Jenkins #31 UNSTABLE /run PARTIAL tamamlandı; #29 kaydının sunumu yenilendi.
5278 değişmez dosya, 1268 SQL dosyası ve plan JSON byte-eşit doğrulandı.
Plan ID: 3c9d1c8a19dfa6f6b9fcf5b08e93fd658c7188fddfa70394fc26c569e2e60804.
Yeni Oracle bağlantısı0, yeni karşılaştırma0, SQL NOT_EXECUTED.
Güncel genel mail yalnız yetkili tek alıcıya gönderildi. Normal v17 günlük
pipeline geri yüklendi; TTBP varsayılanı /INNOVA_ODI manuel /her gün08:00
Europe/Istanbul /Jenkins-only artifact /Git artifact push yok, readback doğrulandı.

Offline: 742 passed /85.193 sn /skip0; tek tam koşu yeşil.
Kanıt: output/plain-report-tests-final.xml. 7 schema /8 example VERIFIED.
Süre ayrımı, kısmi hedefte kesin/UNKNOWN sayımı, sonuç alınamayan hedefte sıfır
uydurulmaması, aynı clock'un zincirde korunması ve değişmez SQL test edildi.
Değişen ek dosyalar: reporting/formatting.py, view.py, üç HTML şablonu,
runtime/aggregate.py, tools/jenkins_notification.py, jenkins_report_presentation.py;
test_report_counts_timing.py ve ilgili eski sunum beklentileri güncellendi.

Release v17 SHA: 27e7571c802aad89c04f7c2b117c5e2d7327a47c4083a728170fac0dc831ac71.
Wheel SHA: 0b0a78c976930d72ee109d7a12ecbdf9889a3fcf37904777fe57dd156717a02c; 125 paket dosyası byte-eşit doğrulandı.
Kanıtlar: output/jenkins-setup/plain-report-build-31-proof.json,
v17-normal-job-proof.json ve plain-report-build-31.png. Kurumsal çıktılar Git dışıdır.
Yeni canlı Oracle kabulü NOT_RUN; mevcut #29 salt okunur karşılaştırma verisi kullanıldı.
Açık sunum engeli yok. Sonraki somut adım: günlük08:00 TTBP koşusu yeni raporu üretir;
uygulama kodu yalnız yetkili private depoya yayımlanır, SQL/JSON/HTML Jenkins'te kalır.

## Anlaşılır rapor durumları — 21 Ekim 2026

Genel mail/web özetindeki BLOCKED, [TABLE], COMMENT ve ham işlem kodları Türkçe
sunum etiketlerine çevrildi. Hazır ve üretilemeyen işlemler birlikteyse hedef
"DDL kısmen hazır", ilgili kayıt "DDL üretilemedi" gösterir. Kısa, kanıtlı
nedenler her kaydın altında küçük yazıyla yer alır; mailde dört sütun genişliğini
kullanır. Tekrarlanan bağlı nesne gerekçeleri birleştirilir. UNKNOWN yokluk diye
sunulmaz; ham teknik gerekçe açılır bölümde ve kanonik JSON'da kalır.

Değişen ürün: reporting/labels.py, view.py, render.py ve üç HTML şablonu.
Yeni tools/jenkins_report_presentation.py doğrulanmış eski arşivden HTML yeniler;
plan JSON/SQL byte'ları aynen korunur, manifest ve paket yeniden doğrulanır.
Yeni paket yalnız doğrulama bitince atomik olarak görünür olur.

Offline: `.venv/Scripts/python.exe -m pytest -q --tb=short
--junitxml=output/plain-report-tests.xml`: 736 passed /88,49 sn /skip0.
`tools/check_contracts.py`: 7 schema /8 example VERIFIED. Kayıtlı 251 üretim
engelinin özeti ve 59 HTML sayfası doğrulandı; teknik durum tokenı0, en uzun
özet240 karakter. Bundle kopyasında plan/SQL değişmezliği ve hatalı doğrulamada
yarım paket yayımlanmaması test edildi.

Jenkins v16 SHA: 7dd7ebbbc56535120e472ac0a43be4c2a8f30b7695f0a7415b9edc94205114fc.
Wheel SHA: 462eebe35c380ab4bd51e9298f4898ccc2697890fdf05c75fea757adae5acb99.
125 paket dosyası çalışma alanıyla byte-eşit; release manifest doğrulandı.
Normal v16 pipeline geri yüklendi, script birebir okunarak doğrulandı;
TTBP varsayılanı, INNOVA_ODI manuel seçimi ve Europe/Istanbul her gün08:00 korunur.
Tek mail alıcısı ve Jenkins-only DDL/JSON/HTML arşivi değişmez.

Jenkins #30 sunum yenilemesi: tamamlandı; 1.266 READY /633 REVIEW /251 BLOCKED, Oracle bağlantısı0.
Kaynak alınan çalışma #29; yeni karşılaştırma veya Oracle bağlantısı yapılmaz.
Canlı Oracle yeni kabulü: NOT_RUN. SQL/DML/COMPILE: NOT_EXECUTED.
#30 receipt, arşiv, sayılar, mail ve görsel kanıtı doğrulandı. Sonraki ek kullanıcı
düzeltmesinin süre/fark sonucu bu dosyanın başındaki #31 kaydındadır.

## TTBP 2.355 engel incelemesi — tamamlandı, 20 Ekim 2026

Eski #25 planının 2.355 BLOCKED operation ID'si kanıtıyla tam bir kez incelendi;
eksik/çift eşleme0. TABLE1.096, INDEX582, diğer677 kayıt; ilk kalan engeller de
ikinci turda tek tek doğrulandı. Eski kayıt sonuçları: 1.699 uyarı,
135 alan-fark eşitlik kanıtı, 78 READY,
191 REVIEW, 252 BLOCKED. Eski kayıtlar yeni işlemlere
bire-çok/çok-bir bağlanabilir: güncel ayrı engel 251.

Kod düzeltmeleri: hedef koruma/UNKNOWN ayrımı; dictionary kolon kaybı; constraint
gruplama; anonymous PK/UK backing index kanıtı; supplemental logging sahte kolon
ayrıştırması ve yeni SQL'de logging korunumu; anonim ALTER UNIQUE ve aynı CHECK
çokluğu; Oracle identifier case/TABLE(collection) bağımlılıkları; gerekli kolon
kanıtıyla FK/%TYPE bağlama; bağımsız default/nullability ve UNKNOWN gözlemi ayrımı.
Ham SQL, ALTER bağlamı, SHA/identity/kanıt ve global PARTIAL korunur. Kapsamlı
negatif testler gerçek key/type, eksik kolon ve metadata engellerini korudu.

Offline: 726 passed /94,69 sn /skip0; tek tam koşu yeşil.
JUnit output/ttbp-blocker-audit/pytest-v13-release.xml. check_contracts 7schema /
8example VERIFIED. Önceki ara odaklarda Windows os.rename WinError5 görüldü;
son tam koşuda tekrarlanmadı; güvenlik/antivirüs ve artifact atomikliği değişmedi.

Jenkins #28 UNSTABLE /run PARTIAL tamamlandı. 12.755 gözlenen fark,
1.265 READY SQL, 632 REVIEW, 251 BLOCKED,
3.277 INFORMATIONAL. UNKNOWN ve kapsam eksikliği nedeniyle kesin toplam
fark iddiası yok. Manifest 5.465 dosya VERIFIED;
SQL 1.265 dosya /759.226 byte. Plan 5c7527f0820f257c30504cd41a1e571e6bd01a98afd998291ecd6b676f9f6eac.

Her eski ID'nin gerekçe/alan/hash/kanıt/yeni işlem eşlemesi audit/index.html,
blocked-audit.csv ve blocked-audit.json arşivindedir. CSV UTF-8 BOM/semicolon,
HTML external CSS; evidence-inputs.zip ve audit-manifest.json kanıtları korunur.
Source #18 frozen SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a; SOURCE277logging+2context,
TARGET317logging+2context doğrulanmış offline reparse. fresh_capture=false /
Oracle connection_attempts=0 /SQL NOT_EXECUTED. Bu görev yeni canlı Oracle
kabulü değildir (NOT_RUN); DDL/DML/COMPILE/trigger/yetki/source repo yazımı yok.

v13 release 26bb1fa563e2294daf2b116d1dfcf768146bfd4284bb1ce9d3b55161c77e2cc8;
wheel 18738619ae91996f150adb983261e5a7feb8ff333f6577802847f50ff868178b.
125 package/asset dosyası workspace byte eşitliği doğrulandı. Normal v13 UI exact
match, varsayılan TTBP /manual INNOVA_ODI, COMPARE ve Europe/Istanbul08:00 doğrulandı.
Mail yalnız onaylı tek alıcı; HTML genel gövde, attachment/log yok. DDL/JSON/HTML
yalnız Jenkins; artifact Git push yok. Private uygulama kodu yayını receipt'i
output/github-code-ttbp-blocker-audit-publication-receipt.json ile ayrıca doğrulanır.

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

# Jenkins arşivi ve kaynak devamı — 20 Ekim 2026

## TTBP v10 doğrulaması — 20 Ekim 2026

- Tam offline: 615 passed / 90,89 sn / skip0; komut .venv/Scripts/python.exe
  -m pytest -q --basetemp output/pytest-ttbp-report-final-20261020-1725
  --junitxml output/jenkins-setup/pytest-ttbp-report-final.xml.
  İlk Temp WinError5 sonuçları korunur; son workspace geçişi hata/skip0.
- Yeni 6 cache/lookup testi, 17 graph queue testi, 5 HTML byte sınırı testi.
  Kararlar/tüketiciler/sıra korunur. Bağımsız son incelemelerde açık P1/P2 yok.
  check_contracts VERIFIED (7 schema / 8 example); diff --check temiz.
- #18 canlı metadata: TTBP CAPTURED, READ ONLY, 5.321 inventory / 24.508 object;
  hata grupları boş. receipt output/jenkins-setup/ttbp-capture-build-18.json.
- #20 çevrimdışı tanı 1.170 SQL sonrası yalnız HTML_SIZE_BUDGET_EXCEEDED;
  log output/jenkins-setup/ttbp-offline-diagnostic-build-20.log. Snapshot tekrar
  okuma kaydedilmiş dosyalardan, Oracle bağlantısı yok. #19 tanı SIGSEGV başarılı
  sayılmaz. #21 yalnız parametre/takvim hazırlığı; DB/Git/SMTP yok.
- v10 release ve wheel exact hash'leri release-proof-v10.json içinde. Günlük
  script LF exact, cron 08:00, RUN_MODE/GENERATOR_RELEASE mevcut; UI kanıtı
  v10-normal-job-proof.json. Artifact Git yayını yok; son20 Jenkins arşivi.
- #22 arşivden VERIFIED: INNOVA_ODI559 SQL/571.756byte/1.666 dosya;
  TTBP1.170 SQL/616.700byte/7.241 dosya. İki target error_code null.
  TTBP counts43.343/1.170/368/2.355, UNKNOWN37.419; kısmi kapsamı korunur,
  kesin toplam fark null. run PARTIAL / Jenkins UNSTABLE; süre10dk0sn.
  fresh_capture=false, source_build18, Oracle connection attempts0,
  execution_status NOT_EXECUTED. Archive/fingerprint ve tek alıcı mail logda.
  Kanıt ttbp-replay-verified-build-22.json, final-run-build-22.json,
  ttbp-final-build-22.log ve ttbp-report-build-22.png. Genel/TTBP HTML UI'da açıldı.
  Oracle syntax/compile/iş verisi kabulü NOT_RUN; gerçek SQL Git push NOT_RUN.

- TTBP catalogreader final offline: 587 passed / 82,89 sn / skip0;
  output/jenkins-setup/pytest-catalog-owner-final.xml. check_contracts VERIFIED.
  Bağımsız P2 owner-existence düzeltildi; son incelemede açık P1/P2 yok.
- #15: CONNECT hata zinciri ORA-04088/00604/20983/06512; guard nesnesi tanılandı.
  #16: mevcut ODI account katalog rolü ve TTBP DDL okuma yetkisi doğrulandı.
- #17: READ ONLY transaction, doğru reader/rol/owner varlığı; 5.321 DBA envanteri,
  20 dictionary grubu, örnek TABLE/PACKAGE/TRIGGER DDL erişimi başarılı. Gerçek
  işletme satırı okuması veya Oracle DDL/DML yok. Kanıt dosyası
  output/jenkins-setup/ttbp-catalog-readonly-proof.json.
- v9 wheel 66d4cac0fac63bf2ed509fb2514fdddcc4e3328ffe73d17d67d1da8776fe5a9a;
  release fcef0159b2287b34d7cd1f7ccf9601c762eae4a24728fd41e5fc6d52fdc34d4a.
  #18 fresh target karşılaştırması başladı; sonuç henüz tamamlanmadı. Normal v9
  daily script exact ve 08:00 UI'dan doğrulandı, artifact Git aşaması yok.
- Son takvim talimatı: günlük Europe/Istanbul 08:00. Canlı Schedule ile script
  trigger aynı; Save sonrası yeniden açılan formda exact script ve açıklama
  doğrulandı. Kanıt output/mail-layout/schedule-0800-proof.json/png.
  Yeni build/mail/Oracle bağlantısı 0; uygulama kodu değişmedi, test NOT_RUN.
  Sonraki planlı tetikleme 21 Ekim 2026 08:00 Türkiye saati.
- Son driver delta sonrası: 489 passed / 84,19 sn / skip 0;
  output/mail-layout/pytest-jenkins-thick-final.xml. Son bağımsız inceleme P1/P2 yok.
  check_contracts VERIFIED; refs 36 matched / 7 bilinen drift / 0 missing.
- #13 gerçek source reuse REUSED_VERIFIED; ODI source 405 matched / 0 rejected;
  TTBP source bağlantısı DPY-3015. Veri tabanına yazmadan mevcut Sync istemcisiyle
  explicit thick yapılandırıldı. Native client kanıtı yeni v8 release manifestinde.
- v8 SHA 1940221e92f8ecf74670cf64416a18d9eeb9ec64684e7afbd5c02f86ea13ad38;
  normal job script exact, 08:40, artifact credential/stage yok. #14 upload ve queue
  UI'da görüldü; #13 tamamlanmasını bekliyor. Live iki owner henüz tamamlanmadı.
- Private code 97d3992e79dd67f310cf5956af40051555acaf6a exact remote/API doğrulandı;
  gerçek DDL Git yayını yapılmadı.
- Offline: PYTHONPATH=src; .venv/Scripts/python.exe -m pytest -q --tb=short
  --junitxml=output/mail-layout/pytest-jenkins-only-final.xml → 483 passed / 71,90 sn,
  skip 0. Son bağımsız incelemede açık P1/P2 yok.
- Artifact Git stage/credential hem canlı job hem şablondan kaldırıldı. Yeni v7
  release config storage_approved=false, push_authorized=false. Yerel artifact
  yayın helper'ı kaldırıldı; hiç çalıştırılmadı. DDL Git push NOT_RUN.
- UI proof: output/mail-layout/jenkins-only-v7-proof.json; script birebir,
  artifact credential yok, cron TZ=Europe/Istanbul ve 40 8 * * *.
- #12: SOURCE PREPARED/PARTIAL; CLI exit10 bug nedeniyle FAILED, target NOT_RUN.
  Snapshot 69.918.714 byte; dışarıdan SHA-256 ve model digest doğrulandı.
- Red→green: partial kaynak devamı, eski snapshot bütünlüğü/tamper/yanlış profile,
  manifest/commit/path/pin reddi, owner scope kanıtı ve gerçek metadata reconcile,
  diğer-owner partial izolasyonu, somut INVALID diagnostics, Jenkins-only stage.
- v7 wheel b31ede6f59a98a126adf4a423ab5239aab9560103a1482fb18f0ce0953acc784;
  release 011e3987880b13a476dbe1bffdd6dbd61c96c4f8e0946563222cdfc345a050ad.
- #13 hash-pinli devam başlatıldı; normal v7 günlük akış geri yüklendi.
  İki hedef canlı sonucu henüz tamamlanmış sayılmaz. Oracle DDL/DML/COMPILE NOT_RUN.

---

# SKY, teknik nesne filtreleri ve TTBP — 20 Ekim 2026 (önceki durum)

- Entegre offline: `.venv/Scripts/python.exe -m pytest -q --tb=short --junitxml=output/mail-layout/pytest-integrated.xml`
  → 414 passed / 40,89 sn / skip 0. Bağımsız çapraz incelemede önemli açık bulgu yok.
- Kod yayını: private Generator deposu; normal push sonrası uzak main ve commit
  API SHA'sı f4560bdcb158a7fe727febe064e04b8ad66baa65 olarak doğrulandı.
  Sırlar, bağlantılar, output/.local/.env/reference-ui ve gerçek SQL kod Git'inde yok.
- Genel mail: %60 Nesne/Fark sütunu, açık 156×30 logo; orijinal PNG değişmedi.
  SKY konu, gerçek çalışma süresi, mevcut önceliğe göre ilk 5 nesne.
- Filtreler: 14 Sync teknik öneki; kaynak/hedef simetrik; GRANT opt-in dışlama.
  Meşru `$` isimleri ve gerçek MATERIALIZED_VIEW_LOG için regresyon kanıtı var.
  Ham snapshot, UNKNOWN ve gerçek bağımlılık engelleri korunur.
- Günlük Europe/Istanbul 08:40 takvimi kaydedilmiş Jenkins formunda doğrulandı.
  Sonraki tetikleme 21 Ekim 08:40. İki şemalı toplam süre henüz ölçülüyor.
- Jenkins #12: v6 release ile INNOVA_ODI + TTBP gerçek salt okunur capture sürüyor;
  canlı sonuç henüz tamamlandı sayılmaz. Source SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a.
- #10/#11 ortam tanısı: Oracle bağlantısı 0; Git var; GitHub HTTPS bağlantısı
  ConnectionResetError, sistem CA ile aynı; proxy yok. Otomatik artifact push
  doğrulanamadı. Yerel artifact push son raporla yapılacak; kaynak Git değişmez.
- Oracle DDL/DML/COMPILE: NOT_RUN. Mail yalnız izinli tek alıcı.
- Kanıt: output/mail-layout/pytest-integrated.xml, measurement-desktop.json,
  logo-fixed.png, columns-fixed.png, schedule-0840.png; output/jenkins-setup/release-proof-v6.json.

---

# Rapor gerekçeleri — 20 Ekim 2026

- Offline: `.venv/Scripts/python.exe -m pytest -q --junitxml=output/report-reasons/pytest-final.xml`
  → 341 passed / 31,51 sn / skip 0. Son helper değişikliği sonrası ilgili 9 test → 4,76 sn.
- İnceleme: yanıltıcı READY ADD_COLUMN açıklaması kırmızı→yeşil kapandı;
  son bağımsız incelemede önemli açık bulgu yok.
- Jenkins #7: REFRESH_VERIFIED; #6'nın doğrulanmış source/target snapshotları;
  yeni Oracle bağlantısı 0; 559 SQL gövdesi byte karşılaştırmasında aynı.
  Farklar ve karar/bağımlılıklar aynı: 2.352 / 559 READY / 123 REVIEW / 5 BLOCKED /
  1.037 INFO; UNKNOWN 0, kapsam COMPLETE. Sonuç UNSTABLE gerçek koşulları korur.
- Güncel plan ve mailde genel bağımlılık cümlesi yok; mailde `işlem /` yok.
  Beş engelin şema/nesne/tür ve koşulu browser DOM üzerinden doğrulandı.
- Mail: yalnız mkaracan@innova.com.tr; genel HTML gövde, ek yok;
  GPU | Oracle DB Migration Generator | UNSTABLE | Build #7.
  Ayrıntı linki gerçek #7 raporunu açar. Normal Jenkins v3 akışı geri yüklendi,
  kaydedilmiş script UI'dan birebir doğrulandı; refresh kalıcı mod değildir.
- Kanıt: output/report-reasons/build-7-console.txt, build-7-plan-summary.json,
  mail-proof.json, mail-preview/index.html, mail-body-build-7.png.
- Yeni Oracle capture, gerçek Oracle DDL/DML ve dış Git push: NOT_RUN.
  Önceki build/raporlar korundu. Release SHA aacc6d65248ad0949f7d14d5cbddd40a45b367683883175969547ad6646f6bec.

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

# 69 blok incelemesi ve rapor sunumu — 19 Ekim 2026

- Eski 69 işlemin tümü fark/kanıt kimlikleriyle ayrı ayrı incelendi. 18 engel
  kaldırıldı, 51 korundu; detay BLOK_INCELEME_69.md ve v11 audit JSON/HTML.
- Önce 7 kırmızı test; spec scope, DB link, partition LONG/LONG RAW, aynı
  plandaki ADD_COLUMN bağımlılığı, mevcut relation şekli, stale projection ve
  sunum sınırları için ek kırmızı testlerden sonra düzeltmeler uygulandı.
- Son tam kapı: 201 passed / 29.43s, 0 skip/failure;
  output/pytest-audit69-delivery.xml. 14 audit testi dahil.
- Contract: 6 schema/7 örnek VERIFIED. Referans: 36 match/7 mevcut drift/0 missing.
- v11: 499 READY, 130 REVIEW, 51 BLOCKED, 1.035 INFORMATIONAL; 2.353 fark,
  0 UNKNOWN; kapsam COMPLETE. SQL NOT_EXECUTED, Oracle/Jenkins yeni bağlantı 0.
- Source/target geçmiş snapshot'ları değişmedi; v8–v10 çıktılarına yazılmadı.
- Final paket/link/sır/wheel doğrulama makbuzu: output/local-report-v11-verification.json.

# INVALID warning-only kuralı ve v8 paket — 19 Ekim 2026

- Kullanıcı kuralı uygulandı: hedef INVALID tek başına genel/bağımlılık engeli
  değildir. 15 INVALID ve 5 korunacak target-only parser sorunu uyarı kaldı.
- Ham target DDL coverage PARTIAL korunur; gerekli karşılaştırma kapsamı COMPLETE,
  difference_count=2353. Eksik gerekli metadata ve yapısal guard'lar korunur.
- İlk 4 kırmızı regresyon sonrası uygulama; incelemede dış FK için iki ek kırmızı
  VALID/INVALID testi sonrası guard düzeltmesi. Dar/bağımsız kapı 11 passed.
- Tam kısa kapı 187 passed / 26.73s; pytest-invalid-target-final.xml; skip yok.
- v8 planı: 447 READY, 119 REVIEW, 69 BLOCKED, 1020 INFORMATIONAL. Kalan bloklar
  INVALID'den kaynaklanmaz. Oracle/Jenkins bağlantısı, DDL/DML veya push yok.
- Bundle 472/run 483 dosya; 19 HTML, max 93396 byte, 0 kırık link/sır eşleşmesi.
  Wheel/import/hash doğrulandı. Ayrıntı INVALID_HEDEF_UYGULAMA.md.

# Etkin collation ve v6 plan paketi — 19 Ekim 2026

- Kaynak metadata yeni ayrı READ ONLY transaction inventory kontrolüyle alındı;
  830 nesne ve 17456 kolon. 405 tablo/16560 kaynak kolon yine eşleşti.
- Target yalnız capability probe: compatible 19, MAX_STRING_SIZE STANDARD.
  Eski target DDL gözlemi korundu; source-v8 ve target-reparsed-v7 türetildi.
- CREATE/ADD etkin collation üretimi, UNKNOWN/unsupported kapıları ve bağımsız
  incelemedeki explicit LOB/noncharacter bypass kırmızı→yeşil doğrulandı.
- Tam kısa kapı: 176 passed / 24.80s; output/pytest-collation-final.xml.
  Dar kapı/bağımsız teyit: 19 passed. check_contracts 6 schema/7 örnek VERIFIED.
- Wheel izole build ve ayrı import/config testi geçti (dist-v6/wheel-smoke-v6).
- local-report-v6: 2353 olgu, 447 READY, 119 REVIEW, 69 BLOCKED, 1020 INFORMATIONAL;
  UNKNOWN 0. Plan BLOCKED/run PARTIAL; tam difference_count=null; NOT_EXECUTED.
- 472 bundle/482 run dosyası, 19 HTML, max 92560 byte, 0 kırık link/sır eşleşmesi.
  180 Git adayında sır eşleşmesi yok. Arşiv local-report-v6.zip doğrulandı.
- SQL uygulanmadı; TTBP/Jenkins kurulumu/yayın NOT_RUN. Ayrıntı COLLATION_UYGULAMA.md.

# Kaynak uzunluk semantiği doğrulaması — 19 Ekim 2026

- A06–A08 somut regresyon: source profili CHAR/BYTE bilirken CREATE/ADD SQL'i
  execution oturumunun varsayılanına kalıyordu. Kırmızı testlerden sonra yalnız
  ilgili tip uzunluğuna doğrulanmış token eklenir. VARCHAR2/CHAR ve kabul edilen
  VARCHAR eş adı kapsanır; source explicit BYTE/CHAR önceliği, yorumlar ve literal
  içeriği korunur. Bare CHAR/NCHAR varsayılan uzunluk 1 karşılaştırmada modellenir.
- CLOB/NCLOB collation'ı Oracle 19c'nin sabit USING_NLS_COMP kuralıyla, yalnız
  belirtilmemişken modellenir; schema default tahmini yapılmaz. Gerçek planda
  3 sahte UNKNOWN olgusu kaldırıldı. Diğer character kolonlar için kullanıcıdan
  gerçek etkin semantik veya tüm örtük kolonları kapsayan yetkili export kaydı gerekir.
- Tam kapı: `python -m pytest -q --junitxml=output/pytest-length-semantics.xml`
  → **156 passed in 19.45s**, exit 0. Son bağımsız dar inceleme **11 passed /
  3.88s**; VARCHAR alias P1 kapandı. Uzun/canlı DDL kabul testi eklenmedi.
- Contract komutu VERIFIED (6 schema/7 örnek); wheel `output/dist-v5`, ayrı import
  `output/wheel-smoke-v5` geçti. Program hash'i yeni planla aynı. 24 vendor hash
  doğrulandı; referanslar 36 match/7 mevcut drift/0 missing
  (`output/reference-check.length-semantics.json`).
- Parser/source/target extractor değişmedi: aynı prepared-source-v6 ve
  target-reparsed-v6 snapshot'ları kullanıldı. Source **917 COMPLETE** kayıt;
  target **1417**, 5 INVALID/PLS hatalı tanım PARTIAL. Bu tur yeni source/target
  bağlantısı açılmadı; mevcut snapshot'a yeni gözlem zamanı yazılmadı.
- Son paket `output/local-report-v5.zip`, giriş `output/local-report-v5/index.html`.
  Plan **BLOCKED**, koşu **PARTIAL**, **NOT_EXECUTED**. 7508 gözlenen olgu;
  **83 READY / 100 REVIEW / 2807 BLOCKED / 1014 INFO**. UNKNOWN: collation **2602**,
  length_semantics **2556**. Güvenilir toplam fark sayısı null kalır.
  Plan ID `40d0612def505007e604d083e25b5d004674314ee820b906e93ca32270a122ef`.
- **132 dosya VERIFIED**; 43 HTML, en büyük 77165 byte, 0 kırık link ve 0 source/
  target parola/endpoint eşleşmesi. Tarayıcıda son rapor doğrulandı.
  Kanıt `output/local-report-v5-verification.json`. Git aday 178 dosya tarandı;
  .local/.env.local/output tracked değil. Otomatik commit/push yok.
- Tamamlanma kanıtı yok: kaynak etkin kolon semantiği eksikliği son üç goal
  turunda art arda kaldı. Önceki ve bu tur ilerleme sağladı; güncel karşılaştırmayı
  tamamlamanın sıradaki gerekli adımı yetkili kaynak bilgisidir. Hedef INVALID
  tanımları salt okuma talimatı nedeniyle burada onarılmaz. TTBP/Jenkins/yayın/A13
  DEFERRED/NOT_RUN. Engel denetimi `output/blocker-audit.length-semantics.json`.

---

# Önceki adlandırılmış backing index doğrulaması — 19 Ekim 2026 (tarihsel)

- A06–A08 zorunlu olumlu yol: yeni boş tabloda PK/UK USING INDEX owner.name için
  kaynak AST parent/kolon/durum kanıtı; tek index CREATE, açık graph kenarı ve
  TABLE → INDEX → CONSTRAINT sırası. Eksik/yanlış/UNUSABLE/çelişkili index hazır
  constraint oluşturmaz. DEFERRABLE+unique index ve cross-owner yolları engelli.
- Inline USING INDEX, doğrulanmış grammar spanlarından ayrı key fazına taşınır;
  DEFAULT/NOT NULL/CHECK, quoted column ve anonim constraint kimliği korunur.
  Doğrudan CREATE INDEX UNUSABLE durumu da modellenir. Normal STORAGE parantezi
  function-based key sanılmaz. Önce kırmızı, sonra yeşil test kanıtları alındı.
- Bağımsız incelemeci iki P1 reproyu ve son **10 dar testi / 3.41s** doğruladı.
  Tam kapı: `python -m pytest -q --junitxml=output/pytest-backing-index.xml`
  → **145 passed in 27.29s**, exit 0. Yeni uzun/canlı DDL kabulü eklenmedi.
- Belgelenmiş A09 `tools/check_contracts.py` komutu uygulandı: **VERIFIED**,
  6 schema/7 örnek, package byte eşitliği, config semantiği, plan hash/referans ve
  örnekler arası bağlar. Schema drift ve yanlış plan core hash'i reddedilir.
- Source aynı yerel sabit Git SHA'dan yeniden hazırlandı:
  `output/prepared-source-v6`, **917 kayıt, inventory/DDL COMPLETE**. 405 tablo
  dosyasında explicit DEFAULT COLLATION/COLLATE yok; hedef semantiğinden kaynak
  değeri türetilmedi. Kaynak NLS_LENGTH_SEMANTICS/default collation bekleniyor.
- Target aynı ham capture'dan **177.64 saniyede, ağsız** yeniden yorumlandı:
  `output/target-reparsed-v6`, 1417 kayıt; 5 INVALID/PLS hatalı tanım PARTIAL.
  Önceki gerçek capture receipt zamanı/consistency kanıtı korundu.
- Son kullanıcı paketi: `output/local-report-v4.zip`; giriş
  `output/local-report-v4/index.html`. Plan **BLOCKED**, run **PARTIAL**;
  7511 gözlenen olgu, **83 READY / 100 REVIEW / 2807 BLOCKED / 1014 INFO**.
  UNKNOWN: collation 2605, length_semantics 2556. Güvenilir toplam fark null.
  Plan ID `bff4cde9ca56c2867a9f5d61e2cee95619aca6016c19c8690b1d923065081ea7`.
- `verify-bundle`: **132 dosya VERIFIED / NOT_EXECUTED**. 43 HTML, en büyük
  77165 byte; 0 kırık göreli link, 0 source/target parola/endpoint eşleşmesi.
  Tarayıcıdaki yeni rapor doğrulandı. Kanıt `output/local-report-v4-verification.json`.
- `output/dist-v4` wheel build ve `output/wheel-smoke-v4` ayrı import kontrolü
  geçti. Program hash'i planla aynı. 24 vendor hash doğrulandı. Referanslar
  36 match/7 mevcut drift/0 missing; `output/reference-check.backing-index.json`.
- Git aday **177 dosyada 0** source/target parola/endpoint eşleşmesi; yerel
  config/cache/credentials/output tracked değil. Eski projeler korunur, commit/push
  ve yeni DB bağlantısı yapılmadı. TTBP/Jenkins/yayın/A13 DEFERRED/NOT_RUN.
- Tam yerel kabul hâlâ kanıtlanmadı: kaynak semantik kaydı eksik ve target
  INVALID tanımları var. Sürekli salt okuma sınırı korunur; SQL uygulanmaz.

---

# Önceki parser/metadata doğrulaması — 19 Ekim 2026 (tarihsel)

- Kırmızı→yeşil: editionable procedure/trigger, anonim constraint koruma ve
  Oracle adlandırması sonrası NO_CHANGE, ALTER INDEX UNUSABLE, ON COMMIT REFRESH
  grant ayrımı, GLOBAL TEMPORARY, birleşik GET_DDL metadata, MAXSIZE AST scope,
  duplicate/ifade mask reddi ve CTAS veri kopyası engeli. Önceki kapsam testleri
  korunur; geniş kabul/Jenkins/DDL uygulama testi eklenmedi.
- Son kapı: `python -m pytest -q --junitxml=output/pytest-parser-metadata-final.xml`
  → **133 passed in 23.73s**, exit 0. Bağımsız incelemeci iki parser/compare
  bulgusunun ve CTAS regresyonunun kapandığını tekrar doğruladı.
- Source `output/prepared-source-v5`: **917 kayıt, inventory/DDL COMPLETE**.
  Sabit SHA ve ham blob kanıtı korundu; source deposuna yazılmadı.
- Target `output/target-reparsed-v5`: **1417 kayıt**, inventory/dictionary
  COMPLETE, DDL PARTIAL. Ham `output/target-capture-v2` yerel dosyalarından
  **176.90 saniyede, ağ bağlantısı açılmadan** yeniden yorumlandı. Capture
  başlangıç/bitiş zamanı ve consistency kanıtı değişmedi; yeni canlı capture değil.
  Recycle-bin ve USER grant kapsam dışı kayıtları kanıtla ayrıldı.
- 5 PARTIAL tanımın tamamı target dictionary'de INVALID/PLS hatalıdır.
  Toplam 15 INVALID nesne sağlık uyarısı raporda görünür; parse edilebilen
  semantic compiler hataları NO_CHANGE ile gizlenmez. Ham ALL_ERRORS metni yerine
  yalnız doğrulanmış ORA/PLS kodları uyarıya alınır.
- Son plan: `output/local-report-v3/targets/LOCAL-ODI`, **BLOCKED**.
  7511 gözlenen fark olgusu; **83 READY, 100 REVIEW, 2807 BLOCKED, 1014 INFO**.
  UNKNOWN alanlar yalnız kaynak collation (2605) ve length_semantics (2556).
  Bunlar varsayılan hedef bilgisiyle eşitlenmedi; yetkili kaynak bilgisi beklenir.
  Koşu PARTIAL, güvenilir toplam fark sayısı null, execution NOT_EXECUTED.
- Plan ID: `f4d11414e999a69a67e95c6c5144f2386d8e2a5f0aba41a4191c97a187f75168`.
  `verify-bundle`: VERIFIED, **132 dosya**. 43 HTML, en büyük 77165 byte,
  0 kırık göreli link, 0 yerel parola/endpoint eşleşmesi. Tarayıcıda görünüm kontrol
  edildi. Kanıt: `output/local-report-v3-verification.json`.
  Paket: `output/local-report-v3.zip` (sıralı dosyalar/sabit ZIP zamanı).
- Son wheel: `output/dist-v3`, log `output/build-wheel-v3.log`.
  `output/wheel-smoke-v3` ayrı import dizininden CLI config/schema/template/
  logo/lisans kontrolü geçti; program hash'i raporla aynı. İlk smoke probunda
  yanlış template/fonksiyon adı düzeltilip kontrol yeniden çalıştırıldı;
  ürün kodu hatası veya geçilmiş A13 matrisi olarak kaydedilmedi.
- 24 vendor adapted hash doğrulandı. Referanslar **36 match / 7 mevcut drift /
  0 missing**; önceki dirty dosyalar değiştirilmedi. Son rapor:
  `output/reference-check.parser-final.json`.
- Git aday 172 dosyada gerçek parola/endpoint eşleşmesi 0. `.local`, mevcut
  `.env.local`, Git cache ve output ignored/untracked. Otomatik commit/push yok.
- Kaynak ve hedefte DDL/DML/veri sorgusu/SQLPlus/DBMS_SQL/NEXTVAL çalıştırılmadı.
  TTBP, Jenkins, artifact Git publication ve A13 geniş kabul DEFERRED/NOT_RUN.

| Alan | Güncel durum |
|---|---|
| implementation_status | LOCAL_COMPARISON_AND_ARTIFACT_FLOW_IMPLEMENTED_WITH_LIMITATIONS |
| offline_verification | PASSED_133_SHORT_TESTS; WHEEL_BUILD_AND_IMPORT_PASSED |
| oracle_integration | READ_ONLY_CAPTURE_REPARSED_OFFLINE; PLAN_BLOCKED; DDL_NOT_EXECUTED |
| jenkins_installation | DEFERRED_NOT_RUN |
| artifact_publication | DISABLED_NOT_RUN |
| remaining_environment_requirements | Authoritative source length/collation semantics; target INVALID disposition before local acceptance |

---

# Önceki yerel motor doğrulaması — 19 Ekim 2026 (tarihsel)

- Kırmızı→yeşil: Git pin/blob/layout, parser/sidecar/context, collector, karşılaştırma,
  gerçek DDL kuralları, graph, bundle, HTML ve CLI testleri. Son regresyonlar:
  existing spec/view bypass, FK PK/UK önkoşulu, UDT/callable/type bağımlılıkları,
  context dönüşümünde inline constraint kaybı, sequence mevcut tüketici,
  yeni boş tablo trigger enabled durumu, private synonym, aggregate sonucu.
- Son kapı: `python -m pytest -q --junitxml=output/pytest-local-engine.xml`
  → **107 passed in 15.50s**, exit 0. Geniş kabul/Oracle DDL fixture yok.
- `pip check`: No broken requirements found. İzole wheel build başarılı;
  `output/build-wheel.log` ve `output/dist`. Wheel ayrı import dizininden
  yüklendi; CLI config, schema, HTML template, logo ve lisans dosyaları bulundu.
  Bu A13 temiz offline kurulum/platform matrisi değildir.
- Source: Git pin → self-contained output/prepared-source-v3; 912 kayıt;
  inventory COMPLETE / DDL PARTIAL, 14 dosyada parse diagnostic.
- Target: canlı salt okuma metadata capture; ilk envanter değişiminde tek
  retry, ikinci okuma tutarlı. output/target-capture-v2: 1452 kayıt;
  inventory/dictionary COMPLETE, DDL PARTIAL. READ ONLY / NOT_EXECUTED.
- Son plan: output/local-report/targets/LOCAL-ODI. **BLOCKED**;
  9043 gözlenen fark olgusu, 78 READY, 90 REVIEW, 2824 BLOCKED, 1051 INFORMATIONAL.
  Bunlar işlem sayılarıdır; tek nesne birden fazla işlem içerebilir.
  Metadata eksik olduğu için toplam güvenilir fark sayısı run.json'da null.
- `verify-bundle`: VERIFIED; 127 dosya; bütün manifest byte/hash değerleri ve
  evidence/change/condition bağlantıları doğrulandı. 43 HTML dosyası,
  en büyük 75422 byte, 0 kırık göreli link. Canlı compile yapılmadı.
  Kanıt output/local-report-verification.json. Paket output/local-report.zip.
- Aynı sentetik girdilerde byte-identical çıktı testi geçti; değiştirilmiş SQL,
  beklenmeyen bundle dosyası, secret ve run/plan status çelişkisi reddedildi.
- Kaynak/target'a DDL/DML/iş verisi sorgusu, SQLPlus/DBMS_SQL/NEXTVAL yok.
  Credential/endpoint taraması: Git aday 168 dosyada 0 eşleşme; .local, .env.local,
  cache ve output ignored/untracked. Parolalar rapor ve loga yazılmadı.
- Referanslar: 36 matched / 7 mevcut drift / 0 missing; tool exit 10.
  vendor/PROVENANCE.json içindeki 24 uyarlama dosyasının hash'i doğrulandı.
  Eski iki proje değiştirilmedi. Mevcut dirty dosyalar korundu.
- Bağımsız son kod incelemesi salt okuma sınırında ihlal bulmadı; iletilen
  önemli graph, FK, UDT/routine ve inline constraint bulguları düzeltildi,
  incelemeci dar reproları tekrar doğruladı.

| Alan | Durum |
|---|---|
| implementation_status | LOCAL_COMPARISON_AND_ARTIFACT_FLOW_IMPLEMENTED_WITH_LIMITATIONS |
| offline_verification | PASSED_107_SHORT_TESTS; WHEEL_BUILD_AND_IMPORT_PASSED |
| oracle_integration | READ_ONLY_CAPTURE_PASSED; PLAN_BLOCKED_PARTIAL_METADATA; DDL_NOT_EXECUTED |
| jenkins_installation | DEFERRED_NOT_RUN |
| artifact_publication | DISABLED_NOT_RUN |
| remaining_environment_requirements | Authoritative source length/collation semantics and object diagnostic gaps before INNOVA_ODI acceptance |

---

## Tarihsel yerel başlangıç kaydı

# Yerel başlangıç doğrulaması — 19 Ekim 2026

- Paket: ZIP içindeki PACKAGE_MANIFEST dosyalarının SHA-256 ve byte değerleri
  doğrulandı. Mevcut .gitignore birleştirildi; kullanıcı dosyaları ezilmedi.
- Kırmızı: modüller yokken ilk config/reference/preflight testleri import
  hatasıyla durdu. Sonraki güvenlik testleri eksik credential key collision,
  output sınırı ve HTTPS askpass desteğini başarısızlıkla gösterdi.
  Provider ValueError metninin sır gibi yansıtılma testi de önce başarısız oldu.
- Yeşil: `.venv/Scripts/python.exe -m pytest -q` → **36 passed in 3.39s**, exit 0. Makine kaydı: output/pytest-startup.xml.
- `pip check` → No broken requirements found. Kurulu CLI `--help` exit 0.
- Yerel validate-config: VALID, 1 target, network_accessed=false; exit 0.
- Son preflight: source/target PASSED; comparison_status NOT_RUN,
  difference_count null, execution_status NOT_EXECUTED; exit 0.
- Oracle: salt okunur transaction, identity, 14 dictionary erişim sorgusu,
  bir GET_DDL örneği ve envanter ön/son eşitliği. Tam capture/compare değildir.
- Source: HTTPS askpass, doğrulanmış TLS; sabit Git tree'de INNOVA_ODI /
  by_object / v1 doğrulandı. Ayrıntılar yalnız output/source-inspection.json.
- Referanslar: 36 matched, 7 changed, 0 missing; tool Python exit 10.
  İşlem sonunda dosya hash/Git status aynı. Kaynak repo değiştirilmedi.
- Git aday dosyaları: gerçek source URL/target host/parola taraması 0 bulgu.
  Yerel config/credentials/cache/output ignored ve tracked değil.

Kapsam durumu:

| Alan | Değer |
|---|---|
| implementation_status | LOCAL_STARTUP_READY; MIGRATION_ENGINE_NOT_IMPLEMENTED |
| offline_verification | PASSED_36_SHORT_TESTS |
| oracle_integration | READ_ONLY_PREFLIGHT_PASSED; FULL_COMPARE_NOT_RUN |
| jenkins_installation | DEFERRED_NOT_RUN |
| artifact_publication | DISABLED_NOT_RUN |
| remaining_environment_requirements | A02–A10 implementation; local INNOVA_ODI comparison before TTBP/Jenkins |

A13 geniş kabul, hash'li wheelhouse/release lock ve platform matrisi NOT_RUN.

---

## Orijinal paket hazırlık kaydı (tarihsel)

# Başlangıç Paketi Doğrulama Kaydı

Tarih: 19 Ekim 2026. Bu kayıt uygulama teslimi değil, mimari/Codex görev paketinin hazırlık kanıtıdır.

## Gerçekleştirilen Kontroller

22 mimari karar, 14 uygulama aşaması ve 76 adlandırılmış kabul senaryosu pakette tanımlıdır. Bunlar yeni üründe uygulanacak gereksinimlerdir; geçti sonucu değildir.

6 JSON Schema kontrol edildi. 7 genel sözleşme örneği + yerel kaynak profili şemalarından geçti. Service/SID çakışması, secret alanı, port sınırı, blocked SQL, unknown değer ve güvensiz yol dahil 8 negatif örnek beklenen şekilde reddedildi. Örnek before/after yönü, plan ID, source/target snapshot digest, SQL/evidence dosya özetleri, counts ve referans ID'leri kontrol edildi.

Seçilmiş mevcut Analyzer testleri yeniden çalıştırıldı: **60 passed in 2.75s**. Kapsam test_table_extraction.py, test_index_extraction.py, test_innova_rendering.py. İlk ortamın ANTLR runtime sürüm uyuşmazlığı, arşivdeki 4.13.2 wheel'inin izole dizinde kullanılmasıyla giderildi; orijinal kaynaklar değiştirilmedi. Log REFERANS_TEST_SONUCU.txt içindedir. Bu çalıştırma Python 3.13.5 üzerindedir; Python 3.12/Windows veya tüm sürüm matrisi testi değildir.

Mevcut innova-db-report/1.0 şablonu sentetik verilerle render edildi ve 1100×1000 ekranda görsel olarak incelendi. İlk render-kayıt denemesinde renderer çıktısının byte olduğu doğrulandı ve byte olarak yazıldı. Ortam tarayıcısının file URL kısıtı nedeniyle aynı üretilmiş HTML doğrudan browser page content olarak incelendi. Bu işlem yeni ürün tasarımı veya canlı Jenkins kabulü değildir.

Paket içi açık Markdown bağlantıları ve onaylı şablon/logo kopyalarının orijinal hash'leri kontrol edildi. PACKAGE_MANIFEST.json tüm teslimat dosyalarını (kendisi hariç) SHA-256/byte sayısıyla kapsar. `python verification/verify_package.py` bu bütünlüğü yeniden ölçer; uygulama kodu çalıştırmaz, ağa veya DB'ye bağlanmaz.

## Henüz Çalıştırılmayanlar

Yeni Generator kodu/build/testleri; gerçek Oracle hedefleri; kurumsal Bitbucket içeriği; kullanıcının Windows çalışma kopyaları; canlı Jenkins işi ve credential tanımları. Bu kayıt bunlar için PASSED veya production-ready sonucu üretmez. Hiçbir uzak Git deposuna commit/push yapılmadı.
# Jenkins ve kaynak kolon metadata doğrulaması — 19 Ekim 2026

- Kaynak Oracle salt okuma oturumu başarılı; 830 nesne envanteri önce/sonra
  tutarlı, 17.456 kolon metadata kaydı alındı. Target'a yeni bağlantı yok.
- 405 Git tablosunda 16.560 kolonun bilinen alanları eşleşti. 10.088 örtük
  uzunluk ve 10.379 collation tamamlandı. source-v6 korundu, source-v7 yeni.
- NUMBER kaynağa dönüşümde collation UNKNOWN regresyonu önce kırmızı, ardından
  15 karşılaştırma testi yeşil. Gerçek dönüşüm REVIEW_REQUIRED olarak korundu.
- Tam kısa kapı: 157 passed / 23.07s; output/pytest-source-metadata.xml.
  Bağımsız dar inceleme: 15 passed / 3.99s; önemli bulgu yok.
- comparison-v2: 2353 gözlenen fark, 0 UNKNOWN, PARTIAL/TARGET_DDL_PARTIAL.
  Beş hedef INVALID kısmi tanımı açık. Tam fark sayısı null; SQL uygulanmadı.
- Jenkins mevcut oturumla yalnız okundu; job/build/credential değişmedi.
  Endpoint/credentials .local içinde; git check-ignore doğrulandı.
- Yeni SQL/HTML/wheel üretimi NOT_RUN; önceki v5 paketi değiştirilmedi.
  Ayrıntı yz/KAYNAK_METADATA_DOGRULAMA.md; sonraki iş collation emission
  doğrulaması ve yeni plan paketi. Kaynak bilgisi bekleme engeli kapandı.

# DDL Sync kaynak bağlantı kontrolü — 19 Ekim 2026 (önceki aşama)

- Kullanıcı yönlendirmesiyle Sync `config/*.toml`, config loader, Jenkins
  credential eşlemesi ve IDE env referansları salt okunur incelendi.
- Sky kaynak endpoint/kullanıcı/parola değerleri repoda bulunmuyor; environment
  üzerinden Jenkins credential kayıtlarından alınıyor. İlgili değişkenler
  süreç ve kalıcı Windows User/Machine ortamlarında mevcut değil.
- Sır değerleri yazdırılmadı; referans repo değiştirilmedi. Oracle/Jenkins
  bağlantısı, DDL/DML ve yeni test çalıştırması yapılmadı. Ürün kodu değişmedi.
- Sonraki adım: kaynak Oracle bağlantısının mevcut yerel profil/dosya yolu.


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


# Jenkins kurulumu — 20 Ekim 2026

ODMG-JENKINS-001 kullanıcı talimatıyla ayrı sky/oracle-db-migration-generator Pipeline olarak kuruldu. Scope yalnız INNOVA_ODI; mevcut Sync işi değişmedi. Source/target daima READ ONLY; gerçek Oracle DDL/DML ve dış Git push NOT_RUN. Kullanıcı mail alıcısını yalnız mkaracan@innova.com.tr olarak belirledi.

Test edilmiş ürün wheel'i değişmedi. Yeni dosyalar tools/jenkins_bootstrap.py, tools/jenkins_run.py, templates/jenkins-generator.groovy, tests/unit/test_jenkins_runtime.py ve docs/JENKINS_ILK_KURULUM.md. Bootstrap resmi SHA'lı CPython3.12 arşivini ve hash kilitli offline wheel'leri iş workspace'ine kurar. Boş file parametresi retained ZIP'e gider, archive path/link/hash sınırı korunur, bytecode yazımı kapalıdır. Gzip linkleri regular dosya kopyalarıyla çözülür; kaynak/target SQL uygulanmaz. Arşiv ham observations/** içermez.

Offline: 324 passed /83.03s, skip0; output/jenkins-setup/pytest-final.xml. 7 schema/8 örnek VERIFIED. Referans audit36match/7öncedenmevcutdrift/0missing; diğer projelerde değişiklik yok. Yeni 11 Jenkins testi ve bağımsız son inceleme başarılı. Python3.10 bootstrap syntax doğrulandı. Yerel env dosyası ve output Git dışında.

Canlı: #1 resmi tar göreli link/Python3.10 filter hatası; #2 boş file parametresi; #3 yavaş gzip geri seek nedeniyle yalnız ENV aşamasında güvenle ABORTED. Düzeltmeler kırmızı→yeşil. #4 ENVIRONMENT_CHECK SUCCESS (Python3.12.15, DB bağlantısı0). #5 ardışık runtime bütünlüğü ve SKY JGit checkout başarılı, sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a; canlı karşılaştırma sürüyor.

Job/build/private release kanıtı output/jenkins-setup altında. ReleaseZIP SHA c6a17a6751ce6892ca5ed92b0c5695cf8d3834e9f941922bd39f0bd298eee589. GitHub depolarının private/boş olduğu yalnız okuma API'si ile doğrulandı; token yazdırılmadı veya Jenkins'e yeni credential kaydı eklenmedi. Otomatik tetikleme kapalı.

Sıradaki somut adım: #5 bitişini, Oracle metadata receipt'ini, arşiv raporunu ve yalnız izinli alıcıya e-postayı doğrula. Başarısızlığı gizleme; INVALID hedef nesneler rapordur. Oracle DDL kabulü daima NOT_RUN. Geniş çoklu target/TTBP/yayın ayarı bu kapsam dışındadır.

---


## Jenkins #6 ve genel mail düzeltmesi — devam

Kullanıcı ilk mailin gövdede genel HTML özeti olmasını ve konu biçimini Sync örneğiyle aynı düzende istedi. Ek dosyalı ilk bildirim bu beklentiyi karşılamadığı için post adımı text/html + readFile(report-email.jenkins.html), attachmentsPattern boş olarak değişti. Konu: GPU | Oracle DB Migration Generator | DURUM | Build #N. Alıcı yalnız mkaracan@innova.com.tr. Sabit Jenkins build arşivi bağlantısı job_url+build_number tam eşleşmesiyle üretilir. Repo yayını henüz yok; olmayan repo linki çizilmez.

#5 stable target gözlemiyle plan üretti, SMTP gönderdi ve UNSTABLE bitti; 7.508 gözlenen fark/95READY/103REVIEW/2.932BLOCKED kaynak BYTE/collation eksikliği yüzündendi. Yereldeki kaynak column correspondence CI'ye eksik taşınmıştı. tools/jenkins_source_semantics.py kapalı SELECT'ler ve iki readonly transaction ile yalnız kaynak kolon metadata'sını okur. Kolon adı kümesi ve duplicate kontrolü, bütün bilinen alan eşitliği ve değişmeyen Git DDL hash'i koşuluyla yalnız eksik BYTE/CHAR/collation tamamlanır. Gözlem saati/capture hash'i run receipt; plan kanıtı zamandan bağımsız. Ham gözlem normal arşiv dışında.

Bağımsız incelemede column set fallback ve saat→plan ID bulguları kırmızı→yeşil kapandı; son19 scopedtest geçti ve açık önemli bulgu yok. Tam paket332passed/35.61s/skip0. Ürün wheel'i hâlâ aynı97d09db...; yeni CI helper'ları ayrı SHA'lı release içinde. Yeni releaseZIP SHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

#6 sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a okundu; canlı kaynak405table/0reject, source/target readonly. Şu anda target821nesne capture sürüyor. Bitişte yeni bodyHTML/mail ve targetplan kapsamı doğrulanacak; bu paragraf nihai başarı kaydı değildir.


# Jenkins ve genel HTML mail — tamamlandı, 20 Ekim 2026

ODMG-JENKINS-001 kuruldu ve canlı doğrulandı. Ayrı sky/oracle-db-migration-generator işi; yalnız INNOVA_ODI. Son #6 UNSTABLE: karşılaştırma tam, 2.352 fark/559READY/123REVIEW/5BLOCKED/1.037INFO; UNKNOWN0. Envanter/DDL/dictionary COMPLETE. Beş gerçek koşul DENEME ad alanı çakışması, I_ADDR_ID parent yokluğu ve PCK_COMPARE_FIELDS/PCK_ISLEM_TIPI_AKTAR2/PCK_LOG_UTIL bağımlılıklarıdır; INVALID hedef nesneler yalnız rapor uyarısıdır. BLOCKED/UNSTABLE bu gerçek plan koşullarını korur, task çalışmasını bloke etmez.

Source Git SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a. Kaynak metadata405tablo/0reject canlı eşleşti; yalnız örtük BYTE/CHAR/collation tamamlandı, Git DDL byte/hash'i değişmedi. Target ilk capture sırasında821→820nesne değiştiği için ikinci read-only capture ile tutarlı snapshot alındı. Ürün veya ajan Oracle DDL/DML uygulamadı. TTBP ve mevcut Sync işi değişmedi.

Kullanıcı talimatındaki genel mail doğrudan HTML gövdesindedir; rapor eki yok. Yalnız mkaracan@innova.com.tr adresine gönderildi. Konu GPU | Oracle DB Migration Generator | UNSTABLE | Build #6. Genel özet, sayılar, hedef ve önemli nesneler ilk bakışta görünür; ayrıntı linki gerçek build6 arşivini açtı. Repo yayını yapılmadı; olmayan repo linki sunulmadı. Gövde önizlemesi output/jenkins-mail-preview/index.html; ekran kanıtı output/jenkins-setup/mail-body-build-6.png.

Doğrulama: .venv/Scripts/python.exe -m pytest -q --junitxml=output/jenkins-setup/pytest-final.xml →332passed/35.61s/skip0. 7schema/8örnek VERIFIED. Son19CI testi ve bağımsız inceleme başarılı; rawcolumnset/duplicate ve timestamp→planid regresyonları kapalı. BootstrapPython3.10syntax geçerli; JenkinsCPython3.12.15 offlinehashlock ile kuruldu. Ürün wheelSHA97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3 değişmedi. ReleaseSHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

PlanID51f8f3c711d26d78c8ed42c3379d291edef3cfe4e4f32d64932b1f0f4f9a4146. Kanıt output/jenkins-setup/live-verification.json; job/build/report URL'leri, sayaçlar, konu/alıcı ve dosya hash'leri bu Git dışı kayıttadır. Raw source/target observations ve bağlantı yapılandırmaları normal Jenkins arşivine girmez. Otomatik tetikleme yok; manuel COMPARE çalışır, sonraki build'de release dosyası boş bırakılabilir. Yerel Git hâlâ unborn/untracked; commit/push yapılmadı. Referans36match/7öncedenmevcutdrift/0missing.

Kapanış: offline_verification=PASSED; oracle_integration=READ_ONLY_CAPTURE_VERIFIED; oracle_ddl_acceptance=NOT_RUN; jenkins_installation=INSTALLED_VERIFIED; notification=SENT_HTML_BODY_SINGLE_AUTHORIZED_RECIPIENT; external_git_publication=NOT_RUN. Aktif görev kapsamında açık kurulum engeli yok. Sonraki somut adım kullanıcı yeni hedef/otomatik tetikleme veya Git yayın kapsamı verirse ayrı değerlendirmedir; mevcut5gerçekplan koşulu silinmez. Aşağıdaki kayıtlar tarihsel aşamalardır.

---

