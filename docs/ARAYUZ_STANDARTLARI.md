# Arayüz standartları

24 Ekim 2026 kullanıcı talimatı. Bu belge uygulama hedefini ve ölçülen durumu
ayırır. Türk Telekom'un iç standart listesi bu repoda sağlanmamıştır.

## TM Forum kapsamı

[TM Forum uyumluluk programı](https://www.tmforum.org/oda/conformance/)
eTOM, SID, Open API ve ODA Component kapsamlarını ayrı değerlendirir.
[ODA bileşen açıklaması](https://www.tmforum.org/oda/implementation-architecture/components-canvas/)
bileşenleri standart Open API'lerle çalışan yapı taşları olarak tanımlar.
[Open API kaynakları](https://www.tmforum.org/resources/toolkit/open-apis-and-data-model-toolkit/)
TMF630 REST API tasarım kılavuzunu listeler.

Bu uygulama iç kullanımda Oracle şema karşılaştırma aracıdır. Belirli bir TMF
Open API sözleşmesi veya ODA Component kimliği uygulanmış değildir. Kurum
üyeliğinden bu araç için bir ürün sertifikasyonu çıkarılamaz. Entegrasyon
kapsamı belirlenmeden özel kontrol API'si TMF uyumlu diye etiketlenmez.
Kurumun zorunlu standart/versiyon listesi ve resmi conformance kabulü NOT_RUN.

## Arayüz hedefleri

[WCAG 2.2](https://www.w3.org/TR/WCAG22/) AA ölçütleri referans alınır:
1.4.3 metin kontrastı, 1.4.4 yüzde200 büyütme, 1.4.10 reflow,
1.4.11 kontrol kontrastı, 2.1.1 klavye erişimi, 2.4.7 görünür odak,
2.5.8 hedef boyutu ve 3.1.1 sayfa dili. Bunlar hedeflerdir, tam WCAG
uygunluğu yalnız birkaç ekran kontrolünden çıkarılmaz.

Ana metin16px, form/kontrol14px veya üzeri, yardımcı metin13px veya üzeri
ürün tercihidir. WCAG'nin bütün yazılar için sabit bir minimum font boyutu
belirlediği iddia edilmez. Durum yalnız renkle anlatılmaz.
Dil TR/EN, tema açık/koyu seçilir. Tercihler tarayıcıda saklanır, sır içermez.
SQL, nesne/şema adları ve özgün rapor gerekçeleri değiştirilmez.

## Ölçülen durum - 25 Ekim 2026

- PASS: 28 frontend testi, üretim derlemesi, lint 0 hata/4 önceki uyarı.
- PASS: TR/EN, iki tema, form sırası, kayıtlı sırların geri gösterilmemesi,
  SQL değerlerinin korunması ve depolama hatası davranışı.
- PASS: örneklenen DOM metinleri en az 13 px. Ölçülen minimum metin kontrastı
  açık temada 5.62:1, koyu temada 7.37:1. Tam sayfa kontrast taraması değildir.
- PASS: 320 px viewport bağlantı sayfası scrollWidth 320 px. Dialog 288 px,
  action düğmeleri dialog sınırları içinde. Kontrol menüleri temayla uyumlu.
- UNAVAILABLE: tarayıcı screenshot API'si capture hatası verdi. Piksel bazlı
  son görsel kabul yapılamadı. DOM/AX ölçümleri dom-metrics.json içinde.
- NOT_RUN: browser zoom yüzde 200, tam WCAG 2.2 AA denetimi, kurumsal zorunlu
  profil/versiyon doğrulaması, resmi TM Forum conformance/sertifikasyon.

Bu örnek kontroller tam standart uygunluğu veya sertifikasyon beyanı değildir.
Kanıt output/ui-preferences altında, önceki backend kabulü ayrı kayıttadır.
