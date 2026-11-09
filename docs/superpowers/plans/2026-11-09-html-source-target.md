# HTML Kaynak ve Hedef Karşılaştırması

Author: Mehmet KARACAN
Date: 2026-11-09

**Goal:** Kullanıcının onayladığı yan yana alan karşılaştırmasını yerel HTML raporuna eklemek.

**Architecture:** Mevcut Jinja2 ve statik HTML korunur. Planın after alanı kaynak, before alanı hedeftir. Karşılaştırma kararları yeniden hesaplanmaz. Bütün kayıtlı farklar nesne kimliği ve işlem bağlantılarıyla eşlenir. Büyük değerler ayrı sınırlı sayfalarda eksiksiz gösterilir.

**Tech Stack:** Python, Jinja2, HTML ve CSS.

**Spec:** 9 Kasım kullanıcı talimatı. Normal ekrandaki gibi kaynak ve hedef yan yana, belirgin farklar, önce yerel önizleme. Jenkins dağıtımı yok.

## Sınırlar

- SQL, plan, kurumsal logo ve eski arşiv değişmez.
- Yeni Oracle karşılaştırması, mail, Jenkins dağıtımı, commit ve push yok.
- Bilinmeyen değer yokluk olarak gösterilmez. NULL, boş metin ve false ayrıdır.
- Harici bağımlılık ve JavaScript eklenmez. Her HTML en fazla 200 KiB olur.
- Metinler Türkçe, alan başlıklarının sözcük başları büyük olur.

## Uygulama

- [x] Kaynak ve hedef yönü, değer durumları, kanonik kimlik ayrımı, işlem tekrarı ve uzun metin için kırmızı test yaz ve çalıştır.
- [x] reporting/comparison.py ile fark görünümünü ve sınırlı sayfaları hazırla. report.html.j2 içinde kısa karşılaştırma ve tam görünüm bağlantısı ekle.
- [x] comparison.html.j2 ve comparison_index.html.j2 ile bütün farkları erişilebilir yap. report.css içine iki sütunlu okunabilir düzen ve koyu tema kurallarını ekle.
- [x] İlgili rapor ve arşiv testlerini çalıştır. Mevcut testlerin yalnız işlem sayfalarını ilgilendiren kontrollerini bu sayfalarla sınırla.
- [x] Kayıtlı sonuçtan ayrı 20261109 önizlemesi üret, eski dosya hash değerlerini ve bağlantıları doğrula.
- [x] Yerel görsel kontrolün kapsamını açıkça kaydet. Devir ve HTML standardını güncelle.

## Kabul Kanıtı

Rapor, arşiv ve Jenkins runtime grubu 206 PASS. Ayrı değer grubu 14 PASS.
Önizleme .local/source-target-preview-20261109-final/index.html.
36.736 özgün dosya aynı kaldı. 19.686 kayıtlı farkın tamamı erişilebilir.
Yeni HTML dosyalarında kırık yerel bağlantı yok. Belge içeriği görseli üretildi.
Gerçek tarayıcı ve mobil etkileşim kabulü NOT_RUN. Jenkins, Oracle ve mail NOT_RUN.

Kod incelemesi sonrasında düz metnin token sanılması, ilk boş satırın
korunması ve gerçek kısıt tokenlarının okunabilirliği düzeltildi.
İşlemler ve DDL bağlantısı nesnenin bulunduğu sayfaya döner.
Kanonik olmayan anahtarlar dosya yolu oluşturulmadan reddedilir.
