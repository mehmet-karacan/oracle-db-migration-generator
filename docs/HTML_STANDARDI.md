# HTML Rapor Standardı

## Sabit Referans

Yeni tasarım icat edilmez. Yüklenen Analyzer'da `workflow.py` schema_version≥2 veya jenkins_artifact tesliminde `build_innova_mail_view`/`render_innova_view` kullanıyor. Bu nedenle ana referans **innova-db-report/1.0**, `templates/innova_v1/report_email.html.j2` ve `assets/innova-logo-approved.png` dosyalarıdır. V5'in koyu başlığı/başka paleti kullanılmaz. DDL Sync'in `templates/mail_report.html` dosyası aynı ürün ailesinin ikincil referansıdır.

`reference-ui/` paketinde asıl şablon, logo, hash kaydı ve eski ürünün sentetik render'ı bulunur. Buradaki 'YZ Destekli' gibi eski ürün ifadeleri tasarım kanıtıdır; Generator çıktısına otomatik taşınmaz. Koşu title'ı **Oracle Migration Artifact Kataloğu**, e-posta title'ı **Oracle DDL Migration Raporu** olur; target ayrıntısı Generator adını taşır. Model adı, AI değerlendirme rozeti ve yorumlayıcı uydurulmaz.

## Görsel Kimlik

ODMG-RPT-UPDATE-001 onaylı referansları web için 1.100 px, e-posta için 820 px shell kullanır; beyaz içerik, #EBF0F4 dış zemin, #F3F6F8 açık alanlar, #111B2D/#253142 başlık/gövde, #68778B ikincil metin, #CF1838 sınırlı kurumsal vurgu. Aptos/Calibri/Segoe UI/Arial fallback zinciri. İnnova logosu değişmeden ve oranı korunarak kullanılır. Font dosyası paketlenmez; harici CDN/font isteği yoktur.

Özet KPI şeridi, sol ince vurgu çizgili bölüm başlıkları, metadata tablosu ve satır bazlı durum badge'leri korunur. Risk rengi yalnız küçük vurgu; tüm sayfayı sarı/kırmızı boyama yoktur. İçerik yoğun diye yazı 9px'e düşürülmez.

## Rapor İçeriği

`index.html`: kaynak SHA ve kapsam, target sayısı, karşılaştırılan/başarısız/eksik hedefler, üretilen READY SQL sayısı, inceleme/blok sayısı, zaman ve build linki. Durumlar metinle de görünür; sadece renk yoktur.

Her target'ın `index.html` sayfası: source/target yönü, schema listesi, fark ve üretim özeti, metadata kapsamı, dependency/risk uyarıları, sınırlı DDL önizleme, tam dosya ve JSON linkleri, validation seviyesi. `Üretildi · Veritabanına uygulanmadı` ifadesi görünürdür.

## Kesin Boyut Sınırları

- Target sayfasında ilk **5** önemli değişiklik; önce BLOCKED/REVIEW, sonra risk, sonra stabil object ID.
- Her SQL önizlemesi en çok **30 satır veya 2.048 karakter**, hangisi önce dolarsa. HTML escaping sonrasında sayfa bütçesi ayrıca ölçülür.
- Tam PL/SQL uzunluğu SQL dosyasında korunur; HTML içine `display:none`, JS string veya JSON blob olarak bile gömülmez.
- Bütün değişiklikler nesne metadata listesinde erişilebilir; sayfa başına **100** satır. İlk beş SQL önizlemesinin dışında kalan farklar kaybolmaz.
- Ana target listesi sayfa başına **50** kayıt; `index.html` giriş noktası kalır, devam sayfalarına açık link verir. N target veri modelinde sabit sınıra dönüşmez.
- Web HTML dosyası en çok **200 KiB**. Bütçe dolarsa SQL önizleme azaltılır, truncation sayısı ve tam liste bağlantısı görünür tutulur. Özet toplamları değişmez.

No-change, connection-error, partial-metadata ve all-blocked durumlarının gerçek boş/uyarı ekranları vardır. Hatalı target '0 fark' kartı olarak çizilmez.

## Jenkins Ve İndirilmiş Rapor

Jenkins artifact sayfalarında inline style/data-image engeli olabilir (K04). Bu yüzden web çıktısı için CSS `assets/report.css`, logo `assets/innova-logo.png` olarak göreli dosyalarla paketlenir; aynı görsel token'lar korunur. JavaScript gerekmez. HTML Publisher bulunmazsa standart Jenkins artifact linki çalışır. İndirme, CSS/logo/SQL/JSON içeren bundle ZIP'tir; yalnız HTML indirilirse bağımlı dosyaların gerektiği anlaşılır.

Generator'da SMTP gönderimi yoktur. E-posta aynı koşu view model'inden inline CSS + CID logo ile **ayrı** statik çıktı olarak üretilir; CID adresi web HTML'ine taşınmaz. Jenkins global CSP'yi gevşetmek, script-src unsafe-inline veya güvenliği kapatmak çözüm olarak uygulanmaz. Admin'in Resource Root URL ayarı ayrı ortam konusudur.

## Güvenlik Ve Kanıt

Jinja2 StrictUndefined + autoescape. SQL/nesne adı/comment/message trusted HTML değildir. Göreli link traversal engellenir. Dış linkler yalnız izinli host/protokol; token query parametresi veya credential linki yoktur. SQL ve JSON artifact bağlantıları tam revision/plan ID ile ilişkilidir; 'latest' linki kanıt yerine geçmez.

Testler: 390/820/1440 px ekran, 200 karakter identifier, Türkçe, `<script>` içeren comment, 5.000 satır body, 51 target, 101 fark, eksik CSS/logo ve broken link. Tarayıcı screenshot karşılaştırmasında aile standardı referans alınır; yeni ürün içeriği farklı olduğu için ham piksel eşitliği beklenmez. Logo, palette, shell, tipografi ve bölüm düzeni ölçülür.


## ODMG-RPT-UPDATE-001 uygulaması

Onaylı ZIP referanslarının özgün byte/hash kayıtları output/report-update-original altında korunur.
Web CSS referansın token ve yerleşimini kullanır; harici CSS/logo paketlenir. Mailde MSO 820 px
wrapper, inline hücre stilleri ve cid:innova-logo vardır. Bağımsız preview aynı onaylı PNG'yi gömer.
Web 50 target / target ayrıntısı 100 işlem sayfalar; HTML bütçesi 200 KiB.
Mail 5 kritik hedef / öncelik sırasındaki ilk 5 benzersiz nesneyle sınırlı;
KPI bütün hedefler üzerinden hesaplanır. Başlangıç/bitiş zamanı farkı çalışma
süresi olarak gösterilir; eksik, hatalı veya negatif zaman farkı Bilinmiyor kalır.
Bilinmeyen fark null kalır, toplam bilinen alt toplam + ? olarak görünür. SQL mailde yer almaz.
Sayılar sunumda Türkçe binlik ayraçlıdır; JSON sayıları ve SQL byte'ları değişmez.
Genel mailde nesne satırının İşlem hücresi yalnız işlem türlerini gösterir;
nesne başına `1 işlem / 1 hedef` gibi tekrar sayıları gösterilmez.
Nesne / Fark, Hedef, İşlem, Sonuç sütunlarına sırasıyla %60/%12/%12/%16
genişlik ayrılır. E-posta uyumluluğu için HTML width attribute ve inline CSS
birlikte kullanılır; küçük ekranda uzun tanımlayıcıların kaydırılması korunur.
Onaylı 3305×630 PNG yeniden çizilmez; e-posta img genişlik/yükseklik attribute'ları
156×30'dur. Yalnız height:auto'ya güvenilmez; mail istemcilerinde doğal piksel/DPI
yüksekliğinin kullanılıp logonun dikey gerilmesi önlenir.
Bağımlılık gerekçeleri ilgili şema, nesne, tür ve gerektiğinde kolonları adlandırır.
Eksik tablo, hazır olmayan işlem, anahtar yokluğu, görünürlük belirsizliği ve ad
alanı çakışması kendi kanıtıyla açıklanır; doğrulanamayan nesne yok sayılmaz.
Yayın linki açık host allowlist + current run ID + immutable SHA + erişim kanıtı ister.
Jenkins fallback ayrıca mevcut run.build_url altındaki sayısal build artifact'i olmalıdır.
# 20 Ekim 2026 görünür nesne ve ortam etiketleri

Görünen hedef adı registry'deki `name` alanıdır (`PROD`); şema ayrıca gösterilir
(`TTBP`). Teknik target ID gruplama ve göreli arşiv yollarında kalır. Planı
üretilemeyen hedefte ad/şema uydurulmaz; fark sayısı bilinmiyor diye gösterilir.
Hata kodları makine kaydında ve teknik kanıt bölümünde korunur.

COMMENT/GRANT kayıtlarının iç `S_<hash>` kimliği nesne adı olarak gösterilmez.
Bilinen bağlı nesne ve varsa kolon, optional `object.display_name` ile etiketlenir;
bilinmeyen bağlı nesne açıkça belirtilir. İç kimlik, operation ID ve SQL gövdesi
korunur. Ek display alanı plan ID'sini ve SQL plan başlık hash'lerini değiştirebilir.
Gerçek 64 hexadecimal veya `S_` + 64 hexadecimal adlı teknik nesneler
`exclude_system_generated` politikasıyla karşılaştırmadan dışlanır; bağlı
index/yorum/grant da aynı politikayı izler. Ham envanter ve dışlama kanıtı korunur.

## 21 Ekim 2026 anlaşılır durum ve nedenler

Genel mail ve web özetinde BLOCKED, REVIEW_REQUIRED, COMMENT veya [TABLE]
gibi iç etiketler gösterilmez. Kullanıcı karşılıkları DDL üretilemedi, İnceleme
gerekli, Açıklama ve Tablo'dur. Üretilemeyen DDL sayısı gizlenmez veya sıfırlanmaz.
Durumun altında küçük yazıyla kısa, nesneye özgü neden gösterilir. Mailde neden
satırı dört sütunun tamamını kaplar; dar Sonuç hücresinde kelimelere bölünmez.
Aynı bağlı
nesneye ait tekrarlar tek açıklamada birleştirilir; asıl eksik bilgi mevcutsa
genel hazır değil ifadesi yerine o bilgi yazılır. Belirsizlik yokluk diye sunulmaz.
Operasyonun tam teknik gerekçesi hedef raporunda açılır teknik ayrıntılarda kalır.
Kanıtlı plan kararları, sayılar, SQL ve karşılaştırma kapsamı sunumla değiştirilmez.
Salt sunum yenilemesi doğrulanmış arşivden yapılabilir; JSON/SQL byte'ları korunur,
yenilenen HTML dosyalarının manifest hash'leri tekrar doğrulanır. Yeni Oracle
bağlantısı veya yeni karşılaştırma yapılmadığı ve kullanılan eski build açıkça yazılır.

21 Ekim ek kullanıcı düzeltmesi: ana başlık altında Karşılaştırma süresi dakika
ve saniye olarak yer alır. Sunum yenilendiyse Rapor yenileme süresi ayrı adla
gösterilir. comparison-timing.json, özgün koşunun zamanlarını ve kaynak SHA'sını
taşır; yeni run.json'un gerçek yenileme zamanları değiştirilmez. Tarihler TSİ
(UTC+3) gösterilir. 75 dakika 8,869 saniye kullanıcıya 75 dk 9 sn yuvarlanır.
Bulunan fark, tamamlanmış hedefte doğrulanmış toplam; kısmi hedefte planın
UNKNOWN dışındaki fark kayıtlarıdır. UNKNOWN kayıtlar bu sayıya eklenmez ve
ayrı sayılır. Eksik kapsamda sayı alt sınırdır; ek fark bulunabileceği yazılır.
Hiçbir hedefin sonucu alınamadıysa Sonuç alınamadı gösterilir, sıfır uydurulmaz.
