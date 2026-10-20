# TTBP Engel İncelemesi Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kayıtlı TTBP planındaki 2.355 engelin tamamını kanıtıyla incelemek, yanlış engelleri düzeltmek ve güncel rapor/DDL'yi Jenkins'te saklamak.
**Architecture:** Mevcut snapshot, comparator, planner ve artifact sözleşmeleri korunur. Nesne bazlı denetim kaydı eski operation ID'lerini yeni karar ve kanıtlarla eşler; genel bir BLOCKED→uyarı dönüşümü yapılmaz.
**Tech Stack:** Mevcut Python CLI, pytest, JSON snapshot/plan ve Jenkins.
**Spec:** AKTIF_GOREV.md son kullanıcı kapsamı.

## Global Constraints

- Source ve target READ ONLY; SQL uygulanmaz, COMPILE veya yetki değişikliği yok.
- Yalnız PROD / TTBP; INNOVA_ODI manuel. Günlük 08:00 Europe/Istanbul.
- UNKNOWN ve yokluk ayrıdır; kısmi kapsam gizlenmez.
- Gerçek SQL/metadata yalnız yerel Git dışı alan ve Jenkins; kod private push kapsamı ayrı.

## Review Focus

- Kaynakta eşleştirilemeyen korunacak hedef nesnesi, yeni SQL üretimi gereken nesneyle karışmaz.
- COMMENT parent varlığı kolon varlığı yerine geçmez; yanlış kolon yorumuna hazır SQL yok.
- Oracle iç backing index ilişkisi gerçek dictionary/constraint kanıtına dayanır.
- Ortak nesnenin eksik DDL/metadata alanı uyarı adı altında güvenli sayılmaz.
- Eski 2.355 operation ID'nin tümü tam bir kez inceleme kaydında bulunur; karar/SQL bağımlılıkları doğrulanır.

## Görevler

- [x] **1. Temel veri ve sayım:** #25 manifestini doğrula; 2.355 BLOCKED ID, neden, nesne, source/target varlığı, fark ve kanıt referanslarını Git dışı denetim kaydına al. Bütünlük ve tekillik assertion'ları çalıştır.
- [x] **2. Kök nedenleri ayır:** Her kaydı incele; bağımsız sorun alanlarını paralel incelemeye ayır. Sayım ve nesne bazlı sonuçları koru.
- [x] **3. Kırmızı test ve en küçük düzeltme:** Kanıtlı her kod hatası için sentetik gerçek comparator/planner/SQL testini önce başarısız çalıştır; ilgili compare/planning/parsing katmanını düzelt. Belirsiz metadata ve gerçek bağımlılık negatif testleri koru.
- [x] **4. Nesne bazlı yeniden doğrulama:** Aynı sabit source/target snapshotlarıyla yeni planı üret; eski 2.355 kaydı yeni kararlarla eşle. Uyarı/READY/REVIEW/gerçek engel sayıları ve gerekçelerini tek tek doğrula. SQL grammar/identity, manifest ve tam pytest çalıştır.
- [x] **5. Jenkins teslimi:** Doğrulanmış yeni release'i kur; rapor/SQL/inceleme kaydını yalnız Jenkins'te arşivle, genel maili tek alıcıya gönder. 08:00 normal TTBP akışını geri yükleyip UI'dan doğrula. yz devir/doğrulama kayıtlarını güncelle; yalnız yetkili uygulama kodunu pushla.
