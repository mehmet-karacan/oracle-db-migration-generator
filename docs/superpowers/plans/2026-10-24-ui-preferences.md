# Arayüz okunabilirliği, dil ve tema planı

Kullanıcının gönderdiği altı ekran ve son talimatı kapsamdır. Ek tasarım
onayı istenmez. Mevcut React/shadcn ve salt okunur motor korunur.

- [x] Tercihler için sürümlü yerel kayıt, TR/EN ve açık/koyu seçim testleri.
- [x] Ortak çeviri sözlüğü, sayfa dili/tarih/sayı biçimi ve görünür UI metinleri.
  Kullanıcının verdiği adlar, SQL ve arşivdeki özgün gerekçeler çevrilmez.
  İngilizce görünümde özgün Türkçe gerekçe dili açıkça belirtilir.
- [x] Üst çubukta dil/tema denetimleri. Proje menüsü Radix Select ile
  klavye, odak, seçili durum ve tema uyumlu yapılır.
- [x] Temel metin 16px, yardımcı metin en az 13px, kontroller en az 40px.
  Renkler tema tokenlarına taşınır. Küçük viewport ve büyütmede reflow korunur.
- [x] Bağlantı formunda önce Bağlantı Türü, sonra Bağlantı Adı. Bağlantı
  adlarındaki orta nokta yalnız sunumda tire olur, stored spec değişmez.
- [x] TM Forum uygulanabilirlik ve WCAG hedefleri resmi kaynaklarla belgelenir.
  Kurumsal zorunluluklar ve sertifikasyon doğrulanmadıkça uyum iddiası yapılmaz.
- [x] Frontend test/build/lint, tarayıcıda TR/EN ve iki tema, menü/klavye,
  taşma ve form sırası doğrulanır. Bağımsız son inceleme ve devir güncellenir.

İnceleme odağı: SQL/UNKNOWN ve frozen spec korunması, yerel tercihlerde sır
olmaması, İngilizce ekranda veri değişmemesi, koyu dialog/menü okunabilirliği,
yerel kayıt erişimi kapalıyken uygulamanın açılması. Oracle/Jenkins/mail yok.

## Teslim kanıtı - 25 Ekim 2026

28 frontend testi PASS, build PASS, lint 0 hata/4 önceki uyarı.
Bağımsız incelemedeki çeviri/kontrast/font bulguları düzeltildi ve regresyonları
geçti. 320 px reflow ve dialog düğme sınırları doğrulandı. Yüzde 200 zoom ve
piksel kontrolü tamamlanmadı, screenshot API UNAVAILABLE. Bunlar tam WCAG kabulü
olarak sunulmadı. Standart kapsamı ARAYUZ_STANDARTLARI.md, komut/loglar ve
sonraki adım yz/DEVIR.md. Yeni canlı bağlantı/Jenkins/mail çalıştırılmadı.
