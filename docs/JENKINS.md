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

## 9 Kasım 2026 Ana Dal Commit'i Jenkins'e Kuruldu

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcı son ana dal commit'inin sabah raporunda kullanılmasını istedi.
Kaynak commit daf616f0ec215dcd8e76fdd42647227ff9336269. git archive ile
çıkarılan bu commit'ten saf Python wheel hazırlandı. Ürünün 343 dosyası
ve 7 yardımcı dosya commit bytes ile eşleştirildi. Pipeline içine gömülü
bootstrap ve scope yardımcıları da aynı commit ile doğrulandı. Yalnız
önceki bağımlılık wheel'leri, Python runtime ve Instant Client korundu.

Yeni release 73f5a38f64fc803eabdf8c7a5a6f1f068c0c0cc25c075027166d92e02a1501f2.
Wheel 382fecf71d3d03288b243639627f5c3b3999e1ffd93420185aeb86ed299ab11e.
source-revision.json commit, wheel ve kurulu dosya hash'lerini taşır.
Normal Pipeline GENERATOR_CODE_COMMIT ile uygulama commit'ini ayrı tutar.
DDL kaynağının GENERATOR_SOURCE_SHA yönü ve Git checkout'u değiştirilmedi.

115 ENVIRONMENT_CHECK kurulum kontrolü SUCCESS. Sunucudaki venv içinden
343 ürün ve 7 yardımcı dosya doğrulandı. DEPLOYED_COMMIT_VERIFIED kaydı
output/versions/build-115.json olarak arşivlendi. Yeni Pipeline bu sürüm
kontrolünü her çalışmada karşılaştırmadan önce yapar. Kurulu dosya veya
commit uyuşmazsa işlem durur. Paket ve çalışma kimlikleri karışmaz.

Kaydedilen Pipeline yeniden açılarak birebir okundu. İş etkin. Günlük
Europe/Istanbul 08.00 zamanlaması, tek alıcı Innova-SKY@innova.com.tr,
varsayılan TTBP ve COMPARE modu doğrulandı. Konu SKY | Schema Compare |
durum | Build #numara biçiminde kalır. Normal sabah çalışması 115'in
ENVIRONMENT_CHECK parametresini devralmaz. İlk seçenek COMPARE olarak kalır.
115 çalışmasında mail gönderilmedi ve yeni Oracle bağlantısı açılmadı.

Çıkarılmış son wheel'den 1427 test PASS, başarısız ve atlanan sıfır.
Komut PYTHONPATH .local/deploy-daf616f-20261109/isolated-product ve çalışma
kökü ile runtime.generation önce import edilerek pytest -q --tb=short.
Kanıt installed-tests.xml. Tek uyarı Starlette deprecation bilgisidir.
Offline paket doğrulaması PASS. Jenkins kurulum kabulü PASS. Yeni canlı
Oracle kabulü NOT_RUN. SQL uygulanmadı. Yeni branch, commit veya push yok.
Bu aşamadaki çalışma ağacı farkları yalnız kurulum ve devir belgeleridir.

Yerel kanıt .local/deploy-daf616f-20261109/completion-receipt.json,
pipeline-readback.groovy, install-115-console.txt, deployed-version-115.json
ve saved-configuration.png. Sonraki zamanlanmış rapor güncel sürüm ve SKY
alıcısıyla çalışacak. Gerçek SQL çıktıları Jenkins yetkili arşivinde kalır.

## 9 Kasım 2026 SKY Ekip Alıcısı Onaylandı

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcı 114 mailini onayladı. Jenkins normal Pipeline alıcısı yalnız
Innova-SKY@innova.com.tr olarak kaydedildi. recipientProviders boş kalır.
İş etkin ve günlük zamanlama Europe/Istanbul 08.00 olarak doğrulandı.
Varsayılan TTBP kapsamı, cbbb70 sürümü ve DDL üretim sonuç kuralı korundu.
Konu SKY | Schema Compare | durum | Build #numara biçimindedir.

Kaydetme sonrasında yapılandırma yeniden açıldı ve Pipeline birebir
okundu. Alıcı satırı dışındaki Pipeline aynı kaldı. İş açıklamasındaki
onay bekleniyor ifadesi kaldırıldı. Yeni çalışma veya mail gönderimi
tetiklenmedi. Sabahki zamanlanmış çalışma ekip adresini kullanacak.
Kanıt .local/sky-recipient-20261109/receipt.json ve recipient-saved.png.
Önceki yalnız kişisel alıcı ve ekip onayı bekliyor kayıtları tarihseldir.

## 9 Kasım 2026 DDL Üretimi ve Uyarılar Ayrıldı

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcı eksiksiz DDL üretiminin SUCCESS vermesini istedi. Jenkins'in
önceki 10 ve 20 kodlarını aynı UNSTABLE sonucuna indirmesi ve planın
kapsam durumunun üretim sonucu olarak kullanılması düzeltildi.
Normal Pipeline artık yalnız 10 kodunu eksik DDL olarak UNSTABLE yapar.
20 ve diğer hata kodları FAILURE verir. Metadata uyarısı tek başına
Jenkins sonucunu değiştirmez. Ekip alıcısı onay bekler.

Yeni runtime/generation.py doğrulanmış plan ve proposal kataloğundan
DDL üretimini hesaplar. runtime/aggregate.py her arşivi verify_bundle
ile doğrular ve ddl-generation.json kaydını rapor tamamlandığında yazar.
Önceki başarı kaydı yeni doğrulama öncesinde kaldırılır. run.json kapsam
ve plan kararlarını korur. tools/jenkins_run.py Jenkins dönüş kodunu
aynı run_id taşıyan üretim kaydından alır. SQL uygulama yetkisi doğmaz.

reporting/view.py ve email/run şablonları metadata, bağımlılık ve diğer
DDL uyarılarını ayrı gösterir. Eksiksiz dosyalarda DDL Üretimi Tamamlandı
başlığı görünür. Üretilmiş dosya için eski DDL desteği gerekiyor metni
kullanılmaz. İlgili dosyaların açıklamalarında nedenler korunur.
Yeni test test_ddl_generation_status.py, güncellenen iki hedef testi
başarı, eksik DDL, başarısız hedef, bilinmeyen katalog ve bozuk SQL'i sınar.

Kurulu release cbbb70f2b8a0eb45dc3083791a5e030d745bb1554cb9b4732c627627f1445a02.
DDL motoru, Oracle kodu ve kurumsal logo önceki 15f87 sürümüyle aynı.
113 ortam doğrulaması SUCCESS. 114, 112 arşivini ayrı dizine kopyalayıp
doğruladı. 2120 DDL hazır, eksik 0. Kaynak ve kontrol SQL'leri dahil
2416 SQL dosyası birebir aynı. Plan JSON ve eski manifest aynı kaldı.
Yeni Oracle bağlantısı sıfır. SQL uygulanmadı. 105 gerçek karşılaştırma
süresi 18 dk 29 sn olarak korundu. Yeni canlı koşu yapılmış gibi sunulmadı.

114 sonucu SUCCESS. Plan ve karşılaştırma kapsamı PARTIAL kalır.
2 metadata belirsizliği, 106 bağımlılık ve 231 diğer DDL uyarısı korunur.
Mail yalnız mkaracan@innova.com.tr adresine gönderildi. Konu SKY | Schema
Compare | SUCCESS | Build #114. Tek bağlantı aynı build'in HTML raporuna
ve DDL dosyalarına gider. Innova-SKY@innova.com.tr onay bekler.

83 kurulu paket testi PASS, başarısız ve atlanan sıfır. Komut PYTHONPATH
.local/ddl-generation-20261109/release/isolated-product ve çalışma kökü
olacak şekilde runtime.generation önce import edilerek pytest çalıştırıldı.
Yeni testler önce kırmızı çalıştı. Tam çalışma PYTHONPATH src ve çalışma
kökü ile python -m pytest -q --tb=short komutunda 1425 PASS ve 1 eski
Git publication hatası verdi. Aynı test önceki 95fa pakette de başarısızdı.
Git publication bu Jenkins yolunda kullanılmıyor. Tam test yeşil denmez.
Yeni canlı Oracle kabulü NOT_RUN. Jenkins kurulum ve kayıtlı arşiv kabulü
PASS. Branch, commit ve push yapılmadı. Diğer çalışma değişiklikleri korundu.

Kanıt .local/ddl-generation-20261109/completion-receipt.json ve aynı
klasörde console, mail, paket manifesti, installed-tests.xml, full-tests.xml
ve ekran görüntüleridir. Sonraki adım kullanıcı mail onayını beklemektir.
Ekip alıcısı açık onay olmadan geri açılmaz.

## 9 Kasım 2026 Eksik DDL Dosyalarının Tamamlanması

Author: Mehmet KARACAN
Date: 2026-11-09

Kurulu release 15f87a51de1baabaced1c62a9c3100e2fc90d05c1801ad8bccf2dc8bd6a4f0cf.
111 ortam kontrolü SUCCESS. 112, gerçek 105 kaynak ve hedef kaydıyla 238
eksik DDL'yi tamamladı. Yeni Oracle bağlantısı sıfır. Önceki 1783 READY SQL
aynı kaldı. Toplam 2120 DDL, eksik 0. 337 uyarılı SQL dosyası proposals
altında korunur. Metadata ve bağımlılık uyarıları silinmez veya READY yapılmaz.

Mail yalnız mkaracan@innova.com.tr adresine gönderildi. Konu SKY | Schema
Compare | UNSTABLE | Build #112. Tek mail bağlantısı aynı build'in HTML
raporunu açar. 2 metadata belirsizliği nedeniyle PARTIAL/UNSTABLE durumu
korunur. Bu durum DDL eksikliği anlamına gelmez. Özgün 105'in 18 dk 29 sn
karşılaştırma süresi comparison-timing.json ile ayrıca korunur. Yeni canlı
koşu yapılmış gibi sunulmaz. SKY ekip alıcısı açık kullanıcı onayı bekler.

64 kurulu paket testi geçti. Tam son test 1417 PASS, eski 95fa pakette de
tekrarlanan 1 yerel Git publication hatası verdi. Uzak yayın veya Git push
yapılmadı. Bu işte artifact Git yayını kullanılmaz. Devir ve tam kanıt
.local/missing-ddl-20261109/completion-receipt.json içinde bulunur.

## 9 Kasım 2026 Canlı Hedef Toplama Düzeltmesi

Author: Mehmet KARACAN
Date: 2026-11-09

Kurulu release 95fa2020ebaf6e7de66021c8d4a5ad21e132dee9d4e827ea3ff4c3c2ca84e416.
Envanter satır sırası gerçek metadata değişiminden ayrılır. Tekrar sayısı,
durum ve tarih değişimleri korunur. Gerçek değişimde sınırlı nesne örneği
kaydedilir. 102 ortam kontrolü ve 105 canlı hedef toplaması doğrulandı.
105 tek denemede 5336 sabit katalog satırı okudu. Karşılaştırma 18 dakika
29 saniye, 11895 fark ve 1882 DDL işlemi üretti. 238 eksik DDL nedeniyle
sonuç PARTIAL ve Jenkins UNSTABLE. SQL uygulanmadı. 313 ilgili test geçti.

Mail yalnız mkaracan@innova.com.tr adresine gönderildi. Konu SKY | Schema
Compare | UNSTABLE | Build #105. Tek bağlantı aynı build'in index.html
raporunu açar. Innova-SKY ekip alıcısı kullanıcı onayına kadar kapalıdır.
Kalıcı Pipeline son kez yeniden okunup doğrulandı. Günlük saat 08.00.
105 için doğrulanmış 97 kaynak hazırlığı bir defalık tekrar kullanıldı.
Normal tanıma eski build kaynağı sabitlenmedi. Kanıt ve açık işler
.local/capture-consistency-20261109/completion-receipt.json içindedir.

## 9 Kasım 2026 Başarısız Hedefte Kaynak Bilgisi

Author: Mehmet KARACAN
Date: 2026-11-09

Ürün başlığı yalnız Schema Compare olur. Raporu eki kullanılmaz.
Hedef okunamadığında kaynak adı ve nesne sayısı aynı çalışmanın
report-context.json kaydından gösterilir. Bu kayıt kaynak SHA ve hedef
listesiyle doğrulanır. Teknik nesne politikası ve kaynak başına tek sayım
kuralı korunur. Kaynak kapsamı PARTIAL ise alt sınır notu kalır.
Karşılaştırma yapılamadıysa fark ve eksik DDL sayıları sıfır gösterilmez.
Nesne tanımı okuma sırasında değişmişse nedeni açık Türkçeyle yazılır.
Yeni başlık ve bağlam 98 ortam kontrolünde, 99 kayıtlı mail önizlemesinde
doğrulandı. 214 ilgili test geçti. Ekip gönderimi onay bekler. Güncel
normal Pipeline ve test maili alıcısı yalnız mkaracan@innova.com.tr olur.
Onay geldiğinde Innova-SKY@innova.com.tr adresine dönüş ayrıca uygulanır.

## 9 Kasım 2026 Jenkins SKY Mail Alıcısı

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcının son açık talimatıyla sky/oracle-db-migration-generator
Pipeline mail alıcısı yalnız Innova-SKY@innova.com.tr oldu. Bu karar
önceki yalnız mkaracan@innova.com.tr alıcı tanımının yerini alır.
CC, BCC ve ek alıcı sağlayıcısı yoktur. Konu SKY | Schema Compare |
durum | Build #numara biçiminde kalır. Saat Europe/Istanbul 08.00,
TTBP kapsamı ve kurulu 60377c6a paketi değişmedi.

Chrome tarayıcı eklentisinde Pipeline kaydedilip tekrar okundu.
Önceki tanımla tek fark emailext alıcısıdır. İş açıklamasındaki mail
adresi de güncellendi. Bütün karşılaştırma ve arşiv adımları aynı.
Yeni karşılaştırma veya mail başlatılmadı. Test NOT_RUN, yalnız ayar
kontrolü yapıldı. Kayıttan okunan tanımın birebir eşitliği doğrulandı.
Kanıt .local/jenkins-sky-recipient-20261109 altında pipeline-before.groovy,
pipeline-after.groovy, pipeline-readback.groovy, receipt.json ve
recipient-saved.png. Genel şablondaki NOTIFY_TO yer tutucusu korunur.
Bu iş için doldurulacak değer Innova-SKY@innova.com.tr olur.
Sonraki normal çalışmanın maili bu dağıtım adresine gider.

# Jenkins Çalışma Sözleşmesi

21 Ekim rapor sunumu yenilemesi: `tools/jenkins_report_presentation.py`, önceki
doğrulanmış tek TTBP arşivinden yeni build için HTML üretir. Karşılaştırma,
Oracle bağlantısı veya SQL üretimi yapmaz. Plan JSON ve bütün SQL byte'ları
korunur, yalnız HTML/assets manifest kayıtları yenilenir ve paket tekrar
doğrulanır. Mailde eski build/tarih, yeni yakalama yapılmadığı ve yenileme
süresinin karşılaştırma süresi olmadığı yazılır. Tek seferlik yenileme sonrası
normal günlük pipeline geri yüklenir, zamanlama ve alıcı değişmez.

Sunum yenilemesi comparison-timing.json ile özgün karşılaştırma başlangıç,
bitiş ve build numarasını korur, tekrarlanan yenilemelerde eski receipt zinciri
en fazla20 koşu izlenir. Aynı source commit doğrulanır. Genel mail ve katalog,
karşılaştırma süresini yenileme süresinden ayrı gösterir. Kanonik run.json
zamanları ve difference_count null değeri değiştirilmez, doğrulanan fark ve
karşılaştırılamayan kayıt sayısı yalnız sunumda ayrı türetilir.

**Güncel kapsam (20 Ekim son kullanıcı kararı):** Günlük 08:00
Europe/Istanbul çalışması yalnız TTBP karşılaştırır. `SCHEMA_SCOPE` varsayılanı
`TTBP`, `INNOVA_ODI` yalnız manuel seçimdir. Görünen hedef adı `PROD`, şema
`TTBP` olur, teknik target ID ve arşiv yolları değişmez. Mevcut yetkili katalog
okuyucusu, karşılaştırılan şemayı değiştirmez. Source ve target READ ONLY kalır.

`tools/jenkins_scope.py`, doğrulanmış iki şemalı registry'den seçilen tek şema
için build'e özel config üretir. Source roots, job scope, target ve kaynak
metadata listeleri birlikte daraltılır, immutable release değiştirilmez.
Şablonun `@@SCOPE_BASE64@@` alanına bu doğrulanmış helper yerleştirilir.
`ENVIRONMENT_CHECK` Oracle bağlantısı veya mail gönderimi yapmaz.

20 Ekim son kullanıcı kararı: mevcut SKY işi rapor/SQL'i yalnız Jenkins
artifact arşivinde saklar, artifact Git publication aşaması/credential binding
yoktur. Mail Jenkins build raporunu açar. Aşağıdaki yayın parametreleri mevcut
işte etkin değildir, yeni açık yetki olmadan kullanılamaz.

**Durum:** 20 Ekim 2026 kullanıcı talimatıyla ilk INNOVA_ODI işi kuruldu.
İlk kurulum ve çalışma kanıtı `docs/JENKINS_ILK_KURULUM.md` içindedir.
Aşağıdaki geniş parametre sözleşmesi sonraki çoklu hedef/yayın düzenidir,
mevcut işte SCHEMA_SCOPE, RUN_MODE ve sabit SHA doğrulamalı GENERATOR_RELEASE görünür.

## Parametreler

| Ad | Tip / Varsayılan | Anlam |
|---|---|---|
| SOURCE_REPO_URL | string, job kurulurken girilir | Kaynak DDL Git URL'si, kodda kurum adresi sabitlenmez. |
| SOURCE_REF | string | SKY ilk kurulum adayı master, gerçek ref doğrulanır. |
| SOURCE_GIT_CREDENTIAL_ID | string | Salt okunur Git SSH credential. |
| SOURCE_PROFILE_FILE_ID | string | Managed JSON kaynak profilinin ID'si. |
| TARGETS_FILE_ID | string | Managed JSON target registry. |
| TARGET_IDS | string = ALL | Tüm enabled target'lar veya virgüllü ID listesi. |
| MAX_PARALLEL_TARGETS | string = 2 | 1–8 tam sayı, sınırlı batch paralelliği. |
| ORACLE_DRIVER_MODE | choice = thin | thin/thick, target özel override olabilir, worker izolasyonu şart. |
| ORACLE_CLIENT_LIB_DIR | string, boş | Thick için agent'a kurulmuş dizin, dosya indirme yoktur. |
| PUBLISH_ARTIFACTS | boolean = false | İzinli arşiv Git push'u. |
| ARTIFACT_REPO_URL | string, boş | Özel çıktı deposu, Source ve Generator URL'lerinden farklı. |
| ARTIFACT_REF | string = main | Artifact branch'i, mevcut default/kurum kuralı kurulumda doğrulanır. |
| ARTIFACT_GIT_CREDENTIAL_ID | string, boş | Yalnız artifact repo'ya yazma yetkisi. |
| ARTIFACT_DESTINATION_APPROVED | boolean = false | Kurumsal verinin bu hedefe aktarımı için job yöneticisi tarafından verilen izin, key sahibi olmak tek başına izin değildir. |

Normal build kullanıcılarının repo URL/credential kombinasyonunu keyfi host'a çevirebildiği güvensiz iş kurulmaz. Güvenilir job kurulumunda `allowedSourceHosts` ve `allowedArtifactRepositories` allowlist'leri tanımlanır, build parametresiyle değiştirilemez. Bu değerler source-profile JSON'unun alanı değildir. Örnek/test job'da yalnız `.invalid` ve geçici yerel Git fixture'ları yetkilidir. Registry yönetimi güvenilir Jenkins yöneticisine aittir. `PUBLISH_ARTIFACTS=true` tek başına allowlist/private erişim politikasını atlayamaz.

## Target Registry

`schemas/targets.schema.json` ve `examples/targets.example.json` esas alınır. Her tanım id/name/enabled, Oracle endpoint, driver mode ve schema mapping/credential ID içerir. Port pozitif, service_name ile sid tam biri, ID benzersiz, schema mapping duplicate yok, enabled hedef bulunmaması INPUT_ERROR. Yeni enabled tanım eklendiğinde `ALL` otomatik kapsar.

Bir target birden fazla schema taşır, schema başına ayrı credential olabilir. Kullanıcı adı/şifre registry'de değil Credentials içindedir. Python'a hedefin gerçek DSN/user/password'u yalnız worker process environment veya izinleri sınırlandırılmış geçici dosya ile verilir. Dosya/console/manifest içine serialize edilmez. Credentials binding'in log maskelemesi bir güvenlik sınırı değildir, Groovy string interpolation'da sır kullanma (K03).

## Pipeline Aşamaları

1. Güvenilir Generator kodunu checkout, dependency lock/wheelhouse kontrolü.
2. Managed file ve parametreleri doğrula, endpoint/credential/publisher allowlist kontrolü.
3. Source ref'i sabitle ve güvenli checkout/blob okuyucu ile source snapshot oluştur.
4. Aktif/seçili target listesini hazırla, bilinmeyen ID'de fail, sessiz ALL yok.
5. Target'ları en fazla MAX_PARALLEL_TARGETS büyüklüğünde batch'lere ayır. Her target closure yalnız kendi immutable config kopyasını kullansın.
6. Branch içinde target ve schema credential scope'u, tek worker, timeout. `env.TARGET_*` ortak global değişkeniyle paralel branch'leri birbirine karıştırma.
7. Worker sonucu ne olursa olsun diagnostic/result JSON'u atomik yaz. `failFast=false`, ayrı target'lar sürsün.
8. Aggregate JSON/HTML hazırla, hash ve link kontrolü, ham sırlar ve gerçek bağlantı yapılandırmaları arşivlenmez.
9. `post/always` içinde rapor/dosyaları arşivle. HTML Publisher varsa publish, yoksa normal artifact linkleri. Hata çıkan koşuda da diagnostic kaybolmasın.
10. Yetkili publication ayrı aşama: payload doğrula, private/kurum allowlist kontrolü, commit/push retry. Yayınlama başarısı ve plan durumu ayrı.

İlk ürün GitHub Actions iş akışı eklemez, mevcut kurumsal Jenkins esas alınır. Eklenti eksikliği varsa core pipeline testleri devam eder, canlı kurulum `ENVIRONMENT_BLOCKED` raporlanır. Config File Provider kurumsal managed JSON için seçilmiştir, `readJSON`/`configFileProvider`/`withCredentials`/Git step gereksinimleri kurulum kontrol listesine yazılır. Dinamik target UI için Active Choices gibi ilave eklenti şartı yoktur.

## Exit Code Ve Build Durumu

| Code | Anlam | Jenkins |
|---|---|---|
| 0 | Seçili tüm target'lar tam karşılaştırılmış, READY, NO_CHANGE veya yalnız INFORMATIONAL farklardan oluşan NO_ACTION, blocking/review yok | SUCCESS |
| 10 | Farklar var, review/unsupported/policy-held işlem nedeniyle tam migration üretilemedi | UNSTABLE |
| 20 | En az bir target error/inconsistent/incomplete, diğer sonuçlar korunur | UNSTABLE |
| 30 | Geçersiz config/source scope/ref/parse-global sorun, plan güvenilir değil | FAILURE |
| 40 | Artifact integrity/security ihlali veya zorunlu publication başarısız | FAILURE |

Öncelik 40 > 30 > 20 > 10 > 0. Başarı/no-change sadece gerçek sonuçlardan türetilir. Connection başarısız target'ı try/catch sonrası 0'a çevirmek yoktur.

## Güvenli Erişim

SSH için doğrulanmış known_hosts, `StrictHostKeyChecking=no` yoktur. HTTPS Git kullanımında key URL'ye gömülmez, provider credential binding/askpass kullanılır. Credentials job trusted code dışında PR build'lerine açılmaz. Hedef profilinde yazma yetkili user kullanıldığını saptarsan otomatik hak düşürme/grant yapma, DBA kurulum koşulu olarak raporla.

Private GitHub kullanımı kullanıcı tarafından belirtilmiştir, bu, kurumun dışa veri aktarım iznini kanıtlamaz. Varsayılan publication kapalı ve Jenkins arşivi açıktır. Artifact Git adresi daha sonra Bitbucket'a değiştirilebilir, kod hosta sabitlenmez. Key veya token hiçbir belge/sohbette istenmez.


## Statik karşılaştırmanın süre ve önbellek ölçümü

Karşılaştırma Python/ANTLR ile deterministiktir, LLM veya AI servisi çağrılmaz.
Oracle metadata okuması, ayrıştırma, planlama ve DDL doğrulaması ayrı işlerdir.
Collector receipt içindeki `phase_timings_seconds`, katalog sorgusu, DDL okuma,
grammar, zenginleştirme ve yan metadata sürelerini taşır, canonical snapshot'a
süre eklenmez. Geçmiş koşuda ayrılmamış aşamaların süreleri tahmin edilmez.

Normal Pipeline `GENERATOR_PARSER_CACHE_DIR=.runtime/parser-cache` kullanır.
Anahtar tam SQL byte SHA'sı, varsayılan şema, metadata bayrağı ve parser artifact
SHA'sını içerir. Yalnız tam ve tipleri doğrulanmış başarılı parser cevabı saklanır,
hata, timeout veya bozuk kayıt yeniden ayrıştırılır. Önbellek boyut sınırlıdır.
Oracle katalog ve GET_DDL her canlı koşuda yeniden okunur, hedef snapshot'ı
önbellekten alınmaz. İlk dolum soğuktur. `.runtime` Git'e ve rapor arşivine girmez.

Kayıtlı metadata yeniden karşılaştırması canlı capture yerine gösterilmez:
kaynak commit'i, özgün metadata zamanı, yeniden hesaplama zamanı ve sıfır yeni
Oracle bağlantısı receipt'te tutulur. Yeniden hesaplama süresi eski canlı koşunun
süresini değiştirmez. Doğrulanmış yerel paket Jenkins'e alındığında kurulu wheel
ve parser fingerprint'i planla aynı olmak zorundadır, normal günlük akış daha
sonra geri yüklenir. Üretilen SQL yalnız Jenkins arşivinde tutulur ve uygulanmaz.

Parser/generator fingerprint dosyaları göreli POSIX adlarının sırasıyla hashlenir,
Windows Path case-folding sırası kullanılmaz. Aynı adlar ve aynı byte'lar için
Windows ile Linux kimliği aynıdır. Dosya kapsamı ve byte doğrulaması korunur.


## 7 Kasım 2026 Standart Rapor

Author: Mehmet KARACAN
Date: 2026-11-07

Günlük SKY işinde onaylanan Şema Karşılaştırma Raporu kullanılır. Saat
Europe/Istanbul 08.00 ve tek alıcı mkaracan@innova.com.tr olarak korunur.
Kurulu rapor paketi ac3e8d08061988b38beda60f90d705c26465d178896b10e9bf204ff0f53d9dd9.
#88 kurulum kontrolü ve #89 kayıtlı arşivle rapor kabulü başarılıdır.
GENERATOR_REPORT_SOURCE_ENVIRONMENT kaynak ortamını,
GENERATOR_REPORT_TARGET_ENVIRONMENT hedef ortamını belirtir. İkisi birlikte
tanımlanır. SKY işi UAT ve PROD kullanır. Şema adı karşılaştırma sonucundan
okunur. Bu alanlar plan ve bağlantı hesabını değiştirmez.

DDL dizini her çalışmanın output/runs/build-N/targets/hedef alanındadır.
Genel DDL butonu aynı build arşivindeki migration.sql veya partial-ready.sql
metin görünümüne gider. Nesne bazlı SQL objects altında tutulur. İnceleme
önerileri proposals, kaynak DDL metinleri source-ddl altındadır. Arşiv
saklama sınırı son 20 build olarak korunur. Mail veya kurulum denemeleri
yeni karşılaştırma sayılmaz ve önceki DDL bağlantısını son başarılı build
kısayoluyla değiştirmez. Geçerli SQL bağlantısı karşılaştırmanın sabit
numarasını taşır.


7 Kasım 2026 son konu kararı

Author: Mehmet KARACAN
Date: 2026-11-07

Mail konusu SKY | Şema Karşılaştırma | DURUM | Build #N biçimindedir.
DURUM Jenkins sonucundan, N çalışma numarasından alınır. Bu karar önceki
tireli konu biçiminin yerini alır. Kaydedilen değişiklik yeni çalışmalarda
geçerlidir. Başlamış Pipeline kendi konu tanımını korur.

## 9 Kasım 2026 Ayrıntılı HTML ve Tek Mail Bağlantısı

Author: Mehmet KARACAN
Date: 2026-11-09

Normal SKY işi kurulu a6496ce80c9f7dc60ca337f9d407d63453827960360fe3566410349cab1d36d8
rapor paketini kullanır. Yalnız rapor katmanı değişti. Motor, bağlantı
ayarları, bağımlılıklar ve özgün logo aynı kaldı. Saat Europe/Istanbul
08.00, TTBP kapsamı ve tek alıcı mkaracan@innova.com.tr korundu.
Konu SKY | Şema Karşılaştırma | DURUM | Build #N biçimindedir.

Mailde tek Raporu ve DDL Dosyalarını Aç bağlantısı bulunur. Bağlantı
kendi karşılaştırmasının sabit build arşivine gider. Hedef başına Genel
DDL düğmeleri epostada tekrarlanmaz. Genel ve nesne bazlı DDL bağlantıları
HTML raporunda bulunur. Ayrıntılı rapor kaynak ve hedef alanlarını yan
yana gösterir. Eski karşılaştırma arşivleri değiştirilmez.

Jenkins 93 kurulum kontrolü SUCCESS. Jenkins 94 kayıtlı 91 sonucu ile
rapor kabulü SUCCESS. Bu kontroller yeni Oracle karşılaştırması veya
mail gönderimi yapmadı. 206 izole paket testi geçti. Sonraki normal
karşılaştırmalar yeni raporu ve tek bağlantılı epostayı kullanır.
## 9 Kasım 2026 Schema Compare Adlandırması

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcı 95 mailinin ulaştığını doğruladıktan sonra ürün adını
Schema Compare olarak belirledi. Normal Pipeline konusu SKY | Schema
Compare | durum | Build #numara, başlık Schema Compare Raporu olur.
Paket 60377c6ae668c812fa78c60beb412c369eaf0f6714e4210d1ccbb65e1dac5acb.
96 ENVIRONMENT_CHECK SUCCESS. Python 3.12.15 ve sıfır Oracle bağlantısı
doğrulandı. Bu kurulumda yeni karşılaştırma ve mail yoktur.
Mail alıcısı yalnız mkaracan@innova.com.tr, günlük saat 08.00 olarak kalır.
Normal Pipeline kayıttan sonra yeniden okunup aynı bulundu. Kanıt
.local/schema-compare-brand-20261109 altında bulunur.

### 9 Kasım 2026 Hedef Toplama Performans Paketi

Kurulum 134 SUCCESS. Temel commit daf616f0ec215dcd8e76fdd42647227ff9336269.
Release 3bd63d437446f705b21ac728b6319e05928fbdcfdf48a290fab7900da095abd0.
Yama 7528ca3588c8f748bac1d2ffcc6a8766e29f62ebd73573d1b170e17d1b20a0e5.
346 ürün ve 8 yardımcı dosyanın hash değeri doğrulandı. Python 3.12.15,
fastjsonschema 2.21.2 ve önceki bağımlılık hash kilitleri korunur.

Jenkins bütün SQL ve HTML çıktılarını arşivlemeyi sürdürür. DDL üretim
makbuzu ve bundle manifestler Jenkins fingerprint kaydı alır. Her SQL
ve HTML dosyasının SHA256 değeri bundle manifestte doğrulanır. Her dosya
için ayrı Jenkins kullanım izi kaydı oluşturulmaz.

137 canlı tekrarında toplam 287,179 saniye, hedef toplama 99,630 saniye,
2120 DDL ve sıfır eksik DDL vardır. 136 ilk sürüm koşusu 310,443 saniyedir.
Beş dakika kabulü aynı kaynakla doğrulanmış önbellek içindir. Hedef Oracle
metadata her seferinde yeniden okunur. SQL veya veri uygulaması yapılmaz.
138 kanıtında 2416 SQL dosyası eski 120 ile plan kimliği yorumları dışında
aynıdır. Tam test 1483 passed, wheel içinden 117 ve 15 passed.

136 ve 137 test alıcısı yalnız mkaracan@innova.com.tr. Son normal tanım
hazırlanan pipeline ile birebir doğrulandı. İş etkin, TZ=Europe/Istanbul
ve 0 8 * * * zamanlaması, Innova-SKY@innova.com.tr alıcısı korunur.
Yeni branch, commit ve push bu görevde yapılmadı.

9 Kasım 2026 ana dal tesliminde performans değişiklikleri origin/main
hedefine yeni branch açılmadan gönderilir. Jenkins paketi doğrudan son
commit'ten oluşturulur ve kurulu dosyalar commit byte değerleriyle doğrulanır.
Bu teslim yeni karşılaştırma veya mail gönderimi başlatmaz. Sabah işi
etkin, Europe/Istanbul 08.00 ve Innova-SKY@innova.com.tr olarak kalır.
Kurulum makbuzu yerel .local/push-perf-20261109/completion-receipt.json
altında tutulur ve Git'e gönderilmez.
