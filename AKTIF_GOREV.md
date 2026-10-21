# AKTIF_GOREV — Jenkins Kurulumu

Görev: ODMG-JENKINS-001. Kullanıcı Jenkins’e girip Generator işini oluşturmayı açıkça istedi.

Kapsam: sky/oracle-db-migration-generator Pipeline; yalnız INNOVA_ODI. Mevcut DDL Sync, Analyzer ve source depoları değişmez. Source/target daima salt okunur. Test edilmiş release, workspace Python 3.12, mevcut Jenkins Credentials, sonuç arşivi. Otomatik tetikleme, Git push ve Oracle DDL/DML yok. Kullanıcının son talimatıyla Jenkins bildirimi yalnız mkaracan@innova.com.tr adresine gider; başka alıcı/CC/BCC yok.

Plan: docs/superpowers/plans/2026-10-20-jenkins-setup.md. Önceki rapor görevi output/jenkins-setup/previous-AKTIF_GOREV.md altında korunur.

Durum: ODMG-JENKINS-001 tamamlandı. #4 ortam kontrolü SUCCESS; #6 tam salt okunur karşılaştırma raporlandı (UNSTABLE, 5 gerçek koşul; UNKNOWN0). Genel HTML gövde maili yalnız izinli alıcıya gönderildi. Son kanıt yz/DEVIR.md başlığı ve output/jenkins-setup/live-verification.json.

20 Ekim kullanıcı rapor düzeltmesi: genel maildeki nesne başına `işlem / hedef`
satırı kaldırılır. Bağımlılık gerekçesi gerçek şema/nesne/tür ve eksik koşulu
belirtir; doğrulanamayan durum yokluk olarak sunulmaz. Karar ve SQL gövdeleri
değişmez. #6'nın doğrulanmış kayıtlarından yeni rapor üretilir; yeni Oracle
bağlantısı açılmaz. Tamamlandı: 341 test geçti; Jenkins #7 UNSTABLE olarak
raporlandı. 559 SQL gövdesi aynı, yeni Oracle bağlantısı 0. Somut gerekçeler
gerçek mail/plan üzerinde doğrulandı; mail yalnız izinli alıcıya gönderildi.
Normal karşılaştırma akışı v3 ile geri yüklendi. Kanıt: output/report-reasons/.

20 Ekim sonraki kullanıcı talimatları:

- Genel mailde Nesne / Fark sütunu genişler; Hedef/İşlem/Sonuç daralır.
  Onaylı logo byte'ları korunur; mail istemcileri için ölçüsü açık tanımlanır.
- Her gün Europe/Istanbul 08:40; raporun 09:00 mesai öncesinde gelmesi hedeflenir.
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
  GRANT kayıtları politika ile kapsam dışında tutulur; gerçek iş nesnelerindeki
  her `$` karakteri dışlama nedeni değildir. Ham envanter ve kanıt korunur.
- Genel raporda gerçek başlangıç/bitiş zamanından çalışma süresi gösterilir.
  Önemli nesneler mevcut karar önceliğiyle sıralanıp ilk 5 ile sınırlandırılır.
- İki şemanın canlı kontrolü Jenkins #12'de sürmektedir. Offline doğrulama
  414 test geçti. Son kod normal push ile private Generator deposunda:
  f4560bdcb158a7fe727febe064e04b8ad66baa65.
- Jenkins agent GitHub HTTPS bağlantısı ConnectionResetError ile kesiliyor.
  Bu durum yalnız otomatik artifact yayınını etkiler; karşılaştırmayı durdurmaz.
  Bu önceki yayın planı aşağıdaki son kullanıcı kararıyla iptal edilmiştir.

20 Ekim son kullanıcı saklama kararı:

- Üretilen DDL, JSON ve HTML şimdilik yalnız Jenkins build artifact arşivinde
  tutulur. Artifact Git deposuna push yetkisi geri alınmıştır; yerel yayın da
  yapılmaz. Generator uygulama kodu için önceki private Git push yetkisi sürer.
- Canlı job ve Pipeline şablonundan artifact publication aşaması ve ilgili
  credential binding kaldırıldı. Mail doğrudan ilgili Jenkins raporunu açar.
  Mevcut 20 build/artifact saklama sınırı korunur; saat Europe/Istanbul 08:40.
- #12 kaynak hazırlığını tamamladı fakat PARTIAL kaydın çıkış kodu 10 runner
  tarafından hatalı fatal sayıldığı için hedef karşılaştırmasına ulaşmadı.
  Bu hata giderilir; kaynak belirsizliği başarı/tamlık gibi sunulmaz. Tek seferlik
  devam ancak önceki snapshot'ın dışarıdan sabit SHA-256'sı, ham dosyalar ve
  güncel sabit Git SHA'sı doğrulanarak yapılır. Oracle her zaman salt okunurdur.

20 Ekim son kullanıcı takvim kararı: günlük başlangıç Europe/Istanbul 08:00.
Bu, önceki 08:40 saatini değiştirir. Hem canlı cron hem declarative Pipeline
trigger ve iş açıklaması 08:00 olarak kaydedilip yeniden okunarak doğrulandı.
Bu takvim değişikliği yeni karşılaştırma veya mail tetiklemez; SQL uygulanmaz.

20 Ekim TTBP kullanıcı görevi: ORA-04088 nedenini salt okunur incele ve TTBP
fark/DDL raporunu üretip yalnız Jenkins'te sakla. Canlı #15 tanısı hedef TTBP
CONNECT aşamasında SYS.BLOCK_TOOLS_TTBP / ORA-20983 reddini gösterdi. Trigger,
kimlik, parola veya yetkiler değiştirilmez. #16 mevcut INNOVA_ODI hesabının
etkin SELECT_CATALOG_ROLE ve SELECT_TTBP yetkilerini, TTBP GET_DDL erişimini
kanıtladı. Bu mevcut yetkiyle açık metadata_reader yapılandırması uygulanır;
session identity + katalog rolü + hedef owner varlığı/DBA envanter erişimi
doğrulanır. Varsayılan kendi-owner erişimi ve source/target yönü değişmez.
ALL_OBJECTS görünürlüğü tamlık kanıtı sayılmaz; seçili şemaya bindli kapalı
DBA metadata sorguları kullanılır. 08:00, tek mail alıcısı ve Jenkins-only
arşiv politikası korunur. Hiçbir üretilen SQL Oracle'da çalıştırılmaz.

20 Ekim son kullanıcı kapsamı: günlük varsayılan yalnız PROD ortamındaki TTBP.
INNOVA_ODI karşılaştırması yalnız kullanıcı isterse manuel seçilir. Mevcut ODI
katalog hesabı TTBP okuma kimliği olarak kalabilir; ODI şeması karşılaştırılmaz.
Kaynak profil/metadata/hedef listesi aynı seçime daralır. Gerçek hash adlı teknik
nesneler ve bunların child kayıtları kaynak/targetta filtrelenir; COMMENT/GRANT
kayıtlarının sentetik S_hash kimliği kullanıcı nesne adı diye gösterilmez,
kanıtlı gerçek tablo/kolon adı gösterilir. Hedef görünen adı PROD olur, şema TTBP
ayrı gösterilir. İç target_id/path/kimlik/DDL semantiği korunur. Tüm değişiklikler
salt okunur sınırı, 08:00 ve Jenkins-only arşiv politikasını korur.

20 Ekim son kullanıcı inceleme görevi: PROD / TTBP planındaki 2.355 BLOCKED
işlemin tamamını operasyon kimliği ve kanıtıyla tek tek incele. Gerçek üretim
engeli olmayanları gerekçeli INFORMATIONAL/uyarıya ayır; kod hatalarını kırmızı
testten başlayarak düzelt. UNKNOWN alanları var/yok veya tam karşılaştırma diye
sunma. Yeni rapor ve DDL yalnız Jenkins arşivinde; varsayılan TTBP, 08:00 ve tek
mail alıcısı korunur. Source/target daima READ ONLY; DDL/DML/COMPILE yok.

20 Ekim 2.355 engel incelemesi tamamlandı: 2.355/2.355 tekil kanıtlı eşleme;
726 test geçti. Güncel plan 1.265 READY SQL /632 REVIEW /251 BLOCKED. #28 rapor,
DDL ve inceleme CSV/JSON yalnız Jenkins arşivinde; yeni Oracle bağlantısı0,
SQL NOT_EXECUTED. Normal v13 PROD/TTBP ve 08:00 geri yüklendi. Ayrıntı yz/DEVIR.md.

21 Ekim kullanıcı sunum düzeltmesi: genel mail ve raporlardaki BLOCKED,
[TABLE], COMMENT gibi teknik etiketleri anlaşılır Türkçe karşılıklarıyla göster.
Üretilemeyen DDL varsa sayısını koru ve durumun altında kısa, somut neden yaz.
Tekrarlanan bağlı nesne gerekçelerini birleştir. Kanıtlı engelleri gizleme;
karşılaştırma kararını, UNKNOWN bilgisini veya SQL'i sunum için değiştirme.
Mevcut TTBP arşivi yeni görünümle Oracle bağlantısız yenilenebilir. Önceki
Jenkins, yalnız tek alıcı mail, 08:00 ve Jenkins-only arşiv yetkileri korunur.

21 Ekim ek kullanıcı düzeltmesi: karşılaştırma süresini ana özette dakika/saniye
olarak göster; görünüm yenileme süresiyle karıştırma. Karşılaştırmanın özgün
başlangıç/bitiş zamanını yenilenen raporlarda da koru. Fark kartı doğrulanmış
bulunan farkların sayısını göstersin; UNKNOWN karşılaştırma kayıtlarını ayrıca
say ve eksik kapsamın ek farklar doğurabileceğini açıkla. Kanonik null toplamı
değiştirme; UNKNOWN'u kesin fark veya eşitlik diye gösterme.
