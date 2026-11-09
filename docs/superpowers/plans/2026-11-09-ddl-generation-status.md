# Schema Compare DDL Üretim Sonucu

Author: Mehmet KARACAN
Date: 2026-11-09

DDL dosyaları eksiksiz ve arşiv bütünlüğü doğrulanmışsa Jenkins SUCCESS verir.
Metadata kapsamı ve bağımlılık uyarıları ayrı görünür. Plan kararları, SQL
dosyaları ve karşılaştırmanın kısmi kapsamı değiştirilmez. Hedef okuması
başarısızsa veya arşiv bozuksa başarı verilmez. Eksik DDL UNSTABLE kalır.

- [x] Üretim, eksik dosya, başarısız hedef ve bozuk SQL testlerini kırmızı çalıştır
- [x] Sonuç kaydı ve ayrı uyarı sunumunu uygula ve doğrula
- [x] Kurulu paket dosyalarını sınırlı değişiklikle yenile ve test et
- [x] 112 arşivini değiştirmeden yeni sonuç oluştur ve SQL eşitliğini doğrula
- [x] Jenkins SUCCESS sonucunu ve yalnız Mehmet KARACAN mailini doğrula

Oracle bağlantısı ve SQL uygulaması yapılmaz. Ekip gönderimi kapalı kalır.

113 kurulum doğrulaması ve 114 DDL sonucu SUCCESS. 2120 DDL, eksik 0.
2416 SQL dosyası kaynak arşivi ve kontrol dosyaları dahil aynı kaldı.
2 metadata belirsizliği, 106 bağımlılık ve 231 diğer işlem uyarısı korunur.
Karşılaştırma kaydı PARTIAL kalır. Üretim kaydı SUCCESS ve exit_code 0 olur.
83 kurulu paket testi geçti. Tam test 1425 PASS, önceki pakette de görülen
1 Git publication hatası. Yeni canlı Oracle kabulü NOT_RUN.
