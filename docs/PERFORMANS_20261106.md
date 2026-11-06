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

## Jenkins dağıtımı ve yerel teşhis

e390fbabca77849f602b11e8c0882c42eda3cb3f ana dala gönderildi.
Jenkins ortam kontrolü 78 başarılı oldu. Yeni paketin kurulduğu doğrulandı.
79 numaralı karşılaştırma kaynak hazırlığında uzadı. Kullanıcının yerelde
inceleme talebi üzerine iptal edildi. Durum ABORTED. Sonuç karşılaştırması
tamamlanmış sayılmaz. İptal bildirimi yalnız mkaracan@innova.com.tr alıcısına gitti.

Yerel teşhis aynı 442089852f615d0304debbb2b61fbafe2719f8f3 kaynak sürümünü
ve 5.687 dosyalı TTBP kapsamını kullandı. İlk 88 saniyelik kayıtta dört
çözümleyicinin toplam doluluğu yaklaşık yüzde 59 oldu. Sıradaki uzun işin
sonucu beklenirken boş çalışanlara yeni dosya gönderilmiyordu. MANIFEST ve
DEPENDENCIES dosyaları da sınırlı kuyruğun yerini tüketiyordu.

Kaynak çözümlemesi artık tamamlanan işler geldikçe kuyruğu yeniliyor.
Sonuçlar dosya yoluyla saklanıp özgün sırada birleştiriliyor. JSON yardımcı
dosyaları parser havuzuna girmiyor. Oracle toplama yolu varsayılan sıralı
çalışmayı koruyor. Sonuç sırası, kanıtlar ve SQL biçimi değişmiyor.

BASEUTILS gövdesi 30 saniyelik, PCK_DUMMY gövdesi 240 saniyelik çözümleme
sınırına ulaştı. PL/SQL grammar ölçümü maliyetin ifade tahmini içinde
olduğunu gösterdi. Beş gerçek dosyada SLL önceliği aynı parser yanıtını
verdi ancak tutarlı hızlanma sağlamadı. Dar bir argüman kontrolü BASEUTILS
CPU süresini yalnız yüzde 4,2 azalttı. Bu iki deney ürüne alınmadı.

Yeni tam test sonucu 1.279 PASS, 267,39 saniye. Kaynak çıktısının seri ve
paralel kanonik byte eşitliği ve uzun ilk görev sırasında kuyruğun ilerlemesi
ayrı testlerle doğrulandı. Kanıt .local/local-diagnostic-tests.xml.

Yerel UI üzerinden TTBP Yerel Performans çalışması başlatıldı.
Kayıt a1b9a9c08bd1435aa3bed5457bbcd2eb. Kullanıcı test ortamı olduğunu
belirtti. Bağlantı adı PROD içerse de ortamın niteliği bu adla çıkarılmadı.
Kaynak sürümü sabitlendi. Yerel UI akışı Jenkins'in ek kaynak metadata
zenginleştirmesini çalıştırmadığı için iki akışın sonuç eşitliği varsayılmaz.
Bu kayıt canlı süre ve hata teşhisi içindir. SQL uygulanmaz.

## Paket önceliği ve yerel depo ölçümü

Kullanıcı uzun çalışmanın tamamlanmasını beklemek yerine önce hız sorununun
giderilmesini istedi. a1b9a9c08bd1435aa3bed5457bbcd2eb durduruldu ve
USER_STOPPED_FOR_PERFORMANCE kaydedildi. Tam Oracle karşılaştırması tamamlanmadı.
Yeni kaynak C:/innova/projeler/sky-db olarak seçildi. Kaynak depo değiştirilmedi.
Ölçüm 881ad00a06474bc737e022f2185bc9fce7307c6b commit'ini okudu.
Çalışma ağacındaki dokuz değişmiş SQL dosyası bu commit ölçümüne dahil edilmedi.

Normal SQL dosyaları artık küçükten büyüğe çözülüyor. Paketler sona alındı.
Paket grubunda büyük gövdeler önce başlatılıyor. Amaç son büyük dosyanın
bütün kısa işlerden sonra tek başına kalmasını önlemek. Sonuçların birleşimi
özgün dosya sırasında kaldı. Kaynak ilerleme birimi dosya, Oracle ilerleme
birimi nesne olarak Türkçe ve İngilizce test edildi.

Sekiz parser ile yerel ölçümde 4.788 paket dışı SQL dosyası 159,096 saniyede
tamamlandı. JSON yardımcı dosyaları dahil ilerleme yaklaşık 5.500 oldu.
Bu sayı nesne sayısı değildir. Toplam kaynak 5.690 dosyadır. Paket aşamasında
yedi kayıt zaman aşımına ulaştı. Bir parser süreci kapatılırken beş saniyelik
process.wait sınırı aşıldı ve TimeoutExpired bütün hazırlığı durdurdu.
Ölçüm tam kaynak sonucu veya canlı kabul sayılmaz. Kanıt
.local/local-source-packages-last-console.log ve aynı adlı klasörde files.jsonl.

BASEUTILS dosya ölçümünde ilk çözümleme 25,14 saniye, grammar aşaması
24,66 saniye sürdü. Aynı parser sürecinde tekrar 6,12 saniye, grammar
5,94 saniye oldu. Paket projection işlemi yaklaşık 0,05 saniyedir.
Yavaşlık fark motorundan önceki PL/SQL grammar aşamasındadır.

Kaynaklar için içerik özeti ve doğrulanmış önbellek yaklaşımı sürdürülür.
Git diff iki metin arasındaki farkı gösterebilir, hedefin güncel envanteri ve
kolon değişiminden DDL çıkarma işinin yerini almaz. Referanslar
[Git diff](https://git-scm.com/docs/git-diff) ve
[ANTLR PL/SQL grammar](https://github.com/antlr/grammars-v4/blob/master/sql/plsql/README.md).
Paket gövdelerinin metin karşılaştırmasını ayrıntılı grammar analizinden
ayırmak daha kapsamlı bir adaydır. Henüz uygulanmadı ve çıktı eşitliği
doğrulanmış sayılmaz. Beş dakika toplam hedefi sağlanmadı.

Parser kapanışında ilk beş saniyelik bekleme aşılırsa tek ek öldürme ve
on saniyelik bekleme uygulanır. Kalıcı hata başarı sayılmaz. Bir slot
kapanamazsa diğer slotların temizliği yine denenir. Çözümleme bütçeleri
değişmedi. Parser, lifecycle, kaynak ve cache grubu 52 PASS, 60,03 saniye.
RunDetail ilerleme birimi grubu 9 PASS. UI build PASS. Bu düzeltmeden sonra
yeni tam kaynak veya canlı Oracle karşılaştırması başlatılmadı.
