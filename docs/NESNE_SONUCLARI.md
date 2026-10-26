# Nesne ve alan farkları

24 Ekim kullanıcı isteğiyle mevcut React/shadcn ailesine nesne odaklı sonuç
görünümü eklendi. Schema Compare Platform salt okunur incelendi, bileşen,
frontend karşılaştırıcı veya framework kodu taşınmadı.

`ObjectResults` nesne türü, hedef, ad araması ve kaydırdıkça 25 nesnelik ek yükleme sağlar.
Seçilen nesne kalıcı sağ `ObjectComparisonPanel` içinde gösterilir, soldaki liste görünür kalır. Kolon, anahtar/kısıt,
indeks ve diğer alan farkları, ayrı sekmede ilgili işlem gerekçesi, kanıt
kimlikleri ve DDL bağlantısı bulunur. Alanlar 50, işlemler 10 kayıtta sayfalanır. İlk nesne otomatik seçilir, filtre/nesne değişiminde panel seçimle birlikte güncellenir. Kaynak ve hedef aynı nötr yüzeyde, İstenen Yapı ve Mevcut Yapı başlıklarıyla gösterilir. UNKNOWN metni uyarı rengini korur.
Hedef/proje/nesne değişince geciken yanıt önceki içeriği yeni seçime taşımaz.

## Doğruluk sözleşmesi

- Kaynak `after`, hedef `before` alanıdır. UI yeni fark hesaplamaz.
- KNOWN null → NULL, UNKNOWN → Bilinmiyor, ABSENT → Yok,
  NOT_APPLICABLE → Uygulanamaz. Gizlenmiş KNOWN tanım → Tanım arşivde.
  Gizleme, bilinmeyen/yok/uygulanamaz durumunu maskelemez.
- Sayılar kanonik fark kayıtları ve işlem kararlarından alınır. Doğrulanmış
  farklar ile UNKNOWN sayısı ayrı gösterilir. Kaydedilmeyen eşit alanlar veya
  tam snapshot varmış gibi sunulmaz. Liste, tam kaynak envanteri değildir.
- Nesne anahtarı kanonik kimlikten gelir. COMMENT/GRANT için mevcut
  `display_name` görünüm ve aramada kullanılır, sentetik adla kimlik değiştirilmez.
- İşlem bağlantıları `change_ids` üzerinden çözülür, nesne adı benzerliğinden
  ilişki üretilmez. İndeksler kendi nesne türünde de incelenebilir, kayıtlı
  parent/ilişki bilgisi yoksa bir tabloya ait oldukları tahmin edilmez.

## Veri ve güven sınırı

Kontrol katmanındaki `comparison-view/1.0`, kapalı Pydantic sözleşmesidir.
Yapısal kolon/kısıt/indeks/sequence alanları ve kısa metadata ifadeleri,
işlem gerekçeleri/kimlikleri ve SQL dosya yolu içerir. Ham tanım, PL/SQL
gövdesi ve SQL statement payload'ları taşınmaz. DDL, açıkça yerel seçilen işte
korunan API'den, gerçek Jenkins işinde aynı build'in yetkili `/*view*/`
bağlantısından açılır. Yol traversal ve protokol ekleme reddedilir.

UI endpoint'leri imzalı/yerel kimlik ve mevcut çalışma erişim kontrolünü
kullanır. Hedef mutlaka frozen profilin hedefleri arasındadır:

- `GET /api/runs/{id}/results/objects?target_id=...&object_type=TABLE&search=...&page=1&size=25`
- `GET /api/runs/{id}/results/objects/{key}?target_id=...&section=columns&page=1&size=50&operation_page=1`

Aktarım yoksa `available=false,total=null` döner, sıfır fark sonucu üretilmez.
Yerel worker'ın mevcut planı salt okunur projekte edilir. Harici Jenkins
sonucu için `tools/ui_import_result_view.py --root ... --run-id ...
--target-id ... --view ...` yerel operatör sınırıdır. Plan/target/source/run,
kayıt sayıları ve change ID kapanışı doğrulanır. Import idempotent/değişmezdir,
başka sonuçla üzerine yazılamaz. SQLite özel state ve audit kullanılır.

## #55 mevcut arşiv aktarımı

Servis hesabı olmadığı için plan yetkili tarayıcı oturumunda salt okunur
görüntülendi. `tools/ui_result_projection.mjs` DOM'daki plandan yalnız yapısal
metadata çıkardı, SQL gövdeleri DOM'da kaldı. Tarayıcı köprüsü dizileri 2.000
kayıtta sınırlandırdığından 500'lük parçalar alınıp kanonik sayılarla denetlendi.

Jenkins `/*view*/` belgesinin `document.characterSet` değeri windows-1254
çıktı. Generator'ın canonical JSON'u UTF-8/ensure_ascii=False ürettiğinden
gösterimde yanlış çözülen metadata string'leri gözlenen kodlama üzerinden
özgün UTF-8'e döndürüldü. `decodeProjectedView` veri içeriğine göre tahmin
yapmaz, UTF-8 belgede değişiklik yapmaz. Uygulama/SQL kararları değişmez.

Bu geliştirme turunda yapılan ilk bozuk kodlamalı metadata importu, tam
metadata yedeği ve audit ile yalnız beklenen eski SHA üzerinden bir defa
düzeltildi. Genel import değişmezlik kuralı gevşetilmedi. Kanıt ve yedekler
`output/object-results/` altında Git dışındadır.

#55: 3.112 nesne, 11.949 kayıt (11.946 doğrulanmış fark +3 UNKNOWN), 4.736
işlem. Aynı plan ID a5787df900c0eced4dcb269fd44a67b77530077c7140cac7e722dbf80b26dcff.
Yeni Oracle bağlantısı, karşılaştırma, SMTP veya Jenkins job değişikliği yok.
Gelecek harici koşuların otomatik metadata aktarımı servis hesabı kurulana
kadar manuel operatör adımıdır. Tam eşit alan envanteri/snapshot keşfi bu
sürümde desteklenmiş sayılmaz. Kurum ortak dağıtımı önceki NOT_RUN kapısıdır.

## 25 Ekim çalışma ekranı ve SQL saklama kararı

Özet yedi kompakt karttır, Toplam Süre ilk karttır. Tekrarlanan tam işlem tablosu
kaldırıldı, işlem/gerekçe/kanıtlar seçili nesnenin İşlemler ve DDL sekmesindedir.
Soldaki listede önceki/sonraki düğmesi yoktur. Yeni sayfa seçimi koruyarak alta
eklenir, çift scroll isteği engellenir. Ek yükleme hatası listeyi silmez ve aynı
sayfa tekrar denenir. Yeni hedef/filtreye gecikmiş eski yanıt taşınmaz.

Varlık alanları Nesne Var/Nesne Yok, nullable alanı NULL Kabul Eder/Etmez şeklinde
gösterilir. UNKNOWN, ABSENT, NULL ve NOT_APPLICABLE birbirine çevrilmez. Kapalı
code/quoted/literal/hint token dizileri yalnız metadata sunumunda okunabilir
metne çevrilir. Literal içeriği ve quoted token tırnakları korunur, rastgele JSON
veya serbest SQL yeniden biçimlendirilmez. Bu gösterim yeni fark hesaplamaz.

Kullanıcı yerel çalıştırılan işin SQL dosyalarının özel yerel run klasöründe
saklanmasını açıkça istedi. Yeni karşılaştırmada Çalıştırma Yeri seçilir:
Jenkins varsayılandır, Bu Bilgisayar yalnız yerel runtime sunuluyorsa açılır.
Yerel seçim kayıtlı Jenkins devrini açıkça atlar. Jenkins hatasında yerele
kendiliğinden geçiş yoktur. Motor, plan ve kaynak/hedef yönü aynıdır.

SqlViewer yerel dosyayı yetkili proje/run artifact API'sinden no-store okur.
Bellekteki görüntü özgün dosya metnidir, çift tırnaklar korunur. Jenkins işi
SQL'i uzak arşivde kalır. Servis okuma hesabı olmadığı için dialog arşiv
bağlantısını gösterir, cross-origin istek veya yerel SQL kopyası oluşturmaz.
Servis dispatch işi external kaydı olmadan da executor=JENKINS ile ayrılır,
archive_build_url hazırsa SQL/HTML Jenkins arşivine gider, değilse SQL linki
üretilmez. Yerel kuyruk Jenkins işini sahiplenmez. Artifact API Jenkins
çalışmasının yerel dosyalarını sunmaz. Her erişimde proje sınırı kontrol edilir.


## 25 Ekim nesne odaklı inceleme kabulü

Özet ve gruplar sunucuda kanonik kayıtların tamamından hesaplanır. Yeni
`difference_kind` filtresi liste sayfalamasından önce uygulanır, DDL kararından
bağımsızdır. `grouped=true` ayrıntısı her sayfada en çok25 tam yapı grubu verir,
kolon/kısıt bir sayfa sınırında bölünmez. JSON pointer escape'leri kimlikte
korunur. `group_sections`, `group_total`, `summary` yüklenmiş sayfadan bağımsız
sayılardır. Eski istemcilerin50 alanlık satır arayüzü korunur.

Yabancı/birincil/benzersiz/kontrol anahtarı etiketleri kayıtlı kind alanından
gösterilir. Nesne veya alt yapı yokluğu yalnız presence/exists kanıtından gelir,
MISSING bir özellik tüm kolonun yokluğu sayılmaz. UNKNOWN alan sayısı ayrıca
korunur. İlgili İşlemler ve SQL düğmesi `operation_group` filtresiyle change_ids
bağını kullanır, başka grubun işlemini ad benzerliğiyle seçmez. İşlem sayfalaması
bu filtreden sonra yapılır. Listede Fark ve DDL ayrı etiketlidir.

Özgün tanımlar için yetkili `GET /api/runs/{id}/results/objects/{key}/definitions`
yeni ve ayrı SQL-body arayüzüdür. Metadata import/ResultView sözleşmesi SQL
almayı sürdürmez. Yerel source/source-snapshot.json ve observations/<target>/
target-snapshot.json belge şeması, kanonik kimlik, plan kaynak/target semantik
digest'i ve blob SHA256'sı doğrulanır. Çok statement dosyasında kayıtlı byte
aralığı ve SHA kullanılabilir, satır/nesne adı üzerinden metin tahmini yapılmaz.
UTF8 özgün snapshot statement metni döner. Cache-Control:no-store ve mevcut
proje/run yetkisi zorunludur. Geçersiz dosya/path/hash durumunda SQL sunulmaz.

Her snapshot/dosya okuması64MiB, gösterilen tanım2MiB ve20.000 satırla sınırlıdır.
İki tanım varsa satır hizalama yalnız görüntüdür. 250.000 hücrelik çalışma
bütçesi aşılırsa değişen bloklar gösterilir. En çok300 satırlık sabit pencere ve
spacer ile DOM birikmez. Özgün karakter, literal, çift tırnak, CRLF/LF ve final
newline hizalama modelinde korunur. Özgün DDL sayfası eşit olsa bile yapısal
metadata kararına eşitlik yazılmaz. Tek tarafın tanımı varsa açık durumla ayrı
gösterilir, eksik taraf boş SQL sanılmaz. Jenkins tanımları yerelden okunmaz.

Doğrulama kanıtları output/structured-results altında. Gerçek#55
ANKET_EMAIL_GONDERIM örneği22 kayıt/2yabancı anahtar/2tamgrup verir. 320px
fixture görünümünde sayfa scrollWidth320 ve içerik kendi içinde kayar.
Yeni arayüz için tam WCAG/TMF sertifikasyonu veya5sn gerçek kullanıcı ölçümü
iddia edilmez. Mevcut UI standart hedefleri korunur.
