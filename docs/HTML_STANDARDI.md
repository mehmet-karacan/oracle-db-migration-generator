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

# HTML Rapor Standardı

## 23 Ekim 2026 kaynak esaslı Tarama Kapsamı

Genel web, hedef web ve mail KPI şeridinin altında Tarama Kapsamı gösterir.
Toplam ve tür dağılımı yalnız seçili kaynak şemalarındaki kapsam içi nesnelere
aittir, değişmeyen nesneler dahildir. Kaynak aynı şemada birden fazla hedef
için tekrar sayılmaz. COMMENT/GRANT metadata kayıtları nesne toplamını
artırmaz, paket tanımı/gövdesi ayrı nesnelerdir. Teknik nesne politikası
korunur. Hedef sayısı/fark/DDL sayısı bu toplamla karıştırılmaz.

Snapshot'tan üretilen scan-summary.json plan ID/source digest/target digest
ile bağlı ve bundle manifestiyle hash'lidir, karşılaştırma veya SQL kararını
değiştirmez. Eski arşivde özet yoksa Bilinmiyor gösterilir. Kaynak envanteri
eksikse sayı gözlenen alt sınırdır, hedef kapsamının eksikliği kaynak
envanteri hakkında eksiklik iddiası üretmez. Genel ve mail kaynak toplamını,
hedef raporu yalnız ilgili şemaların kaynak toplamını gösterir.

## Sabit Referans

Yeni tasarım icat edilmez. Yüklenen Analyzer'da `workflow.py` schema_version≥2 veya jenkins_artifact tesliminde `build_innova_mail_view`/`render_innova_view` kullanıyor. Bu nedenle ana referans **innova-db-report/1.0**, `templates/innova_v1/report_email.html.j2` ve `assets/innova-logo-approved.png` dosyalarıdır. V5'in koyu başlığı/başka paleti kullanılmaz. DDL Sync'in `templates/mail_report.html` dosyası aynı ürün ailesinin ikincil referansıdır.

`reference-ui/` paketinde asıl şablon, logo, hash kaydı ve eski ürünün sentetik render'ı bulunur. Buradaki 'YZ Destekli' gibi eski ürün ifadeleri tasarım kanıtıdır, Generator çıktısına otomatik taşınmaz. Koşu title'ı **Oracle Migration Artifact Kataloğu**, e-posta title'ı **Oracle DDL Migration Raporu** olur, target ayrıntısı Generator adını taşır. Model adı, AI değerlendirme rozeti ve yorumlayıcı uydurulmaz.

## Görsel Kimlik

ODMG-RPT-UPDATE-001 onaylı referansları web için 1.100 px, e-posta için 820 px shell kullanır, beyaz içerik, #EBF0F4 dış zemin, #F3F6F8 açık alanlar, #111B2D/#253142 başlık/gövde, #68778B ikincil metin, #CF1838 sınırlı kurumsal vurgu. Aptos/Calibri/Segoe UI/Arial fallback zinciri. İnnova logosu değişmeden ve oranı korunarak kullanılır. Font dosyası paketlenmez, harici CDN/font isteği yoktur.

Özet KPI şeridi, sol ince vurgu çizgili bölüm başlıkları, metadata tablosu ve satır bazlı durum badge'leri korunur. Risk rengi yalnız küçük vurgu, tüm sayfayı sarı/kırmızı boyama yoktur. İçerik yoğun diye yazı 9px'e düşürülmez.

## Rapor İçeriği

`index.html`: kaynak SHA ve kapsam, target sayısı, karşılaştırılan/başarısız/eksik hedefler, üretilen READY SQL sayısı, inceleme/blok sayısı, zaman ve build linki. Durumlar metinle de görünür, sadece renk yoktur.

Her target'ın `index.html` sayfası: source/target yönü, schema listesi, fark ve üretim özeti, metadata kapsamı, dependency/risk uyarıları, sınırlı DDL önizleme, tam dosya ve JSON linkleri, validation seviyesi. `Üretildi · Veritabanına uygulanmadı` ifadesi görünürdür.

## Kesin Boyut Sınırları

- Target sayfasında ilk **5** önemli değişiklik, önce BLOCKED/REVIEW, sonra risk, sonra stabil object ID.
- Her SQL önizlemesi en çok **30 satır veya 2.048 karakter**, hangisi önce dolarsa. HTML escaping sonrasında sayfa bütçesi ayrıca ölçülür.
- Tam PL/SQL uzunluğu SQL dosyasında korunur, HTML içine `display:none`, JS string veya JSON blob olarak bile gömülmez.
- Bütün değişiklikler nesne metadata listesinde erişilebilir, sayfa başına **100** satır. İlk beş SQL önizlemesinin dışında kalan farklar kaybolmaz.
- Ana target listesi sayfa başına **50** kayıt, `index.html` giriş noktası kalır, devam sayfalarına açık link verir. N target veri modelinde sabit sınıra dönüşmez.
- Web HTML dosyası en çok **200 KiB**. Bütçe dolarsa SQL önizleme azaltılır, truncation sayısı ve tam liste bağlantısı görünür tutulur. Özet toplamları değişmez.

No-change, connection-error, partial-metadata ve all-blocked durumlarının gerçek boş/uyarı ekranları vardır. Hatalı target '0 fark' kartı olarak çizilmez.

## Jenkins Ve İndirilmiş Rapor

Jenkins artifact sayfalarında inline style/data-image engeli olabilir (K04). Bu yüzden web çıktısı için CSS `assets/report.css`, logo `assets/innova-logo.png` olarak göreli dosyalarla paketlenir, aynı görsel token'lar korunur. JavaScript gerekmez. HTML Publisher bulunmazsa standart Jenkins artifact linki çalışır. İndirme, CSS/logo/SQL/JSON içeren bundle ZIP'tir, yalnız HTML indirilirse bağımlı dosyaların gerektiği anlaşılır.

Generator'da SMTP gönderimi yoktur. E-posta aynı koşu view model'inden inline CSS + CID logo ile **ayrı** statik çıktı olarak üretilir, CID adresi web HTML'ine taşınmaz. Jenkins global CSP'yi gevşetmek, script-src unsafe-inline veya güvenliği kapatmak çözüm olarak uygulanmaz. Admin'in Resource Root URL ayarı ayrı ortam konusudur.

## Güvenlik Ve Kanıt

Jinja2 StrictUndefined + autoescape. SQL/nesne adı/comment/message trusted HTML değildir. Göreli link traversal engellenir. Dış linkler yalnız izinli host/protokol, token query parametresi veya credential linki yoktur. SQL ve JSON artifact bağlantıları tam revision/plan ID ile ilişkilidir, 'latest' linki kanıt yerine geçmez.

Testler: 390/820/1440 px ekran, 200 karakter identifier, Türkçe, `<script>` içeren comment, 5.000 satır body, 51 target, 101 fark, eksik CSS/logo ve broken link. Tarayıcı screenshot karşılaştırmasında aile standardı referans alınır, yeni ürün içeriği farklı olduğu için ham piksel eşitliği beklenmez. Logo, palette, shell, tipografi ve bölüm düzeni ölçülür.


## ODMG-RPT-UPDATE-001 uygulaması

Onaylı ZIP referanslarının özgün byte/hash kayıtları output/report-update-original altında korunur.
Web CSS referansın token ve yerleşimini kullanır, harici CSS/logo paketlenir. Mailde MSO 820 px
wrapper, inline hücre stilleri ve cid:innova-logo vardır. Bağımsız preview aynı onaylı PNG'yi gömer.
Web 50 target / target ayrıntısı 100 işlem sayfalar, HTML bütçesi 200 KiB.
Mail 5 kritik hedef / öncelik sırasındaki ilk 5 benzersiz nesneyle sınırlı,
KPI bütün hedefler üzerinden hesaplanır. Başlangıç/bitiş zamanı farkı çalışma
süresi olarak gösterilir, eksik, hatalı veya negatif zaman farkı Bilinmiyor kalır.
Bilinmeyen fark null kalır, toplam bilinen alt toplam + ? olarak görünür. SQL mailde yer almaz.
Sayılar sunumda Türkçe binlik ayraçlıdır, JSON sayıları ve SQL byte'ları değişmez.
Genel mailde nesne satırının İşlem hücresi yalnız işlem türlerini gösterir,
nesne başına `1 işlem / 1 hedef` gibi tekrar sayıları gösterilmez.
Nesne / Fark, Hedef, İşlem, Sonuç sütunlarına sırasıyla %60/%12/%12/%16
genişlik ayrılır. E-posta uyumluluğu için HTML width attribute ve inline CSS
birlikte kullanılır, küçük ekranda uzun tanımlayıcıların kaydırılması korunur.
Onaylı 3305×630 PNG yeniden çizilmez, e-posta img genişlik/yükseklik attribute'ları
156×30'dur. Yalnız height:auto'ya güvenilmez, mail istemcilerinde doğal piksel/DPI
yüksekliğinin kullanılıp logonun dikey gerilmesi önlenir.
Bağımlılık gerekçeleri ilgili şema, nesne, tür ve gerektiğinde kolonları adlandırır.
Eksik tablo, hazır olmayan işlem, anahtar yokluğu, görünürlük belirsizliği ve ad
alanı çakışması kendi kanıtıyla açıklanır, doğrulanamayan nesne yok sayılmaz.
Yayın linki açık host allowlist + current run ID + immutable SHA + erişim kanıtı ister.
Jenkins fallback ayrıca mevcut run.build_url altındaki sayısal build artifact'i olmalıdır.
# 20 Ekim 2026 görünür nesne ve ortam etiketleri

Görünen hedef adı registry'deki `name` alanıdır (`PROD`), şema ayrıca gösterilir
(`TTBP`). Teknik target ID gruplama ve göreli arşiv yollarında kalır. Planı
üretilemeyen hedefte ad/şema uydurulmaz, fark sayısı bilinmiyor diye gösterilir.
Hata kodları makine kaydında ve teknik kanıt bölümünde korunur.

COMMENT/GRANT kayıtlarının iç `S_<hash>` kimliği nesne adı olarak gösterilmez.
Bilinen bağlı nesne ve varsa kolon, optional `object.display_name` ile etiketlenir,
bilinmeyen bağlı nesne açıkça belirtilir. İç kimlik, operation ID ve SQL gövdesi
korunur. Ek display alanı plan ID'sini ve SQL plan başlık hash'lerini değiştirebilir.
Gerçek 64 hexadecimal veya `S_` + 64 hexadecimal adlı teknik nesneler
`exclude_system_generated` politikasıyla karşılaştırmadan dışlanır, bağlı
index/yorum/grant da aynı politikayı izler. Ham envanter ve dışlama kanıtı korunur.

## 21 Ekim 2026 anlaşılır durum ve nedenler

Genel mail ve web özetinde BLOCKED, REVIEW_REQUIRED, COMMENT veya [TABLE]
gibi iç etiketler gösterilmez. Kullanıcı karşılıkları DDL üretilemedi, İnceleme
gerekli, Açıklama ve Tablo'dur. Üretilemeyen DDL sayısı gizlenmez veya sıfırlanmaz.
Nesne adının altında küçük yazıyla kısa, nesneye özgü neden gösterilir. Mailde
neden yalnız Nesne / Fark hücresinde kalır, diğer sütunlara taşmaz. Metin en
fazla 150 karakterdir, özel tablo yapısı gibi bilinen nedenler kısa cümleyle
özetlenir. Tam gerekçe ayrıntılı raporda korunur.
Aynı bağlı
nesneye ait tekrarlar tek açıklamada birleştirilir, asıl eksik bilgi mevcutsa
genel hazır değil ifadesi yerine o bilgi yazılır. Belirsizlik yokluk diye sunulmaz.
Operasyonun tam teknik gerekçesi hedef raporunda açılır teknik ayrıntılarda kalır.
Kanıtlı plan kararları, sayılar, SQL ve karşılaştırma kapsamı sunumla değiştirilmez.
Salt sunum yenilemesi doğrulanmış arşivden yapılabilir, JSON/SQL byte'ları korunur,
yenilenen HTML dosyalarının manifest hash'leri tekrar doğrulanır. Yeni Oracle
bağlantısı veya yeni karşılaştırma yapılmadığı ve kullanılan eski build açıkça yazılır.

21 Ekim son süre yerleşimi: mail ve genel raporda yalnız Karşılaştırma süresi,
Kaynak ve İzlenebilirlik bölümünde küçük (11px), gri bir not olarak yer alır.
Üst bölümde süre kartı veya büyük süre değeri bulunmaz. Başlangıç, bitiş,
TSİ etiketi ve rapor yenileme süresi kullanıcı görünümünde gösterilmez.
comparison-timing.json özgün karşılaştırma zamanlarını ve kaynak SHA'sını,
run.json gerçek yenileme zamanlarını korur. Süre yenileme süresinden türetilmez.
75 dakika 8,869 saniye kullanıcıya75 dk9 sn yuvarlanır.
Bulunan fark, tamamlanmış hedefte doğrulanmış toplam, kısmi hedefte planın
UNKNOWN dışındaki fark kayıtlarıdır. UNKNOWN kayıtlar bu sayıya eklenmez ve
ayrı sayılır. Eksik kapsamda sayı alt sınırdır, ek fark bulunabileceği yazılır.
Hiçbir hedefin sonucu alınamadıysa Sonuç alınamadı gösterilir, sıfır uydurulmaz.

## 23 Ekim 2026 Jenkins dosya erişimi ve genel görünüm

Genel web başlığı Oracle Şema Karşılaştırma Raporu'dur, alt metin kaynak yapı,
hedef durumu ve DDL üretimini açıklar. Tek hedef kartı içerik genişliğini kullanır.
Kaynak toplamı ve tür sayaçları web'de harici CSS ile biçimlenir, Jenkins'in
artifact CSP/sandbox ayarı değiştirilmez. E-posta için inline stiller korunur.

Doğrulanmış Jenkins job/build bağlamında Genel DDL’i görüntüle bağlantısı aynı
sayısal build'in SQL artifact `/*view*/` yoluna gider. DDL dosyalarını indir,
aynı hedefin Jenkins dosya listesini açar, kullanıcı bütün dosyaları ZIP olarak
alabilir. Ana SQL'in nesne dosyalarını sırayla çağırdığı açıklanır. Offline
HTML kendi göreli SQL bağlantısını ve download niteliğini korur. Plan ve
manifest bağlantıları açılır Teknik dosyalar bölümündedir. Bu sunum adımı SQL
byte'larını ve plan kararlarını değiştirmez.

23 Ekim sonraki kullanıcı talimatı: karşılaştırma süresi genel web/mail
başlığının altında, sayaçlardan önce tek satırda gösterilir. Bu talimat önceki
alt gri not yerleşiminin yerini alır. Özgün karşılaştırma süresi korunur,
rapor yenileme süresi bu değere yazılmaz. Eksik/geçersiz özgün saatte
Ölçülemedi gösterilir. Saat/başlangıç/bitiş ve plan kararları değişmez.


## 7 Kasım 2026 Mobil Ve Koyu Eposta

Kaynak Şema ve Hedef Şema etiketleri birlikte kullanılır. Süre ikonunun
boşluğu tablo hücresiyle korunur. Görünen bütün ikonlar semantic renkli
varlıkları kullanır. Logo byte'ları değişmez, açık bir yüzeyde gösterilir.
Mobil özet iki sütun, detaylar alan etiketleriyle alt alta düzenlenir.

email_styles.html.j2 açık ve koyu renkleri birlikte tanımlar. color-scheme
ve supported-color-schemes light dark olur. prefers-color-scheme ve
Outlook veri özniteliği seçicileri aynı renkleri taşır. İstemciler arasındaki
farklar nedeniyle gerçek telefondaki sonuç ayrıca kontrol edilir.
WebKit yaklaşımı [resmi koyu tema belgesine](https://webkit.org/blog/8840/dark-mode-support-in-webkit/)
dayanır. SQL ve rapor sayıları bu sunumdan etkilenmez.


7 Kasım Outlook kabul düzeltmesi. Bölüm başlıklarının ikon boşluğu
email_heading.html.j2 içindeki sabit hücreyle korunur. Mobil son özet
kartı metric-final sınıfıyla tam satıra geçer. Eposta logosunda açık zemin
PNG piksellerinin içindedir. Asıl transparan logo değişmez. Gömülü önizleme
innova-logo-email.png kullanır. CID tüketicisi aynı PNG'yi innova-logo
kimliğine bağlar. Paket bu dosyayı assets/innova-logo-email.png olarak taşır.


7 Kasım sonraki Outlook kabulü önceki beş kartlı mobil görünümün yerini
alır. Hedef sayısı tek bağlam satırı, kalan dört ölçü gerçek iki sütunlu
HTML tablo olur. Özette display değiştiren mobil CSS bulunmaz. Kart
etiketleri aynı yüksekliktedir. Eposta logosu resmî beyaz SVG yollarının
koyu #17283F yüzeydeki PNG sunumudur. Özgün logo varlıkları korunur.
Resmî kaynak kopyası ve türev ilişkisi assets/email-logo-NOTICE.md içindedir.
Logo kontrolünde SVG renkleri yanında gerçek PNG harf pikseli de sınanır.


7 Kasım son kullanıcı kararı önceki logo türevi kullanımını kaldırır.
Kurumsal logo assets/innova-logo.png dosyasıdır ve değiştirilmeden kullanılır.
Başka renk veya zeminle yeniden rasterleştirilmez. Önizlemede gömülü görsel
özgün dosyayla byte düzeyinde aynı olmalıdır. CID tüketicisi de aynı özgün
PNG'yi innova-logo kimliğine bağlar. Önceki logo türevleri yalnız yerel
geçmişte tutulur ve rapor varlık paketine eklenmez.

Rapor başlığı Şema Karşılaştırma Raporu olur. Eposta üst alanında logo ve
başlık solda, kaynak ve hedef şema bilgileri ikonlarla sağda gösterilir.
Mobilde kapsam bilgisi başlığın altına iner. Aynı şema bilgileri başlık
altında ikinci kez yazılmaz. Sayısal özet ve özgün süre değişmez.


7 Kasım son Snapshot referansı sağ üst şema kutusunun yerini alır.
Eposta üst alanında özgün kurumsal logo ve referansta paylaşılan iki mesaj
alanı bulunur. Başlığın altındaki açıklama kaynak ve hedef şemalarını
rolleriyle birlikte adlandırır. Ayrı şema kartı bulunmaz. Hedef Ortam
sayısının ayrı özet satırı kaldırılır. Özet dört temel ölçüden oluşur.
Kaynak ve hedef sayıları iç veri modelinde korunur. Kurumsal logo dosyası
aynen kullanılır ve görünür açıklamalar doğal Türkçe olur.


7 Kasım 2026 son etiket ve logo zemini düzeni

Author: Mehmet KARACAN
Date: 2026-11-07

Nesne türleri, durumlar ve alan başlıklarında sözcük başları büyük olur.
Veri Tipi, Paket Tanımı, Sıra Numarası ve Bulunan Fark bu biçimi kullanır.
Açıklamalar doğal cümle biçimini korur. Teknik kimlikler ve SQL değişmez.
Kurumsal logo aynen kullanılır. Logo arkasındaki açık zemin ayrı 1 piksel
RGB görselidir. CSS arka planı ve klasik Outlook VML desteği bu zemini
taşır. Logo başka zemine rasterleştirilmez veya yeniden renklendirilmez.
Genel DDL butonu aynı Jenkins çalışmasının SQL arşiv görünümüne gider.
Bağlantısı olmayan yerel sonuç için Jenkins adresi oluşturulmaz.
Gerçek istemci görünümü ayrıca kontrol edilir. Yerel render bu kabulün
yerini almaz.


7 Kasım 2026 onaylanan görünüm Jenkins günlük işine alındı. #88 kurulum
ve #89 arşivle HTML kabulü başarılıdır. UAT ve PROD adları işin rapor
ortam alanlarından gelir. Kaynak ve hedef şema adları gerçek sonuçtan
okunur. Genel DDL bağlantısı aynı karşılaştırmanın sabit Jenkins build
arşivine gider. Dağıtım kanıtı yz/DEVIR.md içindeki aynı tarihli kayıttadır.

## 7 Kasım 2026 Ayrıntılı Rapor Düzeni

Author: Mehmet KARACAN
Date: 2026-11-07

Ana çalışma özeti ve hedef ayrıntıları aynı dört ölçüyü kullanır.
Üretilen DDL hazır işlemler ile dosyası bulunan önerilerin toplamıdır.
DDL Dosyası Eksik ölçüsü engelli karar sayısı değildir. Üretilen DDL
türleri doğrulanmış işlem toplamından hazırlanır. Kaynak ve hedef ortam
adları işin sunum ayarlarından, şema adları kayıtlı sonuçtan gelir.

Nesne listesinde aynı nesnenin açık sayfadaki işlemleri birleştirilir.
Soldaki dizinden seçilen nesne sağda açılır. Tür ve DDL dosyası filtreleri
yalnız açık sayfaya uygulanır. Nesne adı tarayıcının Ctrl+F aramasıyla
bulunur. Sınırlı sayfalama korunur. JavaScript veya Jenkins güvenlik
ayarı değişikliği gerekmez.

Değişim, öneri ve kaynak SQL dosyaları statik HTML görüntüleyicide açılır.
SQL metninin tamamı kaçış uygulanarak gösterilir. Büyük metin bölünür,
her sayfa en fazla 200 KiB olur. Özgün SQL indirme bağlantısı ayrıca
bulunur. SQL çalıştırılmaz. Eski arşivin planı ve dosyaları değişmez.

Açık ve koyu tema ile mobil CSS düzeni bulunur. Özgün kurumsal logo
aynı kalır, arkasında ayrı açık yüzey kullanılır. Yerel belge renderı
yazı ve varlık kontrolü sağlar. Gerçek tarayıcıdaki filtre, seçim ve
mobil görünüm kabulünün yerini almaz. Bu aşamada dağıtım yapılmadı.

## 9 Kasım 2026 Kaynak ve Hedef Alan Karşılaştırması

Author: Mehmet KARACAN
Date: 2026-11-09

Nesne ayrıntısında Özellik, Kaynak ve Hedef sütunları bulunur. Alanlar
kolon, kısıt veya nesne özelliği başlığıyla gösterilir. Planın after
değeri kaynak, before değeri hedeftir. Yeni fark hesaplanmaz ve SQL
kararı değiştirilmez. Bilgi Doğrulanamadı, Alan Bulunmuyor, NULL, Boş
Metin ve Hayır farklı durumlardır. Renk yanında durum metni de bulunur.

Sağ nesne paneli ilk üç alanı kısa gösterir. Kaynak ve Hedefi Karşılaştır
bağlantısı nesnenin bütün kayıtlı alanlarını açar. Tüm Kaynak ve Hedef
Farkları dizini işlem oluşturulmamış kayıtları da kapsar. Nesneler ad
tahminiyle birleştirilmez, kanonik kimlik ve açık change_ids bağları
kullanılır. İki taraf için bulunmayan özgün tanım uydurulmaz.

Uzun değerler 2.000 karakterlik parçalara ayrılır ve tüm parçalar aynı
fark kimliğiyle sıralı HTML sayfalarında korunur. Her sayfa en fazla
200 KiB olur. Özetin kısa gösterildiği açıkça belirtilir. İçerik HTML
kaçışıyla gösterilir ve baştaki boş satır korunur. Token biçimindeki
kayıtlı SQL alanları okunabilir sunulur, açıklama metni aynı biçime
benziyor diye dönüştürülmez. Özgün SQL dosyaları değiştirilmez.

Dar ekranda iki taraf aynı tabloda kalır ve yatay kaydırılır. CSS açık
ve koyu yüzey renkleri içerir. Bu çalışma yalnız yerel önizlemedir.
Gerçek tarayıcı ve mobil etkileşim kabulü ayrıca yapılır. Jenkins,
Oracle ve mail işlemi bu değişikliğin kapsamında değildir.

## 9 Kasım 2026 Epostada Tek Arşiv Bağlantısı

Author: Mehmet KARACAN
Date: 2026-11-09

Epostada aynı çalışma arşivine yönlendiren tek bağlantı bulunur.
Raporu ve DDL Dosyalarını Aç bağlantısı karşılaştırmanın sabit çalışma
numarasına bağlı genel raporunu açar. Üst bölümde hedef başına Genel DDL
bağlantıları tekrarlanmaz. Çok hedefli epostada da tek bağlantı kullanılır.
Nesne ve DDL indirme bağlantıları genel HTML raporunda bulunur.

Doğrulanmış arşiv bağlantısı olmayan yerel eposta için Jenkins URL'si
oluşturulmaz. Yayın veya bağlantı doğrulama açıklaması düz metin olarak
korunur. Özgün logo, renkler, özet kartlar ve DDL sayıları değişmez.
## 9 Kasım 2026 Ürün Adı

Author: Mehmet KARACAN
Date: 2026-11-09

Kullanıcının son adlandırma kararı Schema Compare olur. Eposta, ana
rapor ve HTML belge başlığı Schema Compare Raporu olarak yazılır.
Mail konusu SKY | Schema Compare | durum | Build #numara biçimindedir.
Türkçe açıklamalar ve kaynak hedef etiketleri çevrilmez. Özgün kurumsal
logo, renkler, düzen ve tek arşiv bağlantısı korunur. Geçmişte gönderilen
mailler ve geçmiş çalışma arşivleri yeniden yazılmaz.
