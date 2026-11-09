# Schema Compare Kaynak Önbelleği Yenileme

Author: Mehmet KARACAN
Date: 2026-11-09

117 tanısı dört eski hazırlama sürümü kaydı ve dört kayıt sınırı buldu.
Güncel girdinin kaydı yoktu. Snapshot bağlamı ve Git byte kontrolü geçerliydi.
Kayıtlar toplam yaklaşık 320 MB, byte sınırı 1 GB. Gerçek engel kayıt sayısıdır.

- [x] Gerçek Jenkins dizininde kayıt engelini salt okunur doğrula
- [x] Dolu önbellek, bozuk kayıt, boyut ve LRU testlerini kırmızı çalıştır
- [x] Yalnız doğrulanmış uygulama kayıtlarını kilit altında sınırla yenile
- [x] Okuma ve kayıt nedenlerini performans kaydına ekle
- [x] Tam testleri ve kurulacak paketi doğrula
- [x] 116 girdileriyle kayıt ve HIT durumunu parser veya Oracle çağırmadan doğrula
- [x] Aynı kayıtlı kaynak ve hedefle tüm DDL byte değerlerini karşılaştır
- [x] Güncel sürümle yeni canlı testi çalıştır ve toplam süreyi ölç
- [x] Maili yalnız Mehmet KARACAN'a gönder ve sabahki SKY ayarını koru

Kaynak depo, 116 arşivi ve canlı veri değiştirilmez. Yeni kayıt doğrulanmadan
eski kayıt kaldırılmaz. Bozuk veya uygulamaya ait olduğu kanıtlanamayan
dosyalar silinmez. SOURCE PARTIAL durumu ve UNKNOWN alanlar aynen korunur.
Parser timeout yanıtlarının önbelleğe alınmama kuralı değiştirilmez.

1434 tam test ve 65 kurulu paket testi geçti. 118 kurulum, 119 önbellek
ve DDL kabulü, 120 canlı koşu SUCCESS. 119 bir doğrulanmış eski kaydı
yeniledi. Yeni SOURCE kaydı saklandı. 120 HIT_VERIFIED ve kaynak 21.302 sn.
116 ile snapshot hash'i aynı, 2416 SQL dosyası plan başlığı dışında aynı.
Toplam 1689.821 sn yerine 634.126 sn. 5 dakika hedefi henüz karşılanmadı.
Canlı hedef toplaması 333.507 sn ile kalan en büyük aşamadır.
