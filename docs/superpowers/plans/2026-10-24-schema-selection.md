# Bağlantı hesabı ve şema seçimi uygulama planı

Kullanıcı talimatı: kayıtlı bağlantılardan sonra kaynak ve her hedef için
şema eşleştirmesi açıkça seçilecek. Giriş hesabı okunan şemadan bağımsızdır.
Kendi şema adları korunur, farklı adlara dönüşüm desteklenmez. Kullanıcının
onayladığı kapsam doğrudan uygulanır. Ek tasarım onayı ve commit yoktur.

Mevcut React/shadcn, FastAPI ve salt okunur Python motoru korunur.
Eski profil/run kayıtları yeniden yazılmaz. Yeni eşleştirmeler frozen spec
içinde saklanır. Jenkins eşleme kontrolü yeni kapsamı sessizce yok sayamaz.

## Adımlar

- [x] Kırmızı test: eksik/hedef dışı/tekrarlı/farklı adlı eşleşmeler reddedilir.
  Eski profil okuması çalışır, yeni seçim frozen run'da değişmez.
- [x] ProfileInput.target_mappings ve runner target_config uygulanır.
  Her hedef kaynak şemalarının bir alt kümesini açıkça seçer. Farklı giriş
  hesabında mevcut katalog yetki doğrulaması kullanılır, ALL_OBJECTS yeterli
  sayılmaz. Kanonik SQL ve karşılaştırıcı değiştirilmez.
- [x] Kırmızı UI testi: hedef seçmek tek başına yeterli değildir. Her hedefte
  en az bir Kaynak şema / Hedef şema çifti seçilir, profil yükleme ve kapsam
  değişimi eski seçimi yanlış kullanamaz. Kendi bileşenleriyle form uygulanır.
- [x] Çalışma ayrıntısı frozen eşleştirmeyi gösterir. Bağlantı ekranında
  giriş hesabı ve şema kapsamının farklı olduğu açıklanır.
- [x] Birinci taraf metinlerde uzun tire ve yapay üretim ifadeleri temizlenir.
  Markdown kod blokları, kod/SQL noktalı virgülleri, vendor/reference içerikleri
  ve hash kanıtları korunur. Metin taraması ve mevcut testler doğrulanır.
- [x] Python kontrol/runner/katalog testleri, frontend test/build/lint,
  tarayıcı kontrolü ve bağımsız son inceleme yapılır. İki devir belgesi güncellenir.

## İnceleme odağı

- Eski profil/binding ve geçmiş çalışmanın kapsamı değişmemeli.
- Hedef çıkarma veya kaynak değişimi gizli eski eşleşme taşımamalı.
- Kaynakta bulunmayan hedef şeması ve farklı owner adı kabul edilmemeli.
- Farklı giriş hesabı mevcut katalog yetkisi olmadan tamlık iddia etmemeli.
- Metin temizliği SQL, lisans/provenance ve test fixture byte'larını değiştirmemeli.

Yerel offline uygulama kapsamıdır. Yeni canlı Oracle kabulü, Jenkins job
değişikliği, mail veya push yapılmaz. Ortak ortam dağıtımı NOT_RUN kalır.

## Kullanıcının yerleşim düzeltmesi

Şema eşleştirmeleri Bağlantılar ekranında ayrı sekmede hazırlanıp kaydedilir.
Yeni karşılaştırmada bu kayıt seçilir. Giriş bilgileri mevcut Bağlantılar
sekmesinde kalır. SQLite records tablosunda sürümlü schema_mapping kaydı
kullanılır, yeni servis veya veritabanı eklenmez. Profil seçilen eşleştirme
kimliği/sürümüyle birlikte gerçek kaynak/hedef kapsamını sabit olarak taşır.
Eşleştirme sonradan düzenlense bile önceki profil/çalışma sessizce değişmez.

- [x] SchemaMappingInput ve API/store CRUD, proje/yetki/sürüm kontrolleri.
- [x] Bağlantılar ve Şema eşleştirmeleri sekmeleri, kayıt/düzenleme ekranı.
- [x] Yeni karşılaştırmada kayıtlı eşleştirme seçimi ve salt okunur kapsam özeti.
- [x] Güncel testler, tarayıcı kontrolü ve inceleme düzeltmesinin doğrulanması.

Tamamlandı. Kullanıcının ayrı sekme düzeltmesi uygulandı. Son kanıt yz/DEVIR.md ve output/schema-selection altında.
