# Solda liste, sağda karşılaştırma

> executing-plans: aynı oturumda uygula, sonunda tek bağımsız inceleme.

**Goal:** Kullanıcının seçtiği kalıcı iki panelli sonuç çalışma alanı.
**Architecture:** Mevcut sonuç API'si ve shadcn bileşenleri, modal yerine inline panel. Kanonik alan farkları kaynak/istenen ve hedef/mevcut yönünde renkli hücrelerle sunulur. SQL gövdeleri aynı Jenkins linkinden açılır.
**Spec:** 24 Ekim son kullanıcı isteği: sol nesne listesine tıklayınca sağda hedef/karşılaştırma, Git diff benzeri daha anlaşılır sunum.

## Sınırlar

Oracle/Jenkins/SMTP/push yok, mevcut #55 metadata kullanılır. UNKNOWN/ABSENT/null ve COMMENT display_name korunur. Hedef/filtre/nesne değişiminde eski yanıt yeni paneli değiştiremez. Kaydedilmemiş eşit alanlar veya SQL satır diff'i uydurulmaz.

## Adımlar

- [x] RED: modal yok, iki panel birlikte görünür, nesne değişiminde geciken detay reddedilir.
- [x] GREEN: ObjectResults sol gezinme ve kalıcı sağ panel, ObjectDifferenceSheet → ObjectComparisonPanel, diff renkleri, seçim ve sayfalama.
- [x] Tamamlanmış Jenkins koşusunda özet katlanır, sonuç çalışma alanı öncelikli olur.
- [x] Frontend test/build/lint, #55 tarayıcı kontrolü, tek inceleme, devir/durum güncelle.
