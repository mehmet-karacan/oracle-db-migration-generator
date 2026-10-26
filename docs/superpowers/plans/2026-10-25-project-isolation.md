# İkinci proje ayrılığı ve hedef seçici planı

25 Ekim 2026 kullanıcı talimatı. Mevcut UI bileşenleri ve1→N sözleşmesi korunur.

- [x] Hedef dropdown davranışını RED testle tanımla, satır ekleme/kaldırma ve
  eski çiftleri temizleme uygula, boş/çift hedefi engelle.
- [x] Footer kısalt, sekmeleri solda sabitle, kart yüzeylerini tema tokenıyla yumuşat.
- [x] İkinci gerçek yerel proje oluştur, açık TEST bağlantıları ve UI üzerinden
  eşleştirme/profil/ayar kaydet, gerçek ağ ve karşılaştırma çalıştırma.
- [x] SKY kayıt özeti ve iki proje ekranlarını karşılaştır, cross-project API
  okumaları/yazımları/başlatmayı reddetme kontrolleri, test/build/lint ve review.
- [x] Devir ve kanıtları kaydet.

Final review: Critical0/Important0/Minor1. Deferred minor ek çoklu hedef kombinasyon
UI testidir. Tam frontend36/36, Python proje testleri11/11. Diğer deferred/ruling
ve kanıtlar yz/DEVIR.md. Commit/push yok. Test kayıtları inceleme için yerelde kalır.

## Deferred minor kapanışı - 25 Ekim 2026

Kullanıcı sonraki talimatıyla ek çoklu hedef UI/API kabulünü istedi. Farklı iki
çiftle v1, hedef kaldırılmış v2, yeniden boş seçim ve açık seçimle v3 akışı hem
koruyucu otomatik test hem gerçek tarayıcı/SQLite kontrolüyle tamamlandı. SKY ve
önceki kayıtlar değişmedi. Frontend37PASS, kapsam Python12PASS, buildPASS.
Detay yz/DEVIR.md, kanıt output/multi-target-check. Açık minor kalmadı.
