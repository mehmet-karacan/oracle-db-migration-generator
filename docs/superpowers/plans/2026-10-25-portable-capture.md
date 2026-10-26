# Portable Capture Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. One final read-only independent reviewer.

**Goal:** Parametreli SQL*Plus/SQLcl toplama, proje bağlı import ve filtreli offline karşılaştırma.
**Architecture:** Sadece SELECT + DBMS_METADATA üreten tek SQL collector, hex bind request, JSONL/Base64 taşıma. Kontrol API/CLI ortak Python filtresi ve kanonik motor.
**Tech Stack:** Mevcut Python/React/shadcn. Üretim tarafında mevcut SQL*Plus/SQLcl, isteğe bağlı Windows PowerShell5.1 launcher. Yeni servis yok.
**Spec:** docs/TASINABILIR_TOPLAMA_TASARIMI.md.

## Global Constraints
- Oracle salt okunur. Sırlar pakete girmez, SQL payload hiçbir yerde çalıştırılmaz.
- 1 kaynak→N hedef, UNKNOWN, gerçek kaynak byte'ları ve proje sınırı korunur.
- Mevcut kirli codex/shared-ui-oracle-source dalında devam, commit/reset/push yok.
- Tam şema/filtreli kapsam ayrılır, veri tipi karşılaştırma kökü kaynakta sabitlenir.
- SQL*Plus/SQLcl/Oracle canlı kabul ayrı NOT_RUN.

## Review Focus
- Substitution/param SQL injection, Unicode/quote ve dosya yolu kaçışı.
- CLOB/LONG kesilmesi, stream footer/sıra/limit ve sayısal hassasiyet.
- ALL_* görünürlüğünden yanlış yokluk/tamlık, eksikmetadata'yı boş sayma.
- Filtre nedeniyle hedefte farklı veri tipine sahip mevcut tablonun kaybolması.
- Snapshot ID/credential/proje ayrımı, metadata dışı sorgu veya yazma.

### Task1 - Ortak filtre ve SQL paketi
- [x] Kırmızı filtre/script üretim testleri: şema/tür/ad/table/data_types, closure ve bind escaping.
- [x] portable/selection.py, builder.py, templates portable collector/launcher/README.
- [x] CLI prepare-capture ve offline launcher/grammar doğrulaması.

### Task2 - Stream ve kanonik snapshot
- [x] Kırmızı bozuk/eksik/parça/sıra/Unicode/sayı/yetki testleri.
- [x] JSONL okuyucu ve mevcut projection/enrichment ile offline adapter.
- [x] import-capture/karşılaştırma CLI, filtre kapsamı ve gerçek SQL kabulü.

### Task3 - Projeye bağlı UI
- [x] Kırmızı import/project/SNAPSHOT bağlantısı ve filtre runner testleri.
- [x] Portable capture export/import paneli, snapshot seçimi ve ortak filtreler.
- [x] Aynı kimlik kapsamıyla source/target runner, secret/Jenkins sınırı.

### Task4 - Teslim
- [x] README bütün parametreler/örnekler/yetki/çıkış/sınırlar.
- [x] Python/UI/build/lint/grammar/prepare-only/gerçek offline motor kabulü.
- [x] Bağımsız inceleme, önemli bulgu regression düzeltmesi.
- [x] Browser akışı ve yz kayıtları. Aktif görevin kapsamı değiştirilmedi.

Kanıt ve ledger output/portable-capture altında. Mimari yeniden araştırılmaz,
mevcut kararın uygulaması. Kullanıcı ek tasarım/onay turu istemedi.
