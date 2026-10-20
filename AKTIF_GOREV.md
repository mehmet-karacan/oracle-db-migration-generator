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
