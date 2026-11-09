# Jenkins Ayrıntılı Rapor ve Tek Mail Bağlantısı

Author: Mehmet KARACAN
Date: 2026-11-09

**Goal:** Kullanıcının onayladığı ayrıntılı raporu Jenkins'e almak ve mailde bir arşiv bağlantısı bırakmak.

**Architecture:** Kurulu doğrulanmış release temel alınır. Yalnız reporting dosyaları ve wheel kayıtları yenilenir. Normal işte alıcı, konu, saat, kapsam ve motor aynı kalır. Kurulum ENVIRONMENT_CHECK ile, kabul kayıtlı sonuçla yapılır.

**Tech Stack:** Python, Jinja2, Jenkins Pipeline ve tarayıcı eklentisi.

## Sınırlar

- Alıcı yalnız mkaracan@innova.com.tr. CC, BCC ve recipient provider yok.
- Konu SKY | Şema Karşılaştırma | DURUM | Build #N biçimindedir.
- Saat Europe/Istanbul 08.00 ve varsayılan kapsam TTBP korunur.
- Yeni Oracle karşılaştırması ve mail gönderimi yok.
- Kaynak, plan, SQL, motor, bağlantı ayarları ve özgün logo aynı kalır.
- Kaydedilen eski çalışma arşivleri değiştirilmez.

## Adımlar

- [x] Canlı normal işi ve sohbetin önceki mail kararlarını oku.
- [x] İlk ayrıntılı rapor paketini hazırla, izole wheel ile 190 rapor ve arşiv testi çalıştır.
- [x] İlk paketi tarayıcı eklentisiyle yükle. Jenkins 92 ENVIRONMENT_CHECK SUCCESS.
- [x] Tek ve çok hedef için tekrar eden mail bağlantılarını kırmızı testle göster.
- [x] Mailde tek Raporu ve DDL Dosyalarını Aç bağlantısı bırak, yerel testleri çalıştır.
- [x] Son paketi üret, izole kurulu dosyalarla test et ve aynı normal işe yükle.
- [x] Kayıtlı 91 numaralı sonuçla yeni kurulu HTML üretimini, bütünlük ve tek mail bağlantısını sunucuda doğrula.
- [x] Normal Pipeline tanımını tekrar oku, dağıtım kanıtını ve devir kayıtlarını güncelle.

## Güncel Kanıt

İlk paket 65aaf22763f7578876b3f1912ffb54a47b936c21954403c02437acac411668ca.
Mailin tek bağlantı değişikliği kullanıcı tarafından bu kurulum sırasında istendi.
Son paketin kimliği ve kabul sonucu tamamlandığında eklenir.

Son paket a6496ce80c9f7dc60ca337f9d407d63453827960360fe3566410349cab1d36d8.
İzole testler 206 PASS. 93 kurulum ve 94 arşivle kabul SUCCESS.
Mailde tek bağlantı tarayıcı DOM kaydıyla da görüldü. Yeni mail gönderilmedi.
Devir kayıtları güncellendi. Mobil kabul NOT_RUN. Ana raporun Tarama Kapsamı
başlığı hizası ayrıca incelenmeli, bütün görünüm için PASS iddiası yok.
