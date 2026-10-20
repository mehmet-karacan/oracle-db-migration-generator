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
