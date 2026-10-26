# Oracle DB Migration Generator Başlangıç Paketi

**Güncel çalışma:** Paket açıldı, yerel CLI temeli uygulandı. Kullanım için
[README](README.md), kapsam ve devam için [AKTIF_GOREV](AKTIF_GOREV.md) esas
alınır. Aşağıdaki metin orijinal paketin teslim açıklamasıdır, yeni ürünün
veya canlı karşılaştırmanın tamamlandığını göstermez.

**Tarih:** 19 Ekim 2026 · **Paket:** 1.0

Bu paket, uygulayıcının mimariyi yeniden seçmeden uygulama geliştirmesi içindir. Ürün uygulaması değildir, mimari, aktif görev, sözleşmeler, gerçek kod referansları ve doğrulama ölçütlerini içerir.

## Kullanım

1. Paketin içeriğini `C:\innova\projeler\oracle-db-migration-generator` köküne yerleştirin. Dizin zaten doluysa mevcut dosyaların üzerine topluca yazmayın, dosyaları karşılaştırarak ekleyin. `.local` dizini de paketin parçasıdır.
2. geliştirme ortamını bu proje dizininde açın ve kökteki **AKTIF_GOREV.md** dosyasını görev olarak verin. Dosyanın başındaki başlangıç protokolü diğer belgelerin okuma sırasını belirler. Ayrı bir araştırma promptu gerekmez.
3. Gerçek hedef bağlantıları ve erişim anahtarları Jenkins'te tanımlanacaktır. Hiçbir parola/token bu pakete konmadı. `.local/session-context.json` yalnız makine yolları ve kullanıcı tarafından verilen adresleri içerir, Git'e alınmaz.

Yeni repo henüz klonlanmadıysa Uygulayıcı, aktif görevdeki güvenli başlangıç adımını uygular. Mevcut iki referans proje salt okunur kalır. Git commit/push, Jenkins'e iş yükleme ve gerçek veritabanında DDL çalıştırma bu teslimatla otomatik yetkilendirilmiş değildir.

## İki Farklı Depo

`oracle-db-migration-generator`: Kod, testler, genel belgeler, anonim örnekler.

`oracle-db-migration-artifacts`: Üretilen hedef bazlı SQL/JSON/HTML paketleri. Bunun başlangıç belgeleri `templates/artifact_repo/` içindedir. Uygulayıcı bu şablonları hazırlar, gerçek arşiv yayımlaması yalnız yetkili runtime işiyle yapılır.

## Mevcut HTML

Ana referans `reference-ui/innova-report.original.html.j2` ve `reference-ui/reference.html` dosyalarıdır. Bunlar yüklenen Analyzer arşivindeki etkin `innova-db-report/1.0` ailesine dayanır. `reference.html` mevcut şablonun sentetik verilerle render edilmiş görünümüdür, yeni ürünün tamamlandığı anlamına gelmez. Eski v5 tasarımı kullanılmayacaktır.

## Doğrulanmış Ve Henüz Doğrulanmamış Olanlar

İki ZIP içindeki ilgili kodlar incelendi, Schema Compare Platform'un sabit commit'indeki karşılaştırma ve DDL üretim kodları okundu. Seçilmiş 60 Analyzer referans testi çalıştırılıp geçti. Paket JSON örnekleri, şemalar, bağlantılar ve dosya özetleri teslimat kontrolünden geçer.

Kurumsal Bitbucket içeriğine, kullanıcının Windows diskine, gerçek Oracle hedeflerine ve Jenkins kurulumuna bu hazırlık sırasında erişilmedi. Yeni ürün için build/test veya canlı kabul başarısı iddia edilmez. Bu ortam kontrolleri aktif görevde uygulama adımıdır, mimariyi yeniden tasarlama görevi değildir.

## Paket Önce Açıldıysa Git Başlangıcı

Kök dizinde bu paket var ama `.git` yoksa dizini silerek klonlama. A00 kapsamında yalnız paketin manifestindeki dosyaların bulunduğu doğrulanırsa `git init -b main` ile **yerel** repository başlatılabilir ve `.local/session-context.json` içindeki Generator adresi origin olarak eklenebilir. Uzak branch durumu salt okunur fetch ile kontrol edilir. Uzak repo boş değilse ayrı inceleme checkout'u kullanılır, paket/kullanıcı dosyalarının üzerine checkout yapılmaz. Kullanıcıya ait ek dosya veya farklı origin varsa otomatik birleştirme yapılmaz. Bu başlangıç yerel Git hazırlığıdır, commit/push yetkisi vermez.
