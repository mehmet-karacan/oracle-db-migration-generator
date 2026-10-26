# Kaynak hazırlama performansı ve üst süre gösterimi

Kullanıcı: 47 dakikalık kaynak hazırlamayı ayrıntılı ölç, hızlandır, sonuç ve
üretilen DDL değişmesin. Süreyi raporun ilk bölümüne ekle. Bu son talimat önceki
alt gri süre yerleşiminin yerine geçer. Mevcut Python/ANTLR, salt okuma,
TTBP/08:00, Jenkins-only ve tek mail alıcısı kararları korunur. Ek tasarım
onayı/araştırma fazı açılmaz, mevcut workspace değişiklikleri korunur.

- [x] Jenkins'te v23 ve #42'nin sabit ham girdileriyle kaynak hazırlama profili:
  dosya/tür süreleri, gerçek cache hit/miss, worker zamanı, birleştirme/yazma.
  Yeni Oracle bağlantısı yok. Orijinal snapshot/hash ve tam dosya eşitliği ölçülür.
- [x] Ölçülen kök nedene yönelik kırmızı regresyon testi yaz, en küçük doğru
  uygulamayla yeşile getir. Parse kuralları/kapsamı ve hata/UNKNOWN semantiği
  korunur. Tam bayt/owner/parser kimliği doğrulamasından vazgeçilmez.
- [x] Aynı sabit kaynak ve hedef snapshot'larından önce/sonra sonuç, operasyon
  ve SQL byte eşitliğini doğrula, parser/cache/bozuk giriş testlerini çalıştır.
- [x] `test_report_timing_layout.py` ve `test_report_counts_timing.py`: özgün
  karşılaştırma süresi ilk bölümde tek kez görünür, yenileme saatiyle karışmaz,
  bilinmeyende Ölçülemedi. Genel web/mail renderer ve CSS'i buna göre düzenle.
- [x] Tam test/contract/wheel doğrulaması, ölçülmüş iyileştirmeyi Jenkins'e al,
  aynı arşivi yenile, yalnız mkaracan@innova.com.tr bildir. Normal Pipeline'ı
  yeniden oku, süreyi gerçek tarama performansıyla karıştırma.
- [x] `yz/DEVIR.md`, `yz/GELISTIRME_DURUMU.md` güncelle, offline eşitlik,
  Jenkins ölçümü ve yeni canlı Oracle koşusunun durumunu ayrı raporla.

İnceleme odağı: cache bozukluğu/kimlik uyuşmazlığı, zaman aşımı ve sıralama,
başarılı cevabın mutable paylaşımı, parser çıktısının aynı kalması, gerçek
karşılaştırma süresinin korunması. Hız için alan/nesne atlama yapılmaz.

Tamamlanma kanıtı: Jenkins #48 profil, #52 ortam SUCCESS, #53 offline kaynak/plan/1.381SQL eşitliği ve görünüm yenileme UNSTABLE (mevcut belirsizlikler korunur). Aynı kaynak CLI24,35sn. Tam test1022passed/135,04sn. Normal v25/TTBP/08:00 yeniden okundu, mail yalnız izinli alıcıya. Yeni canlı Oracle capture/toplam süre NOT_RUN. Ayrıntılar docs/KAYNAK_HAZIRLAMA_PERFORMANSI.md ve yz/DEVIR.md.
