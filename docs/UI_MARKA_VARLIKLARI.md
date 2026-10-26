# İnnova arayüz marka varlıkları

25 Ekim 2026 kullanıcı talimatıyla frontend logo zemini ve sekme ikonu güncellendi.

Resmî kaynaklar:
- Kurumsal kimlik: https://www.innova.com.tr/kurumsal-kimlik
- Bu sayfanın yayımladığı paket: https://www.innova.com.tr/medias/innova_kurumsal_kimlik.zip
- Resmî sitenin sekme simgesi: https://www.innova.com.tr/favicon.ico

Paketin Logo Seti klasöründeki innova-logo.svg açık tema için, innova-logo-beyaz.svg
koyu tema için kullanılır. İkincisi uygulamada innova-logo-white.svg adındadır.
Dosya içerikleri yeniden çizilmedi, renklendirilmedi veya filtrelenmedi. Her iki
resmî SVG aynı viewBox değerine sahiptir: 0 0 825.84 157.13. Zemin çizen bir tam
sayfa dikdörtgeni yoktur. SVG script/image/foreignObject ve dış referans içermez.

Site favicon.ico dosyası A simgesidir, saydam alfa kanallı106x106ICO olarak
olduğu gibi eklendi. index.html rel=icon linki cache anahtarıyla bu dosyaya gider.
Eski scaffold favicon.svg kullanılmaz. Mevcut PNG/rapor ailesi değiştirilmedi.
BrandLogo bileşeni giriş ve ana ekranlarda tema sürümünü ortak seçer.

Beyaz alanın nedeni mevcut PNG değil, koyu temadaki background:white/padding
stiliydi. Bu stiller sidebar, mobil ve giriş kartından kaldırıldı. Odak/kenarlık
ve genel tema renkleri kapsam dışıdır, değiştirilmedi. Tarayıcıda iki temada da
background rgba(0,0,0,0), padding0, filter none ve image complete doğrulandı.

Resmî dosyaların SHA-256 değerleri:
- innova-logo.svg: `e55b6e6b168811442490d1ceca0f937c0c55676c90e9f924b2dba877a0ef3d78`
- innova-logo-white.svg: `f54dae4b9ce53f37f1f34ce8abf8d75f535734629ba1e4c952b56153069e1d87`
- favicon.ico: `13be8252aa0042230bbd854c26e2142c16c126bd3b9481ce5018707afb50646c`

Kaynak ile ürün dosyası byte eşitliği ve HTTP200 kontrolü output/brand-assets
altında kayıtlıdır. Referans PNG/ICO preview yalnız inceleme içindir, yeni logo
olarak üretilmedi. Firecrawl hesabı kredi hatası verdiği için bir tekrar sonrası
resmî web sitesi doğrudan okundu. Eksik kurumsal kimlik alanı uydurulmadı.
