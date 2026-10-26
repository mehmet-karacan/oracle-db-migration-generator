# Mimari Kararlar

24 Ekim kullanıcı kapsam genişletmesi için ADR-023 geçerlidir, önceki Git-only
kaynak ve UI kapsamı bu karardaki sınırlarla genişletilmiştir.

Sürüm: 1.0 · 19 Ekim 2026. Bu kararlar bu paket için tasarım otoritesi tarafından verilmiştir, uygulayıcıya yeniden seçim konusu olarak bırakılmaz. Kapsamı değiştiren yeni karar kullanıcıya ait ayrı talimat gerektirir.

## ADR-001 - Bağımsız Üçüncü Ürün

**Durum:** Uygulama için bağlayıcı.

Sync gözlemler, Analyzer yorumlar, Generator hedefe özgü SQL üretir. İlk ikisi değiştirilmez, yeni ürün yalnız onların onaylı saf bileşenlerini kullanır.

## ADR-002 - Python CLI

**Durum:** Uygulama için bağlayıcı.

İki mevcut pipeline ürününün Python bileşenlerinden yararlanılır. Python 3.12 varsayılan, 3.11–3.13 destek hedefi. Yeni Java web runtime veya Maven bağımlılığı yoktur.

## ADR-003 - 1 Kaynak Ve N Target

**Durum:** Uygulama için bağlayıcı.

Kaynak SHA her run bir kez sabitlenir. Jenkins managed registry kaç enabled target içeriyorsa ALL o kadar target üretir. Her target schema mapping listesiyle birden fazla owner taşıyabilir.

## ADR-004 - Tam Durum Karşılaştırması

**Durum:** Uygulama için bağlayıcı.

Son Git commit diff’i migration değildir. Target source’un kaç sürüm gerisindeyse tamamı hesaba katılır. V1 changed-files-only modu eklenmez.

## ADR-005 - DDL Repo Tek Kaynak

**Durum:** Uygulama için bağlayıcı.

Kaynak canlı DB yeniden okunmaz, kaynak DDL ara DB’de çalıştırılmaz. Git ref/profile/layout doğrulanır. Boş hedef desteklenir fakat Oracle instance/user oluşturulmaz.

## ADR-006 - Ortak Kanonik Model

**Durum:** Uygulama için bağlayıcı.

Source SQL parse ve target DDL+dictionary aynı immutable modele çevrilir. before=target, after=source. Unknown ve absent birbirine dönüştürülemez.

## ADR-007 - Kontrollü Kaynak Uyarlaması

**Durum:** Uygulama için bağlayıcı.

Minimum Python import kapanışı _vendor alanında provenance ile uyarlanır. Eski repolara yazılmaz, runtime C:\ import veya source workflow bağımlılığı yoktur.

## ADR-008 - Schema Compare Referans Rolü

**Durum:** Uygulama için bağlayıcı.

Java karşılaştırma alanları/test senaryoları referanstır, OracleDdlGenerator’ın eksikleri aynen alınmaz. Migration planner yeni ürünün gerçek katma değeridir.

## ADR-009 - Hedefte Kalıcı Yazma Yok

**Durum:** Uygulama için bağlayıcı.

Allowlist metadata okumaları dışında SQL yok. Üründe apply/deploy/rollback komutu bulunmaz. SQL üretimi execution değildir.

## ADR-010 - Varsayılan Silmeme

**Durum:** Uygulama için bağlayıcı.

Target-only nesneler ve kolonlar korunur/raporlanır. Rename tahmini, drop-recreate, sequence reset, gizli data migration ve blanket exception swallowing yoktur.

## ADR-011 - Kural Bazlı Güvenli Üretim

**Durum:** Uygulama için bağlayıcı.

DDL_KURALLARI matrisi zorunludur. READY pozitif senaryolar gerçekten SQL üretir, belirsizlikte REVIEW/BLOCKED. Tüm türleri unsupported yaparak görev bitirilemez.

## ADR-012 - Bağımlılık Grafı

**Durum:** Uygulama için bağlayıcı.

Topolojik sıra gerçek edge’lerle kurulur. FK cycle ertelenmiş FK fazıyla çözülür, diğer cycle’lar gizli FORCE/stub yerine bloklanır. Bloke prerequisite dependent’a taşınır.

## ADR-013 - Owner Remap Yok

**Durum:** Uygulama için bağlayıcı.

İlk sürüm aynı owner adlarıyla çalışır, farklı schema mapping açık engel üretir. Metin içinde global isim değiştirme yapılmaz.

## ADR-014 - Sırların Jenkins Yönetimi

**Durum:** Uygulama için bağlayıcı.

Bağlantı bilgileri managed config, kullanıcı/parola/key Credentials. Job trusted code/host allowlist ile sınırlıdır. Aktif target listesi koddan bağımsızdır.

**19 Ekim 2026 kullanıcı güncellemesi:** İlk çalışma yereldir. Credentials
`.local/credentials.env` veya environment'tan okunabilir, `.local/` Git'e
alınmaz ve raporlarda sır gösterilmez. Jenkins credential entegrasyonu ancak
yerel INNOVA_ODI karşılaştırmasından sonra yapılır.

## ADR-015 - Worker İzolasyonu

**Durum:** Uygulama için bağlayıcı.

Varsayılan 2, en fazla 8 target eşzamanlı. Her worker ayrı process, target schema okumaları sırayla, iç paralellik 1. Hatalı target diğerlerini iptal etmez.

## ADR-016 - Mevcut Kurumsal HTML

**Durum:** Uygulama için bağlayıcı.

Ana aile innova-db-report/1.0, 820px shell ve onaylı logo. V5 veya yeni renk paleti değil. İlk 5 önemli DDL, 30 satır/2048 karakter sınırı, tamamı ayrı SQL.

## ADR-017 - Web Ve Mail Ayrımı

**Durum:** Uygulama için bağlayıcı.

V1 web/Jenkins raporu, yerel CSS/logo ve script’siz yapı. SMTP gönderimi yok. Mail gerekirse ayrı renderer, web’de CID kullanılmaz.

## ADR-018 - Tek Plan Ve Ayrı Run Kaydı

**Durum:** Uygulama için bağlayıcı.

SQL/JSON/HTML aynı plandan. Timestamp/build ayrı run.json, aynı plan girdisi byte-identical artifact. Plan ID/SQL hash döngüsü kurulmaz.

## ADR-019 - İki Depo Ve Yetkili Yayın

**Durum:** Uygulama için bağlayıcı.

Generator code repo, artifact data repo ayrı. Jenkins archive temel, private/kurum onayıyla opt-in Git publication. Source repo’ya push ve public veri yayını yok.

## ADR-020 - Modelden Bağımsız Devir

**Durum:** Uygulama için bağlayıcı.

AGENTS+tek AKTIF_GOREV, mimari kararlar, proje belleği ve kanıtlı ilerleme kalıcıdır. Uygulayıcı model mimariyi baştan araştırmaz, scope dışına çıkmaz.

## ADR-021 - Harici Lisans Motoru Yok

**Durum:** Uygulama için bağlayıcı.

Liquibase, DBMS_METADATA_DIFF ve başka ticari karşılaştırıcı runtime zorunluluğu değildir. Mevcut ANTLR lisans/provenance korunur, yayın yetkisi varsayılmaz.

## ADR-022 - Kabul Düzeylerini Ayırma

**Durum:** Uygulama için bağlayıcı.

Offline fixture testi, gerçek Oracle kabulü ve Jenkins kurulum testi ayrı. Ortam/credential yokluğunda live NOT_RUN kalır, offline uygulama devam eder.

## ADR-023 - Kullanıcı Talimatıyla Ortak UI Ve Oracle Kaynağı

**Durum:** 24 Ekim 2026 kullanıcı talimatıyla uygulandı, canlı ortak dağıtım NOT_RUN.

Kullanıcı Git veya bağlantı seçerek ekrandan karşılaştırma, Oracle kaynağı ve
uygun sabitlerin ekrandan ayarlanmasını istedi, shadcn tercihine yöneldi ve
yerleşimi “Kurum içi ortak uygulama” olarak seçti. “Hadi geliştirmeye başla”
talimatı bu kapsamın uygulama yetkisidir. ADR-005'in yalnız Git kaynak sınırı
Oracle salt okunur kaynak adaptörüne genişler. Python motoru/CLI korunur,
isteğe bağlı FastAPI kontrol katmanı ve React/shadcn UI eklenir. Yeni Java,
ticari karşılaştırıcı veya AI servisi yoktur.

Oracle kaynak gerçek capture kimliğini taşır, sahte Git SHA verilmez. 1→N,
tam durum, salt okuma, UNKNOWN/kanıt ve deterministik SQL kuralları korunur.
Mevcut HTML rapor ailesi değişmez. Ortak mod imzalı kimlik proxy'si, sürümlü
şifreli sırlar ve Jenkins çalıştırıcısı gerektirir, loopback geliştirme modu
ayrıdır. Canlı SSO/secret sağlayıcısı/dağıtım adresi varsayılmaz.

Günlük TTBP/08:00 işi değiştirilmez. Mail yalnız mkaracan@innova.com.tr,
gerçek SQL Jenkins yetkili arşivinde kalır. Üretim kurulum NOT_RUN durumları
docs/UI_CALISTIRMA_VE_DAGITIM.md içinde açıkça kayıtlıdır.

## ADR-024 - Ortak kullanıcı, proje kapsamı ve Jenkins oturum devri

24 Ekim sonraki kullanıcı talimatıyla doğrulanmış oturumlar ortak `shared`
yetkisini kullanır, UI kullanıcı/rol/model bilgisi göstermez. İmzalı proxy
kimlik doğrulaması korunur. Proje üst seçimdir, bağlantı/profil/run kayıtları
proje kimliği taşır, çapraz bağlantı kullanımı API’de reddedilir. Eski kayıtlar
SKY’ye aittir. Bu ayrım görünüm/iş kapsamıdır, bütün kullanıcılar proje seçebilir.

Jenkins servis hesabı bulunmadığından onaylı mevcut SKY Git→PROD/TTBP profili
server-owned spec hash eşlemesiyle browser handoff kullanır. Durum yerel
kuyrukta çalışmaz, mevcut Jenkins oturumunda kullanıcı/uygulayıcı başlatır.
Gerçek tamamlanmış run metadata’sı kapalı sözleşme, tazelik ve hedef eşleşmesi
ile yerel operatör aracından bağlanır. SQL Jenkins arşivinde kalır. Sonuç
bağlama atomik ve build başına benzersizdir, otomatik polling iddiası yoktur.
Tam servis hesabı/kurumsal dağıtım ayrı NOT_RUN kapısı olarak korunur.

## ADR-025 - Proje ayarları ve kullanıcının parolalı girişi

25 Ekim kullanıcı onayı ADR-024'ün kimlik gösterimi kararını genişletir.
Şema Karşılaştırma ekranında mkaracan / Mehmet KARACAN oturumu gösterilir.
Bütün doğrulanmış kullanıcılar shared capability taşımayı sürdürür. Proxy
modu korunur. Yerel --local-preview parolalıdır, ilk kurulum açık yerel
bootstrap yetkisiyle loopback'te yapılır. Ağ password modunda setup kapalıdır.
Kayıtlı parola geri gösterilmez, scrypt/salt ile tutulur. Oturum token hash'i
özel SQLite içindedir. Ortak TLS deployment bu kod tesliminin kabulü değildir.

Çalışma ayarları proje kimliğinde sürümlenir, eski defaults yalnız SKY.
Eşzamanlı sınır proje bazındadır, process/host toplam tavanı 4 kalır. Frozen
spec ayarları korunur. UI seçili proje kimliği ve API'de nesne sahipliği birlikte
doğrulanır. Scope verilmemiş eski API okumaları SKY'ye aittir. SQL/UNKNOWN ve
Jenkins yetkili arşiv politikası değişmez. Envanter özeti SQL gövdesiz, plan ve
manifest hash'i doğrulanmış metadata olarak saklanır.

## ADR-026 - Açık yerel çalıştırma ve çalışma kaynağına göre SQL saklama

25 Ekim 2026 kullanıcı talimatı: masaüstünde çalıştırılan işin SQL'i özel yerel
run dizininde saklanır ve uygulama içinden okunur. Jenkins çalışmasının SQL'i
Jenkins arşivinde kalır. Önceki Jenkins-only saklama sınırı yalnız açık LOCAL
seçimi için genişler. Varsayılan Jenkins ve legacy istemci davranışı korunur.
Yürütücü kayıt üzerinde sabittir, yerel kuyruk Jenkins işini çalıştırmaz. Ağ
runtime'ında LOCAL seçimi reddedilir. Jenkins SQL'i yerel API'den sunulmaz.
SQL gösterimi salt okunurdur, içerik/çift tırnak korunur. Oracle yazımı yoktur.
