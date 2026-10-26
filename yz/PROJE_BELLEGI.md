# Proje Belleği

Kullanıcı Mehmet KARACAN. Amaç üç otomasyon ürününü tamamlamaktır: DDL'yi Git'e taşıyan, değişikliği yorumlayan, target farkından DDL üreten. Manuel SQL/changeset hazırlama akışı istenmiyor. Yeni Generator ve Artifacts depoları kullanıcı tarafından oluşturuldu. Artifacts görünürlüğü kullanıcı tarafından private yapıldığı belirtildi, bu hazırlıkta tekrar teyit edilmedi.

Source kurumsal SKY DDL Git deposudur, tam adres ve yerel iki referans dizini `.local/session-context.json` dosyasındadır. Kullanıcının henüz target bağlantı listesi yok, Jenkins managed tanımlarıyla dinamik yükleme istenir. Source 1, target N.

Mimari kararları ve görev kapsamı proje belgelerinde tanımlıdır. Uygulama bu kapsam üzerinden ilerler. Ayrı mimari araştırma aşaması açılmaz. Görev dosyası adı her zaman AKTIF_GOREV.md.

HTML mevcut standartla aynı olacak. Uzun DDL'ler HTML'e doldurulmayacak, ilk önemli birkaç değişiklik önizlenip tam SQL/JSON Git/Jenkins'te saklanacak. Artifact repo, başka bir modelin bağımsız okuyup neden-ne-hedef-risk sorularını kanıtla yanıtlayabileceği README/AGENTS/manifest/plan düzeni taşıyacak.

Mevcut projeler ve kullanıcı dosyaları korunacak. Bu pakette ürün kodu geliştirildiği veya canlı sistemde doğrulandığı iddia edilmiyor. Bilinmeyen çevresel bilgiler uydurulmaz, kodun güvenli offline doğrulaması ile canlı kabul ayrılır.
