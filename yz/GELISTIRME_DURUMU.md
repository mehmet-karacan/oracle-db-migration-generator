## 26 Ekim 2026 - UNUSABLE indekslerin dar kapsamlı üretimi (OFFLINE_PASS)

`IX_PUSULA_01` ve `IX_PUSULA_02` için kaynak sözlüğü `UNUSABLE`, normal,
nonunique ve bölümsüz durumu doğruladı. Hedefte parent `PUSULA_OLD` yok ve
kaynakta yeni, bölümsüz heap tablo. Önce
`tests/unit/test_rules.py::test_verified_unusable_index_on_new_heap_table_keeps_source_availability`
RED oldu; `planning/object_rules.py` yalnız bu kanıt birleşiminde tek
`CREATE INDEX ... UNUSABLE` üretir. Sözlük eksikliği, yanlış durum, mevcut parent
ve yanlış ALTER hedefi REVIEW bırakır. Kaynak SQL'in diğer özellikleri yeniden
parse ile denetlenir. Kural `docs/DDL_KURALLARI.md`, sonuç ve sınır
`docs/INNOVA_ODI_KALAN_51_PLANI.md` içine işlendi.

Kayıtlı gerçek run `77f5933fa91841239ae3e892ee429277` çevrimdışı tekrar
planlandı: 1743 fark, 569 READY/SQL, 49 REVIEW, 1 BLOCKED, 610 bilgi. Önceki
567 SQL gövdesi birebir aynı, yalnız iki UNUSABLE indeks SQL'i yeni. DENEME
BLOCKED ve SQL'siz. Bundle VERIFY PASS, 1220 birim testi PASS/132.91 sn,
tek mevcut Starlette uyarısı. Özel kanıt
`.local/unusable-index-proof-current.json` kökündeki verification.json.
Oracle sorgusu/DDL/DML/COMPILE, SMTP, Jenkins ve Git push bu aşamada yapılmadı.
Dört büyük PROD taraması kullanıcı talimatıyla NOT_RUN. Sonraki adım 49 kalan
incelemenin teknik/iş sahibi kararlarını ayrı kanıtlarla değerlendirmek; yeni
canlı Oracle kabulü ayrı.

## 26 Ekim 2026 - Büyük Tarama Ertelemesi ve Küçük Dönüşüm Ölçümü

Kullanıcı, PROD üzerindeki dört büyük kolonun tam uzunluk taramasını şimdilik
erteleme seçimini yaptı. Dört kayıt NOT_RUN; örnekleme sıfır ihlal kanıtı
sayılmayacak. Diğer bağımsız işte VA_DIAMOND_EXTRACTION_DWH.SURE için 15
satırlık salt okunur VALIDATE_CONVERSION toplu sayımı yapıldı. Dolu değerlerde
geçersiz NUMBER=0, oturum `NLS_NUMERIC_CHARACTERS='.,'`. Sonuç yalnız bu oturumun
dönüşüm kuralına bağlı; uygulama sözleşmesi doğrulanmadı, REVIEW korundu.
Özel kayıt `.local/remaining-51-sure-conversion.json`, ham değer 0, DDL/DML/
COMPILE 0. 51 kanıt ledger'ı güncellendi: 16 küçük uyum, 4 NOT_RUN büyük,
1 sınırlı dönüşüm, 1 satır sayımı, 29 teknik/iş sahibi incelemesi.

## 26 Ekim 2026 - Package Body Sözlük Satırı Kanıtı (OFFLINE_PASS)

Hedef `ALL_OBJECTS` aynı ad için PACKAGE ve PACKAGE BODY satırlarını döndürürken
derlenmiş kanıt kontrolü tek satır beklediği için iki işlemin gerekçesi yanıltıcıydı.
Önce sentetik test RED, sonra kök body satırı tür bazlı seçilip kaynak/hedef spec
hash bağı eklendi. Eksik/yinelenen/ilgisiz body satırı ve spec hash drift'i
REVIEW kalır. Değişen ürün dosyası planning/routine_proof.py; test
test_compiled_routine_proof.py; belge docs/DDL_KURALLARI.md. İlgili 51 test PASS,
tam birim takımı 1219 PASS/125.26 sn, bir önceden var olan Starlette uyarısı.

Gerçek canlı Oracle run 77f5933fa91841239ae3e892ee429277 kaynak/hedef
snapshot'larıyla yeni kod çevrimdışı yeniden planlandı. Kanıt
`.local/package-body-proof-current.json` kökündeki verification.json.
567 eski SQL gövdesi aynen korundu; 1743 fark, 567 READY, 51 REVIEW,
1 BLOCKED, 610 bilgi aynı. DENEME SQL'siz. PCK_COMPARE_FIELDS gerçek kaynak/
hedef COMPARE_FIELDS ve COMPARE_FIELDS_LOG kolon imzaları, PCK_HYPERION harici
TTBP.F_CMS_RESULT kolon imzası nedeniyle REVIEW kaldı. Oracle sorgusu, DDL/DML/
COMPILE, mail, Jenkins ve push 0. Bu kod revizyonunun yeni canlı worker kabulü
NOT_RUN; kayıtlı gözlem replay'i PASS.

51 tekil işlemde ölçüm/gerekçe güncellemesi özel
`remaining-51-evidence.json/.csv`: 16 sonradan ölçülen uyum, 4 büyük tablo
NOT_RUN, 1 satır sayısı bilinen etki, 1 sınırlı dönüşüm ve 29 teknik/iş sahibi
kararı. Ölçüm canlı
capture transaction'ıyla aynı değil; otomatik READY terfisi yapılmadı.
VPN yeniden açıldıktan sonra büyük kolonların metadata kontrolü PASS:
ET202204 bölümsüz, ET_PRIM_ISLEMLERI_TT 119, TTNET 115 bölüm; dört kolonun
hiçbirinde doğrudan kolon indeksi görülmedi. Büyük veri taraması yapılmadı.
Kanıt `.local/remaining-51-access-paths.json`.

## 26 Ekim 2026 - PROD Küçük Tablo Uyum Ölçümü (READ_ONLY_PASS)

51 inceleme içindeki 20 toplu veri ölçümü adayından 16'sı küçük PROD hedef
tablolarında salt okunur denetlendi. 6 NOT NULL, 4 NUMBER daraltma, 3 VARCHAR2,
1 unique index, 2 PK: toplam 16 işlemde sıfır uyum ihlali. Yedi tablo taraması
ve iki duplicate aggregate 10 sn çağrı sınırıyla tamamlandı; iş satırı/ham
değer arşivlenmedi. Kanıtlar `.local/remaining-51-target-stats.json` ve
`.local/remaining-51-small-aggregates.json`, yeniden üretim scriptleri
`.local/preflight_51_table_sizes.py` ve `.local/profile_51_small_tables.py`.

`ET202204` yaklaşık 594 bin, `ET_PRIM_ISLEMLERI_TT` 162,8 milyon,
`ET_PRIM_ISLEMLERI_TTNET` 99,9 milyon tahmini satır gösteriyor. Bu tablolardaki
4 VARCHAR2 kontrolü PROD yükü nedeniyle NOT_RUN bırakıldı. Veri ölçümü DDL,
bağımlılık veya gelecekteki yazma sözleşmesini kanıtlamadığından hiçbir işlem
READY yapılmadı; toplam 567 READY/51 REVIEW/1 BLOCKED değişmedi. DENEME
okunmadı, DDL/DML/COMPILE ve mail yok.

## 26 Ekim 2026 - Otomatik PL/SQL Canlı Oracle Kabulü (PASS_WITH_RUNTIME_DRIFT)

Kullanıcı VPN/kurum ağı erişimini açtı. Kaynak ve hedef TCP, kaynak salt okunur
envanter testi PASS. Olağan yerel UI worker ile Oracle kaynak ve tek gerçek
Oracle hedef yeni run `77f5933fa91841239ae3e892ee429277` tamamlandı.
Durum PARTIAL: hedef başına 1743 fark, 567 READY/SQL, 51 REVIEW, 1 BLOCKED,
610 bilgilendirme. Sekiz yeni statik PL/SQL READY kararı otomatik akışta oluştu.
Toplam 478.760 sn (7 dk 59 sn), kaynak hazırlama 176.166 sn (2 dk 56 sn).
Mail NOT_SENT_LOCAL_DEVELOPMENT, DDL/DML/COMPILE 0.

Önceki doğrulanmış gerçek hedefe göre 567 hazır SQL gövdesi, karar sayıları,
kaynak DDL hash'leri aynı. Hedefte 12 eski C$_/I$_ adlı nesne kalkmış,
2 yenisi oluşmuş; iki sequence START WITH/sayaç gözlemi ilerlemiş. Yalnız bu
iki farkın değerleri ve iki işlem ayrıntısı değişti, hazır SQL değişmedi.
Tam snapshot eşitliği yok. Bundle doğrulaması, fark ve operasyon karşılaştırması
`.local/verify_auto_capture_live.py` ile yapıldı; özel kanıt
`.local/auto-capture-live-verification.json` PASS_WITH_RUNTIME_DRIFT.
`DENEME` fonksiyonu BLOCKED, SQL yok, hedef tabloya dokunulmadı.

Canlı run yerel modda yalnız bu bilgisayardaki özel arşive yazıldı. Jenkins
otomatik akış ve SQLcl dosya hedefinin yeni metadata taşıma kabulü NOT_RUN.
Sonraki iş: 51 REVIEW için sınırlı toplu veri ölçümleri, ardından kalan
operasyon/PLSQL kararları. SQL*Plus istemcisi bu makinede yok.

## 26 Ekim 2026 - Kalan 51 İşlemin Tekil Sınıflandırması (OFFLINE_PASS)

Kaydedilmiş gerçek hedef planındaki 51 REVIEW_REQUIRED işlem, fark kimliği ve
neden koduyla bire bir eşlenerek 16 eylem grubuna ayrıldı. Özel kayıt
`.local/plsql-audit-current.json` altındaki `remaining-51-actions.json/.csv`;
yeniden üretim `.local/classify_remaining_51.py`. 51 benzersiz işlem ve grup
toplamı doğrulandı. Değişen kamu belgesi
`docs/INNOVA_ODI_KALAN_51_PLANI.md`; PL/SQL inceleme belgesinin sonraki adımı
güncellendi. İş verisi okunmadı, yeni Oracle bağlantısı açılmadı, SQL/DDL
üretilmedi veya uygulanmadı.

20 işlem toplu salt okunur veri ölçümüne aday: 4 NUMBER daraltma, 7 VARCHAR2
uzunluk/semantik, 6 NOT NULL, 1 unique index, 2 PK. Sekiz
NUMBER(p,0) -> NUMBER değişimi ölçek sözleşmesi nedeniyle metadata-only READY
sayılmadı. Dört kaynak INVALID PL/SQL ve üç hedef etkin imza sapması REVIEW
kaldı. Tek DENEME ad alanı çakışması ayrı BLOCKED, tabloya dokunulmadı.
Normal otomatik PL/SQL akışının canlı kabulü ağ/DPY-6005 nedeniyle BLOCKED;
51 sınıflandırması canlı sonuç veya DDL eşdeğerliği kanıtı değildir.

## 26 Ekim 2026 - Otomatik PL/SQL Metadata Entegrasyonu (OFFLINE_PASS / LIVE_BLOCKED)

Oracle kaynaklı normal UI worker akışı, uygun statik PL/SQL birimlerini seçip
kaynak ve gerçek Oracle hedefte ayrı salt okunur transaction ile metadata
tamamlayacak şekilde güncellendi. Kanıt source/observation özel arşivine hash ile
bağlanır. Tek kendi-owner şema, en çok 64 aday, tam snapshot/filtre altkümesi
bağı ve güvenli UNAVAILABLE fallback'i test edildi. Git kaynağı, SQLcl dosya
hedefi, günlük TTBP Jenkins işi ve DDL uygulama sınırı değişmedi.

Değişen ürün dosyaları oracle/routine_metadata.py, oracle/collector.py,
source/oracle_reader.py, planning/routine_proof.py ve runtime/worker.py.
Yeni test test_routine_metadata_integration.py; filtre/kanıt regresyonu
test_compiled_routine_proof.py. 1213 birim testi PASS/199.67 sn; tek önceden
var olan Starlette uyarısı. Bağımsız incelemenin filtre bağlama ve cleanup
bulguları RED -> GREEN kapatıldı. Plan:
docs/superpowers/plans/2026-10-26-automatic-plsql-capture.md.

Canlı yerel run 4e0d515fcf004849817b4c6f7b1094b2 SOURCE_CAPTURE_ERROR
ile bitti. Bağımsız bağlantı testi DPY-6005 verdi, hem kaynak hem hedef TCP
ucuna erişilemiyor. Oracle snapshot, hedef karşılaştırması, DDL, mail yok.
Canlı toplam süre/eşdeğerlik BLOCKED. Ağ erişimi geldiğinde aynı tek gerçek
hedef profilini yeniden çalıştır; dosya hedefinin yeni ek metadata'sı ayrı iş.
Bu sırada kalan 51 incelemenin veri gerektiren doğrulama planı hazırlanıyor.

## 26 Ekim 2026 - PL/SQL Bağımlılık Kanıtı (ORACLE_READ_ONLY_PASS / OFFLINE_PASS)

Önceki 59 inceleme kaydı tek tek izlendi. INNOVA_ODI kaynak ve hedefinde iki salt
okunur işlemle 1548 metadata sorgusu yapıldı. İş verisi, DENEME tablosu, DDL/DML/
COMPILE, SMTP, Jenkins ve dış Git işlemi yok. Sekiz statik PL/SQL birimi güncel
derleme, DDL hash, bağımlılık, hedef imzası, synonym ve doğrudan yetki kanıtıyla
READY oldu. Hedef başına 559 READY/59 REVIEW/1 BLOCKED -> 567 READY/51 REVIEW/
1 BLOCKED; 1743 fark ve 610 bilgilendirme aynı. DENEME fonksiyon/hedef tablo ad
çakışması BLOCKED kaldı, SQL üretilmedi.

Özel yerel UI run: c0f45c8ca18848988968bafd90943e5c (PARTIAL). İki hedefin
karar/bağımlılık/SQL eşdeğerliği, 59/59 izleme, eski 559 SQL gövdesinin korunması,
sekiz yeni SQL, kaynak/hedef ham DDL hash'leri .local/plsql-audit-current.json
altındaki verification.json içinde PASS. Güncel generator fingerprint'i raporla aynı.
Tam birim takımı 1209 PASS/138.81 sn; bir önceden var olan Starlette uyarısı.

Ürün dosyaları oracle/routine_metadata.py, planning/routine_proof.py,
planning/{object_rules,graph}.py; testler test_{compiled_routine_proof,
routine_metadata_reader}.py. Belgeler docs/DDL_KURALLARI.md,
docs/INNOVA_ODI_PLSQL_BAGIMLILIK_INCELEMESI.md ve uygulama planı. Bağımsız
incelemede bağlantı gözlemi binding'i, hedef kök sapması ve etkin çağrı imzası
bulguları RED -> GREEN kapatıldı. Kalan 51'in nedenleri inceleme CSV'sinde.

Sonraki somut adım: salt okunur metadata okuyucusunu normal yerel UI canlı toplama
akışına bağlamak, yeni canlı koşuda sekiz kararın otomatik oluştuğunu doğrulamak.
Sonrasında 20 veri tipi ve 7 kolon değişikliğinin veri uyumu ayrı kapsamla
incelenebilir. Oracle'da DDL uygulama kabulü ve Jenkins kurulumu NOT_RUN.

## 26 Ekim 2026 - 76 İşlem İncelemesi (OFFLINE_PASS)

Kullanıcı 5 engel/71 incelemeyi detaylandırıp güvenli olanları düzeltmeyi açıkça
istedi. Sonuç hedef başına 559 READY/59 REVIEW/1 BLOCKED, 1743 fark aynı. 76/76 tekil
başlangıç kaydı son operasyonlara bağlandı. 16 kayıttan 17 yeni SQL: 5 BASICFILE
LOB CREATE, 7 BYTE -> CHAR genişletme, 4 NOT NULL gevşetme ve yeni tablo için 1 ayrı kısıt.
Eski 542 SQL gövdesi aynı. İki hedef yolu karar/bağımlılık/SQL eşdeğerliği PASS.
Eski 5 engel çözüldü, kalan 1 gerçek engel kaynak fonksiyon/hedef tablo DENEME çakışması.
Hedef tablo korunur, DROP/rename üretilmez. Açık 59 inceleme veri/çalışma zamanı/
statik çözümleme kanıtı bekler. 5 kaynak program birimi INVALID, COMPILE yapılmadı.

Ruling: dictionary.dependencies kayıtlarını doğrudan tam exporter kanıtına
çevirmedik. Offline varsayım denemesi 14 ek çözümleme/ad alanı engeli çıkardı.
Eksik hedef/statik kanıt ve INVALID kaydıyla routine kapısını gevşetmek yanlış
READY riski taşır. Ayrıntılar docs/INNOVA_ODI_ISLEM_INCELEMESI.md ve özel ledger.
Ruling: mevcut kirli dalda devam edildi, worktree/commit/push yok. Kaynak gövdesi ve
yakalanmış metadata değiştirilmedi. Yeni Oracle bağlantısı, iş verisi okuma, DDL/
DML/COMPILE, Jenkins/SMTP yok. Gerçek Oracle uygulama kabulü ve Jenkins NOT_RUN.

Yeni modüller planning/{lob_rules,column_safety,namespace,review_reasons}.py,
mevcut table_rules/table_ddl/policy/object_rules/graph güncellendi. Sentetik
regresyonlar test_basicfile_lob_planning.py, test_safe_column_expansion.py ve
test_review_reason_details.py. 1163 test PASS/161.46 sn. Son bağımsız incelemede
DEFAULT ON NULL ve yinelenen/çelişkili LOB parametre bulguları RED -> GREEN
kapatıldı. Kaynak/gösterim sözleşmesi korunur, docs/DDL_KURALLARI bu kapalı
genişlemeyi belgeler. Gerçek DDL Oracle'da parse edilmedi, offline parser doğrulandı.

Kanıtlar .local/held-audit-current.json ile bulunan dizinde. operation-audit
JSON/CSV/MD 76 kayıt, verification.json PASS, unit-final.log, lob-ready-ui.png,
namespace-conflict-ui.png. Yeni UI run 13a6dbe5c2aa4b03be417f10763a02a2, baseline 5a6cf3bb20cb4e72be7557ed35c76edd.
UI tab 14 SKY/İnceleme Analizi/DENEME gerekçesinde açık. Sunucu 30724/41752/8800.
UI 2 dk 1 sn kayıtlı gözlem tekrar planlamasıdır, kartlar iki hedef toplamıdır.
Sonraki somut adım: 59 kayıt arasından veri/operasyon kararı veya statik çözücü
kapsamı seçilsin. Özellikle INVALID kaynakları üretici sahibinin düzeltmesi ve
rutinlerin eksik statik hedef kanıtının ayrı ele alınması gerekir.

## 25 Ekim 2026 - INNOVA_ODI SQLcl Canlı Eşdeğerlik Kabulü (PASS)

Kullanıcının gerçek SQLcl toplama + UI import + canlı bağlantı gözlemiyle aynı
sonuç/DDL kabulü tamamlandı. Ayrıntı docs/SQLCL_CANLI_KABUL.md. Önceki offline
NOT_RUN kayıtlarını bu SQLcl/Oracle kabulü günceller, SQL*Plus NOT_RUN kalır.

- SQLcl 26.2/Oracle 19c:823 DDL,90 harici durum kaydı,0 sorgu hatası, OWN sabit envanter.
- Toplama565.530 sn/24.661.019 bayt. SHA256:c6bc1185957c7ac7ad315bccd924caf798252b41a61474e31c0313acfe28c353.
- İki hedefte1743 fark/542 hazır SQL/71 inceleme/5 engel/610 bilgilendirme eşit.
- Doğal farklar, işlem kararları/önkoşulları/dependency kenarları ve542 SQL gövdesi hash'i PASS.
- Kaynak bir kez gerçek Oracle'dan alındı. Son tekrar planlama aynı source ve canlı
  target gözlemiyle yapıldı, yeni DB okuması yok.89.624 sn/GUI1 dk 32 sn bu tekrarın süresi.
- Gerçek UI import, proje ayrımı, yerel dosya SQL görüntüleme PASS.1135 unit/105.98 sn PASS.
- Mevcut SKY eşleştirmesi/profili rev3 yeni dosyaya güncellendi. Diğer projeler korunur.
- Son UI run:5a6cf3bb20cb4e72be7557ed35c76edd. İlk hatalı run:7beeef40f09c413eb75d64266b251b78 korunur.
- Sunucu parent30724/listener41752/8800. UI tab14 SKY dosya hedefi görünümünde teslim.

Ürün düzeltmeleri portable/builder.py, portable/stream.py, portable/adapter.py,
portable/templates/{collect.sql,New-Capture.ps1,README.md}, planning/table_ddl.py,
model/atomic.py, source/oracle_reader.py ve artifacts/bundle.py. Regresyonlar
unit/test_portable_{capture,adapter}.py, test_table_metadata_boundary.py ve
test_atomic_directory.py. CLOB/output/transform/takvim/harici durum ve CREATE TABLE
metadata sınırı gerçek veride RED→GREEN düzeltildi. Kaynak gövdesi/karşılaştırma
kararları gevşetilmedi, veri export SQL'i çalıştırılmadı.

Özel arşiv .local/portable-live-current.json ile bulunur. acceptance.json ve
parity.json PASS. Önceki hash/denemeler, ham DDL, gözlemler ve başarısız runlar
korunur. Genel kanıt output/portable-capture/live-acceptance-summary.json, güncel
beş dosyalı paket output/portable-capture/portable-capture.zip.

Açık kabul sınırı: UI planı mevcut71 inceleme/5 engel nedeniyle PARTIAL kalır.
Dosyada bulunmayan yeni harici referans/synonym/kolon kanıtı UNKNOWN kalır.
SQL*Plus ve Jenkins NOT_RUN. Oracle DDL/DML/COMPILE, SMTP, commit/push yapılmadı.
Sonraki somut adım yeni kullanıcı önceliğine göre bu mevcut inceleme/engel
kayıtlarını değerlendirmek veya ayrı yetkiyle SQL*Plus istemci kabulü yapmak.


## 25 Ekim 2026 - Taşınabilir Oracle Toplama ve Dosyadan Karşılaştırma

Durum: OFFLINE_IMPLEMENTED. Canlı Oracle/SQL*Plus/SQLcl toplama kabulü NOT_RUN.
Kullanıcı şema/nesne türü/nesne adı/kolon veri tipi parametreli, düşük bağımlılıklı
SQL*Plus ve SQLcl toplama paketini ve README'yi açıkça istedi.

- Yeni portable/{selection,builder,stream,adapter}.py ve templates/{collect.sql,New-Capture.ps1,README.md}.
- prepare-capture/import-capture CLI. Uygulama içinde Bağlantılar > Taşınabilir Toplama.
- Projeye bağlı immutable capture kayıtları, özel ham dosya arşivi, SNAPSHOT kaynak/hedef.
- Aynı ortak filtre karşılaştırma UI'sinde kullanılır. Kolon veri tipi filtreleri tam nesne seçer.
- SOURCE/TARGET toplama yönü, hedefte değişmiş veri tipini DDL exportundan kaybetmez.
- Ana envanter partition alt nesnelerinden ayrılır, ayrıntılar mevcut metadata gruplarında kalır.
- Oracle STANDARD için VARCHAR2(4000 BYTE), her CSV listesi en fazla4000 UTF8 bayt.
- Herhangi bir SQL uygulanmaz. Gerçek Oracle, Jenkins ve SMTP çağrısı yapılmadı, push/commit yok.

Doğrulama:
- .venv/Scripts/python.exe -m pytest tests/unit -q:1126PASS/101.34s.
- Son küçük tanılama/PowerShell güncellemesi sonrası scoped54PASS/6.31s.
- web npm test:58PASS/18dosya. npm run build PASS. Lint0error/3önceden mevcut fast-refresh warning.
- Bağımsız inceleme3Important bulgu RED→GREEN,25featuretest.
- Tarayıcı temiz test state: iki dosya import, şema eşleştirmesi, DEMO/NUMBER filtresi,
  gerçek ayrı worker ile COMPLETE,1nesne/1fark/1DDL, yerel SQL görüntüleme PASS.
- Diğer projede dosya/eşleştirme görünmüyor. Paket ZIP tarayıcıdan indirildi ve içerik doğrulandı.
- TR/EN, koyu tema ve320px görüntü kontrol edildi, görünüm override sıfırlandı.
- SQLcl26.2 yalnız sürüm komutu doğrulandı. SQLPlus PATH'te yok. Gerçek DB/client kabulü NOT_RUN.

Açık küçük sınırlar: virgüllü quoted adlar importta reddedilir,64MiB sınırında satır
sonu/bitiş kaydı ek yükü sayılmadığından paket daraltılabilir, SQL closure aynı adlı
farklı owner üstündeki bir indeks/tetikleyiciyi fazladan toplayabilir. Bilinen owner
kanıtı karşılaştırmada bu kaydı eler. README'de açıkça belgelenmiştir.

Geliştirme fixture'ındaki ilk SOURCE_IMPORT denemesi ve bir modül çağrısı genel
CONNECTION_OR_METADATA_ERROR verdi. Eski run üzerine yazılmadı. Aynı spec ile sonraki
inline/ayrı worker ve yeni temiz state tarayıcı kabulü başarılı. Eklenen gerçek worker
regresyonu geçiyor. Hata tekrar ederse yalnız exception class ve stack frame konumu
veren özel failure-diagnostic.json incelenmeli, hata metni/SQL/sırlar loglanmaz.

Kanıtlar: output/portable-capture/{full-unit-final,post-check,ui-suite-final,ui-build-final,ui-lint-final,review-red,review-green}.log.
Paket: output/portable-capture/portable-capture.zip. Ana özel state .local/ui-state korunur.
Ana sunucu PID35172/session60040/8800, auth oturumu korundu. SKY > Taşınabilir Toplama
tab14 teslim edildi. Collector grammar0error ve PowerShell prepare PASS. İzole test
sunucusu PID14520 kapatıldı. Hiçbir sentetik capture ana projelere eklenmedi.
Sonraki somut adım: yetki verildiğinde küçük gerçek kaynak/hedef scope'unda SQLcl ve
SQL*Plus toplama, üretilen dosyanın CLI/UI import ve aynı nesnelerin canlı gözlemle
semantik eşdeğerlik kabulü. Bu kabul yapılmadan production doğrulandı denmez.

## Nesne odaklı karşılaştırma inceleme teslimi - 25 Ekim 2026

Kullanıcının onayladığı nesne → fark özeti → gruplanmış ayrıntı → ilgili SQL
akışı uygulandı. Mevcut motor/plan/DDL kuralları ve proje sınırı değişmedi.
Gruplama sunucuda tüm kayıtlar üzerinden, sayfalama öncesinde yapılır. 25 tam
kolon/kısıt/indeks grubu sayfalanır, FK sayfa sınırında bölünmez. Fark özeti ve
yapı sayıları yüklenen sayfadan bağımsızdır. Varlık yalnız presence/exists
kanıtından gelir, bir alanın MISSING olması kolonun yokluğu sayılmaz. UNKNOWN
ve NULL ayrı kalır. Listede fark türü ve DDL kararı ayrı gösterilir, fark filtresi
sunucuda sayfalama öncesi uygulanır. İlgili İşlemler ve SQL change_ids ile
seçili gruba bağlı kayıtları ve uygulanabilir SQL varsa ortak görüntüleyiciyi açar.

Başlıkta kaynak/hedef bağlantı ve şema açıktır. Ham metadata JSON'u etiketli
değerler ve aşamalı iç içe listeler olarak gösterilir. Üç sekme Yapısal Farklar,
Tanım Karşılaştırması, İşlemler ve SQL. ARIA tab/tabpanel bağı doğrulandı.
TR/EN yeni varlık adları/çoğullar ve iki tema desteklenir. Kaynak bağlantı adı
kullanıcı verisidir, çeviriyle değiştirilmez.

Yerel özgün DDL, özel run snapshot'ından seçili nesne için ayrı yetkili no-store
endpoint'le okunur. Belge/kanonik kimlik/source-target semantic digest ve blob
SHA256 doğrulanır, çok statement dosyasında kanıtlı byte aralığı kullanılır.
UTF8 statement metni/quote/literal/newline korunur. Jenkins'te özgün tanım
aktarılmamışsa ARCHIVED ve bağlantı görünür, yerel SQL kopyası okunmaz.
Eksik tanım eşitlik sayılmaz. Metin hizalama yapısal kararları değiştirmez.
64MiB belge/okuma,2MiB tanım/20.000satır sınırı var. LCS250.000hücre bütçesi
üstünde değişen blok hizalaması kullanılır. DOM sabit300satır pencere/spacer.

Değişen dosyalar control/{structure,definitions,results,api}.py,
web/src/{ObjectResults,ObjectComparisonPanel,DefinitionComparison,MetadataValue,
RunDetail,JenkinsRunDetail}.tsx,resultApi.ts,lineDiff.ts,object-results.css,
translations.ts ve ilgili testler. Plan docs/superpowers/plans/2026-10-25-
structured-results.md, spec docs/SONUC_INCELEME_TASARIMI.md. API ve saklama
sınırları docs/NESNE_SONUCLARI.md/UI_CALISTIRMA_VE_DAGITIM.md içinde güncel.

Doğrulama:55UI/17dosya PASS,84Python ilgili kontrol/proje/özgünDDL ve gerçek
parser/planner/SQL offline kabulü PASS. Build PASS, lint0hata/3öncekiFastRefresh
uyarısı. Bağımsız reviewer10Python PASS, tekP2 (scroll ile DOM birikimi)
kırmızı→yeşil sabit pencere regression testiyle kapandı. Korunan3SQLfixturehash'i
önceki kanıtla aynı. Ana kod dalı codex/shared-ui-oracle-source, commit/push yok.

Özgün DDL DOM metinlerinin iki taraf için de snapshot statement metniyle birebir
eşitliği original-exact-receipt.json içinde doğrulandı. Özet yalnız yapısal
sekmede görünür, SQL ve işlem sekmelerine yer bırakır.

Tarayıcı gerçek#55 ANKET_EMAIL_GONDERIM:22alan/2FK, iki kapalı grup ve
'2 Yabancı Anahtar - Hedefte Eksik' özeti. İlkFK11alanı açılıp ilgili11change
inceleme işlemine geçildi, uygulanabilir SQL olmadığı doğru metinle gösterildi.
İngilizce/koyu görünümde2ForeignKeys özeti veSource/Target bağlamı doğrulandı,
TR/açık tercih geri yüklendi. 320px ayrıfixture sayfa scrollWidth320, panel286.7px,
geniş tablo kendi içinde kayıyor. TamWCAG/TMF veya5sn kullanıcı ölçümü NOT_RUN.

Ayrı8801fixture, yalnız Git/Oracle network sınırı yerine fake collector verip
aynı gerçek motorla DEMO kaynakVARCHAR2(100)/hedefVARCHAR2(50) üretti. İki
özgün snapshot statement'ı hash/byte sınırıyla okunup tarayıcıda satır farkıyla
gösterildi. Fake dictionary uzunluk semantiği eksikliği UNKNOWN olarak kaldı,
PARTIAL kaydı başarıya çevrilmedi. İlk başarısızfixture denemesi özel test
state'indeFAILED olarak korundu. Ana SKY state'e test çalışması eklenmedi.

Kanıt output/structured-results/{ui-final.log,python-final.log,build.log,lint.log,
structured-final.png,original-definitions.png,dark-en-final.png,narrow-proof.json,
filter-proof.json,window-red.log,window-green.log,sql-unchanged.json,progress.md}.
Ana8800 sunucuPID2200/session54532, mevcutparola/oturum korunur. Teslimsekmesi11.
Geçici8801fixture kapanır. Yeni canlıOracle/SQLuygulama/Jenkinskoşusu/job/SMTP/
push NOT_RUN, kurum ortak dağıtım NOT_RUN. Sonraki somut adım kullanıcının8800
üzerinde gerçek#55'te nesne/grup/ilgiliSQL akışını incelemesidir. Jenkins özgün
SQL'ini uygulama içine almak için halen servis okuma erişimi bulunmamaktadır.

## Çalışma ekranı ve yerel SQL görüntüleyici - 25 Ekim 2026

Kullanıcının ekran yenileme ve yerel çalıştırma SQL saklama talimatı uygulandı.
Yeni karşılaştırmada Çalıştırma Yeri Jenkins/Bu Bilgisayar seçilir. Varsayılan
Jenkins ve legacy istemci davranışı korunur. LOCAL yalnız yerel runtime ile,
açık seçimle kayıtlı Jenkins devrini atlar. Sessiz fallback yoktur. Run kaydı
executor/artifact_mode taşır, yerel kuyruk Jenkins işini sahiplenmez.

Çalışma ayrıntısı yedi kompakt KPI gösterir, toplam süre ilk karttır. Kaynak
hazırlama/alt sınır notu kısa satırdadır, rapor başlık yanındadır. Tekrarlanan
tam işlem tablosu kaldırıldı. Nesne arama ve tür seçimi solda, kaynak/hedef nötr
ve okunabilir tabloda sağdadır. Nesne listesi kaydırarak25 kayıt ekler, seçim
korunur, yinelenen scroll engellenir, append hatası kayıtları silmez, tekrar
aynı sayfa denenir. Geç eski hedef/filtre yanıtı karışmaz. Varlık ve NULL izin
metinleri bağlamsaldır, UNKNOWN/ABSENT/NULL/NOT_APPLICABLE korunur. Kapalı
canonical metadata token dizileri okunur gösterilir, literal içeriği değişmez.

SqlViewer yerel run dosyasını proje yetkili no-store API'den okur. Dosyanın
metni/çift tırnağı aynen gösterilir. Jenkins SQL'i uzak arşivde kalır, mevcut
servis okuma hesabı yokken dialog yalnız arşiv bağlantısı verir. Bağımsız
incelemenin tek P2 bulgusu kapandı: external olmadan servis-dispatch edilen
Jenkins kaydı da executor/verified archive_build_url ile ayrılır. Yerel SQL
bağlantısı üretilmez ve artifact endpoint'i Jenkins yerel dosyasını reddeder.

Dosyalar web/src/{RunSummary,ObjectResults,ObjectComparisonPanel,RunDetail,
JenkinsRunDetail,SqlViewer,ComparisonForm,App}.tsx,api.ts,resultApi.ts,
translations.ts,index.css,object-results.css ve ilgili frontend testleri.
Backend control/{api,store,results}.py ve test_control_local_executor.py.
Karar ADR-026, docs/NESNE_SONUCLARI.md ve UI_CALISTIRMA_VE_DAGITIM.md güncel.

Doğrulama: tüm frontend46PASS/15dosya, ilgili backend/proje/ayar/giriş/kuyruk/
Jenkins arşiv testleri ve offline gerçek parser/planner/SQL kabulü74PASS.
Üretim buildPASS, lint0hata/3öncekiFastRefreshuyarısı. Bağımsız reviewer11Python+
15UI PASS, tekP2 regression testinden sonra kapandı. git diff --check temiz.
Korunan üç kaynak/expected SQL fixture hash'i önceki kanıtla aynı.

Tarayıcı gerçek#55: kompakt özet3.805 kaynak/11.946 fark/3UNKNOWN/18dk40sn,
kaydırmada25→50/808nesne, seçili ANKET_EMAIL_GONDERIM korundu. Kaynak/hedef
hücreleri aynı rgb255 yüzey, teknik metadata ham JSON olmadan okunuyor.
Ayrı8801 offline fixture server gerçek motorla tırnaklı UI_DEMO SQL'i üretti.
Canlı Oracle/network sınırı fake collector ile değiştirildi, parser/planner/
SQL emission gerçekti. Browser SQL DOM metni ile üretilen dosyanın SHA256'sı
f54a1cab040438f2ea4456ae119741b556093677c47bfbeaec0ef9b0a03478c6 aynı.
Bu sentetik kabul gerçek SKY karşılaştırması değildir, ana state'e eklenmedi.
Geçici8801tab/server kapandı. Ana8800 PID30220/session87209, mevcutparola ve
oturum korunur. Teslimtab9 gerçek SKY#55 sonuç panelinde bırakıldı.

Kanıt output/results-redesign/{ui-final.log,python-final.log,build.log,lint.log,
browser-proof.json,sql-exact-receipt.json,protected-sql-receipt.json,
summary-final.png,workspace-final.png,local-sql-viewer.png,review-red.log}.
Yeni canlıOracle/SQLuygulama/Jenkinsjob/mail/push NOT_RUN. Kurum ortak dağıtım
NOT_RUN. Jenkins servis okuma hesabı halen yok, uzak SQL uygulama içine
aktarılmış sayılmaz. Sonraki somut adım kullanıcının8800ekranında yeni düzeni
incelemesi, yerel canlı çalışma isterse açık Bu Bilgisayar seçimiyle başlatması.

## Transparan kurumsal logo ve A sekme simgesi - 25 Ekim 2026

Kullanıcı koyu temadaki beyaz logo kutusunu kaldırıp transparan resmî sürümü ve
sekmede İnnova A simgesini istedi. Beyaz alan CSS background:white/padding'den
geliyordu, mevcut PNG zaten alfa içeriyordu. Resmî kurumsal kimlik sayfasındaki
innova_kurumsal_kimlik.zip indirildi, siyah/beyaz yazılı transparan SVG'ler ve
resmî site favicon.ico dosyası byte değişmeden web/public içine alındı.
BrandLogo ortak bileşeni App/AuthGate'de tema sürümünü seçer. Renk filtresi yok.
Sidebar/mobil/giriş kartındaki beyaz zemin ve padding kaldırıldı. index.html
favicon.ico?v=innova-20261025 linkiyle A simgesine gider. Eski PNG ve HTML rapor
ailesi korunur. Kaynak/asset hash'leri docs/UI_MARKA_VARLIKLARI.md içinde.

Dosyalar web/src/{BrandLogo,App,AuthGate}.tsx,index.css, web/index.html,
web/public/{innova-logo.svg,innova-logo-white.svg,favicon.ico}. Görünür varlıklar
kurumun yayımladığı asıllardır, logo yeniden çizilmedi. Public push yapılmadı.

Doğrulama: üretim buildPASS, tüm frontend37PASS/14dosya/22.45sn, lint0hata/
4öncekiuyarı. İki temada background rgba0, padding0, filter none, imgcomplete.
Head'de favicon linki var, üç varlık da HTTP200 ve kaynakla aynı hash döndürüyor.
ICO alfa içeriyor,106x106. Koyu tema screenshot beyaz kutusuz resmî logo gösterir.
Geçici test sekmesi kapandı, önceki tema tercihi geri yüklendi. Native Chrome
sekme ikonunun cache sonrasındaki piksel kabulü NOT_RUN, head/resource doğrulandı.
Tam Python/live Oracle/Jenkins/SMTP/push bu frontend varlık turunda NOT_RUN.

Kanıt output/brand-assets/{asset-hashes.json,browser-proof.json,http-proof.json,
build.log,frontend-tests.log,lint.log,dark-logo.png,diff-check.log}. Sunucu
PID29032/session3110/8800 aynı. Sonraki somut adım kullanıcının sayfayı Ctrl+F5
ile yenileyip Chrome'da yeni favicon ve transparan logo görünümünü kontrol etmesi.
Açık işlevsel engel yok, backend/proje/credential/SQL kayıtları değiştirilmedi.

## Çoklu hedef kalıcı kayıt ve proje ayrımı kabulü - 25 Ekim 2026

Önceki turdaki deferred çoklu hedef testi kullanıcı talimatıyla tamamlandı.
Ürün kodunda hata bulunmadı, üretim kodu değişmedi. Mevcut doğru davranış için
koruyucu UI round-trip ve gerçek SQLite/API testleri eklendi. Bu bir özellik
uygulaması veya RED→GREEN hata düzeltmesi değildir, yeni testler ilk koşuda geçti.

Kontrol projesine TEST - Oracle 2 (çoklu hedef), oracle-test-2.invalid/TEST_ONLY_2
sentetik hedef tanımı eklendi. Gerçek credential kopyalanmadı, bağlantı denenmedi.
Yeni TEST - Çoklu hedef kontrolü eşleştirmesi ayrı kayıt olarak UI'de oluşturuldu.
Eski eşleştirme ve ona bağlı profil korunur. Source schemas TEST_SCHEMA,TEST_AUX.
İlk hedef yalnız TEST_SCHEMA→TEST_SCHEMA, ikinci yalnız TEST_AUX→TEST_AUX kullanır.
Owner remap yapılmaz, farklı hedefler kaynağın farklı alt kümelerini seçer.

Gerçek authenticated UI akışı ve özel SQLite kayıtları:
- v1 iki hedef ve farklı çiftlerle kaydedildi. Tam sayfa yenilenip tekrar açıldı,
  dört checkbox'tan doğru ikisi seçili, diğer ikisi boş doğrulandı.
- İkinci hedef kaldırılıp v2 kaydedildi. Tam yenileme sonrası yalnız ilk hedef ve
  onun çifti kaldı. İkinci hedefin eski target_mappings anahtarı kayıtta yok.
- İkinci hedef yeniden eklendi. Her iki şema checkbox'ı da boş geldi. Çift
  seçmeden kaydetme UI doğrulamasında engellendi, DB'de yeni sürüm oluşmadı.
- TEST_AUX çifti açıkça yeniden seçildi, v3 kaydedildi. Tam yenileme ve tekrar
  açılış sonrası iki farklı çiftin ilk kayıtla aynı olduğu doğrulandı.

Gerçek state'e bağlı API'de SKY listesinden bu kayıt görünmedi, test hedefi
access-info404, kaydı SKY'ye taşıma ve yeni kimlikle SKY'ye kopyalama422.
İlgili API instance'ında workers kapalıydı. SKY kayıt/ayar/çalışma digest'i ve
önceden var olan test bağlantı/eşleştirme/profil/ayar/çalışma digest'i aynı.
Yalnız yeni sentetik hedef ve eşleştirme eklendi. Yeni run sayısı0.

Testler: web/src/SchemaMappingRoundTrip.test.tsx (mock kalıcı yanıt ile gerçek UI
kontrolleri, unmount/remount, üç kayıt ve boş seçimde API'ye gitmeme),
tests/unit/test_control_mapping_catalog.py (SQLite/API üç sürüm, boş çift422,
proje sınırı). Tarayıcı testi gerçek özel state ile ayrıca yapıldı.
Komutlar: npm test -- --run, 37PASS/14dosya/22.67sn. npm run build PASS.
Proje/katalog/workspace Python testleri12PASS/2.62sn. Lint0hata/4öncekiuyarı.
Tam Python suite bu test-only turda NOT_RUN, önceki1096PASS ayrı aşama kanıtıdır.
Önceki review minor konusu kapandı, bu kabul için açık engel/kalan test yok.

Kanıt output/multi-target-check/{ui-focused.log,backend-focused.log,
frontend-tests.log,backend-tests.log,build.log,lint.log,baseline.json,
fixture-ids.json,browser-round-trip.json,isolation-receipt.json,
mapping-versions.json,cleared-pairs.png,saved-multi-targets.png,diff-check.log}.
Üç SQL fixture hash'i önceki temel değerleriyle aynı. Motor/SQL kararları
ve gerçek credential kayıtları değiştirilmedi. Oracle/Jenkins/SMTP/push yok.
Tarayıcı tab7 kontrol projesinin v3 eşleştirmesinde bırakıldı. Sunucu
PID29032/session3110/8800 aynı. Sonraki adım kullanıcının kayıtlı TEST - Çoklu
hedef kontrolü v3 kaydını incelemesidir, yeni uygulama işi gerekmiyor.

## İkinci proje izolasyonu ve hedef seçici teslimi - 25 Ekim 2026

Kullanıcı ikinci proje oluşturarak bağlantı/eşleştirme/ayar/çalışmaların ayrılığını
kontrol etmemizi, alt bilgiyi kısaltmamızı, sekmeleri sola almamızı, kart çizgilerini
yumuşatmamızı ve hedeflerin kaynak gibi seçilebilir olmasını istedi.

Proje Ayrım Kontrolü / IZOLASYON_TEST yetkili UI'de oluşturuldu. Bu projeye iki
açık TEST tanımı ControlStore doğrulamasıyla eklendi. Git example.invalid ve Oracle
oracle-test.invalid, TEST_ONLY sentetik bilgileridir. Gerçek credentials kopyalanmadı,
Oracle/Git erişimi denenmedi. UI'de TEST_SCHEMA eşleştirmesi ve TEST profil kaydı
oluşturuldu, çalıştırılmadı. Proje ayarı Git denemesi4, bildirimfalse olarak UI'den
kaydedildi. SKY denemesi3/bildirim ayarı korundu. Test projede çalışmalar0, SKY1.

Gerçek özel state üzerinde API instance'ı start_workers=False ile kontrol edildi.
Cross-project detail/access-info/run/summary/artifact/result okumaları404,
settings/profile/mapping yazımları422, run başlatma404. Probe mock'u çağrılmadı,
network yok. SKY connection/profile/mapping/settings/run digest'i başlangıçla aynı.
Kayıtların ayrılığı authenticated UI proje geçişlerinde de gözlendi. Kullanıcının
etkileştiği sekmeye müdahale etmemek için kontrol ayrı browser tab6'da yapıldı.

Footer giriş ve ana ekranlarda tam olarak © 2026 İnnova Bilişim Çözümleri A.Ş.
Sekme grubu align-self:flex-start/width:fit-content/justify-content:flex-start.
Kartlarda currentColor'a düşen koyu kenarlık yerine ayrı açık/koyu card-border
ve hafif shadow tokenları var. Form odak/kontrol kontrastı korunur.
Hedefler editable dropdown satırları oldu. Hedef Ekle/Kaldır ile1→N korunur,
aynı bağlantı iki satırda seçilmez. Hedef değişimi/kaldırma eski çiftleri siler.
Boş hedef ve şema çifti eksikliği kayıt öncesinde reddedilir.

Dosyalar web/src/{SchemaMappings,App,AuthGate}.tsx,index.css,translations.ts,
SchemaMappingCatalog.test.tsx,SchemaSelection.test.tsx. Backend ürün kodu değişmedi.
RED hedef seçici2fail, GREEN focused4PASS. Eski checkbox selector'ları dropdown ve
kaldır düğmesiyle güncellendi, kapsam assertion'ları korundu. Tam frontend36PASS/
13dosya/17.21sn. Python proje-kapsam testleri11PASS/1.86sn. BuildPASS,
lint0hata/4öncekiuyarı. Tam Python suite bu UI turunda NOT_RUN, önceki1096PASS
ayrı aşamanın kanıtıdır. Yeni Oracle/Jenkins/SMTP/push yok.

Bağımsız review Critical0/Important0. Minor deferred: iki hedefin farklı çiftlerle
birlikte kaydı, kaldırıp yeniden eklemede çiftlerin yeniden doğrulanması ve tekrar
edit/save kombinasyonunu kapsayan ilave UI uçtan uca testi bu tur eklenmedi.
Mevcut edit/remove ve target-swap testleri geçti, fonksiyonel hata saptanmadı.
Reviewer's declined list rulings: tarayıcı görselleri ve gerçek state izolasyonu
parent tarafından ayrıca doğrulandı. Canlı Oracle/Jenkins ve eski motor değişiklikleri
bu görevin dışında, NOT_RUN. Ruling maliyeti: gerçek entegrasyon kabulü iddiası yok.

Kanıt output/project-isolation/{targets-red.log,targets-green.log,frontend-tests.log,
backend-tests.log,build.log,lint.log,isolation-receipt.json,browser-receipt.json,
sky-before.json,fixture-ids.json,target-selector.png,connections-updated.png,
diff-check.log}. Sekmeler x272, içerik alanı x240+32padding. Kart border
rgb226,231,238. Kontrol sekmesi test proje eşleştirmelerinde açık bırakıldı.
Sunucu PID29032/session3110/8800 aynı. Test tanımları kullanıcı incelemesi için
korundu. Sonraki somut adım: UI'de SKY ve Proje Ayrım Kontrolü arasında geçişle
kontrol. Sentetik bağlantılar gerçek karşılaştırma için kullanılmaz.

## Kullanıcı talimatıyla giriş parolası sıfırlama - 25 Ekim 2026

Kullanıcı parola belirleme sonrası hata bildirdi, açık yanıtıyla sıfırlayıp
yeniden belirlemeyi seçti. Mevcut parola okunmadı veya yeni parola üretilmedi.
Yalnız mkaracan login_account kaydı, uygulama oturumları ve giriş deneme
sayaçları yerel SQLite transaction içinde sıfırlandı. Audit auth.password_reset.
Proje kayıtları, çalışmalar ve bağlantı sırları önce/sonra aynı kaldı.
GET /api/auth/status setup_required=true/setup_allowed=true doğrulandı.
Frontend İlk Giriş ekranında açıldı ve görünür bırakıldı. Parola giriş ve
kaydını kullanıcı yapacak. Gerçek hata metni bu tur gözlenmedi, hatanın kök
nedeninin düzeltildiği iddia edilmez. Ürün kodu değişmedi, yeni test gerektiren
kod değişikliği yok. Kanıt output/workspace-layout/password-reset-receipt.json.
Sunucu PID29032/session3110/8800 devam ediyor. Sonraki adım yeni parola
belirleyip mkaracan ile giriş. Yeni Oracle/Jenkins/SMTP/push yapılmadı.

Son kontrol: kullanıcı reset sonrasında yeni parolasını belirledi. Tarayıcıda
Mehmet KARACAN oturumu ve Yeni karşılaştırma ekranı görüldü. setup_required=false
tekrar doğrulandı. Kullanıcının açık profil menüsüne müdahale edilmedi. Parola
okunmadı veya araçla girilmedi. Sonraki adım ekran ve proje geçişlerinin kullanıcı
kontrolüdür. Screenshot output/workspace-layout/password-reset.png.

## Proje çalışma alanı ve kullanıcı girişi teslimi - 25 Ekim 2026

Kullanıcı onaylı düzen uygulandı. Uygulama adı Şema Karşılaştırma, kısaltma yok.
YEREL GELİŞTİRME bandı, tekrar eden ORACLE başlığı, üst breadcrumb ve tarayıcı
başlığındaki marka eki kaldırıldı. Sidebar açık temada logo ile aynı yüzeyde.
İçerik kullanılabilir genişliği doldurur. Alt bilgi ortalı ve sayfa altındadır.
Profil seçimi/adı üstte tek bölüm, Şema Eşleştirmeleri sekmesi ikon ve sayıyla
belirgin. Git/Oracle/sonuç ikonları anlamlı tema renkleri kullanır. Durum PARTIAL
Kısmen Tamamlandı kalır, işlem aşamasının bitişi İşlem Bitti olarak ayrılır.

Proje izolasyonu: bağlantı, profil, eşleştirme ve run yanında ayarlar da proje
kimliğinde sürümlendi. Eski defaults yalnız SKY içindir, başka proje ondan ayar
miras almaz. UI X-ODMG-Project gönderir, liste query'siyle çelişemez. Detail,
access-info, connection test, result/summary/artifact ve başlatma seçili projeyi
kontrol eder. Farklı proje kaydı 404, payload çelişkisi 422. Legacy kapsam
verilmemiş API istekleri yalnız SKY'ye gider, projeler arası toplu liste yok.
Proje formu key ile sıfırlanır. Generation guard geç yanıtı reddeder. Eski
formun save sonrası run veya connection test başlatması unmount ile kesilir.
Ayarlar run spec içinde dondurulur. Bağlantı test bütçesi de kendi projesinden.
Eşzamanlı sınır proje bazında, host tavanı 4. Terminal claim kapasite tüketmez.

Tek kullanıcı mkaracan / Mehmet KARACAN. Parola yerel ilk girişte belirlenir,
varsayılan parola yok. Salt+scrypt, opaque 8 saatlik oturum, DB'de yalnız token
hash'i, HttpOnly/SameSite strict cookie, giriş deneme sınırı ve çıkış iptali var.
Proxy modu korunur. --local-preview artık parolalıdır ve yalnız loopback'e
bağlanır, allow_password_setup yalnız bu açık yerel bootstrap modunda etkin.
Ağ parola servisinde setup kapalıdır, loopback reverse proxy bunu açamaz.
Ortak capability aynı kalır, parola oturumunda gerçek actor audit'e yazılır.
Kullanıcı parolasını henüz belirlemedi. Gerçek hesabın ilk kurulumu kullanıcıya
bırakıldı. Sentetik parola/giriş/çıkış API testleri PASS, ortak TLS dağıtımı NOT_RUN.

Çalışma ayrıntısına SQL içermeyen /summary endpoint'i ve RunSummary kartları
eklendi. Fark sayısı UNKNOWN hariç, ham counts değiştirilmez. Eksik sayı null
kalır. Envanter türleri açıklama/yetkiyi nesne toplamına katmaz. Birden çok hedef
aynı source owner/digest'i tekrar saymaz. scan_views immutable hash kaydıdır.
#55 arşivinden yalnız scan-summary.json ve ilgili manifest satırı tarayıcıyla
okundu. Plan/scope/byte/hash doğrulandı, özel SQLite kaydına bağlandı. Yeni
Oracle/Jenkins işi veya SMTP yok. 3805 kaynak,11946 doğrulanmış fark,1381 hazır,
655 inceleme,136 engel,3 UNKNOWN. Kaynak envanteri PARTIAL ve alt sınır notu var.
SQL dosyası indirilmedi. Frozen plan/DDL/kanıt kararları değiştirilmedi.

Dosyalar: control/{api,store,password_auth,summary,runner,queue,results,
jenkins_browser}.py, tools/ui_server.py, web/src/{App,AuthGate,ComparisonForm,
Connections,ConnectionWorkspace,SchemaMappings,SettingsPage,RunSummary,
UiPreferences}.tsx, api.ts,index.css,translations.ts ve ilgili testler.
Plan docs/superpowers/plans/2026-10-25-project-workspace.md.

Doğrulama: Python tam suite 1096 PASS /92.98 sn, 1 önceki Starlette/httpx uyarısı.
Frontend 35 PASS /13 dosya. Üretim build PASS, lint 0 hata/4 önceki uyarı.
Bağımsız final reviewer iki Important bulgu bildirdi: terminal claimed kaydı
kapasiteyi kilitliyordu, ağ servisinde proxy ilk kurulum açabiliyordu. İkisi de
RED→GREEN, review-green.log 9 PASS, ardından tam suite PASS. Minor/declined yok.

Tarayıcı: yeni karşılaştırma, bağlantılar ve eşleştirmeler 320 px/scrollWidth320.
Sonuç ekranı da scrollWidth320, alan tabloları kendi alanında yatay kayar.
TR/EN, açık/koyu ve gerçek kart sayıları kontrol edildi. Screenshot bu tur
çalıştı. Önceki screenshot UNAVAILABLE kaydı bu tura uygulanmaz. Viewport
reset sonrası kaydedilen run-summary.png güncel tam ekran kanıtıdır.
Kanıt output/workspace-layout/{python-tests.log,python-tests.xml,frontend-tests.log,
build.log,lint.log,review-red.log,review-green.log,connection-race-red.log,
scan-summary-55.json,scan-manifest-55.json,scan-import-receipt.json,dom-metrics.json,
run-summary.png,login.png,sql-hashes-check.json,diff-check.log}.

Sonraki somut adım: http://127.0.0.1:8800 üzerindeki İlk Giriş ekranında kullanıcı
kendi parolasını belirler, mkaracan ile giriş yapıp görünümü inceler. Sunucunun
son PID/session bilgisi output/workspace-layout/server-receipt.json içinde.
Canlı Oracle kabulü, yeni Jenkins kurulumu, SMTP ve dış push bu tur NOT_RUN.

## Arayüz okunabilirliği, dil ve tema teslimi - 25 Ekim 2026

Önceki şema eşleştirmesi teslimi tamamlandı. Yeni kullanıcı kapsamı da uygulandı.
Mevcut React/shadcn korundu. Ana metin 16 px, yardımcı metin en az 13 px,
SQL/kanıt metni 14 px oldu. Kontroller büyütüldü. Bağlantı formunda önce
Bağlantı Türü, sonra Bağlantı Adı var. Alan etiketlerinin yazımı tutarlı.
Bağlantı adındaki orta nokta sunumda tire olur, kayıtlı spec sessizce değişmez.
Türkçe yardım metni kaynak/hedef seçimi için Şema eşleştirmeleri sekmesini gösterir.

TR/EN ve açık/koyu tema üst çubuktan seçilir. Sürümlü tarayıcı kaydı yalnız
locale/theme taşır, sır içermez. Depolama kapalıysa bellekten çalışır.
Sekmeler arası tercih güncellenir. Sayfa dili ve tarih/sayı biçimi değişir.
SQL, nesne adları, frozen kapsam ve özgün Türkçe gerekçeler korunur. İngilizce
sonuç ekranı özgün gerekçenin Türkçe olduğunu belirtir. Proje ve diğer seçimler
ortak Radix Select kullanır, odak/seçim/menü temaya uyar. RunDetail ayrı yüklenir.

Dosyalar: web/src/{preferences.ts,translations.ts,UiPreferences.tsx,
ChoiceSelect.tsx,UiPreferences.test.tsx,UiLanguage.test.tsx,index.css,
object-results.css,api.ts,resultApi.ts,App.tsx,Connections.tsx} ve diğer görünür
UI bileşenleri, components/ui/{select,dialog,sheet}.tsx, test-setup.ts,
vite.config.ts. Sözleşme/motor/backend bu UI aşamasında değiştirilmedi.

Doğrulama: npm test -- --run, 28 PASS /11 dosya, 25 Ekim 00:26:03,
16.54 sn. npm run build PASS. npm run lint 0 hata, 4 önceki uyarı.
Radix/JSDOM testleri iki worker ile çalışır. Bağımsız son incelemede bulunan
geçici mesaj çevirisi, koyu durum kontrastı, eksik alan/kategori çevirileri ve
SQL font boyutu düzeltildi. Davranış regresyonları RED→GREEN doğrulandı.
Önceki şema aşamasının Python1087PASS kanıtı output/schema-selection altında.
UI-only değişiklikten sonra Python tekrar çalıştırılmadı, güncel Python NOT_RUN.

Tarayıcıda TR/EN, iki tema, form sırası ve menü doğrulandı. Örneklenen metinlerde
minimum 13 px, minimum kontrast açıkta 5.62:1, koyuda 7.37:1. 320 px viewport'ta
bağlantı sayfasının scrollWidth değeri 320 px. Düzenleme dialog'u 16..304 px,
action düğmeleri sınır içinde, taşma yok. Viewport 1280 px'e ve tercihler TR/açık
haline döndürüldü. Tam WCAG kabulü ve yüzde 200 browser zoom NOT_RUN.
Ekran görüntüsü API'si mevcut/eski ve yeni tab'da capture hatası verdi.
Screenshot UNAVAILABLE, eski görseller güncel kanıt diye kullanılmadı.

TM Forum kaynakları ve uygulanabilirlik docs/ARAYUZ_STANDARTLARI.md içinde.
Belirli TMF Open API/ODA kimliği ve kurumun zorunlu profil/versiyon listesi yok.
Üyelikten sertifikasyon çıkarılmadı, resmi conformance NOT_RUN.

Kanıt: output/ui-preferences/{tests.log,build.log,lint.log,dom-metrics.json,
preferences-red.log,project-red.log,error-red.log,theme-label-red.log,
object-label-red.log,sql-hashes-check.json,diff-check.log}. Örneklenen üç SQL
hash'i önceki aşamayla aynı. Yeni Oracle/Jenkins/SMTP/push yapılmadı.
Yerel UI http://127.0.0.1:8800, PID35708/session97103. Ortak dağıtım NOT_RUN.
Sonraki somut adım: kullanıcının güncel ekranda font/tema/dil ve proje menüsünü
kontrol etmesi. Kurumsal standart profili sağlanırsa o profile özel kabul yapılır.

## Şema eşleştirmeleri teslimi - 24 Ekim 2026

Bağlantı hesabı ve karşılaştırılan şema ayrıldı. Kullanıcının son yerleşim
isteğine göre Bağlantılar ekranında Bağlantılar ve Şema eşleştirmeleri sekmeleri
var. İsimli, sürümlü eşleştirme kaydedilir. Yeni karşılaştırma kaydı seçer.
Control models/store/API schema_mapping ve profile mapping_id/revision eklendi.
Her hedef kendi alt kümesini kullanır. Aynı owner adı şartı ve katalog yetki
kontrolü korunur. Eski kayıtlar ve frozen run yeniden yazılmaz. Jenkins semantik
fingerprint'i eşdeğer açık kapsamda aynı, farklı kapsamda farklı kalır.

Dosyalar: control/{models,store,api,runner,jenkins_browser}.py,
web/src/{ConnectionWorkspace,SchemaMappings,TargetSchemaMappings,ComparisonForm,
RunSchemaScope,App,Connections}.tsx, api.ts ve ilgili testler.
Metin temizliği birinci taraf Markdown ve sunum dosyalarında yapıldı. Kod/SQL
noktalı virgülleri, vendor/reference ve kanıt hash'leri korundu. 3 SQL dosyası
SHA-256 birebir aynı. Kalan üretici/uzun tire taramasında eşleşme yok.

Doğrulama: tam Python1087PASS /145.09sn, frontend21PASS /9dosya, buildPASS,
lint0error/4öncekiwarning. Python1mevcut Starlette/httpx deprecation uyarısı.
Bağımsız inceleme 96 ve23 ilgili Python testi ayrıca geçti. Profil dropdown'u
başka seçimden profile dönerken kapsamı siliyordu. Yeni test RED→GREEN,
21 frontend testi düzeltmeden sonra geçti. Teknik test belgesindeki literal
noktalaması da anlamı korunarak düzeltildi. Açık işlevsel bulgu yok.

Kanıt output/schema-selection/{python-tests.log,python-tests.xml,
frontend-tests.log,build.log,lint.log,copy-check.json,mapping-editor.png,
mapping-catalog.png,comparison-picker.png}. Tarayıcıdan mevcut SKY Git → PROD
TTBP kapsamı v1 eşleştirme olarak kaydedildi ve karşılaştırma dropdown'unda
seçildi. Yeni profil/run başlatılmadı, credential değiştirilmedi. Yerel sunucu
PID35708/session97103, 127.0.0.1:8800. Canlı Oracle kabulü, yeni Jenkins
kurulumu ve SMTP bu tur NOT_RUN. Ortak dağıtım/otomatik Jenkins NOT_RUN.

Sonraki kullanıcı kapsamı: okunabilir fontlar, TR/EN, koyu tema, proje menüsü,
form sırası ve Bağlantı Türü yazımı, bağlantı adında nokta yerine tire,
TM Forum uygulanabilirlik kontrolü. Bu yeni UI işi henüz uygulanmadı.

## Git token alanları ve bağlantı düzenleme - 24 Ekim 2026

Connections.tsx: Git kullanıcı adı/Erişim token'ı ve Bitbucket kişisel HTTP
token oluşturma yönergesi, düzenlemede kayıtlı kullanıcı adı + kayıtlı sır
durumu. Token geri dönmez, boş değer korunur. control/api.py access-info
yalnız admin/shared, no-store ve revision doğrulamalı, frozen spec değişmez.
Connections.test.tsx üç RED→GREEN test (geri yükleme, geç yanıt, yükleme hatası),
test_control_api.py sır sızmama/koruma/anonim/rol/sürüm kontrolleri.
Doğrulama: frontend14PASS, buildPASS, lint0error/4öncekiwarning, ilgili
Python36PASS/1mevcutdeprecationwarning. Tarayıcı gerçek kayıt üzerinde yalnız
görüntüleme doğrulandı, output/connection-token-ui/edit-git.png.
Saklama belgeleri CODEX_ARAYUZLERI ve UI_CALISTIRMA_VE_DAGITIM içinde güncel.
Yerel sunucu PID18448/session12479. Yeni Oracle/Jenkins/SMTP/push NOT_RUN,
ortak ortam dağıtımı/otomatikJenkins NOT_RUN. Açık engel yok, sonraki adım
kullanıcı UI kontrolü. Ayrıntılı dosya/komut kanıtı yz/DEVIR.md üst başlığında.

## Kalıcı iki panelli sonuç çalışma alanı - 24 Ekim 2026

Kullanıcının sol liste/sağ karşılaştırma ve Git benzeri görünüm talimatı
uygulandı. ObjectResults sol gezinme, ObjectComparisonPanel sağ inline
karşılaştırma, önceki Sheet kaldırıldı/yeniden adlandırıldı. İlk nesne
otomatik açılır, arama/tür/sayfa değişiminde uygun ilk kayıt seçilir.
Kaynak-istenen yeşil, hedef-mevcut kırmızı, UNKNOWN sarı, INFORMATIONAL
nötrdür. Veri/kararlar ve gerçekSQLler değişmedi. İşlem/DDL sekmesi aynı
paneldedir. Tamamlanmış Jenkins koşusunda özet katlanır, sonuç öncelikli.

Dosyalar: web/src/{ObjectResults,ObjectComparisonPanel,JenkinsRunDetail,
ObjectResults.test}.tsx,object-results.css, docs/NESNE_SONUCLARI.md ve
plan docs/superpowers/plans/2026-10-24-results-workspace.md.
Frontend11testPASS, productionbuildPASS, lint0error/4öncekiwarning.
Modal-yok/iki-panel/nesne değişiminde gecikmiş yanıt testleri RED→GREEN.
Bağımsıztekinceleme önemli/kritikbulgu bulmadı,7ilgilitesti ayrıca doğruladı.
Backend/motor değişmediği için Python testleri bu tur NOT_RUN, önceki
1070PASS kanıtı tarihsel olarak korunur. YeniOracle/Jenkins/SMTP/push0.

Mevcut#55ile yerelUI tarayıcıda kontrol edildi. Kanıt output/results-workspace/
{tests.log,build.log,lint.log,workspace-55.png}. Sunucu öncekiPID27668/
session7901, yeniden başlatılmadı, statikbuild güncellendi. SSO/ortak
dağıtım, otomatikJenkinsaktarımı ve mobilkabul öncekiNOT_RUN kapılarıdır.

## Nesne bazlı sonuç UI teslimi - 24 Ekim 2026

Kullanıcının kendi komponent/yöntem tercihine göre mevcut shadcn ailesi
kullanıldı, referans Schema Compare frontend/comparator kodu taşınmadı.
Plan docs/superpowers/plans/2026-10-24-object-results.md tamamlandı, ayrıntı
docs/NESNE_SONUCLARI.md. Mevcut branch/diff korundu, commit/push yok.

Değişen dosyalar: control/result_models.py,results.py, store.py yeni
comparison_views tablosu, api.py iki sonuç endpoint'i, web resultApi,
ObjectResults,ObjectDifferenceSheet,object-results.css ve RunDetail/
JenkinsRunDetail bağlantısı, tools/ui_result_projection.mjs ve
ui_import_result_view.py. Yeni testler test_control_results.py,
ObjectResults.test.tsx, ui_result_projection.test.mjs.

Çalışan davranış: hedef/nesne türü/ad filtresi,25nesnelik liste, seçilince
genişSheet içinde kolon/kısıt/indeks/diğer alanlar50kayıtta, ilişkili
işlemler10kayıtta sayfalanır. Kaynak=after/hedef=before. KNOWNnull,UNKNOWN,
ABSENT,NOT_APPLICABLE ayrıdır. Gizlenmiş tanım bu durumları maskelemez.
Gerçek COMMENTdisplay_name aramada/başlıkta korunur, canonicalkey değişmez.
Plan/source/target/run,counts,changeIDkapanışı ve güvenliSQLpath doğrulanır.
Aktarım yoksa available=false,total=null. UI yeni fark/Oracle sorgusu yapmaz.

Gerçek#55 sonucu:3112nesne,11949kayıt(11946doğrulanmış+3UNKNOWN),4736işlem.
PlanID a5787df900c0eced4dcb269fd44a67b77530077c7140cac7e722dbf80b26dcff,
UIrun37151129195546f0aee856341450e0e3. Kaynak/targetSQLgövdeleriaktarılmadı,
2631redacteddefinition kaydı,değeri dolu redactedvalue0. İlgiliDDL aynı
Jenkinsbuild'in yetkili /*view*/ linkinden açılır. YeniOraclebağlantısı0,
yeniJenkinskoşusu0, SMTP0, SQLexecutionNOT_EXECUTED.

Tarayıcı aktarımı 2000dizi sınırı nedeniyle500'lükparçalarla yapıldı ve
sayılar doğrulandı. JenkinsJSONviewer charset windows-1254 idi, canonical
UTF8 metadata gözlenen karaktersetinden özgünUTF8'e döndürüldü. İlk kendi
geliştirme importumuzun bozuk kodlaması bir defa exactoldhash denetimi,
metadata yedeği ve audit ile düzeltildi, genelimmutableimport gevşetilmedi.
Kanıt transport-proof-55.json /misdecoded-import-backup-55.json. Yalnız
SQLgövdesizmetadata özelstate/output'a yazıldı, hamplan/SQLindirilmedi.

Doğrulama: `.venv/Scripts/python.exe -m pytest -q
--junitxml=output/object-results/tests-delivery.xml`:1070PASS/224.31sn,
failure/error/skip0. `cd web; npm test`:10PASS, npmrunbuildPASS,
node--test tools/ui_result_projection.test.mjs:3PASS, contracts7schema/
8exampleVERIFIED. Lint0error/4öncekiwarning. Tek bağımsız inceleme ikiP2
buldu, UNKNOWNomission ve COMMENTdisplayname RED→GREEN düzeltildi.
Masaüstünde gerçekBAYS_ADRES_DEGISIKLIK_TALEP tablosunun ACIKLAMA255CHAR
kaynak/2000BYTEhedef değerleri, ilgili23işlem ve Türkçegerekçeler doğrulandı.
COMMENTaraması13gerçekkolonadıyla sonuçverdi. 390pxoverrideAPI uygulanmadı
(DOM1280/1265kaldı), mobilkabulNOT_RUN, geçiciaayarreset/testtabkapalı.

Kanıt output/object-results/{import-55-receipt.json,tests-delivery.xml,
ui-tests.log,node-tests.log,ui-build.log,review-green.log,table-fields-55.png,
table-operations-55.png}. MetadataSHA
51379d49e9fbb4cf59a4ca23cc61600c3e80f5552f0ff620af7ff9337a74f75b.
YerelUI http://127.0.0.1:8800 serverPID27668/session7901. Gerçektablo
ayrıntısı açık bırakıldı. Sonrakiadım: servis hesabı/ortakdeployment ile
harici planmetadataaktarımını otomatikleştir, tam eşit alan envanteri için
ileride kapalı snapshot sunum sözleşmesi gerekir. Bunlar ve OracleSOURCE
canlıkabul öncekiNOT_RUN kapılarıdır.

## Ortak proje UI ve canlı koşu teslimi - 24 Ekim 2026

Kullanıcının mevcut Git/Oracle bağlantıları, tek ortak yetki, üst proje seçimi,
UI’den canlı koşu ve yalnız mkaracan@innova.com.tr mail talimatı uygulandı.
Jenkins servis hesabı bulunmadığı için açık tarayıcı aktarımı kullanıldı,
otomatik Jenkins API/ortak deployment tamamlanmış gibi sunulmaz. ADR-024 ve
docs/superpowers/plans/2026-10-24-projects-shared-live.md. Commit/push yok.

### Uygulama ve offline doğrulama - PASS

- control/models,store,api,jenkins_browser: proje CRUD/default SKY/legacy uyumu,
  bağlantı-profil-run kapsamı, çapraz proje reddi, değişmez proje üyeliği.
  İmzalı kimlik doğrulamasından sonra tek shared yetkisi, anonim proxy hâlâ401.
- web App,ProjectSwitcher,JenkinsRunDetail,ComparisonForm,Connections,RunDetail,
  api,index: üst proje seçimi/ekleme, kapsamlı geçmiş, ortak kullanım etiketleri.
  Kullanıcı/rol/model bilgisi yok, geciken A başlatma yanıtı B ekranını açamaz.
- tools/ui_import_connections.py: alias tabanlı, idempotent, var olan düzenlemeyi
  ezmeyen şifreli import. Git DDL, PROD/TTBP Oracle, kaynak Oracle toplam3kayıt
  .local/ui-state vault’ta. Açık parola kod/belge/UI yanıtında bulunmadı.
- approved spec hash, connection/credential revision ve hedef eşlemesiyle
  server-owned Jenkins browser handoff. state-root/jenkins-bindings.json
  kalıcıdır, eşleşmeyen herhangi bir proje yerel worker’a düşmez. Bekleyen
  istek scheduler’a girmez. ui_link_jenkins_run.py yalnız metadata’yı bağlar,
  zaman/build/Git/hedef/ölçüm kontrolü, atomik tek build→tek kayıt ve overwrite
  reddi vardır. Normal aggregate UUID kimliği korunur, artifact yolu build
  numarasından kurulur. SQL Jenkins dışına kopyalanmadı.

Kanıt: `pytest -q --junitxml=output/shared-projects/tests-final.xml`:1062PASS,
161.63sn, son kalıcı binding ve canonical UUID ekleri dahil control/store/API/
import/acceptance30test11.21snPASS (tests-control-delivery.log). `cd web, npm
test`:6PASS; `npm run build`:PASS. Contracts7schema/8example VERIFIED, pipcheck
PASS, diff--check temiz. Lint0error/4warning (3shadcnfastrefresh +mevcutSQL
effect uyarısı). Tek bağımsız inceleme ikiP2 buldu, proje callback’i ve
duplicate/concurrent link testleri RED→GREEN. Gerçek aggregate UUID uyumu da
RED→GREEN. UI ekran kanıtı ui-result-55.png, bağlantılar ui-connections.png.

### Canlı Git→Oracle karşılaştırması - RAPORLANDI / PARTIAL

#55 UI native Karşılaştırmayı başlat → Jenkins’te başlat → TTBP/COMPARE Build
yoluyla çalıştı. UI id37151129195546f0aee856341450e0e3, canonical run
86c108c6-992f-4139-8ad0-47aad1aac20e. 16:45:15.798–17:03:55.614990 TSİ,
1119.81699sn = **18dk40sn**. Önceki73dk44sn’ye göre %74.6877 daha kısa,
yaklaşık55dk4sn tasarruf. İlk hedef okumasında değişiklik algılandı, ikinci
okuma tutarlı tamamlandı, tekrarın tamamı bu süreye dahildir.

Kaynak Git45690e2ce8030901ee196b96bdb8cc507ec6fe9b, cache HIT_VERIFIED.
5.690dosya hazırlığı22.8309sn (checkpoint okuma13.0227, yazma9.5133, parse0).
Ayrı kaynak Oracle metadata okuması8.2446sn/CAPTURED, eşleşen1269tablo.
Kaynak hazırlama ölçüsü bu ayrı Oracle okumasını içermez.

Rapor: kaynak3805gözlenenalt-sınır /11946bulunanfark /1381hazırDDL /655inceleme
/136üretilemeyenDDL /3UNKNOWN. Kanonik difference_count=null korunur, eksik
kapsam kesin toplam gibi sunulmaz. Bu yeni canlı plan eski SQL byte eşitliği
regresyonunun yerine geçmez. Gerçek SQL uygulanmadı.
http://jenkins.innova.com.tr/job/sky/job/oracle-db-migration-generator/55/artifact/output/runs/build-55/index.html

### Jenkins ve bildirim

Mevcut v25 job değişmedi: TTBP, Europe/Istanbul08:00, son20artifact, tekalıcı.
PipelineSHA1aad9c50649a51b46caea0769b41a519884e3ac890587ff84438ccd478ac730e
tekrar doğrulandı. Console emailext→Sending email to:mkaracan@innova.com.tr,
Finished:UNSTABLE. Mail tekalıcıya gönderildi, inbox teslimi ayrıca ölçülmedi.
Sonuç ve süre tools/ui_link_jenkins_run.py ile UI’ye bağlandı, yeniden başlatma
sonrası ekranda18dk40sn/22.8sn/DDLkısmenhazır ve gerçekraporlinki doğrulandı.
Kanıt output/shared-projects/{live-receipt.json,run-55.json,source-performance-55.json,
source-metadata-receipt-55.json,jenkins-55-console.final.txt,report-55-ui.txt,
report-55.png,ui-result-55.png}. SQL bundle indirilmedi.

Yerel UI http://127.0.0.1:8800, state `.local/ui-state`, serverPID35100/session39976.
Sonraki somut adım: kurum Jenkins servis hesabı ve ortak host/SSO bilgileri
sağlandığında ayrı UI job şablonunu kurarak otomatikbaşlatma/sonuçtakibini
ve ortak dağıtımı kabul et. Bu kapılar, doğrudan Oracle→Oracle canlı kabulü,
kurum ACL/secret/retention/agentkesinti testleri **NOT_RUN**.

## Ortak UI ilk uygulama teslimi - 24 Ekim 2026

Kullanıcı “Kurum içi ortak uygulama” seçti ve geliştirmeyi açıkça başlattı.
Yerel branch codex/shared-ui-oracle-source, önceki rapor/performance diff'i
korundu. Commit/push veya canlı Jenkins job değişikliği yapılmadı.

Uygulananlar:
- web/: React/TypeScript/Vite, resmi shadcn/Radix bileşenleri, Tailwind,
  TanStack Table. Git/Oracle kaynak seçimi, bağlantı/profil CRUD/test, başlat,
  gerçek aşama/süre, hedef sonuçları/arama/sayfalama ve DDL/kanıt çekmecesi.
  Ayar ekranı gerçek API'ye bağlı, 08:00 takvimi salt okunur, alıcı yalnız
  mkaracan@innova.com.tr. Yeni temiz preview'da gerçek/test bağlantısı yok.
- control/: kapalı doğrulama modelleri, sürümlü SQLite kayıt/audit ve Fernet
  credential vault, frozen run spec/credential revision, admin/operator/viewer
  kimlik doğrulaması ve bağlantı ACL, imzalı proxy ve açık loopback geliştirme
  modu, bağımsız worker, global iş sınırı, atomik FIFO claim, orphan recovery,
  deadline ve güvenli hata kodları. Bağlantı testleri ayrı process'te, parola
  byte'ları baş/son boşluklarıyla korunur. Üretim vault anahtarı dışarıdan gelir.
- source/oracle_reader.py, model/snapshot{,_io}.py, compare/snapshots.py,
  oracle/collector.py, plan/run/snapshot şemaları (kök ve paket), planning,
  emission, aggregate, bundle ve mevcut rapor template'leri: gerçek Oracle
  SOURCE origin/snapshot kimliği, sahte Git SHA yok. Kaynak dictionary eksikliği
  PARTIAL/UNKNOWN, bütün SOURCE evidence/context/property/capability referansları
  ayrı namespace. Raw DDL ve tam çok statement'lı COMMENT/GRANT blobları özel
  source dizininde atomik saklanıp hash ile yeniden okunur. Git legacy uyumlu.
- config/runtime.py, parsing/budgets.py, oracle/connection.py ve prepared cache:
  doğrulanan etkin bütçeler kullanılır, ayarlar cache kimliğine dahil edilir.
- tools/ui_server.py, control/jenkins.py, templates/jenkins-ui.groovy,
  tools/ui_jenkins_archive.py: yerel başlatıcı ve ayrı Jenkins UI job şablonu.
  API yalnız RUN_ID gönderir, yetkili Jenkins özel state'inden frozen girdiler
  okunur. Arşive repository/source/observations/control/vault kopyalanmaz.
  Mail yalnız hazırlanır, şablon kurulduğunda frozen bildirim seçimine göre
  tek izinli alıcı kullanılır. Bu tur SMTP/gerçek Jenkins tetikleme yok.
- pyproject ui extra, requirements-ui.lock ve web/package-lock.json, UI kurulum
  belgesi, ADR-023, mimari/arayüz/kaynak sözleşmesi, README ve aktif göreve
  kullanıcı kapsam eki. Ayrıntı docs/UI_CALISTIRMA_VE_DAGITIM.md.

Doğrulama (güncel workspace):
- .venv/Scripts/python.exe -m pytest -q --junitxml=output/shared-ui/tests-delivery.xml
  -> 1053 passed / 214.23sn, failure/error/skip 0. Log tests-delivery.log.
  Tek uyarı Starlette testclient'ın httpx deprecation bildirimi, test hatası yok.
- Çok statement'lı source sidecar blob/hash kontrolü genişletildikten sonra
  tests/unit/test_oracle_source.py -> 5 passed / 3.54sn.
- tools/check_contracts.py -> VERIFIED, 7 schema/8 example, pip check ->
  No broken requirements found. git diff --check temiz.
- web: npm test -> 3 passed, npm run build -> TS/Vite başarılı.
  npm run lint -> exit0, 5 uyarı (3 resmi shadcn fast-refresh export,
  2 fetch/effect set-state uyarısı), lint hatası yok.
- Bir bağımsız whole-change incelemesi tamamlandı. 7 önemli bulgu RED testlerle
  düzeltildi: source dictionary, evidence çakışması, nondefault Git branch,
  source raw kayıt, queue capacity/orphan, 200 kayıt scheduler sınırı,
  driver testi izolasyonu/bütçesi. README kaynak etiketi ve başarısız son
  aşama işareti de düzeltildi. Yeni inceleme döngüsü açılmadı.
- Tarayıcı QA8801 gerçek API: sentetik 127.0.0.1:9 Oracle form/profil kaydı,
  bağımsız worker ile SOURCE_CAPTURE_ERROR/FAILED, sonuç sayısı bilinmiyor,
  sıfır fark/sahte başarı yok. İzole bağlantı testi DPY-6005 gösterdi.
- Sentetik Git dosyası -> gerçek parser/compare/planner/SQL/bundle:
  run b30789819eff45b09144f93ddcce7f8d COMPLETE, 1 gerçek CREATE TABLE işlemi,
  SQL çekmecesinde doğrulandı. Kaynak 2.8sn/toplam4sn SENTETİK fixture ölçümüdür,
  canlı Oracle/73dakikalık koşunun hızlanması değildir.
- output/shared-ui/check-archive-fixture.py: tamamlanmış sentetik işin Jenkins
  HTML mail/arşiv hazırlığı VERIFIED, 3 SQL byte eşit, mail_sent=false.
- Kanıtlar output/shared-ui/{tests-delivery.xml,tests-delivery.log,review-red.log,
  review-green.log,browser-sql.png,preview.png}, tümü Git dışında.

Çalışan önizleme: http://127.0.0.1:8800/ , .local/ui-state temiz geliştirme
state'i. Başlatma: .venv/Scripts/python.exe tools/ui_server.py --local-preview
--root .local/ui-state --port 8800. Bu oturumda process9196/session72546,
sonraki oturumda PID'yi yeniden doğrulamadan kullanma. QA8801 kapatıldı.
Tarayıcı tab7 deliverable olarak bırakıldı. Yeniden açma komutu belgede.

Ayrı kabul durumları:
- Offline kod ve yerel UI: VERIFIED.
- Yeni Oracle→Oracle gerçek canlı kabul: NOT_RUN. Gerçek SQL uygulanmadı.
- Kurumsal SSO/secret sağlayıcısı/ACL, hash'li üretim platform lock,
  yeni Jenkins UI job, servis/retention/agent kesinti kabulü: NOT_RUN.
  API/worker aynı host/yerel disk/PID namespace gerektirir, çok hostlu SQLite
  paylaşımı yok. Üretim agent kaybı uzlaştırması ayrıca kabul edilmelidir.
- Eski canlı performans: #54 Bitbucket502 engeli sürüyor, yeni gerçek toplam
  süre ölçümü yok. Günlük TTBP08:00, tek alıcı, Jenkins-only korunur.

Sonraki somut adım: yerel UI'yi kullanıcıyla incelemek, mevcut kurum SSO/proxy,
Jenkins agent ve secret/ACL yerleşimini doğrulayıp ayrı UI job kurulumunu
somutlaştırmak, ardından yetkili gerçek Oracle→Oracle kabulü yapmak. UI kodunun
hazır olması ortak deployment veya canlı doğrulama tamamlandı demek değildir.

## UI ve ayar kapsamı - 24 Ekim 2026

Kullanıcı Git/Oracle kaynak seçimi, ekrandan karşılaştırma başlatma ve kodda
sabit uygun ayarları UI'ya taşıma kapsamını istedi. UI tercihi uygulayıcıya
bırakıldı: React/TypeScript/Vite +shadcn/ui/Radix/Tailwind +TanStack Table.
Kullanıcı yerleşim sorusuna “Kurum içi ortak uygulama” yanıtını verdi.

docs/UI_KAPSAMI_VE_AYARLAR.md eklendi: somut kod sabitleri/ayar adayları,
ekran-bileşen haritası, bağlantı/profil/çalışma/yönetici ayarları, etkin ayar
kopyası ve cache bağlama, ortak kullanım yetki/kuyruk koşulları. Henüz UI/API
veya DB source uygulanmadı. Mevcut SOURCE/plan/run Git commit bağımlılığı
DB source için gerçek kaynak kimliğine genişletilmeli, sahte Git SHA yok.

Sonraki adım ortak uygulamanın API/bağlantı/çalıştırma/Oracle source sözleşmesi
ve uygulama planı. Gerçek SSO/sır deposu/deployment adresi doğrulanmadı.
Yeni test/Oracle/Jenkins değişikliği NOT_RUN, bu tur kapsam belgesi ve devir
güncellemesi. Mevcut günlük iş, tek alıcı, salt okuma ve Jenkins-only korunur.

## Canlı süre ölçümü engeli - 24 Ekim 2026

Kullanıcının canlı karşılaştırma/tek alıcı mail isteğiyle normal v25 yapılandırma
tam metin SHA'sı yeniden kontrol edilip TTBP/COMPARE Jenkins#54 başlatıldı.
BLOCKED: kaynak Bitbucket Git endpoint'i ve ana sayfası502 Bad Gateway.
Jenkins20yeniden denemeden sonra3dk31sn sonunda kendisi FAILURE ile kapandı.
Kaynak hazırlama ve Oracle karşılaştırması NOT_RUN, bağlantı0/SQL NOT_EXECUTED.
Görünen3dk31sn geçerli karşılaştırma performansı sayılmaz, toplam ölçüm null.
Hata bildirimi yalnız mkaracan@innova.com.tr adresine gönderildi.
Kanıt output/live-performance-54/receipt.json,jenkins-54-console.final.txt,
build-54-failure.png. Kod/job ayarı değişmedi, yeni offline test NOT_RUN.
Normal v25/TTBP/08:00 ve tek mail alıcısı korundu. Sonraki adım Bitbucket
erişimi düzeldikten sonra canlı koşuyu tekrarlayıp gerçek toplam süreyi ölçmek.

## Kaynak hazırlama performansı teslimi - 24 Ekim 2026

Kullanıcı devam talimatıyla checkpoint sonrası çalışma tamamlandı. Jenkins#48
eski kaynak hazırlığını aynı5.688ham dosya ile ölçtü:28dk25sn, büyük paket
gövdeleri24dk37sn, beş240sn timeout yaklaşık20dk4sn. Tam snapshot#42 ile byte
aynı. Eski47dk'nın tam dosya dağılımı bulunmayan konsoldan uydurulmadı.

Yeni prepared-source checkpoint Jenkins v25'te etkin. #53 kaynak CLI24,35sn,
5.691hazırlık dosyası byte eşit, zenginleştirilmiş source, plan kararları ve
sayaçları aynı,1.381SQL byte eşit. Regression header'ı yalnız eski plan ID ile
karşılaştırıldı, provenance farkı gerçek ürün artifact'inde gizlenmedi.
#53 report refresh#47'nin5.285değişmez dosyasını/planını/SQL'ini korudu.
Genel web/mail süresi üstte tek73dk44sn, özgün#42 karşılaştırmasıdır.
Genel DDL /*view*/ gerçek tıklamayla açıldı. Mail yalnız mkaracan@innova.com.tr.
#53 UNSTABLE mevcut PARTIAL/UNKNOWN/inceleme/engelleri korur.

Offline doğrulama:1022passed/135,04sn/failure-error-skip0,
tests-resume.xml,7schema/8example VERIFIED,133paket dosyası wheel ile byte
eşit. Jenkins#52 ortam SUCCESS, v25 normal Pipeline tam metni yeniden okundu,
TTBP/08:00 ve tek alıcı doğrulandı, geçici audit kaldırıldı.
Kaynak/DDL büyük-input kanıtı verification-53-receipt.json,
presentation-53-receipt.json ve jenkins-53-console.final.txt,
report-53-top.png hepsi output/source-performance/ altında. Release ve hash
ayrıntıları yz/DEVIR.md'nin ilk bölümünde. Yeni belge:
docs/KAYNAK_HAZIRLAMA_PERFORMANSI.md. Ürün değişenleri önceki checkpoint'te.

Canlı Oracle kabulü/yeni toplam süre NOT_RUN, bu tur bağlantı0/SQL NOT_EXECUTED.
#49 sabah hedef capture CHANGED_DURING_CAPTURE olduğu için başarılı kabul
sayılmaz, tamamlanmış kaynak hazırlığı bağımsız doğrulanarak güncel checkpoint
seed edildi. Aynı kaynak/profil/parserde hızlanma ölçüldü, yeni girdide ilk parse
maliyeti sürer. Cache4giriş/1GiB dolunca store atlanır, eviction yok.
Sonraki somut adım günlük yeni koşuda toplam süre/cache HIT ve taze hedef
capture sonucunu kontrol etmek, ardından22dk8sn hedef capture maliyetini
incelemek. Dış Git push/commit ve Oracle DDL/DML/COMPILE yapılmadı.

## 17:50 checkpoint - kaynak hazırlama performansı, 23 Ekim 2026

Kullanıcı17:50'de checkpoint istedi, devamı kullanıcı mesajıyla. Yeni kod henüz
Jenkins'e alınmadı. Normal v23/TTBP/08:00 geri yüklenip tam metinle doğrulandı.
Jenkins#48 eski#42 kaynak girdileriyle salt offline profil çıkarıyor, Oracle/mail0.
Dört büyük paket240sn timeout, diğer pek çok dosya birkaç ms cache hit.
Tam profil/snapshot eşitliği sonucu henüz PENDING, koşuyu yeniden başlatma.

Uygulandı: doğrulanmış bütün source hazırlama checkpoint'i (Git/raw/profile/
hazırlama kodu/Python kimliği, PARTIAL/UNKNOWN korunur), CLI ayrı faz süreleri,
Jenkins env/performance receipt, genel web/mail süresi başlık altında. Kaynak/
hedef semantiği ve parser response cache timeout politikası değiştirilmedi.
tests/unit/test_prepared_source_cache.py ve iki süre testi kırmızı→yeşil.
72 odaklı test, ilk full1020passed/120,96sn. RecursionError review düzeltmesi
sonrası son full1022passed/121,06sn, failure/error/skip0, XML
output/source-performance/tests-final.xml. Wheel133 dosya byte eşitliğiyle hazır,
contracts7/8 VERIFIED. Sonuç/SQL eşitliğinin gerçek büyük girdide kontrolü,
Jenkins hız ölçümü, release/üst süreli rapor yayını PENDING.

Sonraki adım #48 profile-receipt.json'u oku, snapshot_byte_equal doğrulanınca
yeni cache hit'ini aynı girdilerle ölç, sabit target ile operation/DDL eşitliğini
doğrula. Yeni Oracle koşusu/SQL execution/Git push NOT_RUN. Ayrıntılı dosya,
hash ve sonraki komutlar yz/DEVIR.md üst checkpoint başlığında.

## Jenkins v23 erişim/görünüm teslimi ve süre incelemesi - 23 Ekim 2026

Tamamlandı: kaynak esaslı belirgin sayaçlar, geniş hedef kartı, Genel DDL
görüntüle ve Jenkins dosya indirme ekranı. Web CSS harici dosyadadır,
CSP değişmedi. test_report_jenkins_access.py iki kırmızı testle Jenkins
/*view*/ ve offline göreli link davranışını sınar. Tam suite1003 passed/89,99sn,
skip/fail0, contracts7/8 VERIFIED, wheel132 dosya byte eşit. Değişen uygulama:
reporting/view.py, templates/run.html.j2, scan_scope.html.j2, assets/report.css,
tools/jenkins_notification.py, HTML standardı güncellendi.

Jenkins#46 ortam SUCCESS, #47 sabit#45 verisinin görünümünü yeniledi, UNSTABLE.
Mail yalnız mkaracan@innova.com.tr. 1.381 SQL/5.285 immutable dosya, plan ID/hash
ve sayılar korundu. Yeni Oracle0, SQL uygulanmadı. Genel DDL ve ZIP listesi
gerçek tarayıcı tıklamasıyla açıldı, source toplam28px/700, yatay taşma yok.
Normal TTBP/08:00 Pipeline tam yeniden okundu, SHA
0ec8315de7151d19e83a6290fe3fd4fff6532a6d8aa137bd6340cbfc425dfaaa.
Kanıt output/report-access-jenkins/delivery-verification.json ve final-report.png.

73dk44sn süre incelemesi: korunan#42 workspace receipt'leri okundu.
46dk59 başlangıç/kaynak hazırlık,26sn kaynak metadata+scope,22dk8 target
capture,4dk11 sonraki snapshot/plan/bundle/rapor. Target grammar_projection
15dk26, ddl_reads4dk59. Kaynak5.688 dosyanın iç faz/cache süreleri yok,
soğuk/sıcak ayrımı kanıtlanmadı. performance-42-{evidence,analysis}.json.
Sonraki adım kaynak faz/tür/cache ölçümü ve pahalı parse girdilerinin ayrımı.
Performans düzeltmesi/yeni canlı ölçüm NOT_RUN, Oracle DDL kabulü/Git push NOT_RUN.
Kaynak PARTIAL/UNKNOWN3 korunur. Ayrıntılar yz/DEVIR.md üst başlığındadır.

## Jenkins v22 teslimi - 23 Ekim 2026

Kullanıcı yetkisiyle v22 Jenkins'e alındı. #44 ortam kontrolü SUCCESS,
#45, #42'nin görünümünü Oracle bağlantısız yenileyip yalnız
mkaracan@innova.com.tr adresine mail gönderdi. 1.381 SQL/5.284 immutable dosya
birebir aynı, source snapshot'tan3.803 nesnelik kaynak sayacı eklendi (PARTIAL,
alt sınır). Mevcut UNKNOWN3 ve136 üretilemeyen işlem gizlenmedi. Normal
TTBP/Europe-Istanbul08:00/COMPARE yeni release ile geri kaydedilip okundu.
1001test/113,44sn, contracts7/8VERIFIED, wheel132dosya byte eşitliği.
Detay/kanıt: yz/DEVIR.md ve output/report-scan-scope-jenkins/.

Aktif kullanıcı devamı: Genel DDL erişimini ve genel sayfa görünümünü düzelt,
sonra#42'nin73dk44sn performans maliyetini incele. SQL dosyası var ve Jenkins
/*view*/ yolu çalışıyor. İlk inceleme artifact sandbox/inline CSS ayrımını
gösteriyor, CSP gevşetilmeyecek. Yeni düzeltme uygulaması henüz tamamlanmadı.
Oracle DDL kabulü/Git push NOT_RUN, referans projeler salt okunur.

## Kaynak nesne envanteri - 23 Ekim 2026

Kullanıcının son talimatıyla HTML/mail Tarama Kapsamı bölümü yalnız seçili
kaynak şemalarındaki nesneleri sayar. Değişmeyen nesneler dahildir, kaynak
birden fazla hedefte tekrar sayılmaz. Tür dağılımı aynı kaynak toplamına
aittir. COMMENT/GRANT metadata kayıtları toplamı artırmaz, kapsam dışı teknik
nesne politikası korunur. Paket tanımı/gövdesi ayrı nesnelerdir.

Snapshot'tan türetilen scan-summary.json plan ID ve source/target digest'ine
bağlıdır ve bundle manifestinde hash'lenir. Genel web, hedef web ve mail aynı
kaynağı kullanır. Eski arşivlerde özet yoksa Bilinmiyor, kaynak envanteri
eksikse gözlenen alt sınır açıklaması vardır. Hedef envanterinin eksikliği
kaynak sayısını veya kaynak kapsam açıklamasını değiştirmez. Plan şeması,
karşılaştırma kararları ve SQL üretim kuralları değiştirilmedi.

Değişenler: reporting/{inventory,view,render}.py, reporting/templates ve
assets/report.css, artifacts/bundle.py, runtime/{worker,aggregate}.py,
tools/jenkins_{notification,report_refresh}.py, test_report_scan_scope.py,
HTML standardı ve uygulama/devir belgeleri.

Doğrulama: `.venv/Scripts/python.exe -m pytest -q
--junitxml=output/report-scan-scope-tests-final.xml`: **999 passed /124,58 sn**.
9 yeni test, önce eksik özellik ve ardından kaynak odaklı düzeltme için
kırmızı test görüldü. Contracts VERIFIED (7 şema/8 örnek). Wheel üretildi,
ayrı dizine kurulu wheel'den 21.228 byte mail render'ı doğrulandı. Sentetik
görünüm 390/820/1440 px çerçevelerde incelendi, gerçek DDL kullanılmadı.
Sentetik görünüm yenilemesinde 13 SQL ve28 immutable dosya birebir korundu.

Offline uygulama/doğrulama PASSED. Yeni Oracle bağlantısı0, canlı Oracle
kabulü NOT_RUN. Jenkins kurulumu/dağıtımı, SMTP gönderimi ve Git push bu tur
NOT_RUN, mevcut08:00/TTBP/tek alıcı/Jenkins-only politikaları değiştirilmedi.
Sonraki somut adım: yeni release Jenkins'e alınacağı zaman yeni karşılaştırma
çıktısındaki source envanter toplamını doğrulamak, eski özetsiz arşivden sayı
uydurmamak. Aktif görev dosyasının kapsamı yeniden yazılmadı.

## Süre sunumunun sadeleştirilmesi - 21 Ekim 2026

Mail ve genel rapordaki üst süre kutusu kaldırıldı. Yalnız özgün karşılaştırma
süresi alt Kaynak ve İzlenebilirlik bölümünde11px gri nottur. Başlangıç/bitiş,
TSİ ve rapor yenileme süresi görünmez, comparison-timing.json ve run.json
zamanları korunur. DDL/plan kararları ve veri toplama kodu değiştirilmedi.
990 test geçti (104,23sn), contracts VERIFIED. Yeni v21 wheel130 paket
byte eşitliğiyle doğrulandı. Jenkins #41 yalnız #40 görünümünü yeniliyor,
normal TTBP/PROD08:00 akışı v21 olarak geri kaydedildi. Oracle bağlantısı0,
DDL/DML/COMPILE0, mail tek onaylı alıcı, SQL arşivi yalnız Jenkins.
Jenkins #41 UNSTABLE tamamlandı,1.379 SQL ve5.284 immutable dosya byte olarak aynı. Plan ID ve kararlar #40 ile aynı, yeni karşılaştırma/SQL üretimi/Oracle bağlantısı0. Genel mail tek onaylı alıcıya gönderildi. Gönderilen HTML ve web raporunda eski saat etiketleri0, üst kutu0, alt not11px, yatay taşma0 doğrulandı. Normal v21 hash b9cbc40c923a2e0953b3af9b37ca692a93f301a27d129c88789a615bed7bf681 ve08:00/COMPARE ayarı geri okundu. Kanıt output/timing-refinement altında Git dışında.

## Kalan 493 kayıt ve mail sütun düzeltmesi - 21 Ekim 2026

Bu bölüm önceki 493 açık kayıt durumunun yerine geçer. Source ve target her
zaman salt okunur kaldı, DDL/DML/COMPILE çalıştırılmadı. Sabit kaynak commit'i
ve #29 metadata'sı yeniden karşılaştırıldı. Yedi partition index için iki
salt okunur hedef katalog bağlantısı yapıldı, kaynak bağlantısı0. Bu çalışma
canlı tam metadata toplama koşusu veya Oracle üzerinde uygulama kabulü değildir.

493/493 benzersiz ID incelendi:435 EXTRA,54 alan eşitliği,4 gerçek tanım farkı.
Yeni planda UNKNOWN0, saptanan fark12.387, READY1.377, REVIEW655, BLOCKED138.
EXTRA kayıtlar bilgi/uyarıdır, hedefe özgü nesneler için DROP üretilmedi.
Global kaynak kapsamı PARTIAL kalır, UNKNOWN0 bütün kaynak SQL'inin veya canlı
Oracle compile durumunun eksiksiz kabulü olarak sunulmaz.
Plan:14f22578237ff9b1d367205000d828afd6fa6efd327e273d88775af8c07a5dae.

Düzeltmeler: envanter proof1.4 ve COMMENT kimlik bazlı yokluk kanıtı,
COMMENT ON MATERIALIZED VIEW, IN(WITH...) grammar girişi, nested routine
lexical scope ve dış çağrı bağımlılıkları, doğrulanmış CREATE+ALTER TYPE son
hali ve onun type bağımlılıkları, DISABLE/NOT DEFERRABLE nullability ve
reconstructed kolon state koruması, gerçek partition/subpartition sayılarıyla
index availability. Yedi indexin730 gerçek partition'ı USABLE bulundu,
N/A üst durumundan UNKNOWN türetilmiyor. Ham SQL ve kaynak byte aralıkları korundu.

Büyük PACKAGE_BODY için ölçülen ilk parse115,9–202,3sn, yalnız128KiB üstü bu
familya240sn bütçe alır. Diğer30/120sn sınırları değişmedi. Parser cache'in
1MiB disk sınırı korunup32MiB açılım sınırına sahip sıkıştırma eklendi,
bozuk/truncated/trailing/şişen cache miss kalır. Dört gerçek büyük paket
sonucunun warm transport okuması0,047–0,079sn, bu canlı toplam koşu süresi değildir.
Kaydedilmiş metadata karşılaştırmasının rapor zamanı4dk36sn, tüm yerel
inceleme/gramer kanıtı toplama süresini veya sonraki canlı koşuyu ifade etmez.

Mail açıklaması Nesne / Fark hücresinde, en fazla150 karakter ve kısa bilinen
nedenle gösterilir. colspan ile diğer sütunların altına taşmaz. Tam açıklama
ayrıntılı raporda kalır. İlk5 nesne, kolon oranları ve mevcut logo korunur.

Doğrulama: `.venv/Scripts/python.exe -m pytest -q
--junitxml=output/remaining-493/tests-final.xml`:992passed,112,11sn, skip/fail0.
`tools/check_contracts.py`:VERIFIED(7şema/8örnek). Wheel130 paket dosyasıyla
çalışma ağacı byte eşitliği doğrulandı. Bundle5.336 dosya VERIFIED,493 kayıt
JSON/CSV ve5 HTML sayfada. Bağımsız incelemenin4 bulgusu kırmızı testle düzeltildi.
İlk yerel arşiv girişiminde target kanıt türü sözleşmeyle uyuşmadı, aktarım
kaydı TARGET_METADATA olarak düzeltildi, sonra bundle doğrulandı. Ürün sözleşmesi
gevşetilmedi. Referans kontrolü36 matched/7 drift, dış projeler değiştirilmedi,
sabit vendor dosyaları değiştirilmedi. Bu drift ayrı devir notudur.

Jenkins: v20 release2b163f5cff17d88bf52d18124d83c0b0a0c1e36c29cfd3c6435df8a74b3a8340.
#39 ENVIRONMENT_CHECK SUCCESS. #40 rapor aktarımı UNSTABLE tamamlandı: aynı plan ID,5.336 bundle dosyası ve UNKNOWN0 Jenkins makbuzundan doğrulandı. Genel mail tek onaylı alıcıya gönderildi, bu statü138 üretilemeyen işlem/eksik kapsamı yansıtır.
Normal pipeline hash f4dead35196b55e8cc5d444485dafa111d59bd0c0c82239ea1b0276695c849f5,
08:00 Europe/Istanbul, TTBP/PROD, varsayılan COMPARE ve geçici rapor parametresi0
UI'dan tekrar okundu. Son mailde5 açıklamanın tamamı ilk hücrede, dört sütun korunarak ve yatay taşma0 olarak ölçüldü, ekran kanıtı final-mail-layout.png. SQL/JSON/HTML yalnız Jenkins, artifact Git push kapalı.
Mail yalnız onaylı tek alıcıya, genel HTML gövdesiyle ve SQL/log eki olmadan.

Açık durumlar:138 üretilemeyen işlemin gerçek nedenleri raporda, bu sayı belirsiz
karşılaştırma sayısı değildir. Üç baseline dışı eski büyük kaynak gövdesinin
bireysel yeniden parse kanıtı NOT_RUN. Sonraki somut adım normal08:00 canlı
metadata koşusunda toplam süreyi izlemek ve istenirse kalan DDL üretim nedenlerini
ayrı kapsamda ele almak. Oracle üzerinde DDL kabulü NOT_RUN, salt okuma sınırı sürer.
Yerel kanıtlar output/remaining-493 altında Git dışında, sırlar ve ham metadata
kod yayınına dahil edilmez.

## 4.645 kayıt incelemesi ve statik performans - teslim, 21 Ekim 2026

Önceki ara devirlerin yerine bu son durum esas alınır. Kaynak ve hedef salt
okunur kaldı, bu incelemede yeni Oracle bağlantısı0, SQL/DML/COMPILE0.
Yeni canlı metadata capture ve Oracle üzerinde DDL kabulü NOT_RUN, doğrulanmış
#29 metadata'sı ve sabit kaynak commit'i yeniden karşılaştırıldı.

4.645/4.645 benzersiz kayıt ID'si JSON/CSV ve47 HTML sayfada incelendi.
Eski kayıtların sonucu:4.021 kaynakta olmayan hedef nesne/alanı,489 belirsiz,
53 bilgi,80 alan eşitliği,2 doğrulanmış fark. Yeni temsil edilen4 alanla
son planda toplam493 UNKNOWN bulunuyor. Sonuçta11.066 doğrulanmış fark,
1.382 READY,657 REVIEW,139 BLOCKED, kapsam PARTIAL kalır. UNKNOWN kayıtlar
bulunan fark toplamına eklenmedi. Hedefe özgü nesneler için DROP üretilmedi.

Düzeltmeler: kapalı kaynak header/context proof1.2, ayrı ALTER/DROP/SQLPlus
birimi için fail-closed kontrol, identity BY DEFAULT/ISEQ ve FLOAT126,
8 VIEW query wrapper'ı, stored unit içindeki TRG identifier lexer çakışması,
hedef DDL/katalog identity çelişkisinin UNKNOWN kalması ve gerçek kök nedenin
bağımlı açıklamaya taşınması.6 timeout body'nin yalnız kimliği doğrulandı,
DDL/semantik bilgisi UNKNOWN kaldı. Kaynak global kapsamı COMPLETE yapılmadı.
BAREM_TANIM CREATE ve OLUSTURMA_TARIHI açıklaması dahil11 SQL hazırdır,
KULLANICI bağımlılığı olan2 foreign key ayrı gerekçeyle tutulur. İzole tablo
kanıtındaki13 READY, bütün bağımlılık grafiğinin sonucu gibi sunulmaz.

Eski489 belirsiz kaydın435'inde kaynak yokluğunu kapalı kapsamla kanıtlama
sınırı,32'sinde kaynak kolon semantiği,7'sinde eksik partition index status,
6'sında IN(WITH) grammar desteği,4'ünde nested routine analizi,3'ünde büyük
package/timeout,2'sinde çok ifadeli TYPE evolution desteği bulunur. Bunlar
tekil nedenleriyle raporlandı, başarılı veya eşit diye gizlenmedi.

Karşılaştırma Python/ANTLR ile statiktir, LLM/AI servisi çağrılmaz.
Scope parent index, metadata row index ve sidecar decode tekrarları azaltıldı.
Başarılı parser cevabı tam byte/hash/şema/flag/artifact anahtarıyla sınırlı
cache'e alınır, hata/timeout ve bozuk payload cache hit sayılmaz. Canlı Oracle
metadata'sı her koşuda yeniden okunur. Collector aşama zamanları receipt'e
ayrıldı. Mail/web süre alanı başlık altında tek kompakt kutuda gösterilir.
Windows/Linux Path sıralamasından doğan artifact fingerprint farkı2 kırmızı
testle kanıtlandı ve göreli POSIX ad sırasıyla düzeltildi, hash kontrolü atlanmadı.

Son doğrulama:
- `.venv/Scripts/python.exe -m pytest -q --junitxml=output/unknown-audit/tests-release-portable-final.xml`:886 PASS/159.92sn, skip/error/failure0.
- `tools/check_contracts.py`:7 schema/8 örnek VERIFIED, `git diff --check`0.
- Gerçek son replay toplam326.51sn, raporda clock farkı5dk23sn. Bu yalnız
  frozen metadata yeniden hesaplama süresidir. Son plan e723ce96…669d31,
 5355file bundle VERIFIED,101 HTML/2507 yerel bağlantı/0 kırık link.
- v19 wheel127 package dosyasıyla byte-eşit, Linux release SHA
  f404a21f0d9b7fe3451ebecab6f5917eb770cd6890a9d5845473cd5acadff9f6.
- Jenkins#36 bağlantısız runtime kurulumu SUCCESS. #37 frozen paket aktarımı,
  Windows/Linux Path hash sırası farkıyla güvenli biçimde durdu, bu hata
  giderilip #38 Linux üzerindeki aynı wheel+parser kimliğiyle VERIFIED oldu.
- Jenkins#38 UNSTABLE:5355 bundle dosyası,47 inceleme sayfası,CSV/JSON,
  hazır SQL ve gerekçeler arşivde. Genel HTML maili yalnız izinli alıcıya gitti.
  Yeni Oracle bağlantısı0, özgün capture#29. Gerçek canlı performans NOT_MEASURED.
- Normal v19 Pipeline hash14306490…d6019 tam geri okundu, günlük
  Europe/Istanbul08:00, varsayılanTTBP/PROD, parser cache açık, geçici
  VERIFIED_REPORT parametresi kaldırıldı. Artifact Git push kapalı.
- Kanıtlar `output/unknown-audit/`, `output/jenkins-setup/release-proof-v19.json`.
  `jenkins-38-archived-receipt.json` ve `jenkins-normal-v19-readback.json`
  gerçek Jenkins UI'den tekrar okunmuştur. SQL/ham metadata/sırlar Git'e girmez.


Değişen dosyalar: compare/projection_adapter,scope,snapshots, oracle/collector,
enrichment, parsing/adapter,client,fingerprint,grammar_compat,inventory,
projections,response_cache,worker, planning/graph,table_rules, reporting
labels/CSS/mail/run şablonları, source/sidecars, source semantics aracı,
Jenkins şablonu, ilgili regresyon testleri, HTML/Jenkins belgeleri ve devirler.

Sonraki ölçüm: normal08:00 PROD/TTBP koşusunda yeni collector fazlarını ve
ilk dolum/sıcak cache sürelerini değerlendir. Yerel frozen replay süresi75dk
canlı sürenin yeni karşılığı değildir. Kalan parser/metadata destek sınırları
kayıt bazında görünür, source/target yazma yetkisi yoktur.

## 4.645 belirsiz kayıt, BAREM ve süre incelemesi - devam, 21 Ekim 2026

Aktif kullanıcı isteği: #29 PROD/TTBP verisindeki her UNKNOWN kaydını incele,
kod hatalarını düzelt, gerçek bilgi eksikliğini koru, source/target her zaman
salt okunur. Ayrıca süre sunumu ve 75 dakikalık statik işlem iyileştiriliyor.
Bu kayıt ara devirdir, bütün işin tamamlandığı anlamına gelmez.

43 yeni payload ve 29.050 yeniden kullanılan DDL blobu SHA256 ile doğrulandı.
4645/4645 benzersiz ID çizelgesi output/unknown-audit/coverage/ altında:
3666 yerel alan yokluğuna sızan global envanter belirsizliği, 845 kaynak
nesne yokluğu kanıtsız, 89 kolon semantiği, 45 parser/metadata alanı.
Yerel _absence düzeltildi. Identity BY DEFAULT ve FLOAT126 kanonik okumaları
düzeltildi, kaynak correspondence 1235→1266 tablo, 35→4 gerçek red.
BAREM_TANIM CREATE+3constraint+9COMMENT çevrimdışı READY kanıtlandı.
Bağımlılık gerekçesi artık gerçek kolon/kök nedeni taşıyor.

İlk bütün frozen replay: UNKNOWN4645→922, READY1266→1381,
BLOCKED251→142, gerçek metadata #29 olarak kaldı, Oracle bağlantısı0.
Replay süresi239.02sn: validatedload35.48, correspondence5.66,
compare10.25, plan46.61, bundle112.43. Bu canlı75dk yerine ölçülmüş
bir süre değildir, eski metadata yeniden hesaplandı. Yeni view/header
inventory/cache iyileştirmeleri henüz bu replay sonucuna dahil değil.
İlk replay: output/unknown-audit/fixed-replay/ (5359file VERIFIED).

Süre kökeni: kaynak hazırlık/setup2224.06sn, kaynak catalog6.80sn,
correspondence/setup15.54sn, target capture+parse1913.26sn,
son karşılaştırma/plan/arşiv349.21sn. LLM/AI çağrısı yok, statik Python/ANTLR.
Scope indeks ve metadata satır indeksleri byte-eşit sonuçla iyileştirildi.
Sidecar parent index/single decode:46scopedtest PASS.
Süre alanı mevcut HTML ailesinde kompakt özet alanına taşındı.

Jenkins #32 ve #33 yalnız frozen workspace dosyalarını aktardı, SQL/Git/SMTP
ve Oracle bağlantısı0. Normal v17/08:00 pipeline her seferinde geri yüklendi.
Eksik353SQLinput blobu için ek frozen export gerekebilir. Şu anda üç alt
çalışma: guarded inventoryproof, geçerli VIEW/TRG parser uyumluluğu,
exact-byte+parser-hash bounded parser cache. Final fullsuite, bağımsız
inceleme, yeni wheel/release, Jenkins replay/arşiv/mail ve private code
push HENÜZ YAPILMADI. Sonuçlar tamamlanınca bu ara durum güncellenecek.

## Rapor süresi ve doğrulanan fark sayısı - tamamlandı, 21 Ekim 2026

Mailin ana başlığında gerçek karşılaştırma süresi dakika/saniye olarak görünür.
Son özgün #29 karşılaştırması 08:00:00–09:15:09 TSİ, 75 dk 9 sn sürdü.
Rapor yenileme süresi ayrı adla yazılır. comparison-timing.json özgün clock'u
ve source SHA'sını korur, run.json'un gerçek yenileme zamanları değişmez.
Tekrarlanan yenilemeler de eski receipt zincirinden aynı karşılaştırmayı bulur.

Fark kartındaki Bilinmiyor kaldırıldı. Güncel PROD /TTBP: 6936 doğrulanmış
bulunan fark, 4645 kayıt eksik bilgi nedeniyle karşılaştırılamadı.
Kanonik observed_differences=11581 bu iki grubun toplamıdır,
UNKNOWN kayıtlar kesin fark sayısına eklenmez. Kapsam eksikliği ve ek fark
bulunabileceği görünür. Kanonik difference_count=null değeri değiştirilmedi.
1266 hazır DDL /633 inceleme /251 üretilemeyen DDL kararları ve SQL aynıdır.

Jenkins #31 UNSTABLE /run PARTIAL tamamlandı, #29 kaydının sunumu yenilendi.
5278 değişmez dosya, 1268 SQL dosyası ve plan JSON byte-eşit doğrulandı.
Plan ID: 3c9d1c8a19dfa6f6b9fcf5b08e93fd658c7188fddfa70394fc26c569e2e60804.
Yeni Oracle bağlantısı0, yeni karşılaştırma0, SQL NOT_EXECUTED.
Güncel genel mail yalnız yetkili tek alıcıya gönderildi. Normal v17 günlük
pipeline geri yüklendi, TTBP varsayılanı /INNOVA_ODI manuel /her gün08:00
Europe/Istanbul /Jenkins-only artifact /Git artifact push yok, readback doğrulandı.

Offline: 742 passed /85.193 sn /skip0, tek tam koşu yeşil.
Kanıt: output/plain-report-tests-final.xml. 7 schema /8 example VERIFIED.
Süre ayrımı, kısmi hedefte kesin/UNKNOWN sayımı, sonuç alınamayan hedefte sıfır
uydurulmaması, aynı clock'un zincirde korunması ve değişmez SQL test edildi.
Değişen ek dosyalar: reporting/formatting.py, view.py, üç HTML şablonu,
runtime/aggregate.py, tools/jenkins_notification.py, jenkins_report_presentation.py,
test_report_counts_timing.py ve ilgili eski sunum beklentileri güncellendi.

Release v17 SHA: 27e7571c802aad89c04f7c2b117c5e2d7327a47c4083a728170fac0dc831ac71.
Wheel SHA: 0b0a78c976930d72ee109d7a12ecbdf9889a3fcf37904777fe57dd156717a02c, 125 paket dosyası byte-eşit doğrulandı.
Kanıtlar: output/jenkins-setup/plain-report-build-31-proof.json,
v17-normal-job-proof.json ve plain-report-build-31.png. Kurumsal çıktılar Git dışıdır.
Yeni canlı Oracle kabulü NOT_RUN, mevcut #29 salt okunur karşılaştırma verisi kullanıldı.
Açık sunum engeli yok. Sonraki somut adım: günlük08:00 TTBP koşusu yeni raporu üretir,
uygulama kodu yalnız yetkili private depoya yayımlanır, SQL/JSON/HTML Jenkins'te kalır.

## Anlaşılır rapor durumları - 21 Ekim 2026

Genel mail/web özetindeki BLOCKED, [TABLE], COMMENT ve ham işlem kodları Türkçe
sunum etiketlerine çevrildi. Hazır ve üretilemeyen işlemler birlikteyse hedef
"DDL kısmen hazır", ilgili kayıt "DDL üretilemedi" gösterir. Kısa, kanıtlı
nedenler her kaydın altında küçük yazıyla yer alır, mailde dört sütun genişliğini
kullanır. Tekrarlanan bağlı nesne gerekçeleri birleştirilir. UNKNOWN yokluk diye
sunulmaz, ham teknik gerekçe açılır bölümde ve kanonik JSON'da kalır.

Değişen ürün: reporting/labels.py, view.py, render.py ve üç HTML şablonu.
Yeni tools/jenkins_report_presentation.py doğrulanmış eski arşivden HTML yeniler,
plan JSON/SQL byte'ları aynen korunur, manifest ve paket yeniden doğrulanır.
Yeni paket yalnız doğrulama bitince atomik olarak görünür olur.

Offline: `.venv/Scripts/python.exe -m pytest -q --tb=short
--junitxml=output/plain-report-tests.xml`: 736 passed /88,49 sn /skip0.
`tools/check_contracts.py`: 7 schema /8 example VERIFIED. Kayıtlı 251 üretim
engelinin özeti ve 59 HTML sayfası doğrulandı, teknik durum tokenı0, en uzun
özet240 karakter. Bundle kopyasında plan/SQL değişmezliği ve hatalı doğrulamada
yarım paket yayımlanmaması test edildi.

Jenkins v16 SHA: 7dd7ebbbc56535120e472ac0a43be4c2a8f30b7695f0a7415b9edc94205114fc.
Wheel SHA: 462eebe35c380ab4bd51e9298f4898ccc2697890fdf05c75fea757adae5acb99.
125 paket dosyası çalışma alanıyla byte-eşit, release manifest doğrulandı.
Normal v16 pipeline geri yüklendi, script birebir okunarak doğrulandı,
TTBP varsayılanı, INNOVA_ODI manuel seçimi ve Europe/Istanbul her gün08:00 korunur.
Tek mail alıcısı ve Jenkins-only DDL/JSON/HTML arşivi değişmez.

Jenkins #30 sunum yenilemesi: tamamlandı, 1.266 READY /633 REVIEW /251 BLOCKED, Oracle bağlantısı0.
Kaynak alınan çalışma #29, yeni karşılaştırma veya Oracle bağlantısı yapılmaz.
Canlı Oracle yeni kabulü: NOT_RUN. SQL/DML/COMPILE: NOT_EXECUTED.
#30 receipt, arşiv, sayılar, mail ve görsel kanıtı doğrulandı. Sonraki ek kullanıcı
düzeltmesinin süre/fark sonucu bu dosyanın başındaki #31 kaydındadır.

## TTBP 2.355 engel incelemesi - tamamlandı, 20 Ekim 2026

Eski #25 planının 2.355 BLOCKED operation ID'si kanıtıyla tam bir kez incelendi,
eksik/çift eşleme0. TABLE1.096, INDEX582, diğer677 kayıt, ilk kalan engeller de
ikinci turda tek tek doğrulandı. Eski kayıt sonuçları: 1.699 uyarı,
135 alan-fark eşitlik kanıtı, 78 READY,
191 REVIEW, 252 BLOCKED. Eski kayıtlar yeni işlemlere
bire-çok/çok-bir bağlanabilir: güncel ayrı engel 251.

Kod düzeltmeleri: hedef koruma/UNKNOWN ayrımı, dictionary kolon kaybı, constraint
gruplama, anonymous PK/UK backing index kanıtı, supplemental logging sahte kolon
ayrıştırması ve yeni SQL'de logging korunumu, anonim ALTER UNIQUE ve aynı CHECK
çokluğu, Oracle identifier case/TABLE(collection) bağımlılıkları, gerekli kolon
kanıtıyla FK/%TYPE bağlama, bağımsız default/nullability ve UNKNOWN gözlemi ayrımı.
Ham SQL, ALTER bağlamı, SHA/identity/kanıt ve global PARTIAL korunur. Kapsamlı
negatif testler gerçek key/type, eksik kolon ve metadata engellerini korudu.

Offline: 726 passed /94,69 sn /skip0, tek tam koşu yeşil.
JUnit output/ttbp-blocker-audit/pytest-v13-release.xml. check_contracts 7schema /
8example VERIFIED. Önceki ara odaklarda Windows os.rename WinError5 görüldü,
son tam koşuda tekrarlanmadı, güvenlik/antivirüs ve artifact atomikliği değişmedi.

Jenkins #28 UNSTABLE /run PARTIAL tamamlandı. 12.755 gözlenen fark,
1.265 READY SQL, 632 REVIEW, 251 BLOCKED,
3.277 INFORMATIONAL. UNKNOWN ve kapsam eksikliği nedeniyle kesin toplam
fark iddiası yok. Manifest 5.465 dosya VERIFIED,
SQL 1.265 dosya /759.226 byte. Plan 5c7527f0820f257c30504cd41a1e571e6bd01a98afd998291ecd6b676f9f6eac.

Her eski ID'nin gerekçe/alan/hash/kanıt/yeni işlem eşlemesi audit/index.html,
blocked-audit.csv ve blocked-audit.json arşivindedir. CSV UTF-8 BOM/semicolon,
HTML external CSS, evidence-inputs.zip ve audit-manifest.json kanıtları korunur.
Source #18 frozen SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a, SOURCE277logging+2context,
TARGET317logging+2context doğrulanmış offline reparse. fresh_capture=false /
Oracle connection_attempts=0 /SQL NOT_EXECUTED. Bu görev yeni canlı Oracle
kabulü değildir (NOT_RUN), DDL/DML/COMPILE/trigger/yetki/source repo yazımı yok.

v13 release 26bb1fa563e2294daf2b116d1dfcf768146bfd4284bb1ce9d3b55161c77e2cc8,
wheel 18738619ae91996f150adb983261e5a7feb8ff333f6577802847f50ff868178b.
125 package/asset dosyası workspace byte eşitliği doğrulandı. Normal v13 UI exact
match, varsayılan TTBP /manual INNOVA_ODI, COMPARE ve Europe/Istanbul08:00 doğrulandı.
Mail yalnız onaylı tek alıcı, HTML genel gövde, attachment/log yok. DDL/JSON/HTML
yalnız Jenkins, artifact Git push yok. Private uygulama kodu yayını receipt'i
output/github-code-ttbp-blocker-audit-publication-receipt.json ile ayrıca doğrulanır.

## Devam eden 2.355 engel incelemesi - 20 Ekim 2026

Temel #25 planı doğrulandı, TABLE1.096 / INDEX582 / diğer677 eski BLOCKED
işlemin tümü için kanıt kayıtları output/ttbp-blocker-audit altında Git dışıdır.
#26/#27 kayıtlı dosya okumasıdır, Oracle/SMTP/source Git yazımı yok.
29.083 arşiv girdisinin SHA/byte kontrolü geçti. Windows case çakışmaları
ZIP-backed loader ile ele alınır, veri bütünlüğü kontrolü gevşetilmez.

Compare/parsing/planning düzeltmeleri kırmızı testlerle uygulandı: dictionary
kolon kaybı, anchored tip/package referansları, anonymous constraint index,
UNKNOWN koruma kayıtları, constraint gruplama ve supplemental logging.
Gerçek dönüşüm/bağımlılık engelleri negatif testlerle korunur. Tam offline
pytest 692 passed /101,71 sn /skip0, tek tam koşu yeşil, JUnit
output/ttbp-blocker-audit/pytest-full-audit.xml. Son source reparse ek çalışması,
yeni plan ve 2.355-ID nihai eşlemesi sürüyor. Canlı Oracle kabulü bu inceleme
için NOT_RUN, SQL NOT_EXECUTED. v12/Jenkins teslimi ve private kod push henüz
NOT_RUN. PROD/TTBP varsayılanı,08:00 ve Jenkins-only artifact politikası korunur.

## Güncel kapsam: yalnız PROD / TTBP - 20 Ekim 2026

Son kullanıcı talimatı: günlük varsayılan yalnız TTBP, INNOVA_ODI ancak manuel
SCHEMA_SCOPE seçimiyle. Jenkins 08:00 Europe/Istanbul korunur. tools/jenkins_scope.py
build'e özel dört config kapsamını birlikte daraltır, immutable iki şemalı registry
değişmez. Source/target READ ONLY, Oracle DDL/DML/COMPILE NOT_RUN. Hedef adı PROD,
TTBP şema olarak görünür, iç LOCAL-TTBP kimliği ve arşiv yolları korunur.

Gerçek 64-hex / S_64-hex teknik nesneler ile bağlı INDEX/COMMENT/GRANT policy
filtresine dahil edildi. Ham inventory ve scope-exclusions kanıtı korunur.
Sentetik COMMENT/GRANT hash kimlikleri silinmez: bilinen bağlı nesne/kolon,
optional object.display_name ile HTML/mail/README'de gösterilir. Belirsiz bağlı
nesne açık etiketlenir. Planı olmayan hedefte sahte ad/şema yok, UNKNOWN ve
bilinen hata kodu gösterilir. İç object/operation ID, dosya yolu ve SQL gövdesi
korunur, plan ID ve SQL header hash değişebilir. Bağımsız son inceleme P1/P2 yok.

Git paket bütünlüğü: eski unanchored artifacts/ ignore kuralı uygulamanın altı
artifacts Python modülünü de Git dışında bırakmıştı. /artifacts/ olarak düzeltildi,
6 gerçek kaynak modülü private kod yayınına alınır. Üretilen çıktı/.local/SQL
arşivleri yine Git dışıdır. Wheel içindeki 123 kaynak/asset dosyası workspace ile
byte eşitliği üzerinden doğrulandı. Kurumsal sırlar/yapılandırmalar yayımlanmaz.

Doğrulama: check_contracts 7 schema / 8 example VERIFIED. Son tam koşu 636 testte
630 passed, 6 Windows os.rename WinError5 (assertion/ürün kararı hatası değil),
skip0. İki dar tekrarın her biri 5 passed / 1 aynı Windows erişim hatası verdi,
başarılı tekrarların birleşimi aynı altı testin tamamını kapsıyor. Tek koşuda
tam yeşil iddia edilmez, aralıklı Windows filesystem kilidi açık ortam sınırlamasıdır.
JUnit: pytest-ttbp-prod-windows-failures.xml, pytest-ttbp-prod-windows-rerun.xml,
pytest-ttbp-prod-windows-rerun2.xml. Yeni scope 3, hash 22 ve yan kayıt/hata etiket
23 testleri odak doğrulamalarda geçti. Testler için güvenlik/antivirüs değiştirilmedi.

v11 release SHA f00a4c805204b9faa379266f9ce10c8740b47bbac8b6b590322edecc83842d9a,
wheel afcd482dfc165429b08ca1c2fb4d86caf3df310ad34ce7b6cbd4a6c7d8d4071b.
Jenkins normal v11 script UI'dan byte normalize exact-match doğrulandı,
SCHEMA_SCOPE ilk TTBP/ikinci INNOVA_ODI, RUN_MODE ilk COMPARE, cron 08:00.
Kanıt release-proof-v11.json ve v11-normal-job-proof.json. #23 seçili TTBP
ENVIRONMENT_CHECK SUCCESS, Oracle/Git source checkout/mail0.
#24 TAMAMLANDI: yalnız PROD / TTBP, Jenkins UNSTABLE / run PARTIAL. 43.343 gözlenen
satır, 1.170 READY SQL / 368 inceleme / 2.355 engel / 966 bilgi. Kısmi envanter/DDL
ve 37.419 UNKNOWN nedeniyle kesin difference_count=null, dictionary COMPLETE.
Target error_code=null. Manifest 7.241 dosya VERIFIED, 1.170 SQL / 616.700 byte.
Plan 98b88b50c2cc256a8272c6df67947d60cf5b001b7ae4de51bdc64aace1e96571.
Run 45bd3e14-2453-4043-b856-329290b4f6a3, kaynak ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a.
#18 yakalaması yeniden kullanıldı, fresh_capture=false / source_build=18 /
Oracle connection_attempts=0 / NOT_EXECUTED. Rapor süresi 7 dk 31 sn, tüm build
8 dk 2 sn. PROD/TTBP ve gerçek COMMENT tablo/kolon etiketleri HTML/mail'de görüldü,
görünür LOCAL-ID / S_64hex bulunmadığı DOM metninden doğrulandı. Eski ve yeni
sayımın aynı kalması beklenen durum: sentetik yan kayıtlar korunur, gerçek hash
teknik nesneler policy kapsamında dışlanır. Ham inventory/scope-exclusions korunur.

#24 mail açıklamasında yerel tek seferlik helper'ın varsayılan Windows encoding
ile okunması kaynaklı mojibake görüldü, normal ürün notification helper'ı doğru
UTF-8'dir. #25 #24 doğrulanmış paketin rapor özetini yeniledi: UTF-8 note doğrulandı,
targets_equal ve bundle_manifest_unchanged=true, plan ID ve 1.170 SQL değişmedi.
comparison_rerun=false / sql_regenerated=false / database_connections=0 /
NOT_EXECUTED, credential binding yok. #25 TAMAMLANDI: 53 sn build, rapor yenileme
33 sn, Jenkins UNSTABLE / PARTIAL, yeni run 8cff1abe-997a-4c55-92f2-714b63bdcd36.
Arşiv/fingerprint ve mail yalnız onaylı tek alıcıya Jenkins logunda doğrulandı,
attachment/log yok. Son mail DOM metninde PROD/TTBP, gerçek tablo/kolonlar ve temiz
Türkçe not görüldü, görünür LOCAL-ID/S_64hex/mojibake yok. Son hedef raporu açık
bırakıldı. Kanıt ttbp-prod-final-presentation-build-25.json,
ttbp-prod-presentation-build-25.log ve ttbp-prod-mail-build-25.png (output/jenkins-setup).
Normal günlük taze source/target okuyan v11'e geri döndü ve UI exact-match/08:00
bir kez daha doğrulandı (v11-normal-job-proof-final.json). Özel kod yayını ayrıca
output/github-code-ttbp-scope-prod-publication-receipt.json ile kanıtlanır,
üretim SQL'i/raporlar/yerel sırlar bu commit/push kapsamına girmez. Sonraki bakım
adımı TTBP kısmi kaynak/parse kapsamını nesne bazında azaltmaktır. Mevcut kapsam,
etiket ve Jenkins-only rapor/DDL teslimi tamamlandı. Artifact Git push NOT_RUN.
Canlı Oracle compile/iş verisi kabulü NOT_RUN, Oracle'a DDL/DML/COMPILE uygulanmadı.

# Jenkins arşivi - 20 Ekim 2026 güncel durum

## TTBP - 20 Ekim 2026 güncel ek

Mevcut yetkili katalog hesabıyla #18 TTBP READ ONLY capture tamamlandı:
5.321 envanter, 24.508 metadata nesnesi, dictionary/capability hata yok.
#20 çevrimdışı kesin kök neden HTML_SIZE_BUDGET_EXCEEDED, 1.170 READY SQL'in
ayrıştırması başarılıydı. HTML boyutuna göre sayfalama ve JSON tam kanıt bağlantısı
uygulandı. Aynı bağımlılık analizi ve doğrusal lookup tekrarları azaltıldı,
heap sıralaması eski sıra/engel kararlarını korur. Üç yeni test dosyası dahil
615 passed / 90,89 sn / skip0, bağımsız incelemede açık P1/P2 yok.
V10 yeni immutable release + normal günlük 08:00 exact LF/UI doğrulandı.
#22 tamamlandı: UNSTABLE/PARTIAL, iki hedefte error_code null. INNOVA_ODI
1.857 fark/559 DDL, TTBP 43.343 gözlenen satır/1.170 DDL/368 inceleme/2.355 engel.
TTBP 37.419 UNKNOWN ve kısmi kapsam nedeniyle kesin toplam null, hazır alt küme
arşivlenmiştir. TTBP 7.241 manifest dosyası, 1.170 SQL/616.700 byte VERIFIED.
Genel HTML mail yalnız tek yetkili alıcıya gönderildi, gerçek iki hedef HTML'i
arşivde açıldı. #18 yakalamalarından çevrimdışı yeniden üretim10dk0sn,
Oracle bağlantı girişimi0, SQL NOT_EXECUTED. Normal günlük08:00 v10 geri yüklü.
Oracle yazma ve DDL Git push NOT_RUN. Kalan parser/kapsam eksikleri rapordadır.
Kanıtlar ve sonraki bakım adımı DEVIR.md başındaki ek bölümde.

Son görev TTBP ORA-04088: hedefte araç bağlantısını reddeden mevcut logon trigger
tanılandı. Güvenlik/Oracle kullanıcıları değiştirilmedi. Mevcut ODI katalog okuma
yetkisiyle explicit metadata_reader desteği tamamlandı, identity+role+owner varlığı
ve tam DBA metadata erişimi kapalı sorgularla doğrulanır. 587 test passed /
82,89 sn, bağımsız review P2 kapandı, açık P1/P2 yok. #17 salt okunur canlı erişim:
5.321 katalog nesnesi, 20 dictionary grubu ve üç DDL türü başarılı. #18 v9 gerçek
karşılaştırma sürüyor, henüz TTBP plan/DDL tamamlandı iddiası yok. Günlük normal
v9 script + 08:00 exact UI doğrulandı, yalnız Jenkins arşivi, SQL uygulanmaz.
Dosya/kanıt/sonraki adım yz/DEVIR.md başındadır.

Son kullanıcı saati: her gün Europe/Istanbul 08:00 (08:40 yerine). Canlı cron,
declarative trigger ve açıklama kaydedilip yeniden okunarak doğrulandı.
Sonraki planlı başlangıç 21 Ekim 08:00. Yeni build/mail/DB bağlantısı yok.
Kanıt schedule-0800-proof.json/png, uygulama kodu değişmedi, test tekrar edilmedi.
#14 son canlı sonuç: ODI 1.857 fark/559 DDL, TTBP ERROR/ORA-04088, plan/DDL yok.
Aşağıdaki kuyruk/08:40 bilgileri önceki durumdur, ayrıntılar yz/DEVIR.md başında.

Son ek: 489 passed / 84,19 sn / skip 0, son bağımsız inceleme P1/P2 yok.
Jenkins-only uygulama kodu 97d3992e79dd67f310cf5956af40051555acaf6a normal
push ile doğrulandı. #13 kaynak snapshot'ı hash piniyle doğruladı, ODI metadata
405 tablo eşleşti. TTBP DPY-3015 için mevcut Sync Oracle Instant Client 19.28
yeni v8 release'e lisans/hash/provenance ile alındı, iki owner explicit thick.
Yeni driver helper kırmızı→yeşil 6 test, thin native load yok, mixed/error
güvenli reddedilir. Oracle yazma/verifier değişikliği yoktur. v8 normal script
Jenkins'te birebir kaydedildi, Git publication yok. #14 paket yüklendi ve #13
ardında kuyruğa girdi. Canlı karşılaştırma sonuçları halen bekleniyor.

Kullanıcı artifact Git push'unu iptal etti. DDL/JSON/HTML yalnız Jenkins build
artifact arşivinde, son 20 build/artifact saklama ayarıyla tutulur. Mail doğrudan
Jenkins raporunu açar, 08:40 Europe/Istanbul değişmedi. Kod deposu push yetkisi sürer.
Canlı job ve template publication stage/credential içermez, v7 exact UI doğrulandı.

Offline 483 passed / 71,90 sn / skip 0, bağımsız son incelemede açık P1/P2 yok.
#12 PARTIAL prepare exit10 runner hatası giderildi, ham UNKNOWN korunur.
Yeni owner scope kapalı kanıtla doğrulanır, TTBP kaynağındaki parser eksikleri
temiz ODI envanterine taşınmaz. Dış dosya hash piniyle aynı SHA snapshot resume
doğrulanır, günlük normal akış fresh source hazırlar. #13 gerçek iki hedef
salt okunur çalışma sürüyor, live henüz tamamlandı sayılmaz. Oracle DDL/DML/COMPILE
NOT_RUN. Dosya, komut, sonraki somut adım yz/DEVIR.md başındadır.

---

# SKY, süre, ilk 5 ve iki şema - 20 Ekim 2026 (önceki durum)

Offline uygulama: 414 passed / 40,89 sn, bağımsız çapraz inceleme temiz.
SKY konu, %60 Nesne/Fark sütunu, 156×30 logo, süre ve öncelikli5nesne hazır.
Sync teknik nesne filtreleri + GRANT dışlama opt-in policy ile uygulanır,
ham envanter ve UNKNOWN/bağımlılık güvenliği korunur. INNOVA_ODI+TTBP için
ayrı credential/sessionowner doğrulamalı runner ve owner bazlı source kanıtı var.
scope-exclusions.json filtre kanıtını taşır. Dosyalar ve komutlar yz/DEVIR.md başında.

GitHub code son push doğrulandı (f4560bdcb158a7fe727febe064e04b8ad66baa65),
SKY/TTBP/filtre uygulaması bu commit'te. Jenkins günlük 08:40
Europe/Istanbul doğrulandı. #12 v6 release ile canlı salt okunur iki şema koşusu
sürüyor, henüz tamamlandı iddiası yok. Gerçek Oracle DDL/DML/COMPILE NOT_RUN.
Jenkins agent GitHub HTTPS ConnectionResetError, proxy kullanıcı yanıtı bekleniyor.
Bu yalnız otomatik artifact push'u etkiler, yerel GitHub erişimi ve karşılaştırma sürer.

---

# Rapor gerekçeleri ve işlem hücresi - tamamlandı, 20 Ekim 2026

Genel mailde nesne başına `işlem / hedef` satırı kaldırıldı. planning/graph.py
ve object_rules.py gerekçeleri gerçek şema/nesne/tür, kolon ve eksik koşulla
açıklar. Karar kuralları değişmedi. email.html.j2, jenkins_notification.py,
tek seferlik jenkins_report_refresh.py, iki regresyon test dosyası ve HTML
standardı güncellendi. Ayrıntılı dosya/kanıt kaydı yz/DEVIR.md başındadır.

341 test / 31,51 sn / skip 0, son helper düzeltmesi sonrası ilgili 9 test geçti.
Bağımsız incelemede açık önemli bulgu yok. Jenkins #7 UNSTABLE: #6 snapshotları
ile aynı 2.352 fark, 559 READY, 123 REVIEW, 5 BLOCKED, 1.037 INFO, UNKNOWN 0.
559 SQL gövdesi birebir aynı, yeni Oracle bağlantısı 0. Genel belirsiz gerekçe
ve gereksiz sayı satırı gerçek plan/mailde yok. Genel HTML mail yalnız izinli
tek alıcıya gönderildi, normal Jenkins v3 Pipeline geri yüklendi ve doğrulandı.

Kanıt output/report-reasons/, release SHA aacc6d65248ad0949f7d14d5cbddd40a45b367683883175969547ad6646f6bec.
Offline=PASSED, Jenkins=VERIFIED, yeni Oracle capture=NOT_RUN, Oracle DDL/DML ve
dış Git push=NOT_RUN. Açık düzeltme engeli yok, sonraki manuel COMPARE normal
salt okunur capture yapar. Önceki immutable raporlar korunur.

---

# Jenkins ve genel HTML mail - tamamlandı, 20 Ekim 2026

ODMG-JENKINS-001 kuruldu ve canlı doğrulandı. Ayrı sky/oracle-db-migration-generator işi, yalnız INNOVA_ODI. Son #6 UNSTABLE: karşılaştırma tam, 2.352 fark/559READY/123REVIEW/5BLOCKED/1.037INFO, UNKNOWN0. Envanter/DDL/dictionary COMPLETE. Beş gerçek koşul DENEME ad alanı çakışması, I_ADDR_ID parent yokluğu ve PCK_COMPARE_FIELDS/PCK_ISLEM_TIPI_AKTAR2/PCK_LOG_UTIL bağımlılıklarıdır, INVALID hedef nesneler yalnız rapor uyarısıdır. BLOCKED/UNSTABLE bu gerçek plan koşullarını korur, task çalışmasını bloke etmez.

Source Git SHA ce8d62d18f46657b702a12bd5fe6fc58ec27cb5a. Kaynak metadata405tablo/0reject canlı eşleşti, yalnız örtük BYTE/CHAR/collation tamamlandı, Git DDL byte/hash'i değişmedi. Target ilk capture sırasında821→820nesne değiştiği için ikinci read-only capture ile tutarlı snapshot alındı. Ürün veya ajan Oracle DDL/DML uygulamadı. TTBP ve mevcut Sync işi değişmedi.

Kullanıcı talimatındaki genel mail doğrudan HTML gövdesindedir, rapor eki yok. Yalnız mkaracan@innova.com.tr adresine gönderildi. Konu GPU | Oracle DB Migration Generator | UNSTABLE | Build #6. Genel özet, sayılar, hedef ve önemli nesneler ilk bakışta görünür, ayrıntı linki gerçek build6 arşivini açtı. Repo yayını yapılmadı, olmayan repo linki sunulmadı. Gövde önizlemesi output/jenkins-mail-preview/index.html, ekran kanıtı output/jenkins-setup/mail-body-build-6.png.

Doğrulama: .venv/Scripts/python.exe -m pytest -q --junitxml=output/jenkins-setup/pytest-final.xml →332passed/35.61s/skip0. 7schema/8örnek VERIFIED. Son19CI testi ve bağımsız inceleme başarılı, rawcolumnset/duplicate ve timestamp→planid regresyonları kapalı. BootstrapPython3.10syntax geçerli, JenkinsCPython3.12.15 offlinehashlock ile kuruldu. Ürün wheelSHA97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3 değişmedi. ReleaseSHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

PlanID51f8f3c711d26d78c8ed42c3379d291edef3cfe4e4f32d64932b1f0f4f9a4146. Kanıt output/jenkins-setup/live-verification.json, job/build/report URL'leri, sayaçlar, konu/alıcı ve dosya hash'leri bu Git dışı kayıttadır. Raw source/target observations ve bağlantı yapılandırmaları normal Jenkins arşivine girmez. Otomatik tetikleme yok, manuel COMPARE çalışır, sonraki build'de release dosyası boş bırakılabilir. Yerel Git hâlâ unborn/untracked, commit/push yapılmadı. Referans36match/7öncedenmevcutdrift/0missing.

Kapanış: offline_verification=PASSED, oracle_integration=READ_ONLY_CAPTURE_VERIFIED, oracle_ddl_acceptance=NOT_RUN, jenkins_installation=INSTALLED_VERIFIED, notification=SENT_HTML_BODY_SINGLE_AUTHORIZED_RECIPIENT, external_git_publication=NOT_RUN. Aktif görev kapsamında açık kurulum engeli yok. Sonraki somut adım kullanıcı yeni hedef/otomatik tetikleme veya Git yayın kapsamı verirse ayrı değerlendirmedir, mevcut5gerçekplan koşulu silinmez. Aşağıdaki kayıtlar tarihsel aşamalardır.

---

# Jenkins kurulumu - 20 Ekim 2026

ODMG-JENKINS-001 kullanıcı talimatıyla ayrı sky/oracle-db-migration-generator Pipeline olarak kuruldu. Scope yalnız INNOVA_ODI, mevcut Sync işi değişmedi. Source/target daima READ ONLY, gerçek Oracle DDL/DML ve dış Git push NOT_RUN. Kullanıcı mail alıcısını yalnız mkaracan@innova.com.tr olarak belirledi.

Test edilmiş ürün wheel'i değişmedi. Yeni dosyalar tools/jenkins_bootstrap.py, tools/jenkins_run.py, templates/jenkins-generator.groovy, tests/unit/test_jenkins_runtime.py ve docs/JENKINS_ILK_KURULUM.md. Bootstrap resmi SHA'lı CPython3.12 arşivini ve hash kilitli offline wheel'leri iş workspace'ine kurar. Boş file parametresi retained ZIP'e gider, archive path/link/hash sınırı korunur, bytecode yazımı kapalıdır. Gzip linkleri regular dosya kopyalarıyla çözülür, kaynak/target SQL uygulanmaz. Arşiv ham observations/** içermez.

Offline: 324 passed /83.03s, skip0, output/jenkins-setup/pytest-final.xml. 7 schema/8 örnek VERIFIED. Referans audit36match/7öncedenmevcutdrift/0missing, diğer projelerde değişiklik yok. Yeni 11 Jenkins testi ve bağımsız son inceleme başarılı. Python3.10 bootstrap syntax doğrulandı. Yerel env dosyası ve output Git dışında.

Canlı: #1 resmi tar göreli link/Python3.10 filter hatası, #2 boş file parametresi, #3 yavaş gzip geri seek nedeniyle yalnız ENV aşamasında güvenle ABORTED. Düzeltmeler kırmızı→yeşil. #4 ENVIRONMENT_CHECK SUCCESS (Python3.12.15, DB bağlantısı0). #5 ardışık runtime bütünlüğü ve SKY JGit checkout başarılı, sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a, canlı karşılaştırma sürüyor.

Job/build/private release kanıtı output/jenkins-setup altında. ReleaseZIP SHA c6a17a6751ce6892ca5ed92b0c5695cf8d3834e9f941922bd39f0bd298eee589. GitHub depolarının private/boş olduğu yalnız okuma API'si ile doğrulandı, token yazdırılmadı veya Jenkins'e yeni credential kaydı eklenmedi. Otomatik tetikleme kapalı.

Sıradaki somut adım: #5 bitişini, Oracle metadata receipt'ini, arşiv raporunu ve yalnız izinli alıcıya e-postayı doğrula. Başarısızlığı gizleme, INVALID hedef nesneler rapordur. Oracle DDL kabulü daima NOT_RUN. Geniş çoklu target/TTBP/yayın ayarı bu kapsam dışındadır.

---

# Rapor/artifact güncellemesi - 20 Ekim 2026

ODMG-RPT-UPDATE-001 yerel uygulaması tamamlandı. Onaylı ZIP'in iki tasarımı gerçek
Run → Target → Plan → Object modeline bağlandı. Source ve target daima salt okunur,
bu aşamada Oracle bağlantısı dahi açılmadı. Parser/compare/karar motoru değiştirilmedi.

2.353 fark, 559 hazır DDL, 123 inceleme, 5 kaynak/sözleşme koşulu, 1.038 bilgi.
559 SQL gövdesi önceki tamamlanmış motor paketiyle byte karşılaştırmasında aynı,
yalnız plan kimliği header'ı ve dosya yolları yeni rapor build'iyle değişti.
Birleşik SQL sıra/hash kontrolü ve eski flat bundle doğrulaması başarılı.
Beş gerçek koşul yz/MOTOR_TAMAMLAMA.md içinde, rapor üretimi için engel değiller.

313 passed / 51,22 sn, skip 0. 7 şema / 8 örnek VERIFIED.
İki farklı run aynı tek immutable planı kullanıyor. 14.346 statik bağlantı doğrulandı.
En büyük HTML 115.129 byte (<200 KiB). Web/target/email 390/820/1.440 px olmak üzere
9 browser kontrolü, yatay taşma 0. Onaylı logo SHA'sı iki ZIP referansıyla birebir aynı.
Mail 5 kritik target / 10 benzersiz nesne, CID ve ayrı gömülü preview, SQL body mailde yok.
Nesne README/review kanıtları, binlik ayraçlar ve gerçek dosya yolları tamamlandı.

Arşiv sahiplik/kilit/atomik yazma/rollback/dedup ve integrity conflict kontrolleri var.
Opt-in publisher private kurum deposu, izinli host/SSH remote, storage ve push yetkisi,
literal generated pathspec, bütün payload sır taraması ve doğrulanmış sabit son SHA linki ister.
Başarısız push/404/retention/yanlış run/yanlış Jenkins build için olmayan link çizilmez.
Bağımsız incelemedeki 3 bulgu kırmızı→yeşil kapandı, yeniden incelemede yeni önemli bulgu yok.

Plan: `1c5950cc93efb9d9420bbf94743ef8e9112038bef627cdb130775d503f8e078f`
Generator: `4912b9ea900f5670551106003b9983500232a4a9ca1d8be1b9c6b7bdeed932d1`
Source SHA: `3b028ebaa8c0c0b15d3095810f6a5e4f910c939f`
Wheel SHA: `97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3`

Kanıt: output/report-update-final-verification.json. Rapor: output/report-update-final/run/index.html.
Mail: output/report-update-final/run/report-email.preview.html.
Arşiv: output/report-update-final/store/README.md, her run ayrı, plan tek kopya.
Teslim ZIP'leri: output/report-update-final-run.zip ve output/report-update-final-store.zip.
Test: output/pytest-report-update-final.xml. Patch: output/report-update-code.patch.
Reference hash değişimi 0, eski 7 drift korunuyor. Git adaylarında sır/endpoint eşleşmesi 0.
Kod repo unborn/untracked olduğu için git diff boş, önceki dosya baseline'ından patch/hash listesi üretildi.

Offline uygulama: VERIFIED. Wheel build/ayrı dizine kurulum/installed import + archive smoke: VERIFIED.
Canlı Oracle DDL/compile kabulü: NOT_RUN. Gerçek artifact push/SMTP/Jenkins: NOT_RUN.
Eski belgede adı geçen tools/check_release.py mevcut değil: NOT_AVAILABLE, uygulanmış kapı sayılmadı.
Sonraki somut iş Jenkins geçişidir: docs/JENKINS_GECIS_HAZIRLIGI.md.
Önceki backend kanıtları ve ZIP görev orijinalleri korunuyor, v1/v2 rapor çıktıları ara kanıttır,
son teslim output/report-update-final'dır. Otomatik code commit/push yapılmadı.

---

# Motor tamamlama - 20 Ekim 2026

Son motor aşaması tamamlandı. 2.353 fark, 559 READY, 123 REVIEW_REQUIRED,
5 BLOCKED, 1.038 INFORMATIONAL. Kapsam inventory/DDL/dictionary COMPLETE,
UNKNOWN 0. Eski 55 blok: 47 READY, 2 INFORMATIONAL, 1 REVIEW, 5 BLOCKED.
Sekiz RANGE/INTERVAL CREATE, ayrılan 10 constraint ve bağlı indeks/yorum SQL,
tarih function index, typed partition karşılaştırması, private/PUBLIC synonym
metadata çözümü uygulandı. Büyük DDL parser bütçesi 30/120 sn, UNKNOWN routine
metadata doğru sınıflanır. Uyumlu mevcut sequence API tüketicisi ayar incelemesine
gereksiz bağlanmaz, sequence ayarı REVIEW ve sayaç/reset yasağı aynı.

Beş gerçek koşul: DENEME FUNCTION/TABLE namespace çakışması, I_ADDR_ID için
eksik C$_0COPY_MTS_ADDR parent, PCK_COMPARE_FIELDS spec/tablo sözleşmesi incelemesi,
PCK_ISLEM_TIPI_AKTAR2 eksik relation/sequence, PCK_LOG_UTIL kaynak BIN$ dependency.
Bunlar giderilmiş gibi gösterilmedi. Tam 55 satır: yz/MOTOR_TAMAMLAMA.md.

282 passed/57,99s, skip yok, output/pytest-backend-completion-final.xml.
6 schema/7 örnek VERIFIED. Reference 36 matched/7 önceden mevcut drift/0 missing,
actual hash değişimi 0. Bağımsız inceleme ve yeni canlı capture bulguları kırmızı→yeşil
kapandı. Son inceleme sequence negatifleri/yeni sequence çakışma korumasını doğruladı.

Source/target her zaman salt okunur. Ön metadata 90 ve yeni tam target capture
954 sabit allowlist sorgusu, toplam 2 target bağlantısı. Source DB bağlantısı 0,
DDL/DML/COMPILE, iş verisi, gerçek push/SMTP/Jenkins değişikliği yok.
Target yeni capture 1.417 nesne: output/target-capture-backend-v1. Aynı raw bloblar
30/120 sn sınırlı parser ile yeniden yorumlandı: output/target-reparsed-backend-v2.
Üç VALID büyük paket COMPLETE, kalan beş target-only INVALID parse bulgusu
uyarıdır. Ham coverage PARTIAL gerçeği, karşılaştırma COMPLETE ayrımı korunur.
Source output/prepared-source-review130-v2, Git SHA ve 917 raw DDL değişmedi.

Teslim: output/backend-completion-v2 ve ZIP. 559 SQL grammar/identity/hash,
566 dosya manifest, dependency sırası, ZIP byte roundtrip, sır/endpoint scan
VERIFIED. HTML/schema 18 dosya bu aşamada değişmedi. Makbuz:
output/backend-completion-final-verification.json.
Plan ID: 75f547faa72f2f424446ba81cf9f86162fbdd405309bf99b8dd45281ec5c1bdb
Generator SHA: b602b46c62e6780a6ed2ba2e86398ccf8d925e5d11d4798f66c993fc540dcff1
ZIP SHA: aa43d0bff686ea1d6bc4d7acc2cd19ea7a01a567f93f091f107703a3f2a0b756
Wheel: output/dist-backend-completion-v2, kurulu import/hash smoke VERIFIED.
İlk no-isolation build setuptools eksikliğinden başarısızdı, isolated build başarılı.

v1 backend-completion paketi ilk capture timeoutlarından dolayı PARTIAL kapsamlı
ara adaydır, teslim değildir. v2 gerekli bloblar yeniden ayrıştırıldıktan sonra
üretilmiştir. Eski output paketleri silinmedi/üzerine yazılmadı. partial-ready.sql
tam migration veya uygulama onayı değildir, gerçek SQL uygulanmadı.

Değişen ürün dosyaları: parsing/{adapter,dependencies}.py, model/plan.py (yalnız
internal unqualified reference bilgisi), planning/{partition_rules,index_rules,policy,
table_rules,object_rules,graph}.py, oracle/{queries,reference_metadata,collector}.py.
Tests: yeni test_backend_completion.py (49 test), test_rules.py/test_blocker_audit.py
artık desteklenen partition beklentisi, test_collector.py SELECT newline uyumu.
Docs: DDL_KURALLARI.md, plan ve durum/devir/doğrulama. Referans repolar salt okunur.
Unborn repo nedeniyle git diff tek başına kanıt değildir, output altında eski
backend baseline ve final patch tutulur. Commit/push yok.

implementation_status: COMPLETE_SUPPORTED_LOCAL_SCOPE
offline_verification: VERIFIED
oracle_integration: READ_ONLY_METADATA_CAPTURED, DDL_ACCEPTANCE_NOT_RUN
jenkins_installation: NOT_RUN
artifact_publication: NOT_REQUESTED
remaining_environment_requirements: Beş kaynak/sözleşme koşulu ve 123 veri/policy
incelemesi, bunlar HTML/Jenkins kodu beklediğinden kalmıyor.

Sonraki kullanıcı görevi: Downloads/oracle-migration-yalnizca-guncelleme.zip,
SHA-256 ac8ca4161fe5f40966fac992d58188bffb7ee16c075e16f0c928b1cd244f61f6.
AKTIF_GOREV değişiklik yönergesi ve iki onaylı HTML referansı içerir, rapor/e-posta,
Run→Target→Plan→Object saklama ve immutable link/dedup güncellemesi. Mevcut
motor kapatıldıktan sonra bu görev uygulanır. Gerçek push/Jenkins için ayrıca
kullanıcı yetkisi şartı sürer. Source/target read-only tüm sonraki işlerde de bağlayıcı.

## Önceki aşamaların tarihsel kaydı

# 130 inceleme kaydı - motor çalışması, 19 Ekim 2026

Kullanıcı HTML tasarımını ayrı yürütürken motor tarafındaki 130 REVIEW_REQUIRED
kaydın tamamı incelendi. 3 READY (PCK_HYPERION BODY ve iki sequence trigger),
1 INFORMATIONAL (PK_COMPARE_FIELDS_LOG), 4 somut dependency BLOCKED,
122 REVIEW_REQUIRED. Aynı 2.353 mantıksal fark korunur. Güncel motor planı:
502 READY · 122 REVIEW · 55 BLOCKED · 1.036 INFORMATIONAL, UNKNOWN 0,
inventory/DDL/dictionary karşılaştırma kapsamı COMPLETE, plan BLOCKED.

Eski 51 blok korunur. Dört ek blok yeni fark değil, önceki genel inceleme
gerekçesinin somut dependency kanıtına dönüşmesidir: PCK_CALL_CENTER parent
partition tablo, PCK_COMPARE_FIELDS değişen spec/katalog referansları,
PCK_ISLEM_TIPI_AKTAR2 eksik ISLEM_HESAP_DENEME3/dış sequence,
PCK_LOG_UTIL recyclebin dependency. Hedef INVALID bu kararların nedeni değildir.

Source/target her zaman salt okunur. Bu tur yalnız yerel snapshot okundu,
Oracle/Jenkins bağlantısı 0, SQL NOT_EXECUTED, iş verisi/COMPILE/REPAIR yok.
HTML/CSS/renderer ve JSON schema sözleşmeleri değişmedi (18 dosya hash'i aynı).
Referans projelerde bu tur hash değişikliği 0. .local sırları Git dışında,
commit/push yok. Kullanıcının eşzamanlı HTML çalışmasına müdahale edilmedi.

## Değişen motor dosyaları

- source/sidecars.py: exporter PACKAGE/TYPE spec+body union, owner/conflict
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
→ 233 passed / 31,59 sn, skip/failure yok. Kırmızı→yeşil kanıtları
output/pytest-review130-*.xml içinde. Bağımsız kod incelemesinin quoted
DBMS_SQL ve FOLLOWS bulguları önce 3 fail/29 pass ile üretildi, sonra kapatıldı.

`tools/check_contracts.py` → 6 schema/7 örnek VERIFIED.
`tools/verify_references.py --report output/reference-review130-final.json`
→ 36 matched/7 önceden mevcut drift/0 missing (exit 1), önceki audit69 ile
actual hash'ler birebir aynı. Bu 7 kayıt yeni hata veya bu turda değişiklik değildir.

`.\.venv\Scripts\python.exe output/verify-review130-final.py` → VERIFIED.
502 SQL grammar/nesne kimliği, tüm fark kapsama/evidence/dependency sırası,
509 bundle dosyası/hash ve ZIP byte roundtrip, sır/özel endpoint eşleşmesi 0.
233 test XML'i ve 130+51 belge satırı/linkleri kontrol edildi.

Yeni çıktı **output/backend-review130-v2** ve aynı adlı ZIP. JSON/SQL-only,
HTML render çağrılmadı. plan.json/evidence.json/objects/*.sql/partial-ready.sql
mevcut JSON sözleşmesindedir. migration.sql yok, partial-ready.sql tam migration
veya uygulama onayı değildir. 130 audit ve 51+4 teknik audit JSON pakettedir.
Makbuz: output/review130-final-verification.json.

Plan ID: 81bb901a0c8356c7125c02f80bcec474119c7195ad850231cbe6e2abba6403b9
Generator hash: 7c21ca22422d9e3845fe8fabdb133de4fe42bbf78748251ace138ab0f246a72b
ZIP SHA-256: 170e829968e43107c7e5bb2b315963c9a6f5676b990a4b33910a827439af4204

Kaynak: output/prepared-source-review130-v2/source-snapshot.json, v8'den
aynı 55 sidecar hash'iyle dependency yeniden bağlandı, 917 nesnenin raw DDL'i
birebir aynı, roundtrip doğrulandı. Git SHA değişmedi:
3b028ebaa8c0c0b15d3095810f6a5e4f910c939f.
Target: output/target-reparsed-v7/target-snapshot.json, önceki capture aynı.
Ham target DDL PARTIAL, korunan target-only INVALID parse sorunları ve uyarılar
aynı kuralla raporlanır. Bu tur canlı snapshot/capture yenilenmedi.

output/prepared-source-review130-v1 tarihsel başarısız ara denemedir,
span kanıt sırası nedeniyle yeniden yüklemeye uygun değildir, kullanılmaz.
output/backend-review130-v1 ara adayıdır, teslim v2'dir. Eski v11 HTML raporu
ve önceki output paketleri üzerine yazılmadı. Wheel bu tur yeniden üretilmedi.

## Sonraki somut adım

HTML çalışması yeni backend-review130-v2 plan/evidence/SQL verilerini mevcut
sözleşmeyle kullanabilir, v11 HTML eski 499/130/51 sayılarını taşır. UI değişimi
sonrası yeni plan üretilirse generator fingerprint ve plan ID yeniden hesaplanır,
doğrulanmış v2 paket yerinde değiştirilmez.

Motor için en yüksek etkili sonraki iş: 8 eksik partition CREATE desteği,
37 parent bağımlı yorum/indeks buna bağlı. Ayrıntılı sınırlar TEKNIK_EKSIKLER_51.md.
Grant allowlist, NUMBER/CHAR-BYTE/NOT NULL, sequence sayaç ve gerçek eksik
metadata koşulları varsayımla gevşetilmedi. Yeni ürün kapsamı eklenmedi.

Offline motor uygulama/doğrulaması: VERIFIED. Yeni canlı Oracle DDL kabulü:
NOT_RUN. TTBP geçişi/Jenkins kurulumu/yayın: NOT_RUN, sonraya bırakıldı.

## Önceki aşamaların tarihsel kaydı

# 69 blok incelemesi - güncel durum, 19 Ekim 2026

Önceki 69 kaydın 18 yanlış/toplu engeli kaldırıldı, 51 gerçek engel korundu.
Nesne bazlı tam çizelge: [BLOK_INCELEME_69.md](BLOK_INCELEME_69.md).
Güncel v11: 2.353 fark, 499 READY, 130 REVIEW, 51 BLOCKED, 1.035 INFORMATIONAL,
UNKNOWN 0, karşılaştırma kapsamı COMPLETE, plan BLOCKED/run PARTIAL.

201 test / 29.43s (pytest-audit69-delivery.xml), 14 audit regresyonu dahil.
6 schema/7 örnek VERIFIED. Kod, test ve HTML sunumu uygulandı, source/target
salt okunur kaldı. Yeni Oracle/Jenkins bağlantısı veya Git push yapılmadı.
Canlı DDL kabulü NOT_RUN, TTBP/Jenkins/yayın ertelendi. Ayrıntılı güncel devir
DEVIR.md içindedir. v8–v10 ara/tarihsel çıktıları korunur.

Değişen dosyalar: planning/{table_rules,object_rules,rules,graph,builder}.py,
model/plan.py (yalnız internal intent kolon kanıtı), parsing/dependencies.py,
reporting/{formatting,render}.py, templates/report.html.j2, runtime/aggregate.py,
tests/unit/test_blocker_audit.py, yz devir/durum/doğrulama/inceleme belgeleri.

## Önceki aşamaların tarihsel kaydı

# Geliştirme Durumu - 19 Ekim 2026

Güncel kullanıcı kuralı: hedef INVALID yalnız rapor uyarısıdır, onarım veya VALID
hale getirme ilk kabul koşulu değildir. Korunacak beş target-only INVALID parse
sorunu karşılaştırmayı bloklamaz. Ham target snapshot DDL PARTIAL korunurken
karşılaştırma kapsamı COMPLETE ve difference_count=2353'tür. Kalan 69 blok gerçek
bağımlılık/yapısal veya destek koşullarındandır. Ayrıntı INVALID_HEDEF_UYGULAMA.md.
Bu değişiklikte yeni Oracle/Jenkins bağlantısı açılmadı.

Yerel INNOVA_ODI → INNOVA_ODI plan/SQL/HTML akışı çalışıyor. Kaynak metadata
belirsizlikleri kapandı, güncel plan 69 güvenlik/özellik bloğu nedeniyle BLOCKED,
run PARTIAL. SQL Oracle'a uygulanmadı. TTBP ve Jenkins kurulumu sonrada.

| Alan | Durum | Güncel kanıt |
|---|---|---|
| A00 referans tabanı | DRIFT KAYITLI | 36 match/7 mevcut drift/0 missing, eski projelere yazılmadı |
| A01 config/domain | UYGULANDI | Kapalı schema, immutable kimlik/KnownValue/kanıt |
| A02 Git kaynak | UYGULANDI | Sabit SHA/blob, checkout/hook/push yok |
| A03 parser/sidecar | UYGULANDI, DESTEK SINIRLI | prepared-source-v8: 917 kayıt, inventory/DDL COMPLETE |
| Kaynak etkin kolon semantiği | DOĞRULANDI | 405 tablo/16560 kolon eşleşti, 10088 BYTE, 10379 collation tamamlandı |
| A04 target collector | UYGULANDI | READ ONLY + allowlist, opsiyonel capability hatası UNKNOWN, izin hatası boş şema değil |
| Gerçek target | DDL PARTIAL | target-reparsed-v7: 1417 kayıt, 5 INVALID/PLS hatalı kısmi tanım, toplam 15 INVALID uyarısı |
| A05 compare | UYGULANDI | before=target/after=source, 2353 olgu, 0 UNKNOWN, tam fark sayısı 2353 |
| A06–A08 SQL/graph | KAPSAMLI YEREL AKIŞ | 447 READY, 119 REVIEW, 69 BLOCKED, 1020 INFORMATIONAL |
| Etkin collation emission | OFFLINE DOĞRULANDI | CREATE/ADD, enabled/disabled/unknown, explicit LOB/noncharacter ve tablo default kapıları |
| A09 artifact | VERIFIED | 472 bundle/483 run dosyası, plan/evidence/SQL hash ve grammar |
| A10 HTML | DOĞRULANDI | 19 HTML, max 93396 byte, 0 kırık link, Innova görünümü tarayıcıda kontrol edildi |
| Kısa offline kapı | PASSED | 187 test / 26.73s, pytest-invalid-target-final.xml, skip/failure yok |
| Contract kapısı | VERIFIED | 6 schema, 7 örnek, ağsız |
| Wheel | PASSED | dist-v8, wheel-smoke-v8, kurulu kod hash'i planla aynı |
| Sır taraması | PASSED | Run dosyaları ve 184 Git adayında 0 gerçek endpoint/parola eşleşmesi |
| TTBP/Jenkins kurulumu/A13 | DEFERRED / NOT_RUN | İlk INNOVA_ODI tam kabulü kanıtlanmadı |
| Artifact publication | DISABLED / NOT_RUN | Commit/push yok |

Güncel rapor output/local-report-v8/index.html, arşiv output/local-report-v8.zip,
doğrulama output/local-report-v8-verification.json. Kaynak source-v8 ve target
reparsed-v7 kullanıldı. Target DDL eski capture-v2 gözlemidir, yalnız hedef
capability parametreleri yeni okundu. Kaynak inventory kontrolü ayrı READ ONLY
transaction'larla yenilendi. Ayrıntı COLLATION_UYGULAMA.md ve DEVIR.md.

## Açık sınırlar

49 bağımlılık, 14 kapsanmayan tablo özelliği, 4 Oracle iç nesnesi ve 2 index
tanımı bloke. Daraltma/tip değişimi, mevcut tablo constraint/data etkisi,
grants ve rutin dış bağımlılıkları otomatik READY yapılmaz. INVALID target
nesneleri salt okuma sınırında düzeltilmez. Kaynak bağlantı bilgisi beklenmiyor.

Yalnız READY alt küme partial-ready.sql içinde. Tam migration.sql yok, çıktı
çalıştırma onayı veya canlı syntax/compile testi değildir. Oracle üzerinde
DDL/DML veya iş verisi testleri NOT_RUN. TTBP/Jenkins/yayın için yeni adım yok.

| Kapanış alanı | Değer |
|---|---|
| implementation_status | LOCAL_COMPARISON_AND_ARTIFACT_FLOW_IMPLEMENTED_WITH_LIMITATIONS |
| offline_verification | PASSED_187_TESTS_CONTRACTS_WHEEL_BUNDLE |
| oracle_integration | READ_ONLY_METADATA_CAPTURED, COMPARISON_COMPLETE, INVALID_REPORTED, DDL_NOT_EXECUTED |
| jenkins_installation | DEFERRED_NOT_RUN, READ_ONLY_LOOKUP_AUTHORIZED |
| artifact_publication | DISABLED_NOT_RUN |
| remaining_environment_requirements | Dependency/unsupported-feature review, INVALID status is report-only |

Eski paket ve aşama kanıtları değiştirilmedi, DOGRULAMA_KAYDI.md tarihsel
kayıtları korur. Goal UI kaydı BLOCKED kaldı, resume aracı yokluğu kullanıcıya
bildirildi. Bu, source erişim engelinin sürdüğü veya çalışma durduğu anlamına gelmez.

## Son teslim doğrulaması

v11 paket VERIFIED: 525 bundle / 538 run dosyası,
21 HTML, en büyük 93223 byte, 945 yerel bağlantı doğrulandı,
0 kırık bağlantı, 0 gerçek sır/endpoint eşleşmesi. 187 Git adayında
0 gerçek yerel sır eşleşmesi. Kod/wheel kurulu import hash'i planla aynı.
201 passed / 29.43s, 6 schema/7 örnek VERIFIED, Oracle/Jenkins/DDL kabulü ayrımı korunur.

ZIP SHA256: `e2eaab489238433d2bed460a32bcd642ba477aa6feef5fee50a1f37ebe38879b`.
Wheel SHA256: `c0597eb640799adcff005b47a34aa5c8b9b55199b2ccf4db86ae4469cf0f41e5`.
Yerel rapor: http://127.0.0.1:8574/targets/LOCAL-ODI/index.html
69 satırlı çizelge: http://127.0.0.1:8574/blocker-audit69.html
Tarayıcıda 2.353 sayı biçimi, 499/130/51 sonuçları, yalnız somut INVALID/LOB
uyarıları ve nesne bazlı çizelge doğrulandı. Static server exec session 54719,
yalnız 127.0.0.1 rapor servisi. Eski server'lar tarihsel yerel çıktılardır.

## Jenkins #6 ve genel mail düzeltmesi - devam

Kullanıcı ilk mailin gövdede genel HTML özeti olmasını ve konu biçimini Sync örneğiyle aynı düzende istedi. Ek dosyalı ilk bildirim bu beklentiyi karşılamadığı için post adımı text/html + readFile(report-email.jenkins.html), attachmentsPattern boş olarak değişti. Konu: GPU | Oracle DB Migration Generator | DURUM | Build #N. Alıcı yalnız mkaracan@innova.com.tr. Sabit Jenkins build arşivi bağlantısı job_url+build_number tam eşleşmesiyle üretilir. Repo yayını henüz yok, olmayan repo linki çizilmez.

#5 stable target gözlemiyle plan üretti, SMTP gönderdi ve UNSTABLE bitti, 7.508 gözlenen fark/95READY/103REVIEW/2.932BLOCKED kaynak BYTE/collation eksikliği yüzündendi. Yereldeki kaynak column correspondence CI'ye eksik taşınmıştı. tools/jenkins_source_semantics.py kapalı SELECT'ler ve iki readonly transaction ile yalnız kaynak kolon metadata'sını okur. Kolon adı kümesi ve duplicate kontrolü, bütün bilinen alan eşitliği ve değişmeyen Git DDL hash'i koşuluyla yalnız eksik BYTE/CHAR/collation tamamlanır. Gözlem saati/capture hash'i run receipt, plan kanıtı zamandan bağımsız. Ham gözlem normal arşiv dışında.

Bağımsız incelemede column set fallback ve saat→plan ID bulguları kırmızı→yeşil kapandı, son19 scopedtest geçti ve açık önemli bulgu yok. Tam paket332passed/35.61s/skip0. Ürün wheel'i hâlâ aynı97d09db..., yeni CI helper'ları ayrı SHA'lı release içinde. Yeni releaseZIP SHA222ecbfec12f8c3bb66f99a98694a06bfbf49561660883365a5aabc294f91e7a.

#6 sourceSHAce8d62d18f46657b702a12bd5fe6fc58ec27cb5a okundu, canlı kaynak405table/0reject, source/target readonly. Şu anda target821nesne capture sürüyor. Bitişte yeni bodyHTML/mail ve targetplan kapsamı doğrulanacak, bu paragraf nihai başarı kaydı değildir.
