## 9 Kasım 2026 Kaynak Önbelleği Düzeltildi ve Canlı Tekrarlandı

Author: Mehmet KARACAN
Date: 2026-11-09

117 salt okunur tanısı gerçek engeli doğruladı. .runtime/prepared-source-cache
altında dört eski hazırlama sürümü kaydı vardı. Sınır dört kayıttı. Güncel
key 25393520b376aeff19fcaf75c20a5693f375394f99657addf614fdee50a4d964
yoktu. Girdi ve snapshot bağlamı geçerliydi. Eski kayıtlar yaklaşık 320 MB,
byte sınırı 1 GB idi. Engel kayıt sayısıydı. Eski kayıtların hazırlama
fingerprint'i güncel değerden farklıydı. Böylece okuma MISS, yazma false kaldı.

source/prepared_cache.py artık kilit altında en az kullanılan doğrulanmış
kaydı sınırlar içinde yeniler. Yeni kayıt tüm hash ve Git byte kontrollerinden
geçmeden eski kayıt silinmez. Kaynak deposu ve önceki çalışma arşivleri
silinmez. Kaydın kapalı manifesti, binding hash'i, tam dosya listesi ve dosya
hash'leri doğrulanır. Tanınmayan, bozuk ve reparse içeren kayıtlar korunur.
Kayıt sınırı 4 ve byte sınırı 1 GB olarak kalır. Son başarılı okumada yalnız
dizin zamanı güncellenir. İçerik hash'leri değişmez. Mevcut Git, profil,
Python, hazırlama sürümü ve snapshot kapsam doğrulamaları gevşetilmedi.

cli.py performans kaydına checkpoint_load_reason, checkpoint_store_reason
ve checkpoint_evicted_entries alanlarını ekler. HIT durumunda yazma
NOT_ATTEMPTED ve checkpoint_stored false normaldir. Kaynak mevcut doğrulanmış
kayıttan okunmuştur. Bu durum 116'daki MISS ve yazılamayan kayıtla karıştırılmaz.
Parser timeout yanıtlarını kaydetmeme ve canlı metadata'yı yeniden okuma
kuralları değişmedi. TARGET snapshot kaynak önbelleği yapılmadı.

Yeni testler önce kırmızı çalıştı. Tam test 1434 PASS, kurulu paketten 65
ilgili test PASS. Başarısız ve atlanan sıfır. LRU, dolu önbellek, bozuk ve
bilinmeyen kayıt, büyük yeni kayıt, kilit çakışması ve aynı byte değerlerini
koruyan HIT ölçüldü. Önceki testin kapasitede kayıt atmama beklentisi yeni
kullanıcı isteğine uygun doğrulanmış eski kayıt yenileme beklentisine çevrildi.
Diğer bozuk kayıt ve kaynak değişim kontrolleri aynen korundu.

118 paket kurulumu SUCCESS. Temel commit daf616f0ec215dcd8e76fdd42647227ff9336269.
Kaynak düzeltme hash'i 48379a2f045947e2ecf0dfeadf58e92e0ae6b80b7194d0764a348b19deff6a78.
Release 6ab8d9aaa24cc8cc6d43a43a7717be222454cba6710e6de0e3707ac56fa42236.
Wheel 595df48722132e8c7b79d93e2632625e4297f0d2554e025ad39682641e41751a.
Yalnız cli.py ve source/prepared_cache.py değişti. DDL motoru, parser,
bağımlılıklar ve rapor byte değerleri önceki 73f5a38 paketiyle aynı.
GENERATOR_CODE_PATCH_SHA ve source-revision.json iki dosyalık farkı açıkça
kaydeder. Paket saf daf616f commit'iymiş gibi sunulmaz. Yeni Git push yoktur.

119 kabulü Oracle'a bağlanmadan yapıldı. 116'nın orijinal kaynak snapshot'i
7fe9557329a627e4e8294b6b7d4f4166abf11685c06b3295d14503b749feee6d hash'iyle
sabitlendi. Git byte değerleri ve profil yeniden doğrulandı. Hazırlamanın
semantik bileşenleri değişmediği için açık kabul betiğiyle kayıt oluşturuldu.
Bu işlem eski sürüm kayıtlarını otomatik geçerli sayma değildir. Normal
okumada yeni hazırlama fingerprint'i zorunlu kalır. Bir doğrulanmış eski
kayıt yenilendi. Kayıt yazımı 39.758 sn, yükleme 12.693 sn. Ayrıştırıcı
çağrısı yasaklanarak CLI tekrarlandı ve HIT_VERIFIED ile 20.984 sn sürdü.
Snapshot canonical byte değerleri ve bütün raw_ddl byte değerleri aynı kaldı.
SOURCE PARTIAL ve UNKNOWN alanları değiştirilmedi.

119 aynı kayıtlı zenginleştirilmiş kaynak ve hedefle DDL'yi yeniden üretti.
İşlem kimlikleri, kararlar, bağımlılıklar, farklar ve sayılar aynıydı.
2416 SQL dosyası yalnız yazılım sürümüyle değişen plan kimliği yorum başlığı
hariç birebir aynı. DDL gövdeleri ve source-ddl arşivi değişmedi. Toplam
2120 DDL, eksik 0. Eski plan 644bd93c26f49ae347bc13688d2bd4edc86339569918aacacae3274da8262e0f,
yeni plan 128cffea7c01f0b50d706454ff8cc8d2aab1d8c17b977d522e38fa3a5a043327.

120 canlı test SUCCESS. Kaynak Git commit'i 0598ba1f689dcb1b3640ecd7b0169ba72600a7a7
olarak 116 ile aynı tutuldu. Hedef Oracle metadata'sı yeniden salt okunur
toplandı. Kaynak hazırlığı 864.685 sn yerine 21.302 sn, HIT_VERIFIED ve
parse 0. Snapshot hash'i 116 ile birebir aynı. Hedef toplaması 333.507 sn,
gözlemi yazma 32.538 sn, fark hesaplama 11.836 sn, plan 60.801 sn ve paket
üretimi 50.625 sn. Karşılaştırma 591.519719 sn, mailde 9 dk 52 sn.
Uçtan uca süre 634.126 sn, 10 dk 34 sn. 116 uçtan uca 1689.821 sn idi.
Kazanç 1055.695 sn, yaklaşık yüzde 62.47. 5 dakika hedefi henüz karşılanmadı.
Hedef toplaması 5 dk 34 sn ile kalan en büyük aşamadır. Sonraki performans
çalışması canlı hedefteki projeksiyon ve toplam okuma duvar süresini azaltmaktır.

Canlı sonuç 11895 fark, 3805 kaynak nesnesi, 2120 DDL ve eksik 0. Metadata
belirsizliği 2, bağımlılık uyarısı 108, diğer DDL uyarısı 229. Karşılaştırma
kapsamı PARTIAL, DDL üretimi SUCCESS. Canlı koşuların bütün SQL byte değerleri
ayrıca karşılaştırılmadı. Byte eşitliği kabulü aynı 116 girdileriyle 119'da
yapıldı. Bu iki doğrulama birbirinin yerine sunulmaz. SQL uygulanmadı.

120 maili yalnız mkaracan@innova.com.tr adresine gönderildi. Konu SKY |
Schema Compare | SUCCESS | Build #120. Koşu sonunda normal Pipeline birebir
okundu. Innova-SKY@innova.com.tr, günlük Europe/Istanbul 08.00 ve etkin iş
korunur. Normal iş master ref'ini kullanır. Yalnız performans testi sabit
kaynak SHA'sını kullandı. Kalıcı Pipeline iki dosyalık düzeltme paketine
sabitlendi. Yeni branch, commit veya dış Git push yapılmadı.

Offline kabul PASS, yeni canlı Oracle kabulü PASS, Jenkins kurulumu ve
koşusu PASS. Kanıt .local/cache-fix-20261109/completion-receipt.json,
diagnostic-117-console.txt, cache-acceptance.json, ddl-equality.json,
full-tests.xml, installed-tests.xml ve live-120-console-final.txt içindedir.

## 9 Kasım 2026 Güncel Sürümle Canlı Süre Testi

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcı güncel sürümle canlı karşılaştırma, toplam süre ve yalnız kişisel
mail istedi. 116 Canlı Süre Testi SUCCESS tamamlandı. Generator commit
daf616f0ec215dcd8e76fdd42647227ff9336269 ve kurulu 73f5a38 sürümü tekrar
343 ürün ve 7 yardımcı dosya hash'iyle doğrulandı. Git SKY kaynak commit'i
0598ba1f689dcb1b3640ecd7b0169ba72600a7a7. Kaynak TTBP UAT, hedef canlı
TTBP PROD. Oracle işlemleri yalnız metadata okumasıydı. SQL uygulanmadı.

Uçtan uca süre 1689.821 saniye, yuvarlak 28 dk 10 sn. Bu süre arşiv ve
SMTP gönderimini içerir. run.json ve maildeki karşılaştırma süresi
1641.94357 saniye, yuvarlak 27 dk 22 sn. Bu iki süre aynı kapsam değildir.
5 dakikalık uçtan uca hedef karşılanmadı. Önceki 105 kaydı 18 dk 29 sn
idi. Bu koşu kaynak hazırlığında MISS aldı. Farklı önbellek koşullarından
arındırılmış bir hızlanma iddiası yapılmaz.

5687 kaynak dosyası hazırlığı 864.685 sn sürdü. Git okuması 0.375 sn,
SQL ayrıştırması 853.455 sn, snapshot yazımı 10.725 sn. Önbellek okuması
MISS ve checkpoint_stored false. Yeni kaynak kaydı saklanmadı. Bunun
kapasite, bağlama veya tutarlılık kontrolünden hangisi nedeniyle olduğu
bu koşuda ayrıca doğrulanmadı. Sonraki koşunun HIT olacağı söylenemez.

Canlı hedef toplaması 462.083 sn, gözlemi dosyaya yazma 32.133 sn.
Kapsam 0.009 sn, fark karşılaştırması 12.039 sn, plan 82.857 sn ve paket
üretimi 105.056 sn. Hedef metadata okuması CAPTURED. 5336 envanter kaydı
ve 2942 DDL okuma işi işlendi. Katalog nesne sayısı 24510.
Hedef DDL okuma etkin duvar süresi 63.119 sn. grammar_projection
1438.395 sn değeri çalışan sürelerinin toplamıdır. Paralel duvar süresi
gibi sunulmaz. Aynı şekilde ddl_reads 324.548 sn toplam çalışan süresidir.

Sonuç 11895 doğrulanmış fark, 3805 taranan kaynak nesnesi ve 2120 DDL.
Eksik DDL 0. Metadata belirsizliği 2 kayıt, bağımlılık uyarısı 108 işlem,
diğer DDL uyarısı 229 işlem. Karşılaştırma kapsamı PARTIAL, doğrulanmış
DDL üretimi SUCCESS. Önceki 112 ile DDL sayısı aynı. Bu adımda dosyaların
birebir içerik karşılaştırması yapılmadı, böyle bir iddia kurulmaz.

Mail yalnız mkaracan@innova.com.tr adresine gönderildi. Konu SKY | Schema
Compare | SUCCESS | Build #116. Tek koşuluk Replay betiği properties veya
kalıcı pipeline yazmadı. Koşu sonunda normal Pipeline yeniden okundu ve
önceki dosyayla birebir aynı bulundu. Innova-SKY@innova.com.tr alıcısı,
Europe/Istanbul 08.00 zamanlaması ve etkin iş durumu korunur.

Offline testler önceki sürüm kurulumunda 1427 PASS idi. Bu adımda ürün
kodu değiştirilmedi ve birim testleri tekrarlanmadı. Gerçek Oracle kabulü
PASS, Jenkins koşusu PASS. Yeni branch, commit veya push yapılmadı.
Kanıt .local/live-daf616f-20261109/completion-receipt.json, son konsol,
normal Pipeline önce ve sonra dosyaları ile ekran görüntüleridir.

Sonraki somut iş kaynak ayrıştırma süresini ve checkpoint_stored false
nedenini düzeltmektir. Bu ölçüm koşusu sırasında program veya önbellek
ayarları değiştirilmedi. Gerçek SQL Jenkins yetkili arşivinde saklanır.

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

## Paket SHA Ve Tekrarlanan Doğrulama

Author: Mehmet KARACAN
Date: 2026-11-06

Sabit kaynak commit'i 881ad00a06474bc737e022f2185bc9fce7307c6b ile yerel
TTBP toplaması yapıldı. Hedefteki 107 paketin 69'u içerik özetiyle aynı
bulundu. Ham SHA eşleşmesi olmadı. Boşluk ve normal yorum farkları
ayrılırken literal, tırnaklı ad ve hint değerleri korunur. Kaynak paketin
kimliği, raw DDL hash'i ve COMPLETE parser kanıtı doğrulanmadan bu kısa
yol kullanılmaz. Gerçek fark mevcut parser yolunu izler.

Kaynak paketin SHA kanıtı planlama ve SQL yazımında da kullanılır.
CREATE OR REPLACE başlığı dışında kaynak gövdesine dokunulmaz.
Üretilen SQL bu kaynak metniyle birebir aynı değilse parser yeniden çağrılır.

| Ölçüm | Önce | Sonra |
| --- | --- | --- |
| Planlama | 624,99 sn | 76,03 sn |
| DDL ve rapor paketleme | 161,19 sn | 48,93 sn |
| Karşılaştırma, plan ve rapor | 801,74 sn | 141,33 sn |

Son tekrar çalışma aynı kaydedilmiş kaynak ve hedef snapshot dosyalarını
kullandı. Dosyaları yükleme dahil 210,34 saniye sürdü. Bu süre canlı Oracle
toplamasını içermez. 2.007 SQL dosyası, yalnız plan kimliği satırı hariç aynı.
Fark ve karar sayıları değişmedi. Kanıt özel .local dizininde
package-sha-sql-equality.json ve package-sha-final-report-performance.json.

Canlı hedef toplama 747,11 saniye sürdü. DDL okumaları 301,77 saniye,
dictionary okumaları 19,41 saniye, harici referans metadata işlemleri
30,88 saniye, sidecar birleştirme 61,17 saniye sürdü. Paralel grammar
toplamı 1.397,03 çalışan saniyesidir ve duvar saatiyle toplanmamalıdır.
İlk kaynak hazırlığı 475,52 saniyedir.

Kaynak arşivinde Windows harf büyüklüğü çakışması önbelleği geçersiz
kılıyordu. Git yolları mantıksal olarak aynı tutuldu. Çakışma bulunan
kapsamda source-storage.json dosyası fiziksel hash yollarını belirliyor.
Sabit Git içeriğinden doğrulanan 8.867 nesneli kaynak artık aynı snapshot
ve raw DDL ile önbellekten açılıyor. Ölçülen yükleme 55,00 saniye.
PARTIAL kaynak PARTIAL olarak kalır. İlgili sekiz paket tam sayılmaz.

Tam test 1.304 PASS. Son tip denetimi sonrasında ilgili grup 74 PASS.
Oracle DDL/DML, Jenkins ve SMTP çalıştırılmadı. Uçtan uca beş dakika hedefi
sağlanmadı. Kalan temel maliyet canlı DDL okuma ve farklı paketlerin çözümlemesi.

### Ayrı Paket Ölçümü Ve SQL Eşitliği

İzole eski paket çözümlemesi 463,05 saniye, SHA yolu 456,49 saniye sürdü.
69 paketin yeniden kullanılmasına rağmen kalan büyük paketlerin grammar
beklemeleri bu aşamanın süresini belirledi. Tek başına SHA hedef ayrıştırmasını
yaklaşık 6,56 saniye hızlandırdı. Büyük kazanç kaynak paketinin planlama ve
yazım sırasında tekrar ayrıştırılmamasından geldi.

Sıkı fark ve karar listesi eşitliği geçmedi. SQL üretmeyen altı metadata
belirsizliği çıktı, iki bağımlılık kaydı eklendi. Net dört teknik kayıt farkı
tam eşitlik gibi sunulmadı. Ardından kaydedilmiş hedef yorumunu sabit tutan
ayrı SQL denetimi yapıldı. SHA kısa yolu 69 pakette aynı snapshot sonucunu
verdi. Eski ve yeni 1.285 hazır SQL ve öneri kaydının tümü aynı. Kimlik,
sıra, karar, bağımlılık ve SQL gövdesi hash değerleri birlikte karşılaştırıldı.
SQL içermeyen kayıtlar bu denetimde ayrı raporlandı. Kanıt
.local/package-sha-controlled-sql-verification.json dosyasında.

Bu son kodla yeni uçtan uca canlı koşu yapılmadı. Rapor tekrarının 210,34
saniyesi bütün canlı sürenin beş dakikaya indiği anlamına gelmez.

## 7 Kasım 2026 Canlı Toplama Ve Planlama Sonucu

Author: Mehmet KARACAN
Date: 2026-11-07

Son yerel canlı koşu 292,44 saniyede tamamlandı. Bu 4 dakika 52 saniyedir.
Sabit kaynak commit'i 881ad00a06474bc737e022f2185bc9fce7307c6b ve doğrulanmış
kaynak önbelleği kullanıldı. Oracle hedefi yeniden toplandı. Süre kaynak
hazırlığını, hedef toplamayı, snapshot arşivini, karşılaştırmayı, DDL paketini
ve genel HTML raporunu kapsar. Tanı amacıyla yapılan seri tekrar bu süreye
dahil değildir. Kullanıcı tablosu veya verisi taranmadı. SQL uygulanmadı.

Bu sonuç aynı kaynak için önbellekli çalışmadır. Önceki checkpoint'teki
güncel kodla ilk kaynak hazırlığı 395,40 saniyedir. Soğuk başlangıcın beş
dakikaya indiği veya bütün ortamlarda sabit süre sağlandığı iddia edilmez.

| Aşama | Önceki Checkpoint, 4 Okuyucu | Yeni Tekrar, 4 Okuyucu | Son Tekrar, 8 Okuyucu |
| --- | --- | --- | --- |
| Kaynak hazırlığı | 29,90 sn | 41,07 sn | 30,61 sn |
| Canlı Oracle toplama | 130,57 sn | 169,05 sn | 110,94 sn |
| Snapshot kaydetme | 30,02 sn | 44,37 sn | 34,95 sn |
| Karşılaştırma | 7,47 sn | 8,16 sn | 8,22 sn |
| Planlama | 65,46 sn | 43,50 sn | 38,69 sn |
| DDL ve hedef raporu | 42,83 sn | 56,03 sn | 49,27 sn |
| Genel rapor dahil toplam | 322,67 sn | 385,06 sn | 292,44 sn |

Dört okuyuculu yeni tekrar 6 dakika 25 saniye sürdü. Bu yavaş ölçüm
saklandı. Oracle ve yerel dosya süreleri çalıştırmalar arasında değişiyor.
Aynı tekrarlar arasında DDL okumasının kesişimleri bir kez sayılan süresi
95,30 saniyeden 46,90 saniyeye indi. Sekiz okuyuculu toplam aktif çalışan
süresi 325,51 saniyedir. Bu toplam duvar saatiyle toplanmaz.

### Kaldırılan Tekrarlar

Planlama profili kolon alanı çıkarımının toplam 8.200 kez çağrıldığını ve
aynı tabloların tekrar hesaplandığını gösterdi. Birim metinleri de aynı
karar içinde tekrar token'lara ayrılıyordu.
PlanningContext kolon ve kanonik alanları yalnız ilgili plan içinde saklar.
Kaynak ve hedef ayrı tutulur. Nesnenin aynı kimlikte farklı bir örneği de
ayrı değerlendirilir. Sonuç sözlükleri değiştirilemez. Hedefler veya projeler
arasında ortak önbellek yoktur. Bağımlılık kontrolleri atlanmaz.

Paket, prosedür ve benzeri nesne kararları bir kez çıkarılan token'ları
başlık dönüşümünde yeniden kullanır. Değiştirilmiş type tanımı yeniden
okunur. Ham gövdeye dokunulmaz. Aynı kayıtlı kaynak ve hedefle profil aracı
kapalı planlama 35,48 saniyedir. Profil aracının 302,88 saniyesi tanı
yükünü içerir ve hız kazancı hesabında eski normal süre diye kullanılmaz.

Oracle DDL okuyucu sınırı 1 ile 8 arasındadır. Yerleşik connector varsayılanı
8, dışarıdan verilen connector varsayılanı 1 olur. Ortam değişkeni
GENERATOR_ORACLE_DDL_WORKERS veya mevcut oracle_ddl_workers runtime ayarı
sayının açıkça azaltılmasını sağlar. Ana metadata oturumu bu okuyuculara
ektir. Her okuyucu kendi bağlantısını, salt okunur işlemini ve kimlik
kontrolünü korur. Oturum paylaşımı, yetki, süre ve kapatma hataları başarı
sayılmaz. Öncesi ve sonrası envanter kontrolü korunur.

### Çıktı Eşitliği Ve Özel Kanıtlar

Kayıtlı sabit girdilerde 8.486 işlemin SQL hash'i, kararı, sırası, gerekçesi
ve bağımlılığı aynı kaldı. Her iki yeni canlı koşudaki 2.007 SQL dosyası
önceki checkpoint ile yalnız üretilen plan kimliği yorumu dışında aynı.
Kaynak DDL arşivindeki dosyalar hiçbir yorum çıkarılmadan karşılaştırıldı.
Fark ve karar sayıları değişmedi. Canlı hedefte sequence sayaçları
ilerlediği için snapshot digest'i değişti. Bu değişim aynı snapshot iddiası
diye sunulmaz. Her canlı koşunun kendi okuma kaydı seri olarak tekrar
işlendi. Snapshot, evidence ve ham DDL byte değerleri aynı, eksik sorgu sıfır.

Son canlı koşu .local/ui-state/runs/eb3f0cb0a4314c9a8b7806b146f5d18a
altındadır. collection-benchmark.json süre ve seri tekrar kanıtıdır.
planning-eight-readers-sql-equality.json ve planning-equivalence.json
.local altında SQL ve işlem eşitliğini tutar. metadata-read-trace.json
gerçek SQL içerir. Bu dosyalar Git'e veya dış servise taşınmaz.

Son tam test 1.325 PASS, 196,40 saniye. Komut PYTHONPATH=src ile
python -m pytest -q --tb=short --junitxml=.local/oracle-eight-readers-tests-final.xml.
Tek uyarı mevcut Starlette/AnyIO kullanım dışı kalma bildirimidir.
git diff --check geçti.
Jenkins ve SMTP çalıştırılmadı. Commit ve push yapılmadı.


## 9 Kasım 2026 Hedef Toplama Darboğazı

120 canlı koşusunda hedef toplama 333,507 saniye, toplam süre 634,126
saniyedir. DDL okuma etkin duvar süresi 48,217 saniyedir. Parser işçi
sürelerinin toplamı duvar süresi olarak yorumlanmaz. PCK_ISLEM_DAGITIM
hedefte PARSER_TIMEOUT ile 240 saniye sınırına ulaşmıştır. Kaynak kaydı da
aynı pakette kısmi bilgiyi korur.

İç içe TO_CHAR, NVL ve sayısal fonksiyonlarda unary_expression_core ve
string_function kararları uzun ileri bakış oluşturmuştur. Sabit grammar'ın
mevcut dalları dar önkoşullarla seçilir. Argüman, kalan token ve EOF kontrolü
atlanmaz. Üçüncü taraf parser dosyaları değiştirilmez. Kısa örneklerde
referans parse ağacı ve hata davranışı karşılaştırılmıştır. Büyük yerel
kaynak paket eski sınırda kalmak yerine 99,566 saniyede tam çözümlenmiştir.

Paket eşitliğinde aynı metni iki kez lex etme kaldırılmıştır. Slash içeren
literal veya hint için önceki kanonik dönüşüm korunur. Kaynak bağımlılıkları
hedef toplamasında iki kez çıkarılmaz. Oracle sorguları ve metadata kapsamı
korunur. Makbuza en yavaş çözümlemeler ve uygulama duvar süreleri eklenmiştir.

Sabit JSON sözleşmeleri fastjsonschema 2.21.2 ile hızlandırılır. Yalnız
draft 7 ve 2020 kurallarının ortak alt kümesi derlenir. Bilinmeyen schema
anahtarı standart jsonschema 4.26.0 yolunda kalır. Hızlı reddin son kararı da
standart doğrulayıcıya bırakılır. Girdi varsayılanlarla değiştirilmez.
Bağımlılık wheel'i SHA256 ile sürüm paketine dahil edilmiştir.

Yerel tam test 1470 passed. Son makbuz eklemelerinden sonraki hedefli test
75 passed. Tam paket içinden bağımsız doğrulama 101 passed. Jenkins 123
ENVIRONMENT_CHECK SUCCESS, 345 ürün dosyası ve 7 yardımcı dosya doğrulandı.
Oracle bağlantısı ve mail gönderimi bu kurulumda yapılmadı.

Yeni sürüm 1d65598c3841c093fefbae67a359f93faf5041803064f88e23834349fd7c87a3.
Temel commit daf616f, açık yama özeti
e74b68e57aa5defa08d3ac07e9c0af300d87b3be00425058002ad32ef20b36b8.
Önceki kaynak önbelleği düzeltmesi korunur. Yeni commit veya push yapılmadı.

124 koşusu aynı kayıtlı 120 girdileriyle SQL eşitliğini ve hedefin yeniden
çözümlemesini denetliyor. Oracle bağlantısı yasaktır. Kısmi kaynak snapshot
açık kabul adımında aynı Git byte değerlerine bağlanır ve kısmi kalır.
Bu, canlı hedefin veya parser timeout yanıtının önbelleğe alınması değildir.
Normal kaynak önbelleğinin sürüm, profil ve ham dosya kontrolleri gevşetilmez.

Canlı tekrar NOT_RUN. Toplam 5 dakika kabulü henüz doğrulanmadı.
Test maili yalnız mkaracan@innova.com.tr adresine gönderilecek. Normal
Innova-SKY@innova.com.tr ve Europe/Istanbul 08.00 ayarı korunur. SQL uygulanmaz.


### 9 Kasım 2026 Gerçek Girdide Yakalanan Dış Birleştirme Regresyonu

124 kabulünde EMITTED_SQL_PARSE_FAILED oluştu. Canlı Oracle testi ve mail
başlatılmadı. 125 ve 126 koşularında mevcut 1187 değişim SQL'i ve 530
oluşturma SQL'i salt okunur parser tanısından geçirildi. 127 koşusu
VIEW_KARNE_KRITER_DETAY için Oracle dış birleştirme işaretinin fonksiyon
argümanı gibi okunduğunu gösterdi. Hızlı seçimde (+) ayrı tutuldu.
Referans parse ağacıyla birebir regresyon testi önce kırmızı, sonra yeşil
çalıştı. Gerçek yerel VIEW de COMPLETE sonucu verdi.

Yeni süre alanları için metadata testi güncellendi. İç içe ve örtüşen
süreler iki kez toplanmaz. Son tam kontrol 1471 passed, 0 failed, 0 skipped.
Paket içinden kontrol 102 passed. Önceki 1470 passed sonucuna ek yeni
dış birleştirme testi vardır. Starlette için önceki deprecation uyarısı
devam eder ve bu görevle ilgili değildir.

128 ENVIRONMENT_CHECK SUCCESS ile düzeltilmiş paket kuruldu.
Sürüm 231420775218e0287f6a881c2f6f37859a445e67b4b04138c48dd80d3da05275.
Yama özeti 89331d8a451d213a243a8bc21eb4d15775c97470c783b52b327498efabc44c8d.
345 ürün dosyası ve 7 yardımcı doğrulandı. Önceki 1d65598c paketi canlı
karşılaştırma için kullanılmadı. 129 SQL eşitlik ve hedef çözümleme kabulü
devam ediyor. Canlı kabul ve beş dakika hedefi henüz NOT_RUN.

### 9 Kasım 2026 Hedef Toplama Ölçümü

| Ölçüm | 120 | 130 |
| --- | --- | --- |
| Jenkins toplamı | 634,126 sn | 372,930 sn |
| Rapor karşılaştırması | 591,520 sn | 330,238 sn |
| Kaynak hazırlığı | 21,302 sn | 14,641 sn |
| Hedef toplama | 333,507 sn | 127,050 sn |
| Üretilen DDL | 2120 | 2120 |
| Eksik DDL | 0 | 0 |

129 kayıtlı eşitlik kabulünde 2416 SQL dosyası yalnız plan kimliği yorumları
haricinde aynı çıktı. Hedefteki 2942 ana nesnenin daha önce bilinen metadata
alanları korundu. 130 her hedef metadata değerini Oracle üzerinden yeniden
okudu. Parser önbelleği yalnız aynı ham SQL ve aynı parser sürümündeki tam
çözümlemeyi kullandı. Kaynak önbelleği HIT_VERIFIED ve parse süresi sıfırdır.

130 içinde kaynak referans analizi 18,151 sn, plan 57,408 sn ve çıktı
36,969 sn sürdü. Uçtan uca beş dakika hedefi henüz sağlanmadı. Saf token
konumlarını sınırlı bellekte tekrar kullanan ikinci iyileştirme doğrulanıyor.
133 çevrimdışı ölçümünde aynı referanslar 18,269 yerine 10,620 sn sürdü.

### 9 Kasım 2026 Son Kabul

| Ölçüm | 120 Baseline | 136 İlk Yeni Sürüm | 137 Aynı Sürüm Tekrarı |
| --- | --- | --- | --- |
| Jenkins toplamı | 634,126 sn | 310,443 sn | 287,179 sn |
| Rapor karşılaştırması | 591,520 sn | 300,159 sn | 278,631 sn |
| Hedef toplama | 333,507 sn | 122,503 sn | 99,630 sn |
| Kaynak hazırlığı | 21,302 sn | 14,350 sn | 14,067 sn |
| Ek metadata birleştirmesi | 9,5 sn dolayında | 31,548 sn | 9,211 sn |
| Üretilen DDL | 2120 | 2120 | 2120 |
| Eksik DDL | 0 | 0 | 0 |

137 ile arşiv ve mail dahil beş dakika hedefi sağlandı. Bu kabul aynı
kaynak için doğrulanmış kaynak checkpoint ve aynı SQL parser önbelleğiyle
ölçüldü. 136 ilk yeni sürüm bu sınırı 10 saniye aştı. Yeni veya değişmiş
paketlerin ilk çözümlemesi için aynı süre garantisi verilmez. Her koşuda
Oracle metadata yeniden okunur. Row veya uygulama verisi taranmaz.

Temel bekleme ağdan önce büyük paketin 240 saniyelik parser sınırıdır.
Daha dar grammar kararları ve tam girdi kontrolü bu sınırı kaldırdı.
Tekrarlı kanonik lexer geçişi, kaynak referans çıkarımı ve aynı SQL'in
plan için yeniden okunması azaltıldı. Sözleşme doğrulaması eşdeğer ortak
JSON Schema kurallarında hızlandırıldı. Son kurulumda üçüncü taraf grammar
aynıdır. Jenkins tüm çıktıları arşivler, kullanım izi SHA256 içeren manifest
üzerinden tutulur. Arşiv ve mail aşaması 136 ve 137 için yaklaşık 10 ve
9 saniyedir. 130 tanı aşaması içerdiği için doğrudan soğuk parser süresi
olarak yorumlanmaz.

135 aynı eski kaynak ve hedefle tüm karar ve farkları korudu. 138 gerçek
120, 135, 136, 137 dosyalarını karşılaştırdı. 2416 SQL dosyasında yalnız
oluşturulan plan kimliği yorumları dışında değişiklik yoktur. Canlı metadata
uyarı sayısı 3 kayıttır ve eski 120 ile aynı değildir. Uyarılar gizlenmedi.
DDL üretimi SUCCESS, eksik DDL sıfır ve SQL uygulaması NOT_EXECUTED.

Tam test 1483 passed. Kurulan wheel üzerinden 117 ve 15 passed.
Kurulum 134, kayıtlı kabul 135, canlı 136 ve 137, SQL kanıtı 138 SUCCESS.
Sabah 08.00 SKY alıcısı korundu. Test mailleri yalnız mkaracan@innova.com.tr.
