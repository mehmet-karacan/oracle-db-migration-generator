# Şema Karşılaştırma performans ölçümü

Author: Mehmet KARACAN
Date: 2026-11-06

Amaç tam kaynak ve hedef karşılaştırmasını beş dakika içinde tamamlamak.
Nesne kapsamı, farklar, DDL metinleri ve zaman aşımı bütçeleri korunur.
Bu belge çevrimdışı ölçümleri kaydeder. Canlı toplam süre henüz ölçülmedi.

## Ölçülen sonuçlar

8.867 nesneli kayıtlı kaynak, hedef kimliği verilmiş kopyasıyla karşılaştırıldı.
Bu deney gerçek üretim hedefi karşılaştırması değildir.

| Aşama | Önce | Sonra |
| --- | --- | --- |
| Karşılaştırma | 26,32 sn | 20,97 sn |
| Planlama | 11,03 sn | 0,47 sn |
| İki aşamanın toplamı | 37,35 sn | 21,44 sn |

Fark ve tam plan hash değerleri aynı kaldı. Ham DDL bulunmayan bu büyük
kayıttan SQL eşitliği sonucu çıkarılmadı. CREATE TABLE ve ADD COLUMN
SQL byte eşitliği ayrı gerçek parser testinde doğrulandı.
Ölçüm dosyası `.local/comparison-performance-20261106.json`.

40 tablo ve tablo başına 50 kolon içeren kaynakta soğuk çözümleme
2,2560 saniyeden 1,9274 saniyeye indi. Sıcak önbellekte aynı küçük örnek
0,5125 saniyeden 0,6813 saniyeye çıktı. Süreç yönetimi küçük ve sıcak
girdide ek maliyet yaratabiliyor. Dört koşunun kaynak özeti aynı.
Ölçüm dosyası `.local/parallel-source-benchmark.json`.

1.703 dosyalı kayıtlı paketin doğrulaması profilsiz 2,26 saniye sürdü.
Jenkins akışındaki fazladan doğrulama kaldırıldı. Paket yazımında ve genel
rapor öncesinde bütünlük doğrulaması devam ediyor. Bozulmuş dosya son
doğrulamada reddediliyor.

## Uygulanan değişiklikler

- Değişmez snapshot özeti aynı nesne için bir kez hesaplanır.
- Kısa SQL parçalarının kanonik sonucu en fazla 4.096 kayıtla saklanır.
  2.048 karakterden uzun metinler bu önbelleğe girmez.
- Bağımsız kaynak dosyaları ayrı parser süreçlerinde çözümlenir.
  Sonuçlar girdi sırasında birleştirilir. ContextVar ayarları taşınır.
- Oracle DDL okuması aynı ana iş parçacığında ve aynı salt okunur oturumda
  sürerken alınan metinler parser havuzunda çözümlenir. Kanıt sırası ve
  toplama öncesi ve sonrası envanter kontrolü korunur. Receipt içindeki
  grammar_projection artık worker sürelerinin toplamıdır. Örtüşen
  süreler toplanarak toplam geçen süre hesaplanmaz. Bunun için total kullanılır.
- `GENERATOR_PARSER_WORKERS` varsayılan 4, izin verilen aralık 1 ile 8.
  1 seri referans çalıştırmasıdır. Bekleyen işler süreç sayısının iki
  katıyla sınırlıdır. Parser zaman aşımı kuyruğa girişte başlamaz.
- Hedef çalışma ölçümü observations altındaki performance.json içinde
  capture, kayıt yazımı, kapsam, karşılaştırma, planlama ve paket sürelerini tutar.
  Ölçüm plan kimliğini ve SQL dosyalarını değiştirmez.

## Kabul sınırı

Beş dakika hedefi henüz doğrulanmadı. Tarihsel kayıtlardaki beş adet
240 saniyelik parser zaman aşımı dört süreçte iki dalga gerektirebilir.
Sadece paralellik bu durumda hedefi sağlamaz. Yeni sürüm parser önbelleği
kimliğini değiştirir. İlk çalışma soğuk önbellekle ayrıca ölçülmelidir.

Yeni canlı ölçümde kaynak hazırlığı, hedef receipt içindeki
phase_timings_seconds ve observations altındaki performance.json birlikte
incelenmelidir. Ağ, Git erişimi ve Oracle metadata süresi toplam ölçüme
dahildir. Zaman aşımını azaltmak veya nesne atlamak hızlandırma sayılmaz.
