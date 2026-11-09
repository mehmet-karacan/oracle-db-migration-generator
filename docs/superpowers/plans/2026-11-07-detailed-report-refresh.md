# Ayrıntılı Rapor Düzeni Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

Author: Mehmet KARACAN
Date: 2026-11-07

**Goal:** Ana rapor, hedef ayrıntısı ve nesne listesini onaylanan mail ailesiyle tutarlı hale getirmek.

**Architecture:** Mevcut Jinja2 ve statik HTML korunur. Ortak sayım ve nesne grupları rapor katmanında hazırlanır. SQL yalnız kaçış uygulanmış metin olarak gösterilir.

**Tech Stack:** Python, Jinja2, HTML ve CSS.

**Spec:** `.local/detailed-report-review-20261107/review.md`, kullanıcı onayı.

## Global Constraints

- Mevcut çalışma alanında devam edilir, yeni branch ve push yok.
- SQL, plan, eski arşiv, kurumsal logo byte'ları değişmez.
- Her HTML en fazla 200 KiB, JavaScript ve dış bağımlılık yok.
- Jenkins güvenlik ayarları değişmez. Mail tasarımı korunur.
- Yeni Oracle karşılaştırması ve mail yok. Ayrı yerel önizleme hazırlanır.

## Review Focus

- Eksik DDL sayısı planın engelli karar sayısıyla karışmaz.
- Aynı nesnenin işlemleri ve çoklu hedefler birbirine karışmaz.
- Uzun SQL ve nesne adları HTML sınırını veya kaçış kurallarını bozmaz.
- Öneri ve kaynak SQL eşlemeleri eski arşivden de geri okunur.
- CSS filtreleri yalnız açık sayfayı süzer ve bunu görünür biçimde belirtir.

## Task 1 Ortak Rapor Verileri ve SQL Görüntüleyici

**Files:** reporting/web.py, reporting/render.py, reporting/view.py, templates/sql.html.j2, tests/unit/test_report_detail_refresh.py.

- [x] Sayım, SQL metni, kaçış ve eski eşleme testlerini önce kırmızı çalıştır.
- [x] Gerçek dosya eşlemeleri, gruplanmış nesneler ve bölümlenmiş SQL HTML üretimini uygula.
- [x] SQL ve planın aynı kaldığını, bütün metnin sayfalarda bulunduğunu doğrula.

## Task 2 Ortak Tasarım ve Nesne Akışı

**Files:** templates/run.html.j2, templates/report.html.j2, templates/web_header.html.j2, templates/ddl_types_web.html.j2, assets/report.css.

- [x] Özet ölçüleri, tür dağılımı, dönüş yolları ve nesne grupları için kırmızı test çalıştır.
- [x] Kaynak ve hedef bağlamı, ortak başlık, renkli ikonlar, sol nesne dizini ve sağ ayrıntıları uygula.
- [x] Tür ve dosya durumunu CSS filtreleriyle süz. Nesne bulma için sayfa dizini ve Ctrl+F açıklaması göster.
- [x] Açık ve koyu tema CSS kuralları, mobil düzen, görünür dönüş bağlantısı ve etkin sayfa işaretini sınayan testleri çalıştır. Gerçek tarayıcı kabulü NOT_RUN.

## Task 3 Kayıtlı Sonuçla Kabul

**Files:** tools/jenkins_report_presentation.py gerektiğinde, docs/HTML_STANDARDI.md, yz/DEVIR.md, yz/GELISTIRME_DURUMU.md.

- [x] Rapor ve arşiv testlerini çalıştır, yeni hataları düzelt.
- [x] Kayıtlı yerel sonuçtan ayrı dizine önizleme üret, önceki arşiv hash'lerini karşılaştır.
- [x] Belge renderında yazı ve varlıkları kontrol et, gerçek istemci sınırını belirt. Grid ve etkileşim kabulü NOT_RUN.
- [x] Devir kayıtlarını güncelle. Commit ve dağıtım bu planın parçası değildir.

Sonuç 192 PASS. Kanıt .local/detailed-report-final-tests.xml.
Önizleme .local/detailed-report-preview-20261107/index.html.
36.736 eski dosyanın hash değerleri aynı, kırık yerel bağlantı sıfır.
Jenkins kurulumu, canlı Oracle kabulü ve mail NOT_RUN.
