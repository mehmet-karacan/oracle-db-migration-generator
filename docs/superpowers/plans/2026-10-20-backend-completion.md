# Kalan motor yeteneklerinin tamamlanması

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Inline uygulama; sonda tek bağımsız bütün değişiklik incelemesi.

**Goal:** HTML/Jenkins dışında yerel INNOVA_ODI akışındaki motor destek eksiklerini kapatmak; gerçek veri/kaynak koşullarını somut raporlamak.

**Architecture:** Mevcut snapshot → compare → plan/graph → SQL akışı. RANGE/INTERVAL için typed doğrulama kaynak suffix'i aynen korur. Yeni function index kapalı ifade/tip/NLS kuralıyla doğrulanır. Mevcut partition farkları tanınan ama veri taşıyan dönüşüm olarak incelemeye ayrılır; DROP/recreate yok.

**Tech Stack:** Mevcut Python CLI/ANTLR/pytest; yeni servis, framework veya bağımlılık yok.

**Spec:** AKTIF_GOREV.md, docs/DDL_KURALLARI.md, yz/TEKNIK_EKSIKLER_51.md ve 20 Ekim kullanıcı talimatı.

## Global Constraints

- Source/target daima READ ONLY; SQL NOT_EXECUTED. Metadata okuması yalnız sabit allowlist sorgularla; iş verisi yok.
- HTML/CSS/renderer ve JSON schema sözleşmesi değişmez. Referans projeler salt okunur.
- Grant allowlist, veri daraltma/NOT NULL/public contract ve sayaç politikası değişmez.
- Kaynak nesne yokluğu/namespace çakışması varsayımla giderilmez; somut reason/kanıt üretilir.
- Aynı workspace kullanıcı tarafından yetkilendirildi; unborn repo/eşzamanlı HTML nedeniyle worktree/commit/push yok.

## Review Focus

1. RANGE bound sırası/arity/key tipi yanlışken grammar geçebilir: semantik doğrulama ve olumsuz test.
2. INTERVAL MAXVALUE/çoklu key/uyumsuz tip ile geçemez; kapalı ifade listesi.
3. Constraint ayırırken partition/depolama suffix'i veya inline key kaybolamaz; emission roundtrip.
4. Function index literalini kolon sanma, örtük dönüşüm ve farklı NLS ortamı; tip/kaynak ifadesi korunumu.
5. Metadata name resolution varlığı kolon/FK/spec uyumu sayılmaz; dar resolver ve negatif kanıt.

## Task 1 — RANGE/INTERVAL CREATE

Files: new planning/partition_rules.py; planning/{policy,table_rules}.py; tests/unit/test_backend_completion.py.
Interface: range_layout(obj, columns) → immutable RangeLayout veya ValueError; ham DDL değiştirilmez.

- [x] Yeni RANGE ve INTERVAL tablo/constraint/index/comment için kırmızı test; gerçek sekiz tablo suffix/hash kanıtı.
- [x] Key/bound/interval typed doğrulama, artan sınırlar ve kapalı destek; CTAS/LOB/IOT/subpartition/invalid interval negatifleri korunur.
- [x] Yalnız doğrulanan partition gate açılır; TABLE_BASE ve constraint grafı aynı kalır; emitted SQL yeniden parse edilir.

## Task 2 — Function index ve mevcut partition farkları

Files: new planning/index_rules.py; planning/object_rules.py, planning/table_rules.py; aynı test dosyası.
Interfaces: index_key_columns(context, table, key_tokens) → kolonlar ve ortam koşulları; partition_change(context, desired, actual, changes) → mevcut Operation.

- [x] DATE/TIMESTAMP TO_CHAR(typed_column,'YYYYMM') için gerçek SQL ve parent dependency kırmızı testi.
- [x] Destek dışı/dynamic/user-function/implicit conversion/unknown type kanıtlarını READY yapma; raw ifade aynen kalır.
- [x] Mevcut partition farkını typed key/bound/interval üzerinden ayır; yalnız fiziksel fark policy ile INFO, gerçek yerleşim değişimi REVIEW, belirsizlik BLOCKED.

## Task 3 — Eksik bağımlılıkların somutlaştırılması

Files: oracle/queries.py ve gerektiği kadar collector/metadata; planning/graph.py; aynı test dosyası.
Interface: mevcut KnownValue capabilities içinde kanıtlı name-resolution; JSON schema değişmez.

- [x] Eksik relation/callable, PUBLIC synonym ve yanlış tip/kolon/FK için kırmızı test.
- [x] Yalnız gerekli metadata'yı READ ONLY sorgularla yakala; yeni ayrı snapshot/receipt üret, eski output'a yazma.
- [x] Kaynak orphan index ve ortak namespace çakışmasına tekil neden ver; kayıp kaynak üretme veya target nesne silme yok.

## Task 4 — Teslim ve doğrulama

Files: output/backend-completion-* JSON/SQL bundle ve denetim makbuzları; yz durum/devir/doğrulama kayıtları.

- [x] Tüm 2.353 farkın kapsandığını ve eski 55 bloğun nesne bazlı yeni kararını doğrula.
- [x] Kısa tam pytest, 6 schema/7 örnek; reference hash ve HTML/schema sınırları; sır/endpoint scan.
- [x] Her READY SQL grammar/identity/hash ve dependency sırası; deterministik offline tekrar; tek bağımsız kod incelemesi ve gerekli düzeltme.
- [x] Ürün destek eksikliği ile gerçek kaynak/veri/policy koşullarını ayrı teslim et. Canlı DDL/Jenkins NOT_RUN; HTML bekleniyor.

Ek tasarım/onay ve commit adımı kullanıcı talimatıyla yoktur. Veri taşıyan bilinmeyen dönüşüm sırf blok sayısını azaltmak için hazır yapılamaz.
