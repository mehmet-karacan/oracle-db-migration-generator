# UI kapsamı ve ekrandan yönetilecek ayarlar

**24 Ekim son kullanıcı kararı:** Üstte proje seçimi, tek ortak çalışma
yetkisi, kullanıcı/rol/model bilgisi gösterilmez. Aşağıdaki ilk taslakta yer
alan yönetici/operatör ayrımının yerine bu karar geçer. Mevcut SKY profili
servis hesabı bulunana kadar açık Jenkins tarayıcı aktarımı kullanır.

**24 Ekim uygulama güncellemesi:** Bu belge ilk kapsam envanteridir. UI/API,
Oracle kaynak adaptörü ve ayar aktarımı uygulandı. Güncel çalışan özellikler,
kurulum komutları ve canlı NOT_RUN sınırları
[UI çalıştırma ve dağıtım](UI_CALISTIRMA_VE_DAGITIM.md) belgesindedir.

Tarih: 24 Ekim 2026. Durum: kod incelemesine dayalı kapsam/ayar envanteri,
çalışan UI veya Oracle kaynak adaptörü teslimi değildir.

Kullanıcı Git ve doğrudan Oracle kaynağının ekrandan seçilmesini, bağlantı
bilgileriyle karşılaştırma başlatılmasını ve kodda sabit kalan uygun ayarların
ekrandan yönetilmesini istedi. UI kütüphanesi seçimini uygulayıcıya bıraktı,
bu kapsam için seçim shadcn/ui'dir. Önceki Ant Design önerisinin yerine geçer.

## Teknoloji ve görünüm

- React + TypeScript + Vite.
- shadcn/ui, Radix tabanlı bileşen ailesi ve Tailwind CSS tema değişkenleri.
- Sonuç tablosu için TanStack Table, sunucuda sayfalama/sıralama/filtreleme.
- Mevcut Python karşılaştırma motoru korunur. UI motoru yeniden yazmaz.
  Python API ve çalıştırıcı bağlantısı uygulama tasarımında tamamlanacaktır.
- Onaylı İnnova logo/renk ailesi ve Türkçe metinler korunur. Kaynak tasarım
  referansı mevcut kurumsal raporlardır, yönetim ekranı veri yoğun çalışmaya
  uygun geniş yerleşim kullanır.
- UI bileşenleri mevcut script'siz Jenkins HTML/mail artifact'lerine taşınmaz.
  Dış CSS, HTML boyut bütçesi, SQL/plan byte bütünlüğü kuralları korunur.

shadcn/ui'nin daha fazla birleştirme ve bakım sorumluluğu getirmesi kabul
edilen bir uygulayıcı tercihidir: bağlantı/test/çalışma/nesne ayrıntısı aynı
görsel dilde özelleştirilebilir, tablo davranışları açıkça ürünün kontrolünde
kalır. İkinci bir UI bileşen kütüphanesi eklenmez.

Kaynaklar:
[Vite kurulumu](https://ui.shadcn.com/docs/installation/vite),
[Radix tablo bileşimi](https://ui.shadcn.com/docs/components/radix/data-table),
[Tema](https://ui.shadcn.com/docs/theming).

## Ekran ve bileşen haritası

| Ekran / bölüm | Ürün bileşeni | shadcn karşılığı |
| --- | --- | --- |
| Genel yerleşim | `AppShell` | Sidebar, Breadcrumb, Separator |
| Yeni karşılaştırma | `ComparisonForm` | Field, Input, Select, Radio Group, Button |
| Kaynak seçimi | `SourceSelector` | Radio Group / Tabs, Git ve Oracle |
| Git profili | `GitSourceForm` | Combobox, Input, Field |
| Oracle bağlantısı | `OracleConnectionForm` | Input, Select, Dialog, Alert |
| Hedef seçimi | `TargetSelector` | Combobox, Checkbox, Badge |
| Kapsam ve gelişmiş ayarlar | `ComparisonScopeForm` | Accordion, Checkbox, Switch, Field |
| Çalışma takibi | `RunProgressPanel` | Progress, Badge, Alert, uygulamaya ait aşama listesi |
| Çalışma geçmişi | `RunHistoryTable` | Table + TanStack Table, Pagination |
| Fark/DDL listesi | `DifferenceTable` | Table + TanStack Table, Input, Select, Badge |
| Nesne ve SQL ayrıntısı | `ObjectDetailSheet` | Sheet, Tabs, Scroll Area |
| Bağlantı/profil yönetimi | `ConnectionRegistryPage` | Table, Dialog, Field |
| İşletim ayarları | `SettingsPage` | Tabs, Field, Switch, Alert |

Bu İngilizce ASCII adlar planlanan ürün bileşenleridir, mevcut kodda varmış
gibi sunulmaz. Kullanıcı alan adları ve durumlar Türkçedir. Aşama yüzdesi
yalnız ölçülebilen iş sayısından türetilir, bilinmeyen toplamda uydurma yüzde
veya kalan süre gösterilmez.

## Her karşılaştırmada seçilecekler

| Alan | Mevcut dayanak / gerçek eksik | UI davranışı |
| --- | --- | --- |
| Kaynak türü | Git kaynak okuyucusu var, Oracle source adaptörü yok | Git / Oracle seçimi, her biri gerçek backend akışını çalıştırır |
| Git deposu ve ref | `job-settings` source_url/source_ref, Git ref çözümleme var | Tanımlı depo, branch/tag/commit, erişimi test et |
| Git yerleşimi/kökleri | `SourceProfile.layout`, `schema_roots` | Profilden gelir, gelişmiş bölümde doğrulanmış kök seçimi |
| Oracle kaynak | Hedef metadata collector'u var, SOURCE kimlik/model desteği eklenmeli | Tanımlı bağlantı veya yeni bağlantı, erişilebilir şemaları seç |
| Hedefler | `TargetConfig` listesi var, Jenkins wrapper iki hedefe sabit | Tanımlı bir veya birden çok Oracle hedefi |
| Nesne kapsamı | object_types, excluded_object_types | Türkçe tür seçimi, gerçek karşılaştırma kapsamını baştan daraltır |
| Teknik nesne filtresi | exclude_system_generated | Açıklamalı kapsam seçimi, iki tarafa aynı uygulanır |
| Fiziksel özellikler | compare_physical_storage | Gelişmiş karşılaştırma ayarı |
| Bildirim | Jenkins tek alıcı gönderimi | Bildirim tercihi, mevcut izinli tek alıcı korunur |

Bir sonuç tablosunda yalnız satır gizlemek, yeniden karşılaştırma kapsamı
seçmek değildir. Sonuç arama/filtreleri planı ve DDL'yi değiştirmez. Kapsam
değişikliği yeni çalışma gerektirir.

## Bağlantı ve profil yönetimi

Bağlantı adı, ortam etiketi, host, port, Service Name veya SID, kullanıcı/
credential referansı, şema listesi ve etkinlik durumu yönetilir. Bağlantı testi
yalnız oturum açabilmeyi değil seçili şemaların metadata/DDL görünürlüğünü de
raporlar. Parola ayrı sır depolamasında tutulur, API yanıtı, çalışma ayar
kopyası, tarayıcı kalıcı depolaması ve artifact içine açık parola yazılmaz.
Jenkins mevcut Credentials referanslarını kullanmaya devam eder.

`tools/jenkins_run.py` içindeki `TARGET_OWNERS`, `SOURCE_CREDENTIALS`, sabit
aynı-endpoint kontrolü, `tools/jenkins_scope.py` içindeki TTBP/INNOVA_ODI seçim
listesi ve PROD ad ataması kayıtlı profil/bağlantı verisine taşınacak adaylardır.
Mevcut doğrulamalar körlemesine kaldırılmaz, yerine seçili bağlantı, şema,
credential ve yetki ilişkisini doğrulayan genel kontroller gelir. Yeni bağlantı
eklemek için kod veya Jenkins Pipeline düzenleme zorunluluğu kaldırılır.

## Yönetim ayarları

| Ayar | Bugünkü değer / yer | Tasarım kapsamı |
| --- | --- | --- |
| Metadata yakalama bütçesi | TargetConfig varsayılan900sn, schema30–7200sn | Bağlantı/profil bazında, mevcut sınırlar içinde |
| Oracle bağlantı ve çağrı süresi | connection.py:8sn /15000ms | Sınırlı yönetici ayarı, anlık çalışan oturuma uygulanmaz |
| Parser bütçeleri | adapter.py:30/120/240sn,24KiB/128KiB eşikleri | Gelişmiş işlem profili, sürelerin sonuç kapsamını etkileyebildiği belirtilir |
| Toplam iş bütçesi | Jenkins şablonu120dk | Çalıştırıcıya uygulanan ve doğrulanan işletim ayarı |
| Git yeniden denemeleri | #54 checkout'ta20tekrar gözlendi, ürün kontrolü açık değil | Uygulamaya ait sınırlı deneme sayısı/gecikme, global Jenkins ayarı değiştirilmez |
| Hazırlanmış kaynak cache'i | prepared_cache.py:4giriş /1GiB | Etkinlik ve sınırlı kapasite profili, kullanım/hit/miss görünümü |
| Parser response cache'i | response_cache.py:boyut/kayıt sabitleri | İleri işletim profili, bütünlük sınırları kullanıcıya kaldırılabilir seçenek olmaz |
| Zamanlama | Canlı Jenkins08:00 Europe/Istanbul | Saat/gün/saat dilimi, mevcut Jenkins zamanlayıcısına tek noktadan yansır |
| Saklama | Jenkins son20build/artifact | Doğrulanan saklama politikası, eski kayıt silme otomatik bu aşamada yapılmaz |
| Rapor önizlemesi | İlk5nesne,30satır/2048karakter | UI sayfalaması ayrı, mail/artifact mevcut üst sınırları korunur |
| Liste görünümü | Yeni UI | Sayfa boyutu, sütun görünürlüğü, sıralama ve filtre tercihleri |

Cache temizleme veya kapasite düşürme ayrı, kapsamı görünür bir işlem olur,
ayar kaydetme kullanıcı SQL/artifact dosyalarını silmez. Cache'in bugün dolunca
yeni store'u atladığı ve otomatik eviction yapmadığı açıkça gösterilir.

## Ayar modeli

Üç seviye: uygulama varsayılanları → kayıtlı karşılaştırma profili → çalışmaya
özel seçim. Sunucu etkili ayarları doğrular, izin dışı alanlar istemciden
gelse de uygulanmaz. Her çalışma sır içermeyen etkin ayar kopyası ve ayar
sürümüyle kaydedilir. Ayarı değiştirmek çalışan işi veya geçmiş planı değiştirmez.

Kaynak/parsing kapsamını veya parser bütçesini değiştiren ayarlar kaynak
hazırlama/cache kimliğine dahil edilir, eski PARTIAL sonucu yeni bütçeyle
üretilmiş gibi gösterilmez. Yalnız sunum tercihleri kanonik plana girmez.
Canlı Oracle kaynak snapshot'ı her yeni canlı çalışmada taze toplanır, Git
checkpoint'i Oracle kaynağına uygulanmaz.

Oracle source desteğinde Git commit uydurulmaz. Kaynak türü ve gerçek kaynak
kimliği snapshot/plan/run/cache/rapor sözleşmelerinde açık tutulur. Git commit
ile Oracle capture kimliği ayrı alanlardır. Kaynak bir kez gözlenip aynı run'ın
bütün hedeflerinde aynı kaynak snapshot'ı kullanılır.

## Ekrana açılmayacak davranışlar

Salt okuma, UNKNOWN bilgisinin korunması, kanıt/bundle bütünlüğü ve kaynak/
hedef yönü kullanıcı anahtarı değildir. Oracle'a SQL uygulama, otomatik drop,
sequence reset ve desteklenmeyen owner remap ayarı eklenmez. Bunlar kodda
unutulmuş kullanıcı tercihleri değil mevcut ürünün doğruluk sınırlarıdır.

Mevcut günlük TTBP/08:00, yalnız izinli alıcı ve Jenkins-only artifact politikası
bu envanter hazırlanırken değiştirilmedi. UI ayar kaydının gerçek zamanlayıcı ve
çalıştırıcıya aktarımı uygulanıp doğrulanmadan kaydedildi/uygulandı denmez.

## Kurum içi ortak kullanım

Kullanıcı 24 Ekim'de yerleşimi **kurum içi ortak uygulama** olarak seçti.
Bu tercih yerel tek kullanıcılı uygulama varsayımının yerine geçer.

- Kimlik doğrulama sunucuda yapılır, mevcut kurumsal kimlik sağlayıcısına
  entegrasyon hedeflenir. Kullanılan sağlayıcı henüz doğrulanmadı, belirli
  bir SSO ürünü varmış gibi varsayılmaz.
- Operatör izinli bağlantı/profilleri görür, karşılaştırma başlatır ve yetkili
  sonuçları inceler. Yönetici bağlantı, profil, zamanlama ve işletim ayarlarını
  yönetir. Görüntüleme ve değiştirme yetkileri API'de de denetlenir.
- Ortak bağlantı kaydında parola gösterilmez. Bağlantıya kullanma yetkisi
  verilmesi, sır değerini görüntüleme yetkisi anlamına gelmez.
- Çalışma kaydında başlatan kullanıcı, kaynak/hedefler, profil/ayar sürümü,
  başlangıç/bitiş, aşama süreleri ve artifact ilişkisi bulunur. Bildirim alıcısı
  mevcut izinli tek alıcı olarak kalır, ortak UI kurulması kendiliğinden herkese
  mail gönderme yetkisi sağlamaz.
- Aynı anda başlatılan işler sunucuda sınırlı kuyruk ve ayrı çalışma alanlarıyla
  yönetilir. Ekranın kapanması işi kaybettirmez, sayfa yeniden açıldığında
  çalışma kimliğinden durum alınır. Her HTTP isteğinde uzun karşılaştırma
  doğrudan çalıştırılmaz.
- Mevcut Jenkins zamanlaması tek zamanlayıcı olarak korunur, UI'ya ikinci bir
  bağımsız günlük tetikleyici eklenmez. Rapor/SQL için geçerli Jenkins-only
  saklama politikası dağıtım tasarımında korunur.

## Uygulama sırası

1. Bağlantı/profil/etkin çalışma ayarı sözleşmesi, mevcut Git işlerine uyumluluk.
2. Gerçek Oracle kaynak adaptörü ve Git→Oracle /Oracle→Oracle testleri.
3. shadcn UI: bağlantılar, yeni karşılaştırma, gerçek ilerleme, sonuç ve ayarlar.
4. Jenkins ile aynı motor/ayarların kullanımı, gerçek bağlantı ve uçtan uca doğrulama.

Kurumsal kimlik entegrasyonu, sunucudaki sır saklama sağlayıcısı ve gerçek
deployment adresi henüz doğrulanmadı, belirli bir altyapı varmış gibi gösterilmez.
Burada yeni servis kurulmadı, bağımlılık yüklenmedi, canlı bağlantı açılmadı ve
UI kodu üretilmedi. Sonraki somut adım bu envanterden ortak uygulamanın API,
bağlantı kayıtları, çalıştırma ve Oracle source sözleşmesini çıkarmaktır.
