# İlk Jenkins kurulumu

**Güncel kapsam (20 Ekim son kullanıcı kararı):** Yalnız TTBP varsayılandır.
`SCHEMA_SCOPE=INNOVA_ODI` yalnız kullanıcı manuel istediğinde seçilir. Seçim
source roots, hedef ve kaynak metadata hesap kapsamını aynı anda daraltır.
Raporda `PROD` ve `TTBP` görünür; eski `LOCAL-TTBP` ID'si iç kimlik/bağlantılar
için korunur. Katalog okuyucusu INNOVA_ODI olması, ODI şemasının da
karşılaştırıldığı anlamına gelmez. Source ve target READ ONLY kalır.

**Güncel takvim (20 Ekim son kullanıcı yanıtı):** Her gün Türkiye saatiyle
08:00. Canlı Schedule ve Pipeline trigger birlikte güncellenip yeniden okunarak
doğrulandı. Aşağıdaki 08:40 kayıtları önceki karardır.

**Güncel saklama kararı (20 Ekim):** DDL, JSON ve HTML yalnız Jenkins build
artifact arşivinde tutulur. Artifact Git yayın aşaması ve credential binding
canlı job'dan ve Pipeline şablonundan kaldırıldı. Yerel artifact push da
yapılmaz. Mail doğrudan ilgili build raporuna gider. Mevcut son 20 build/artifact
saklama sınırı ve günlük Europe/Istanbul 08:00 korunur. Kod deposunun private
push yetkisi sürer. Aşağıdaki önceki artifact yayını yetkisi artık geçerli değildir.

20 Ekim güncellemesi: kullanıcı günlük Europe/Istanbul 08:40 çalışmasını ve
mevcut iki private GitHub deposuna kod/artifact push'unu açıkça yetkilendirdi.
Kod ve runtime raporları ayrı depolardır. Geçici GitHub hedefi, kurumiçi depo
hazır olduğunda değiştirilir. Aşağıdaki ilk kurulumun manuel/yayınsız kaydı tarihseldir.

Yayın adımı `tools/jenkins_publication.py` ile karşılaştırma tamamlandıktan sonra
çalışır. Trusted release içindeki ayrı artifact-publication.json açık depoyu,
private storage/push onayını ve allowlist'i taşır; credential değeri taşımaz.
Mevcut Jenkins GitHub credential'ı process environment içinde bağlanır. Canonical
SSH origin için yalnız süreçte HTTPS rewrite ve scoped Authorization header
kullanılır; token argv'ye, URL'ye veya Git config dosyasına yazılmaz.
Private/yazma yetkisi taze API'den doğrulanır. Ayrı owned checkout, immutable
plan, iki commit, normal push ve exact remote SHA doğrulanır. Private README
erişimi HTML login sayfası yerine GitHub Contents API ve sabit commit ref ile
kanıtlanır. Başarısız yayında SQL/karşılaştırma korunur, mail gerçek Jenkins
arşivine gider; doğrulanmış yayında mail sabit GitHub run README'sine bağlanır.
Mail yalnız mkaracan@innova.com.tr adresine gider. Source/target salt okunur.

Önceki kullanıcı kapsamı INNOVA_ODI ve TTBP'yi birlikte içeriyordu. Aynı sabit Git SHA
iki owner için okunur; her hedef kendi schema mapping ve credential kimliğiyle
doğrulanır. Kaynak dictionary kanıtı da her owner için ayrı hesap/oturumdan
toplanır. Bir hedefin bağlantı veya metadata hatası diğerinin raporunu durdurmaz;
doğrulanamayan alanlar UNKNOWN kalır. Oracle DDL/DML/COMPILE uygulanmaz.

Genel konu `SKY | Oracle DB Migration Generator | DURUM | Build #N` biçimindedir.
Gerçek build başlangıcı ve rapor bitişi arasındaki süre gösterilir; en önemli
5 nesne mevcut karar sırasıyla seçilir. Teknik nesne filtreleri ve GRANT
dışlama profilde açık policy olarak tanımlıdır; ham envanter silinmez.

Jenkins agent'tan GitHub HTTPS bağlantısı #10/#11 tanısında ConnectionResetError
ile kesildi. Sistem CA ile sonuç değişmedi; TLS doğrulaması kapatılmadı. Bu
ortamda otomatik GitHub yayını henüz doğrulanmış sayılmaz. Karşılaştırma, Jenkins
arşivi ve tek alıcılı mail çalışmaya devam eder. Yerel yetkili erişimle yapılan
artifact push ayrıca kaydedilir; Jenkins otomatik yayın kanıtı yerine sunulmaz.

## Tarihsel ilk kurulum kapsamı

Kapsam yalnız INNOVA_ODI. Source Git checkout/metadata okuması, hedef Oracle metadata okuması; DDL/DML, COMPILE ve Git push uygulanmaz. INVALID nesneler rapor bulgusudur. İş otomatik tetiklenmez.

`templates/jenkins-generator.groovy` güvenilir job şablonudur. Kurumsal source/target ayarları ve sır değerleri içermez. İlk kurulumda SHA ile doğrulanan offline ZIP, Stashed File Parameter üzerinden yüklenir. Sonraki build'de dosya seçilmezse korunmuş ZIP aynı SHA ile yeniden doğrulanır. Boş file parametresi yükleme sayılmaz.

Sistem Python 3.10 değiştirilmez. Resmi, sabit SHA'lı CPython 3.12 ve hash kilitli Linux wheel'leri bu işe özel workspace altında hazırlanır. Arşivdeki göreli linkler yalnız arşiv içindeki dosya içeriklerine çözümlenir; dosya sistemi linki yaratılmaz. Runtime dosyaları her build'de doğrulanır. Python bytecode yazımı kapalıdır; ardışık build bütünlük kontrolünü bozmaz.

Build parametreleri:

- `ENVIRONMENT_CHECK`: Python/dependency/config kontrolü; Oracle bağlantısı ve e-posta gönderimi yok.
- `COMPARE`: sabit source commit'i ve yalnız INNOVA_ODI target metadata'sını karşılaştırır. SQL yalnız dosya üretilir.
- `GENERATOR_RELEASE`: ilk kurulumda ZIP; sonraki build'lerde boş bırakılabilir. Cache kaybında aynı doğrulanmış ZIP tekrar yüklenir.

Mevcut SKY source Git ve INNOVA_ODI DB credential kimlikleri kullanılır. Credential değerleri Groovy'ye interpolate edilmez, JSON'a veya arşive yazılmaz. URL/credential build parametresi yoktur. TTBP credential'ı kullanılmaz.

Sonuç arşivi `output/runs/build-N/**` altındadır; ham `observations/**` dışlanır. Sonuç 10/20 UNSTABLE, 30/40 FAILURE olarak korunur. UNSTABLE, raporlanmış inceleme/engel veya eksik hedef sonucunu gösterir; başarılı/no-change diye sunulmaz.

Kullanıcı talimatıyla bildirim yalnız **mkaracan@innova.com.tr** adresine gider; CC/BCC/dağıtım listesi/recipient provider yoktur. COMPARE sonunda onaylı genel HTML özeti doğrudan mail gövdesinde gösterilir; ek dosya açılması gerekmez. Hedef/fark/DDL/inceleme/engel sayıları, önemli nesneler ve sabit Jenkins build arşivi bağlantısı görünür. Konu `GPU | Oracle DB Migration Generator | DURUM | Build #N` biçimindedir. SQL body, sistem logu veya rapor eki gönderilmez. Git bağlantısı yalnız gerçek yayın olduğunda kullanılabilir; bu ilk kurulum Jenkins arşivini kullanır. Plugin/güvenlik ayarı değiştirilmez.

Git DDL'de yazmayan etkin BYTE/CHAR ve collation için önceki yerel doğrulama akışı Jenkins'e taşındı. Mevcut SKY INNOVA_ODI credential'ı ile yalnız kaynak kolon dictionary metadata'sı okunur; kaynak DDL hâlâ sabit Git commit'idir. Oturum sahibi ve iki ayrı salt okunur transaction envanteri doğrulanır. Her tablo için canlı kolon kümesi (duplicate dahil) ve bilinen bütün Git kolon alanları birebir eşleşmeden eksik semantik tamamlanmaz. Drift yaşayan tablo UNKNOWN kalır. Git DDL byte/hash'i korunur. Kanonik eşleşme kanıtı zaman içermez; observation zamanı ve tam capture hash'i ayrı run receipt'tedir. Ham kaynak gözlemi ve target observations normal arşiv dışında kalır. Güncel metadata geçmiş SCN garantisi değildir.

GitHub env erişimi salt okuma ile kontrol edildi; iki depo private ve boştur. Bu kurulum dış Git push'u gerektirmez. Job ayrı release ile çalışır; Jenkins arşivi kullanılır.

## Doğrulama kaydı

Canlı #4 ortam kontrolü SUCCESS; #6 karşılaştırma UNSTABLE (tam kapsam, UNKNOWN0; 2.352fark/559READY/123REVIEW/5gerçekkoşul). Genel HTML gövde maili izinli tek alıcıya gönderildi ve ayrıntı bağlantısı doğrulandı. Sonuçlar `yz/DOGRULAMA_KAYDI.md` ve yerel `output/jenkins-setup/live-verification.json` kanıtında kayıtlı. Oracle DDL/DML kabulü her zaman NOT_RUN; ürünün SQL uygulama aşaması yoktur.
