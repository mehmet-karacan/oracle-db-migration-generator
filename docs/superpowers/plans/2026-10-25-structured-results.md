# Structured Results Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, one final read-only reviewer.

**Goal:** Nesne → fark özeti → gruplanmış ayrıntı → ilgili SQL akışını teslim et.
**Architecture:** Canonical kayıtların salt okunur sunum projeksiyonu, mevcut UI ve Python kontrol API.
**Tech Stack:** React/TypeScript/shadcn, FastAPI/Python. Yeni framework veya servis yok.
**Spec:** docs/SONUC_INCELEME_TASARIMI.md (kullanıcı onaylı mesajın somut sözleşmesi).

## Global Constraints
- Motor/plan/DDL değişmez. UNKNOWN, kaynak/target yönü, proje ve 1→N sınırı korunur.
- Yerel SQL özel run içinde, Jenkins SQL uzak arşivde, canlı run/SMTP/push yok.
- Mevcut kirli codex/shared-ui-oracle-source dalı devam eder, commit/reset yok.
- Kullanıcı metni Türkçe/TR-EN, tanımlayıcılar English ASCII.

## Review Focus
- Sayfalama sınırında bölünmüş FK/kolon ve eksik toplam özeti.
- MISSING alanı tüm nesne/kolon yokluğu sanma, UNKNOWN'u gizleme.
- Filtre/hedef/proje değişirken eski yanıt veya SQL'in geri gelmesi.
- Özgün DDL yolu/span/hash yanlışlığı ve Jenkins SQL'ini yerelleştirme.
- Büyük/boş/tekrarlı satırlı SQL'de içerik/line number kaybı veya DOM patlaması.

### Task 1: Kanonik yapısal projeksiyon
- [x] Kırmızı test:2FK/22alan, tam grup sayfalama, fark türü filtresi ve UNKNOWN.
- [x] results.py group/summary/filter projeksiyonu, API closed arg doğrulama.
- [x] İlgili Python testleri yeşil.

### Task 2: Grup ve nesne akışı
- [x] Kırmızı UI testi: özet, bağlam, tek grup adı, aç/kapat, grup SQL erişimi.
- [x] ObjectResults fark filtresi, ObjectComparisonPanel gruplanmış görünüm.
- [x] CSS/TR-EN ve eski seçim/scroll/hata testleri yeşil.

### Task 3: Özgün tanım karşılaştırması
- [x] Kırmızı test: yerel snapshot hash/span/quote, proje ve Jenkins sınırı.
- [x] Object definition endpoint ve bounded satır karşılaştırma görünümü.
- [x] İki özgün tanım ve eksik/arşiv durumları testte yeşil.

### Task 4: Teslim kabulü
- [x] Build/lint/UI/ilgili Python ve offline motor kabulü.
- [x] Gerçek#55 gruplar, ayrı offline fixture SQL, TR/EN/tema/dar ekran kontrolü.
- [x] Tek bağımsız inceleme, önemli bulgu regression düzeltmesi.
- [x] AKTIF_GOREV eki ve yz/GELISTIRME_DURUMU, yz/DEVIR güncel.

Kanıt/ledger output/structured-results altında. Ayrı araştırma/ürün/framework
fazı yok. Son kullanıcı onayı doğrudan uygulama yetkisidir.


Son kabul:55UI/17dosya,84Python kontrol/ayrılık/özgünDDL/gerçek offline motor
kabulü PASS. Build PASS, lint0hata/3öncekiFastRefreshuyarısı. Bağımsız incelemenin
tekP2 bulgusu (scroll ile DOM birikmesi) sabit300satır pencere/spacer ve kırmızı→
yeşil regression testiyle kapandı. Ham nesne metadata'sı etiketli yapılarla
sunulur, iç içe değerler ve büyük listeler aşamalı açılır. Tab/tabpanel ARIA bağı
ve EN varlık/çoğul adları regression kapsamındadır. Gerçek kullanıcı5sn ölçümü,
kurumsal dağıtım, yeni canlı Oracle/Jenkins/SMTP/push NOT_RUN.
