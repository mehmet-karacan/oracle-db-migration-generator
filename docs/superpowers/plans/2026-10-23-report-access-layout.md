# Genel rapor erişimi ve görünüm düzeltmesi

Kullanıcı sırası: önce Genel DDL erişimi ve sayfa görünümü, sonra#42'nin
73dk44sn süresinin nedenlerini kayıtlı aşama/işlem kanıtlarıyla incelemek.
Yeni Oracle karşılaştırması, SQL uygulaması veya CSP gevşetmesi yoktur.

Tanı: #45 SQL dosyası vardır, Jenkins'in /*view*/ yolu metni açar. Artifact
HTML'sindeki doğrudan indirme tıklaması gezinme/indirme olayı üretmedi.
Jenkins varsayılan sandbox ve inline CSS kısıtlarıyla uyumludur. Harici CSS
çalışır, yeni kaynak kartının inline stilleri web'de uygulanmamaktadır.

- [x] Kırmızı test: Jenkins'e ait doğrulanmış build bağlamında ana düğme SQL
  View yoluna, dosya indirme bağlantısı Jenkins'in yerel dosya ekranına gider.
  Offline rapor kendi göreli SQL yolunu korur. SQL byte'ları değişmez.
- [x] Mail hazırlayıcının zaten doğruladığı job/build bağlamıyla genel web
  raporunu da üret, genel/teknik bağlantıları anlaşılır biçimde ayır.
- [x] Mevcut HTML ailesinde tek hedefe geniş kart, sade eylemler, kaynak
  bölümünde harici CSS, sayfa başlığı işi açıklar. Süre alt gri not kalır.
- [x] Test, sentetik CSP görünümü ve gerçek Jenkins tıklamasını doğrula,
  sabit planı yeni build'de yenile, yalnız yetkili alıcıya bildir.
- [x] Normal TTBP08:00 Pipeline'ını geri oku, ardından eski koşunun süre
  maliyetini incele, ölçülmeyen ayrıntı için sonuç uydurma.
