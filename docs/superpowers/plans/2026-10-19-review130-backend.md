# 130 İnceleme Kaydının Motor Tarafında İncelenmesi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 130 inceleme kaydını tek tek kanıtlandırmak, doğrulanan motor hatalarını düzeltmek ve 51 destek/önkoşul engelinin teknik işlerini somutlaştırmak.

**Architecture:** Mevcut Python snapshot → compare → rule/graph → SQL akışı korunur. Eski source snapshot'taki dependency sidecar'ları aynı SHA/hash ile yeniden bağlanır. Sunumdan bağımsız, mevcut plan JSON sözleşmesi ve SQL dosyaları üretilir.

**Tech Stack:** Mevcut Python CLI, ANTLR adaptörü, immutable snapshot/plan, pytest.

**Spec:** AKTIF_GOREV.md, docs/DDL_KURALLARI.md ve kullanıcının 130 inceleme/motor çalışması yetkisi.

## Global Constraints

- Source ve target her zaman salt okunur, bu tur mevcut yerel snapshot'lar yeterli. SQL uygulanmaz.
- HTML/CSS/renderer ve JSON schema sözleşmeleri değiştirilmez, eşzamanlı tasarım çalışması korunur.
- Grant allowlist, daraltma/tip/NOT NULL, sayaç ve gerçek metadata gereksinimleri varsayımla gevşetilmez.
- Paket/SQL gövdesi yeniden biçimlendirilmez, referans projeler ve eski output paketleri değiştirilmez.
- Yerel sırlar .local altında kalır, commit/push/Jenkins/TTBP kurulumu yok.

## Review Focus

1. Paket union sidecar'ın yanlış owner/name veya ilgisiz body'ye bağlanması: birebir kimlik/path testi.
2. Dinamik SQL'in dictionary dependency listesiyle yanlış READY olması: declared KNOWN olsa da review testi.
3. Aynı kolonlardaki ilgisiz/unusable/disabled/eksik kanıtlı indeksin backing index sanılması: olumsuz dictionary sınır testleri.
4. Trigger'da sequence assignment dışındaki çağrı/DML/header etkisinin kabul edilmesi: tek dar gövde olumlu, ek statement olumsuz testi.
5. 130 eski işlemin yeni planda fark veya kanıt kaybetmesi: her eski change_id için yeni kapsama eşlemesi.

## Task 1: Paket dependency kapsamı ve dinamik SQL

**Files:** source/sidecars.py, planning/object_rules.py, tests/unit/test_review130.py.
**Interfaces:** merge_sidecars(snapshot, artifacts) mevcut arayüz, JSON body `dependencies`/kanıt alanları mevcut sözleşmede.

- [x] Birleşik PACKAGE sidecar → spec/body ve explicit body kapsamı için kırmızı test.
- [x] merge_sidecars içinde eşleşen çiftleri kanıtla bağla, tekrar bağlamayı idempotent tut.
- [x] declared KNOWN + EXECUTE IMMEDIATE için kırmızı test, dinamik SQL'i incelemede tut.
- [x] Dar testleri çalıştır, eski source ham DDL/hash değişmeden yeni source snapshot türet.

## Task 2: Mevcut doğrulanmış PK/UK backing index

**Files:** planning/backing_index.py, planning/object_rules.py, tests/unit/test_review130.py.
**Interfaces:** existing_backing_index(context, index, table, columns) → kanıt ID tuple veya None.

- [x] Kaynak implicit PK/UK ve hedefte dictionary ile doğrulanmış farklı adlı backing index için kırmızı test.
- [x] Enabled/validated constraint, owner/table, ordered columns, valid normal unique index, görünürlük ve implicit kaynak association kontrolü uygula.
- [x] Eksik/disabled/unusable/başka kolon/explicit ad negatiflerini doğrula, yalnız mükerrer indeks işlemini INFORMATIONAL yap.

## Task 3: Yeni boş tablo için dar sequence trigger

**Files:** planning/object_rules.py veya planning/trigger_rules.py, tests/unit/test_review130.py.
**Interfaces:** Mevcut SqlIntent/DependencyReference, yeni JSON alanı yok.

- [x] Yeni boş tablo ve `:NEW.ID := sequence.NEXTVAL` tek gövdesi için kırmızı test.
- [x] Yalnız basit BEFORE INSERT/FOR EACH ROW, doğrulanmış NUMBER kolon ve tek sequence atamasını kabul et, sequence/table graph kanıtını koru.
- [x] Ek DML/çağrı, eksik sequence, mevcut tablo, identity/virtual, farklı header olumsuzlarını doğrula.

## Task 4: 130 satır denetim ve teslim

**Files:** output/review130-* (Git dışı), yz/INCELEME_130.md, yz/TEKNIK_EKSIKLER_51.md ve devir kayıtları.

- [x] Her eski inceleme kaydını nesne, gerekçe, önce/sonra, yeni karar ve kanıtlarıyla eşle.
- [x] Aynı 2.353 farkın tamamını kapsayan schema-valid plan JSON ve gerçek SQL üret, HTML üretimini çağırma.
- [x] Kısa tam pytest ve schema sözleşme kontrolünü çalıştır, bağımsız son kod incelemesi yap.
- [x] SQL grammar/hash/dependency ve sır kontrollerini doğrula, 51 engel için somut destek işi/çözüm koşulu kaydet.
- [x] Güncel devir/durum/doğrulama belgelerini güncelle, canlı DDL kabulü ve Jenkins NOT_RUN kalır.

Kullanıcı doğrudan uygulamayı yetkilendirdi, ek tasarım/onay turu yok. Commit/push adımı yoktur.
