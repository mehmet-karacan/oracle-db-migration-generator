# AKTIF_GOREV - Jenkins Kurulumu

Görev: ODMG-JENKINS-001. Kullanıcı Jenkins’e girip Generator işini oluşturmayı açıkça istedi.

Kapsam: sky/oracle-db-migration-generator Pipeline, yalnız INNOVA_ODI. Mevcut DDL Sync, Analyzer ve source depoları değişmez. Source/target daima salt okunur. Test edilmiş release, workspace Python 3.12, mevcut Jenkins Credentials, sonuç arşivi. Otomatik tetikleme, Git push ve Oracle DDL/DML yok. Kullanıcının son talimatıyla Jenkins bildirimi yalnız mkaracan@innova.com.tr adresine gider, başka alıcı/CC/BCC yok.

Plan: docs/superpowers/plans/2026-10-20-jenkins-setup.md. Önceki rapor görevi output/jenkins-setup/previous-AKTIF_GOREV.md altında korunur.

Durum: ODMG-JENKINS-001 tamamlandı. #4 ortam kontrolü SUCCESS, #6 tam salt okunur karşılaştırma raporlandı (UNSTABLE, 5 gerçek koşul, UNKNOWN0). Genel HTML gövde maili yalnız izinli alıcıya gönderildi. Son kanıt yz/DEVIR.md başlığı ve output/jenkins-setup/live-verification.json.

20 Ekim kullanıcı rapor düzeltmesi: genel maildeki nesne başına `işlem / hedef`
satırı kaldırılır. Bağımlılık gerekçesi gerçek şema/nesne/tür ve eksik koşulu
belirtir, doğrulanamayan durum yokluk olarak sunulmaz. Karar ve SQL gövdeleri
değişmez. #6'nın doğrulanmış kayıtlarından yeni rapor üretilir, yeni Oracle
bağlantısı açılmaz. Tamamlandı: 341 test geçti, Jenkins #7 UNSTABLE olarak
raporlandı. 559 SQL gövdesi aynı, yeni Oracle bağlantısı 0. Somut gerekçeler
gerçek mail/plan üzerinde doğrulandı, mail yalnız izinli alıcıya gönderildi.
Normal karşılaştırma akışı v3 ile geri yüklendi. Kanıt: output/report-reasons/.

20 Ekim sonraki kullanıcı talimatları:

- Genel mailde Nesne / Fark sütunu genişler, Hedef/İşlem/Sonuç daralır.
  Onaylı logo byte'ları korunur, mail istemcileri için ölçüsü açık tanımlanır.
- Her gün Europe/Istanbul 08:40, raporun 09:00 mesai öncesinde gelmesi hedeflenir.
  Bu açık talimat önceki manuel çalıştırma sınırının bu iş için güncellenmesidir.
- Generator kodu ve raporlar ayrı, mevcut private GitHub depolarına push edilir.
  Kullanıcı bunları kurumiçi depolar hazır olana kadar geçici hedef olarak onayladı.
  .local/.env/output/reference-ui ve gerçek bağlantı/sır bilgileri kod Git'ine girmez.
  Bu açık talimat önceki dış Git push NOT_RUN sınırını bu iki depo için günceller.
- Bu işler tamamlanınca INNOVA_ODI'ye ek TTBP salt okunur karşılaştırması yapılır.
  Oracle DDL/DML/COMPILE ve kaynak DDL deposuna push hiçbir aşamada yapılmaz.

20 Ekim son kullanıcı rapor kapsamı:

- Proje/mail konu öneki SKY olur. Genel mail yalnız izinli alıcıya gider.
- DDL Sync'in teknik nesne ad filtreleri kaynak ve hedefe aynı uygulanır.
  GRANT kayıtları politika ile kapsam dışında tutulur, gerçek iş nesnelerindeki
  her `$` karakteri dışlama nedeni değildir. Ham envanter ve kanıt korunur.
- Genel raporda gerçek başlangıç/bitiş zamanından çalışma süresi gösterilir.
  Önemli nesneler mevcut karar önceliğiyle sıralanıp ilk 5 ile sınırlandırılır.
- İki şemanın canlı kontrolü Jenkins #12'de sürmektedir. Offline doğrulama
  414 test geçti. Son kod normal push ile private Generator deposunda:
  f4560bdcb158a7fe727febe064e04b8ad66baa65.
- Jenkins agent GitHub HTTPS bağlantısı ConnectionResetError ile kesiliyor.
  Bu durum yalnız otomatik artifact yayınını etkiler, karşılaştırmayı durdurmaz.
  Bu önceki yayın planı aşağıdaki son kullanıcı kararıyla iptal edilmiştir.

20 Ekim son kullanıcı saklama kararı:

- Üretilen DDL, JSON ve HTML şimdilik yalnız Jenkins build artifact arşivinde
  tutulur. Artifact Git deposuna push yetkisi geri alınmıştır, yerel yayın da
  yapılmaz. Generator uygulama kodu için önceki private Git push yetkisi sürer.
- Canlı job ve Pipeline şablonundan artifact publication aşaması ve ilgili
  credential binding kaldırıldı. Mail doğrudan ilgili Jenkins raporunu açar.
  Mevcut 20 build/artifact saklama sınırı korunur, saat Europe/Istanbul 08:40.
- #12 kaynak hazırlığını tamamladı fakat PARTIAL kaydın çıkış kodu 10 runner
  tarafından hatalı fatal sayıldığı için hedef karşılaştırmasına ulaşmadı.
  Bu hata giderilir, kaynak belirsizliği başarı/tamlık gibi sunulmaz. Tek seferlik
  devam ancak önceki snapshot'ın dışarıdan sabit SHA-256'sı, ham dosyalar ve
  güncel sabit Git SHA'sı doğrulanarak yapılır. Oracle her zaman salt okunurdur.

20 Ekim son kullanıcı takvim kararı: günlük başlangıç Europe/Istanbul 08:00.
Bu, önceki 08:40 saatini değiştirir. Hem canlı cron hem declarative Pipeline
trigger ve iş açıklaması 08:00 olarak kaydedilip yeniden okunarak doğrulandı.
Bu takvim değişikliği yeni karşılaştırma veya mail tetiklemez, SQL uygulanmaz.

20 Ekim TTBP kullanıcı görevi: ORA-04088 nedenini salt okunur incele ve TTBP
fark/DDL raporunu üretip yalnız Jenkins'te sakla. Canlı #15 tanısı hedef TTBP
CONNECT aşamasında SYS.BLOCK_TOOLS_TTBP / ORA-20983 reddini gösterdi. Trigger,
kimlik, parola veya yetkiler değiştirilmez. #16 mevcut INNOVA_ODI hesabının
etkin SELECT_CATALOG_ROLE ve SELECT_TTBP yetkilerini, TTBP GET_DDL erişimini
kanıtladı. Bu mevcut yetkiyle açık metadata_reader yapılandırması uygulanır,
session identity + katalog rolü + hedef owner varlığı/DBA envanter erişimi
doğrulanır. Varsayılan kendi-owner erişimi ve source/target yönü değişmez.
ALL_OBJECTS görünürlüğü tamlık kanıtı sayılmaz, seçili şemaya bindli kapalı
DBA metadata sorguları kullanılır. 08:00, tek mail alıcısı ve Jenkins-only
arşiv politikası korunur. Hiçbir üretilen SQL Oracle'da çalıştırılmaz.

20 Ekim son kullanıcı kapsamı: günlük varsayılan yalnız PROD ortamındaki TTBP.
INNOVA_ODI karşılaştırması yalnız kullanıcı isterse manuel seçilir. Mevcut ODI
katalog hesabı TTBP okuma kimliği olarak kalabilir, ODI şeması karşılaştırılmaz.
Kaynak profil/metadata/hedef listesi aynı seçime daralır. Gerçek hash adlı teknik
nesneler ve bunların child kayıtları kaynak/targetta filtrelenir, COMMENT/GRANT
kayıtlarının sentetik S_hash kimliği kullanıcı nesne adı diye gösterilmez,
kanıtlı gerçek tablo/kolon adı gösterilir. Hedef görünen adı PROD olur, şema TTBP
ayrı gösterilir. İç target_id/path/kimlik/DDL semantiği korunur. Tüm değişiklikler
salt okunur sınırı, 08:00 ve Jenkins-only arşiv politikasını korur.

20 Ekim son kullanıcı inceleme görevi: PROD / TTBP planındaki 2.355 BLOCKED
işlemin tamamını operasyon kimliği ve kanıtıyla tek tek incele. Gerçek üretim
engeli olmayanları gerekçeli INFORMATIONAL/uyarıya ayır, kod hatalarını kırmızı
testten başlayarak düzelt. UNKNOWN alanları var/yok veya tam karşılaştırma diye
sunma. Yeni rapor ve DDL yalnız Jenkins arşivinde, varsayılan TTBP, 08:00 ve tek
mail alıcısı korunur. Source/target daima READ ONLY, DDL/DML/COMPILE yok.

20 Ekim 2.355 engel incelemesi tamamlandı: 2.355/2.355 tekil kanıtlı eşleme,
726 test geçti. Güncel plan 1.265 READY SQL /632 REVIEW /251 BLOCKED. #28 rapor,
DDL ve inceleme CSV/JSON yalnız Jenkins arşivinde, yeni Oracle bağlantısı0,
SQL NOT_EXECUTED. Normal v13 PROD/TTBP ve 08:00 geri yüklendi. Ayrıntı yz/DEVIR.md.

21 Ekim kullanıcı sunum düzeltmesi: genel mail ve raporlardaki BLOCKED,
[TABLE], COMMENT gibi teknik etiketleri anlaşılır Türkçe karşılıklarıyla göster.
Üretilemeyen DDL varsa sayısını koru ve durumun altında kısa, somut neden yaz.
Tekrarlanan bağlı nesne gerekçelerini birleştir. Kanıtlı engelleri gizleme,
karşılaştırma kararını, UNKNOWN bilgisini veya SQL'i sunum için değiştirme.
Mevcut TTBP arşivi yeni görünümle Oracle bağlantısız yenilenebilir. Önceki
Jenkins, yalnız tek alıcı mail, 08:00 ve Jenkins-only arşiv yetkileri korunur.

21 Ekim ek kullanıcı düzeltmesi: karşılaştırma süresini ana özette dakika/saniye
olarak göster, görünüm yenileme süresiyle karıştırma. Karşılaştırmanın özgün
başlangıç/bitiş zamanını yenilenen raporlarda da koru. Fark kartı doğrulanmış
bulunan farkların sayısını göstersin, UNKNOWN karşılaştırma kayıtlarını ayrıca
say ve eksik kapsamın ek farklar doğurabileceğini açıkla. Kanonik null toplamı
değiştirme, UNKNOWN'u kesin fark veya eşitlik diye gösterme.

21 Ekim yeni kullanıcı incelemesi: #29/#31 TTBP planındaki 4.645 UNKNOWN
karşılaştırma kaydını difference ID ve kanıtıyla tek tek incele, koddan
kaynaklananları düzelt, gerçek eksikliği açık ve somut nedenle raporla.
BAREM_TANIM.OLUSTURMA_TARIHI gibi bağımlı DDL'lerde yalnız hazır değil demek
yerine üretimi durduran kök neden ve gerekli nesne/kolon bilgisi gösterilsin.
75 dk 9 sn çalışma süresinin aşama/kod maliyetini ölç ve gereksiz tekrarları
gider. Karşılaştırma deterministik/statiktir, LLM/AI servisi eklenmez. Süre
alanları mevcut HTML ailesine uygun profesyonel düzende yerleştirilsin.
Source/target daima READ ONLY, Oracle DDL/DML/COMPILE yok. TTBP varsayılanı,
08:00 takvimi, tek mail alıcısı ve yalnız Jenkins artifact arşivi korunur.


21 Ekim son kullanıcı görevi: #38 planındaki kalan493 UNKNOWN kaydı ID bazında
incele, kod hatalarını gider ve karşılaşılan desteklenmeyen SQL yapılarını
mevcut statik parser/model içinde destekle. Gerçek bozuk/eksik kaynak bilgisi
başarılı veya eşit diye gösterilmez. Source/target daima READ ONLY kalır.
Ek sunum düzeltmesi: mailde nesne açıklaması dört sütuna yayılan ayrı satır
olmaz, Nesne / Fark hücresinde kısa neden gösterilir, tam neden ayrıntılı
raporda korunur. Önceki Jenkins-only DDL,08:00,TTBP ve tek alıcı sınırı sürer.

21 Ekim son sunum talimatı: süre kutusu üstte yer almaz. Karşılaştırma süresi
mail ve genel raporun alt izlenebilirlik bölümünde küçük, gri tek satırdır.
Başlangıç/bitiş, TSİ etiketi ve rapor yenileme süresi kullanıcı görünümünden
kaldırılır, özgün zamanlar teknik JSON kayıtlarında korunur. Yalnız sunum
yenilenir, SQL ve karşılaştırma kararları değişmez, salt okuma sınırı sürer.

## 24 Ekim 2026 UI uygulama kapsamı

Kullanıcı ortak UI/Oracle source/ayar ekranlarını istedi ve “Hadi geliştirmeye
başla” dedi. Önceki görev geçmişi korunarak bu kullanıcı talimatı uygulanır.
Plan docs/superpowers/plans/2026-10-24-shared-ui-oracle-source.md, ADR-023.
Yalnız bu repo kodu ve sentetik offline/yerel UI doğrulaması. Mevcut Jenkins
job değişikliği, yeni canlı Oracle kabulü, SMTP veya push bu aşamada yapılmaz.
Ortak SSO/Jenkins UI deployment NOT_RUN, detay yz/DEVIR.md ve
UI_CALISTIRMA_VE_DAGITIM.md. Günlük TTBP/08:00, tek alıcı ve Jenkins-only sürer.

## 24 Ekim 2026 sonraki kullanıcı talimatı - ortak proje ve canlı UI koşusu

Mevcut Git/Oracle bağlantıları UI’ye aktarılır, üst SKY alanı proje seçimi
olur. Bütün doğrulanmış oturumlar aynı ortak yetkiyle karşılaştırır, rol/kullanıcı
ve model bilgisi gösterilmez. Kullanıcı UI’den canlı karşılaştırma ve maili
yalnız mkaracan@innova.com.tr adresine açıkça istedi. Bu, önceki UI aşamasının
yeni canlı koşu/mail NOT_RUN sınırını bu deneme için günceller. Oracle READ
ONLY, SQL yalnız Jenkins arşivi, TTBP/08:00 ve dış push sınırları korunur.
Jenkins servis hesabı henüz yok: mevcut yetkili tarayıcı oturumuna açık aktarım
ve doğrulanmış çalışma metadata’sının UI’ye bağlanması kullanılır. Otomatik
API/ortak deployment kurulmuş gibi sunulmaz. Plan projects-shared-live.md.

## 24 Ekim 2026 - nesne bazlı sonuç UI

Kullanıcı tablo seçildiğinde kaynak/hedef farklarını istedi ve başka ürünün
birebir kopyası yerine kendi bileşenlerimizi/yöntemlerimizi seçti. Mevcut
React/shadcn içinde kaydedilmiş alan farkları, nesne seçimi ve bağlı işlem/DDL
gerekçeleri uygulanır. Kanonik motor/SQL kararı ve UNKNOWN sözleşmesi korunur.
Mevcut #55 sonucu yalnız SQL gövdesiz yapısal metadata ile UI’ye bağlanır,
yeni Oracle koşusu/SMTP/Jenkins job değişikliği veya push bu aşamada yoktur.
Plan docs/superpowers/plans/2026-10-24-object-results.md.

24 Ekim son yerleşim talimatı: sol nesne listesi kalıcı, seçilen nesnenin kaynak/hedef karşılaştırması sağ panelde. Modal yerine aynı çalışma alanı, kanonik veri üzerinden diff renkleri. Plan results-workspace.md. Yeni Oracle/Jenkins/SMTP/push yok.

24 Ekim bağlantı düzenleme talimatı: Git kullanıcı adı/token alanları ve
Bitbucket kişisel token yönergesi netleşir. Düzenlemede kullanıcı adı ve
kayıtlı sır durumu görünür, token/parola geri gösterilmez, boş değer korunur.
SQLite/Fernet saklama kullanıcıya açıklanır. Gerçek bağlantılar değiştirilmez,
yeni Oracle/Jenkins/SMTP/push yok.

24 Ekim şema seçimi talimatı: kayıtlı bağlantılardan sonra kaynak şemaları ve
her hedefin kaynak/hedef şema çiftleri karşılaştırma ekranında açıkça seçilir.
Giriş hesabı karşılaştırılan şemadan bağımsızdır. Mevcut yetkiler doğrulanır,
yeni yetki verilmez. Aynı adlı şemalar desteklenir, owner remap yapılmaz.
Birinci taraf arayüz/rapor/belge metinleri sadeleştirilir, kod ve SQL için
gerekli noktalı virgüller korunur. Plan 2026-10-24-schema-selection.md.
Yeni canlı Oracle/Jenkins/SMTP/push bu uygulama aşamasında yoktur.

## 25 Ekim 2026 - arayüz okunabilirliği, dil ve tema

Önceki şema seçimi Bağlantılar ekranında ayrı Şema eşleştirmeleri sekmesine
alınır. Kullanıcı sonraki kapsamda genel fontların büyütülmesini, TR/EN,
açık/koyu tema, düzgün proje dropdown'u, Bağlantı Türü alanının önce gelmesini
ve tutarlı etiket yazımını istedi. Bağlantı adlarında orta nokta yerine tire
sunulur. TM Forum uygulanabilirliği resmi kaynaklarla belgelenir, tanımlanmamış
kurumsal sertifikasyon iddia edilmez. Mevcut motor, frozen kayıtlar ve SQL
korunur. Yeni canlı Oracle/Jenkins/SMTP/push bu UI aşamasında yapılmaz.
Plan docs/superpowers/plans/2026-10-24-ui-preferences.md.

## 25 Ekim 2026 - onaylı proje çalışma alanı ve giriş düzeni

Uygulama adı Şema Karşılaştırma, kısaltma kullanılmaz. Kullanıcı tek başlık,
tam genişlik, bütünleşik sidebar, ortalı copyright, profil akışının üstte tek
bölümü, belirgin Şema Eşleştirmeleri ve gerçek çalışma özetlerini onayladı.
Kullanıcı adı mkaracan, görünen ad Mehmet KARACAN ve parola girişi istenir.
En önemli sınır: bütün bağlantı/eşleştirme/profil/ayar/iş/sonuç seçili projeye
aittir, başka projeye taşınmaz veya karışmaz. Sistem kimliği ve görünüm
tercihleri ortak kalır. İlk parola kullanıcı tarafından yerelde belirlenir.
Plan 2026-10-25-project-workspace.md. Yeni Oracle/Jenkins/SMTP/push yok.

## 25 Ekim 2026 - ikinci proje kabulü ve hedef seçimi

Kullanıcı ikinci bir proje oluşturularak bağlantı/eşleştirme/ayar/çalışma ayrılığını
kontrol etmemizi istedi. Yalnız açık TEST tanımları, gerçek bağlantı veya yeni
karşılaştırma çalıştırmadan yerel UI/API kontrolü. Alt bilgi şirket adıyla biter,
sekme grubu soldadır, kart kenarlıkları yumuşar, hedef bağlantıları dropdown ile
1→N seçilir. Kayıtlı eski eşleştirme kapsamı ve SKY kayıtları değiştirilmez.

## 25 Ekim 2026 - çoklu hedef kabulünün tamamlanması

Kullanıcı farklı şema çiftleriyle çoklu hedef kaydetme/yeniden açmayı, hedefi
kaldırıp tekrar eklerken eski çiftlerin dönmemesini ve proje ayrımını doğrulamayı
istedi. Yerel kontrol projesi/sentetik tanımlar, UI ve API testleri kapsamdır.
Yeni Oracle/Git erişimi, karşılaştırma koşusu, Jenkins/SMTP/push yoktur.

## 25 Ekim 2026 - kurumsal transparan logo ve favicon

Kullanıcı resmî kurumsal kimlik kaynağından transparan İnnova logosu ve tarayıcı
sekmesine A simgesi istedi. Tema başına resmî sürüm kullanılır, beyaz zemin
kaldırılır. Bu frontend sunum değişikliğidir. Rapor/SQL/karşılaştırma verisi,
Oracle/Jenkins/SMTP ve dış yayın kapsam dışıdır.


25 Ekim kullanıcı çalışma ekranı kapsamı: kompakt özet ve toplam süre kartı,
kaydırarak nesne yükleme, okunabilir nötr kaynak/hedef paneli ve ortak SQL
izleyici. Kullanıcının açık ek kararıyla yerel çalıştırılan işin SQL'i özel yerel
run klasöründe saklanabilir. Jenkins işi Jenkins arşivinde kalır. Çalıştırma Yeri
Jenkins varsayılandır, Bu Bilgisayar açık seçimdir. Sessiz fallback yoktur.
Motor/SQL kararları, UNKNOWN ve proje sınırı korunur. Yeni canlı Oracle,
Jenkins koşusu/job değişikliği, SMTP ve dış Git push bu tur yapılmaz.
Plan docs/superpowers/plans/2026-10-25-results-redesign.md, ADR-026.


25 Ekim sonraki kullanıcı onayı: nesne → fark özeti → gruplanmış ayrıntı → ilgili
SQL akışı uygulanır. Kolon/kısıt/indeks alanları tam gruplar halinde sunulur,
fark türü filtresi DDL kararından ayrılır. Kaynak/hedef bağlantı ve şema görünür.
İki özgün yerel DDL varsa satır karşılaştırması yapılır. Eksik/UNKNOWN/uzak
Jenkins tanımı uydurulmaz, SQL kuralları değiştirilmez. Plan:
docs/superpowers/plans/2026-10-25-structured-results.md. Canlı Oracle, Jenkins
koşusu/job değişimi, SMTP ve Git push yoktur.
