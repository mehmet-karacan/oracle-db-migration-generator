# Çalışma ayrıntısı ve yerel SQL görüntüleyici

Kullanıcı ekranın yeniden düzenlenmesini istedi. Ek tasarım onayı yok.
Python motoru/SQL kararları, proje sınırı, UNKNOWN ve kaynak biçimi korunur.

- [x] Kompakt özet şeridi. Toplam süre kartların içinde, kaynak hazırlama
  ikincil bilgi. Aynı sayı farklı bölümde tekrarlanmaz.
- [x] Sol liste arama/nesne türü/seçim, kaydırdıkça25 kayıt. Önceki/sonraki
  nesne düğmesi kalkar. Append hatası ve geç hedef/arama yanıtı korunur.
- [x] Sağ panel büyük nötr karşılaştırma tablosu. Kaynak/hedef başlıkları
  açık, varlık/NULL/UNKNOWN anlamları alan bağlamıyla gösterilir. Kırmızı/yeşil
  hücre dolgusu yok. İşlem ve SQL görünümü aynı çalışma alanında.
- [x] Ortak SQL dialog'u yerel dosyayı no-store okur. Biçim/çift tırnak aynı.
  Jenkins SQL'i Jenkins'te kalır, servis hesabı yoksa arşiv bağlantısı açıkça
  belirtilir. SQL kalıcı olarak tarayıcıya/SQLite'a kopyalanmaz.
- [x] Kullanıcının sonraki talimatı: yerel çalıştırılan işlerin SQL'i özel yerel
  run klasöründe kalabilir. UI'de açık Yerel/Jenkins seçimi. Varsayılan Jenkins
  ve eski talepler korunur. LOCAL yalnız yerel runtime yeteneğiyle mümkündür.
- [x] Davranış testleri, ilgili Python/UI test/build/lint, gerçek#55 görsel
  kontrolü ve sentetik yerel SQL kontrolü, bağımsız review ve devir.

Dosyalar RunSummary/ObjectResults/ObjectComparisonPanel/SqlViewer/RunDetail/
ComparisonForm, api/resultApi, CSS/translations; control.api/store yürütücü
seçimi. Yeni servis/framework, Oracle yazımı, Jenkins job değişimi veya mail yok.
İnceleme odağı: geç sayfanın yeni filtreye karışması, çift scroll isteği,
append hatasında seçimin kaybı, yerel/Jenkins sessiz fallback, SQL quote/biçim,
proje dışında SQL erişimi, bilinmeyen sayının sıfır/tam gösterilmesi.


Uygulama kaydı: 25 Ekim 2026. Kullanıcı isteği ek tasarım onayı olmadan uygulanır.
Bağımsız incelemede servis-dispatch Jenkins kaydının external olmadan yerel
etiket/SQL yolu aldığı bulundu. Kırmızı regression testinden sonra executor ve
archive_build_url ayrımı, yerel artifact reddi ve kuyruk filtresi doğrulandı.
Tarayıcıda önceki index.css renk kurallarının nötr yeni kuralları bastırdığı
görüldü, eski kurallar yerinde düzeltildi. Teknik token metadata gösterimi kapalı
sözleşmeyle okunur hale getirildi, gerçek SQL byte'ları değiştirilmedi.
Doğrulama/log ve ekran kanıtları output/results-redesign altında Git dışındadır.
