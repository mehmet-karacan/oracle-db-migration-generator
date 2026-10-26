# Kaynak hazırlama performansı - 24 Ekim 2026

Kapsam: kaynak hazırlığını mevcut parser, kapsam, PARTIAL/UNKNOWN kararları ve
DDL içeriği korunarak hızlandırmak. Oracle metadata ve hedef gözlemi yeniden
kullanılan kaynak checkpoint'inin parçası değildir.

## Ölçülen darboğaz

22 Ekim #42'nin özgün karşılaştırması 73 dk 44 sn sürdü. Başlangıçtan kaynak
metadata aşamasına kadar 46 dk 59 sn geçti, yaklaşık 18 sn runtime hazırlığı da
bu aralıktadır. Eski ayrıntılı konsol artık bulunamadığından 47 dakikanın her
dosyaya tam dağılımı geriye dönük olarak kanıtlanamıyor.

#48 aynı Git commit'ini ve 5.688 ham dosyayı okuyup eski v23 hazırlığını yeniden
ölçtü. Tam kaynak snapshot'ı #42 ile kanonik byte düzeyinde aynı çıktı.

| Ölçüm | Süre / sayı |
| --- | --- |
| Parse, envanter ve birleştirme | 1.705,19 sn - 28 dk 25 sn |
| PACKAGE_BODY toplamı | 1.477,15 sn - 24 dk 37 sn |
| Beş büyük gövdede tekrar timeout | yaklaşık 1.203,64 sn - 20 dk 4 sn |
| Başarılı parser response cache hit | 4.429 |
| Parser response cache miss | 503 |
| Hit sonuçlarını okuma toplamı | 18,04 sn |

Beş timeout: PCK_DUMMY, PCK_ISLEM_DAGITIM, PCK_ISLEM_DAGITIM5,
PCK_ISLEM_DAGITIM_UAT_YEDEK ve PCK_ISLEM_DAGITIM_YEDEK. Her biri 240 sn sınırına
ulaştı. Başarılı sonuç cache'i timeout veya hatalı yanıt saklamadığı için aynı
tam kaynak tekrar hazırlanırken bu maliyet yeniden ödeniyordu. Büyük başarılı
paket parse'ları ve response cache miss'leri kalan maliyete de katkı veriyor.
Bu tekrar ölçümü, #42'nin soğuk hazırlama süresiyle birebir aynı deney değildir.

## Uygulama

`PreparedSourceCache` bitmiş kaynak hazırlığının doğrulanmış checkpoint'ini
saklar. Anahtar, sabit Git SHA, bütün güncel ham dosyaların gerçek byte hash'i,
yol/tür/owner bilgileri, profil, hazırlama/parser kodu ve Python sürümünü içerir.
Kullanımdan önce kapalı dosya listesi, hash'ler, profil, input manifest ve
snapshot semantiği yeniden doğrulanır. Bozuk, eksik veya farklı girdide normal
hazırlamaya dönülür. Kaynak repository içine cache yazılmaz.

PARTIAL checkpoint yeniden kullanıldığında PARTIAL kalır, timeout tanıları ve
UNKNOWN kanıtları korunur. Başarılı parser response cache'inin hata/timeout
saklamama politikası değişmedi. Oracle correspondence ve target capture her
normal çalışmada tazedir. Hazırlama süreleri ayrıca
`source-preparation-performance.json` artifact'ine aktarılır.

#51 Jenkins ölçümü: aynı 5.688 dosya için CLI hazırlama 24,58 sn,
5.691 hazırlık dosyası (5.688 ham dosya + üç manifest/snapshot) birebir aynı.
İç ölçüm 22,79 sn: Git okuma 0,27 sn, checkpoint doğrulama 12,89 sn,
snapshot yazma 9,62 sn, parser 0 sn. Bu kaynak hazırlama ölçümüdür, toplam
canlı karşılaştırma süresi değildir. #51'in son SQL kontrol betiği bellek içi
shallow-copy hatasıyla durdu, disk artifact'leri değişmedi. Düzeltilmiş betiğin
tam sonucu ayrı Jenkins doğrulama makbuzunda tutulur.

#53 düzeltilmiş tam offline kontrolü tamamladı: kaynak CLI 24,35 sn,
5.691 hazırlık dosyası aynı, zenginleştirilmiş kaynak ve planın bütün kararları,
farkları, kanıtları ve sayaçları aynı. 1.379 hazır nesne SQL'i, toplu SQL ve
salt okunur postcheck olmak üzere 1.381 SQL dosyası byte düzeyinde doğrulandı.
Yeni release'in generator kimliği farklıdır, SQL header regresyonunda yalnız
özgün plan ID kullanıldı. Bu provenance normalizasyonu gerçek üretim
artifact'ine yazılmadı. Görünüm yenilemesi eski plan/SQL byte'larını korur.
Güncel #49 kaynak hazırlığı da kendi tamamlanmış hazırlama kanıtı, ham Git
dosyaları ve snapshot hash'i doğrulanarak ikinci checkpoint olarak saklandı,
başarısız/değişmiş hedef sonucu yeniden kullanılmadı.

Offline kontrol makbuzu: `output/source-performance/verification-53-receipt.json`.
SQL hash listesi SHA-256:
`1b3067eed7dcd88a49c74b7ceab5bfffc1576169231465c10514b9108812cbc4`.
24 Ekim tekrar doğrulaması: 1.022 test / 135,04 sn, failure/error/skip 0.
Sözleşme denetimi: 7 schema / 8 example VERIFIED. Günlük normal Jenkins v25,
TTBP ve 08:00 yapılandırması kaydedildikten sonra tam metin yeniden okunarak
doğrulandı, tek seferlik kontrol betiği normal Pipeline'da bulunmuyor.

## İşletim sınırları

- Farklı commit, profil, ham girdi veya hazırlama kodunda checkpoint miss olur,
  ilk hazırlama maliyeti devam eder. Bu değişiklik parser algoritmasını
  hızlandırdığı iddiasını taşımaz.
- Cache dört giriş / 1 GiB ile sınırlıdır. Dolunca eski girişler otomatik
  silinmez, yeni store atlanır ve normal hazırlama sürer.
- #49'un 24 Ekim canlı hedefi capture sırasında değişti
  (`CHANGED_DURING_CAPTURE`). Bu gözlem başarılı karşılaştırma sayılmaz.
  Tamamlanmış kaynak hazırlığı kendi hash/commit kanıtıyla ayrıca kullanılabilir.
- #42 hedef capture yaklaşık 22 dk 8 sn idi: grammar/projection 15 dk 26 sn,
  DDL okuma 4 dk 59 sn, capture sonrası yaklaşık 4 dk 11 sn daha vardı.
  Bu maliyetler bu kaynak checkpoint değişikliğiyle ortadan kaldırılmış sayılmaz.
- Genel raporun üstündeki süre özgün karşılaştırma süresidir. Görünüm yenileme
  veya yalnız kaynak hazırlama ölçümü bu değerin yerine yazılmaz.

Kanıtlar Git dışında `output/source-performance/` ve yetkili Jenkins
artifact arşivindedir. Bu aşamada Oracle DDL/DML/COMPILE çalıştırılmaz.

## 24 Ekim canlı UI koşusu #55

Bitbucket erişimi düzeldikten sonra mevcut v25 TTBP işi UI’den tarayıcı
oturumu aktarımıyla çalıştırıldı. Gerçek başlangıç/bitiş 16:45:15.798–
17:03:55.614990 TSİ:1119.81699sn (18dk40sn), önceki73dk44sn’den %74.6877
daha kısa. Hedef ilk okumada değiştiği için yapılan ikinci tam okuma da
bu süreye dahildir. İkinci okuma tutarlı sonuç verdi.

Kaynak hazırlık22.8309sn, HIT_VERIFIED, Git0.2943/checkpoint13.0227/
yazma9.5133/parse0sn. 5.690dosya, SHA45690e2ce8030901ee196b96bdb8cc507ec6fe9b.
Ayrı kaynak Oracle metadata yakalaması8.2446sn, bu hazırlık ölçüsüne dahil
değildir. Rapor1381hazırDDL/655inceleme/136üretilemeyenDDL/3UNKNOWN ile PARTIAL.
Mail yalnız mkaracan@innova.com.tr, SQL uygulanmadı. Bu canlı ölçüm farklı
zamanlı kaynak/hedef verilerini içerir, önceki byte-eşitlik regresyonunu
yeniden yapılmış saymaz. Kanıt output/shared-projects/live-receipt.json ve
aynı klasörde run-55.json/source-performance-55.json, gerçekSQLJenkins’te.
