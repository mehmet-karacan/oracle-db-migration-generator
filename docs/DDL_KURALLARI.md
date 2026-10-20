# DDL Üretim Ve Güvenlik Kuralları

## Karar Sınıfları

**READY:** Tanımlı V1 kuralıyla, yeterli metadata/parse/bağımlılık kanıtıyla üretilebilir SQL. Otomatik uygulanmaz ve Oracle üzerinde test edildiği anlamına gelmez.

**REVIEW_REQUIRED:** Fark ve aday dönüşüm belli; veri, yetki, bağımlılık veya operasyon koşulu ayrıca doğrulanmalıdır. Aday SQL varsa `review/` altında tutulur, ana migration'a eklenmez.

**BLOCKED:** Eksik/çelişkili metadata, belirsiz dönüşüm, desteklenmeyen söz dizimi veya güvenlik engeli. Uygulanabilir SQL yoktur; açık reason code vardır.

**INFORMATIONAL:** Fark görülmüştür fakat politika gereği uyarlama yapılmaz. Örneğin hedefe özgü nesne, mevcut sequence sayacı veya fiziksel kolon sırası. Bu fark rapordan silinmez.

`risk=LOW` ile `decision=READY` eş anlamlı değildir. READY işlem dahi lock/compile/uygulama davranışı riski taşıyabilir. JSON'da üretim, onay ve execution durumları ayrı tutulur; execution her zaman `NOT_EXECUTED`.

## V1 Zorunlu Yetkinlik Matrisi

| Nesne/Dönüşüm | İlk Teslimatta Beklenen Davranış |
|---|---|
| Eksik normal heap TABLE | Doğrulanmış tam DDL'den CREATE; kolon tipi/uzunluk/CHAR-BYTE/default/NOT NULL kaybolmaz. Named PK/UK/CHECK ayrıştırılır; FK sonraki faza taşınır. Karmaşık depolama özelliği sessiz atılmaz. |
| Eksik nullable kolon | Doğrulanmış tip ile `ALTER TABLE ADD`; yalnız gerçekten eksik alan eklenir. |
| VARCHAR2/NVARCHAR2/RAW genişletme | Aynı tip ve aynı semantik; hedef sürüm limiti, partition key/domain index engeli ve metadata tamlığı doğrulanırsa READY. Diğer durum REVIEW/BLOCKED. |
| NUMBER precision genişletme | Scale değişmiyorsa ve her iki taraf explicit/bilinense, Oracle sınırları ve bağımlılıklar uygunsa READY. Unconstrained NUMBER↔NUMBER(p,s) otomatik güvenli sayılmaz. |
| Veri tipi daraltma/değiştirme | Otomatik READY yok. Veri kontrolü gereği + REVIEW; dönüşüm belirsizse BLOCKED. |
| Default ekleme/değiştirme | Mevcut kolon için doğrulanmış ifade ve bağımlılıklarla üretilir; data backfill yapılmaz. DEFAULT ON NULL ayrı özellik, otomatik normal DEFAULT sayılmaz. |
| NOT NULL | Yeni boş tablo tanımında üretilebilir; mevcut tabloda sıkılaştırma veya gevşetme REVIEW. İş verisi okunmadan veri uyumu iddia edilmez. |
| Virtual/identity kolon | Tam tanınmış yeni tablo tanımında korunur; mevcut tabloda değiştirme V1 BLOCKED. İç sequence nesnesi ayrı migration yapılmaz. |
| Kolon sırası | Farkı raporla; tablo drop/recreate, görünmez-görünür döngüsü veya data copy üretme. |
| Eksik named PK/UK/CHECK/FK | Yeni oluşturulan boş tabloda önkoşullarla üret; mevcut tabloda veri uyumu gerektiren eklemeler REVIEW. FK referansı/external object bilinmiyorsa BLOCKED. |
| Değişen constraint | ENABLE/VALIDATE, deferrable, delete rule, expression ayrı fark. Drop+recreate otomatik ana dosyada yok; REVIEW/BLOCKED. |
| Eksik nonunique normal index | Tablo/kolonlar ve ad çakışması doğrulanırsa CREATE INDEX. Existing rows için unique index REVIEW. |
| Eksik tarih function index | 20 Ekim kullanıcı kapsamıyla: bilinen DATE/TIMESTAMP kolonunda TO_CHAR ve kapalı sayısal tarih formatı, gözlenmiş GREGORIAN session calendar, parent/kolon kanıtı varsa kaynak ifade korunarak CREATE. Örtük tip dönüşümü, başka fonksiyon, bilinmeyen NLS veya unique existing rows REVIEW. |
| PK/UK backing index | Tablo DDL/constraint ile aynı index iki kez oluşturulmaz; dictionary association + AST kanıtı gerekir. |
| Değişen index | Otomatik DROP+CREATE yok. Görünürlük/depolama gibi dönüşümler REVIEW; domain/bitmap/function-based/partition bakım kuralları destek yoksa BLOCKED. |
| Eksik SEQUENCE | Kaynak explicit tanımı korunur; NOCACHE/CACHE doğru üretilir. Başlangıç değerinin source snapshot'tan geldiği işaretlenir. Aynı planda yeni/boş tüketiciler dışında mevcut veriyle çakışma belirsizse REVIEW. |
| Mevcut SEQUENCE | START WITH/LAST_NUMBER runtime state olarak raporlanır, reset yok; NEXTVAL okunmaz. CACHE/CYCLE/ORDER/MIN/MAX/INCREMENT değişiklikleri ayrı değerlendirilir ve V1 REVIEW. |
| VIEW | Tanınan sıradan view için CREATE OR REPLACE; kolon ve sorgu metni korunur. FORCE ile eksik bağımlılık gizlenmez. Materialized/editioning özel durumları ayrı. |
| PACKAGE_SPEC/BODY | Yalnız değişen bileşen üretilir. Spec gerekliliği ve body bağımlılıkları korunur. Ham kodda yalnız kanıtlı CREATE header/terminator müdahalesi; body içerik kaybı yok. Public imza değişimi + çözümlenmeyen dış tüketici REVIEW. |
| PROCEDURE/FUNCTION | Tam parse/kimlik/bağımlılık kanıtı varsa CREATE OR REPLACE. İşlev çağrısı yapılmaz. |
| TRIGGER | DDL+ENABLE/DISABLE birlikte modellenir. Yeni trigger ancak yeni boş tablo veya etkisizlik kanıtı varsa READY; mevcut iş tablolarında yeni/değişen trigger REVIEW. Yan etkili trigger'ı düşük risk sanma. |
| TYPE_SPEC/BODY | Standalone tanınmış yeni type/type body, doğrulanmış tip grafıyla CREATE edilebilir. Kullanılan mevcut type evrimi, FORCE veya cascade dönüşümü BLOCKED. |
| Private SYNONYM | Referans owner/name doğrulanırsa CREATE OR REPLACE; DB link/private-public scope karıştırılmaz. Public synonym REVIEW; DB link üretimi yok. |
| COMMENT ON TABLE/COLUMN | Ayrı sidecar'dan karşılaştır; tek tırnak/q-quote korunur. Ekle/güncelle üret; kaldırma ayrı açık fark ve inceleme gereği. |
| Object GRANT | Grantee+object+privilege+grant option şeklinde ayrı kimlik. Yalnız profilde açık allowlist ile READY; varsayılan REVIEW. Column grant desteklenmiyorsa BLOCKED. REVOKE otomatik yok. |
| MATERIALIZED VIEW/LOG | Envanter, metin farkı ve bağımlılık görünür; V1 auto emission yok, REVIEW/BLOCKED reason. Destekleniyormuş gibi boş SQL verme. |
| Eksik RANGE/INTERVAL TABLE | 20 Ekim kullanıcı kapsamıyla: tam parse, typed key, artan/sabit ve kayıpsız temsil edilebilir NUMBER veya açık takvimli tarih sınırları; kapalı pozitif interval kuralı. Ham partition/depolama suffix'i aynen korunur; constraint/FK/backing graph ayrılır. MAXVALUE interval, LONG/LONG RAW ve bilinmeyen ifadeler kapalıdır. |
| Mevcut partition yapısı farkı | Key/ad/bound/interval ve semantik partition seçenekleri aynı, yalnız fiziksel ayarlar farklıysa mevcut policy ile INFORMATIONAL. Tanınmış gerçek yerleşim değişikliği REVIEW; eksik/çelişkili kanıt BLOCKED. Veri taşıma, DROP/recreate, split/merge otomatik üretilmez. |
| Subpartition/LOB/IOT/external/cluster table | Kapsanamayan fiziksel semantics `BLOCKED_UNSUPPORTED_FEATURE`; alanları atarak normal tabloya dönüştürme. |
| DIRECTORY/DB LINK/USER/ROLE/JOB/policy | Envanter ve açık kapsam dışı notu; DDL yürütme/oluşturma yok. Özellikle credential içeren nesneler yayınlanmaz. |
| Hedefte fazla nesne/kolon | `INFORMATIONAL: TARGET_ONLY_PRESERVED`; varsayılan DROP yok. Yeni isim+eski isim benzerliğinden RENAME çıkarma. |

Bu matris 'incele ve istersen uygula' listesi değildir: READY satırları için çalışan pozitif senaryo, diğerleri için doğru sınıflandırma ve engelleme ilk teslimatta zorunludur. Bütün projeyi güvenlik bahanesiyle yalnız raporlama/no-op'a indirgeme.

## Kaynak DDL İle Migration DDL Farkı

Mevcut tablo değişti diye `CREATE TABLE` basılmaz. Schema Compare `OracleDdlGenerator`'ındaki mevcut `CHANGED TABLE` boşluğu, yalnız `turAdi()` ile eksik kolon tanımı ve `minimumValue()` ile sequence başlangıcı yeni ürüne taşınmaz. Yeni planner bu kuralları tamamlayan ayrı katmandır.

CREATE için orijinal DDL'nin doğrulanmış AST/span temsili kullanılır. FK veya backing index ayrıştırması sonrasında **yeniden parse + statement/özellik kapsamı kontrolü** yapılır. Tanınmayan clause'u sessiz düşürmek yoktur. Tip veya metadata modeli eksikse hash'li ham SQL korunur fakat hazır SQL'e alınmaz.

## Doğru Sıralama

Önce gerçek dependency edge'leri; sadece tür sıralaması yeterli değildir. Açık bir graph'ta stabil topolojik sıra kullanılır. Eşitlikte object identity hash'i deterministik bağlayıcıdır.

Genel fazlar: bağımlı tipler/sequence → tablonun temel kolonları → PK/UK/CHECK ve gerektiğinde backing index → FK → view ve routine/spec/body grafı → trigger/synonym → comment/grant. Bir kolon default'u sequence gerektiriyorsa edge üretilir. PL/SQL type kullanıyorsa type önce gelir. Body spec'ten önce gidemez. Foreign key cycle, FK'leri tablolardan ayırarak çözülür. View/type/PLSQL cycle otomatik FORCE/boş stub yaratılarak çözülmez; `DEPENDENCY_CYCLE` ve etkilenen işlemler BLOCKED.

Kaynak `dependencies.json` ve hedef `ALL_DEPENDENCIES` mevcut SQL'in grafını anlatır; gelecekteki yeni SQL için AST referansları da gerekir. Dynamic SQL adayları `candidate` olarak kalır, doğrulanmış edge sayılmaz. Kapsam dışı zorunlu referansın target'ta varlığı kanıtlanamazsa dependent operation hazır olamaz.

20 Ekim motor güncellemesi: yalnız niteliksiz relation adı için, kendi şeması ve PUBLIC synonym zinciri sabit metadata sorgularıyla çözülebilir. Qualified ad PUBLIC fallback yapmaz; uzak link, cycle, yanlış tür veya bilinmeyen uç hazır sayılmaz. INDEX/TRIGGER gibi ayrı ad alanları relation'ı gölgeleyemez. Bu varlık kanıtı FK key/kolon veya değişen spec sözleşmesinin yerine geçmez.

Uygulama dayanakları: [Oracle CREATE TABLE](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-TABLE.html), [CREATE INDEX](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-INDEX.html), [Format Models](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Format-Models.html). Sayısal tarih formatı dönüşümünde implicit conversion yapılmaz; interval return leading precision sınırı korunur.

## Birleşik SQL Ve Kısmi Plan

Tüm seçili farklar hazır/izinli veya yalnız açıklanmış policy-ignored ise, en az bir READY işlem için `migration.sql` oluşturulur. Bu dosya kontrollü `@@objects/...` sırasıyla paket içindeki tam SQL dosyalarını çağırır. `-- plan_id`, kaynak SHA, target ID ve 'üretildi, uygulanmadı' başlığı içerir.

Herhangi bir REVIEW/BLOCKED fark varsa target planı `REVIEW_REQUIRED`/`BLOCKED` kalır. Bağımsız hazır işlemler `partial-ready.sql` adıyla ayrılabilir; `migration.sql` gibi tam başarı izlenimi verilmez. Bloke bağımlılığa bağlı işlem partial dosyasına dahi girmez. İnceleme adayları `review/` altında; executable aggregate'a asla dahil edilmez. 0 READY işlemde boş deployment dosyası oluşturulmaz.

## SQLPlus Çalıştırma Sözleşmesi

Ürün SQLPlus'ı hedefte çalıştırmaz; DBA için ürettiği script'in runner biçimini açıkça belirler. Düz SQL `;`, PL/SQL tam block `END;` ve tek satır `/` ile sonlanır. Düz SQL'e ilave `/` ekleyip komutu iki kez çalıştırma. Header'da `SET DEFINE OFF`, `WHENEVER SQLERROR EXIT SQL.SQLCODE` ve `WHENEVER OSERROR EXIT FAILURE` bulunur; bağlantı/parola bulunmaz. İlk iki satır kaynak code'un parçası değil runner directive olarak modele kaydedilir. `@@` yalnız generator tarafından oluşturulan güvenli göreli yola gider.

`CREATE OR REPLACE ...` compile uyarısı üretebilir; hata olmaması valid object demek değildir. Ayrı `postcheck.sql`/JSON koşulları seçili nesnelerde `ALL_ERRORS` ve validity kontrolü için hazırlanır; bu dosya otomatik çalıştırılmaz. Gerçek target üzerinde syntax-check adına DBMS_SQL.PARSE veya DDL parse çalıştırma.

## Tekrar Çalıştırma Ve Rollback

Bu ürün migration ledger veya at-most-once executor değildir. `READY` SQL'in tekrar çalıştırılabilirliği garanti edilmez. Hedef uygulandıktan sonra tekrar karşılaştırma NO_CHANGE vermelidir. Mevcut nesneye kör IF EXISTS/ORA-955 yutma wrapper'ı üretme. Oracle patch seviyeleri bilinmeden yeni `IF EXISTS` sözdizimini kullanma.

Kaynak snapshot önceki version bilgisiyle karşılaştırılabilir fakat her ALTER için güvenli rollback üretildiği iddia edilmez. Veri kaybına yol açan ters SQL, gerçek veri geri yüklemesi değildir. Rollback motoru V1 kapsamı dışındadır.

## Hedef INVALID durumu — kullanıcı netleştirmesi, 19 Ekim 2026

INVALID nesneler ve ORA/PLS derleme hata kodları uyarı olarak raporlanır.
INVALID tek başına genel planı veya varlığı doğrulanmış bağımlılığı BLOCKED
yapmaz; nesneye otomatik COMPILE/REPAIR uygulanmaz. Korunacak target-only
INVALID parser hatası karşılaştırma kapsamını eksiltmez; ham capture gerçeği
ayrı korunur. Gerekli DDL/dictionary eksikliği, bilinmeyen referans, FK/kolon/key
yapısı ve bloke prerequisite yine gerçek engeldir. Bu ayrım VALID ve INVALID
dış FK'lerde yalnız ALL_OBJECTS varlığıyla hazır SQL üretmeyi engeller.
