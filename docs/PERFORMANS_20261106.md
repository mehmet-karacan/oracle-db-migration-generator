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
