# Engelli ve İnceleme İşlemleri Uygulama Planı

> **For agentic workers:** Mevcut yetki kapsamında inline executing-plans. Yeni tasarım/onay turu, commit ve push yok.

**Goal:** INNOVA_ODI kabulündeki 76 işlemin tamamını kanıtıyla incelemek, güvenle üretilebilenleri düzeltmek.
**Architecture:** Aynı Python parser, kanonik snapshot ve deterministik planlayıcı. Kaydedilmiş gerçek gözlemler değişmez. Yeni planlar ayrı özel arşive yazılır.
**Tech Stack:** Mevcut Python/ANTLR, pytest ve yerel UI.
**Spec:** Kullanıcının 26 Ekim 2026 talimatı, docs/DDL_KURALLARI.md ve kaynak/hedef sözleşmesi.

## Global Constraints

- Oracle DDL/DML/COMPILE, iş verisi okuma, SMTP, Jenkins değişikliği, commit/push yok.
- Kaynak gövdeleri, ham DDL ve eski raporlar korunur. Gerçek SQL yalnız .local özel arşivinde.
- UNKNOWN, daraltma, benzersizlik veya çalışma zamanı etkisi kanıtsız READY olmaz.
- İlk 76 işlem tekil ID ile başlangıç/son karar, gerekçe, fark ve kanıta bağlanır.
- Canlı gözlem ve SQLcl dosyası aynı kaynakla tekrar karşılaştırılır.

## Review Focus

- LOB clause kaybı, yanlış kolon eşleşmesi, SECUREFILE/partition/CTAS yanlış kabulü.
- BYTE/CHAR değişiminde karakter ve bayt kapasitesinin birlikte kanıtlanması.
- NULL gevşetmede PK/NOT NULL/CHECK ayrımı, eksik dictionary, generated kolonlar.
- Oracle dictionary dependency ile exporter dependency ayrımı, INVALID/stale kaynak ve dynamic SQL.
- Eski hazır SQL'lerin ve farkların değişmemesi, yeni bağımlılıkların doğru sıralanması.

### Task 1: Başlangıç denetimi
- [x] Sabit kaynak/hedef ve plan hash'lerini doğrula,76 işlemlik özel JSON/CSV başlangıç kaydı oluştur.
- [x] Her kategori için gerçek kök nedeni ve gerekli ek koşulu kaydet. PL/SQL dictionary kanıtının mevcut kullanımını ölç.

### Task 2: Güvenli üretim kuralları
- [x] Sentetik kırmızı test, minimal uygulama, negatif regresyon: yeni boş heap tabloda sınırlı BASICFILE LOB korunumu.
- [x] Sentetik kırmızı test, minimal uygulama, negatif regresyon: kapasitesi kanıtlanmış VARCHAR2 BYTE→CHAR genişlemesi.
- [x] Sentetik kırmızı test, minimal uygulama, negatif regresyon: metadata ile doğrulanmış NOT NULL gevşetme.
- [x] Kaynak bağımlılık kanıtını doğru kullanabilen dar durumları test et. Eksik/INVALID/dinamik referanslarda engeli koru.
- [x] Kalan inceleme nedenlerini somut özellik/değer ve eksik koşulla açıkla.

### Task 3: Kanıtlı teslim
- [x]76 başlangıç kaydının tamamını yeni kararlara eşle, fark kümesi ve eski hazır SQL'leri doğrula.
- [x] İki hedef yolunda yeni plan/DDL eşdeğerliğini ve bundle bütünlüğünü doğrula.
- [x] Tam birim testleri ve gerekli yerel UI kontrolü, yeni rapor, kalıcı devir ve kullanıcıya sayısal sonuç.

Tamamlandı: docs/INNOVA_ODI_ISLEM_INCELEMESI.md ve özel verification.json.
