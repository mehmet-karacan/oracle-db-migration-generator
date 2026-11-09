# Schema Compare Hedef Okuma Tutarlılığı

Author: Mehmet KARACAN
Date: 2026-11-09

Amaç, hedef okumasını engelleyen koşulu tanılamak ve gerçek karşılaştırmayı
tamamlamaktır. Mail yalnız mkaracan@innova.com.tr adresine gider. SKY ekibi
onay verilene kadar alıcı değildir. Oracle DDL veya DML uygulanmaz.

Canlı kısa tanı 5336 satır ve 26 tekrar eden tür ile ad anahtarı gösterdi.
Altı kısa okumada gerçek fark veya sıra farkı görülmedi. Bunun 97 hatasının
kesin nedeni olduğu iddia edilmez. Satır sırası kontrolündeki program hatası
sentetik testte yeniden üretildi. Gerçek içerik değişimi ve tekrar sayısı
kontrolü korunur. Hata halinde değişen nesne örnekleri kaydedilir.

- [x] Canlı kısa envanter tanısı ve sabit sorgu sınırını doğrula.
- [x] Sıra değişimi, tekrar sayısı ve gerçek tarih değişimi testlerini kırmızı çalıştır.
- [x] inventory_consistency.py ve collector tanı kaydını uygula.
- [x] Kurulu motor sürümüyle 99 testin geçtiğini doğrula.
- [x] Örnek sayısı sınırı testini ve 214 rapor testini çalıştır.
- [x] Yalnız collector tutarlılık düzeltmesi içeren paketi kur.
- [x] Kaynak SHA aynıysa 97 hazırlığını sabit SHA256 ile tekrar doğrulayarak kullan.
- [x] Canlı hedefi yeniden topla ve DDL üreten karşılaştırmayı tamamla.
- [x] Genel DDL, nesne dosyaları ve mailin tek bağlantısını kontrol et.
- [x] Maili yalnız kullanıcıya gönder ve devir kaydını tamamla.

Önceki performans değişiklikleri bu pakete karıştırılmaz. Kaynak yeniden
kullanımında SHA veya ham dosya uyuşmazlığı kabul edilmez. Tutarlılık
kontrolü kapatılmaz. Gerçek değişim sürerse yeni nesne örnekleriyle devam
edilir. Commit, push ve yeni branch yoktur.

Canlı 105 sonucu hedef CAPTURED ve tek denemedir. 5336 satır sabit kaldı.
Gerçek plan üretildi. 11895 fark ve 1882 DDL işlemi raporlandı. 238 kayıtta
DDL eksik, 2 kayıt doğrulanamadı. Bu yüzden sonuç PARTIAL ve Jenkins
UNSTABLE. Bütün DDL üretildi iddiası yoktur. Süre 18 dakika 29 saniye.
Mail gönderimi yalnız kullanıcıya tamamlandı. Ekip onayı bekler.
97 sabah hatasının kesin nedeni bu çalışmayla kanıtlanmadı. Sıra eşitliği
hatası sentetik testle doğrulanıp düzeltildi. 105 okumalarında sıra da aynıydı.
