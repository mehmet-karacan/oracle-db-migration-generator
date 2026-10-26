# Ortak UI ve Oracle kaynak desteği uygulama planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Git/Oracle kaynağı, bağlantı ve profil yönetimi, gerçek karşılaştırma başlatma/takip/sonuç ve doğrulanan ayar ekranlarını aynı uygulamada sunmak.

**Architecture:** Mevcut Python motoru korunur. Ayrı kontrol paketi doğrulanmış kayıtları/sırları/iş kuyruğunu yönetir, uzun işler API isteğinde çalışmaz. React arayüz aynı API'yi kullanır. Yeni API varsayılan olarak kimlik doğrulamasız ortak erişime açılmaz, yerel geliştirme açık loopback modu, ortak dağıtım imzalı kimlik proxy'si gerektirir.

**Tech Stack:** Python/FastAPI/SQLite/Fernet, React/TypeScript/Vite/shadcn(Radix)/Tailwind/TanStack Table. Oracle mevcut salt okunur collector.

**Spec:** docs/UI_KAPSAMI_VE_AYARLAR.md, kullanıcı 24 Ekim “Hadi geliştirmeye başla”.

## Global Constraints

- Git-only mevcut snapshot/plan/SQL formatı değişmez, Oracle kaynağı gerçek origin/capture kimliği taşır, sahte commit yok.
- Oracle DDL/DML/COMPILE, dış push/commit ve mevcut canlı Jenkins job değişikliği yok.
- Gerçek kurumsal SQL Jenkins-only politikasında kalır. Yerel geliştirme çıktısı Git dışındaki test/geliştirme çalışma alanındadır, ortak production arşiv entegrasyonu yapılandırılmadan dev modu production diye sunulmaz.
- Kurumsal SSO/proxy adresi ve dağıtım hedefi verilmedi, yapılandırılabilir imzalı proxy doğrulaması uygulanır, canlı entegrasyon NOT_RUN kalır.
- Mevcut uncommitted rapor/performance değişiklikleri korunur. Yerel codex/shared-ui-oracle-source branch'inde, kullanıcı tarafından seçilen aynı workspace'te çalışılır, ayrı onay/commit/push yok.
- Test önce kırmızı, sonra en küçük doğru uygulama. Aşamalar output/shared-ui/progress.md'ye kaydedilir.

## Review Focus

- Sahte proxy başlığı, yetkisiz bağlantı kullanımı, sırların JSON/log/artifact'e sızması reddedilmeli (Task 1/3).
- Oracle kaynağı Git commit'e zorlanmamalı, TARGET tarafına ait kanıtlar SOURCE'a doğru taşınmalı (Task 2).
- Ayar değişikliği geçmiş/çalışan işi değiştirmemeli, sonuç filtresi planı etkilememeli (Task 1/3).
- Hatalı/kararsız/eksik Oracle capture sıfır fark veya başarı diye sunulmamalı (Task 2/3).
- İş API sürecinden bağımsız sürmeli, tekrar başlatılan API yarım işleri başarıya çevirmemeli (Task 3).

### Task 1: Kayıtlar, sırlar ve etkin ayarlar

Files: control/{models,store,auth}.py, tests/unit/test_control_store.py.
Interface: validated connection/profile/settings documents, immutable sanitized run specification, encrypted credential resolution.
- [x] RED: invalid endpoints/refs/unsupported policy, admin/operator ACL, encrypted secret roundtrip, immutable revision/config snapshot, bounded settings.
- [x] GREEN: typed validation, SQLite atomic revisions, Fernet secret vault, signed proxy verification/local loopback guard.
- [x] Verify focused tests, no network/SQL.

### Task 2: Gerçek Oracle kaynak kimliği

Files: source/oracle_reader.py, model/{snapshot,snapshot_io}.py, schemas/{snapshot,plan,run}.schema.json, planning/rules.py, artifacts/bundle.py, emission/sql.py, reporting/view.py, runtime/aggregate.py.
Interface: collect_source(...) -> SOURCE snapshot + provenance/receipt, source_commit=None, legacy Git serializations unchanged.
- [x] RED: fake collector capture converted with SOURCE evidence, unstable capture blocked, Oracle plan and real CREATE SQL, old Git source descriptor exact.
- [x] GREEN: optional typed Oracle origin, capture ID and semantic fingerprint, shared collector full capture, both source descriptors through plan/report/bundle.
- [x] Verify source + contracts + representative existing planner tests.

### Task 3: API ve bağımsız iş çalıştırma

Files: control/{api,runner,worker,settings}.py, tools/ui_server.py, tests/unit/test_control_api.py, tests/acceptance/test_control_run.py.
Interface: /api/{session,connections,profiles,settings,runs}, connection test and run detail/operations/artifacts, standalone worker consumes frozen config.
- [x] RED: anonymous/forged access denied, invalid config cannot start, operator cannot use restricted connection, real Git fixture + offline Oracle collector produces verified SQL, API restart marks orphaned jobs interrupted.
- [x] GREEN: validated CRUD, audit, bounded process queue, current engine invocation, progress and real failures, paginated canonical operations, safe artifact path/size controls.
- [x] Verify API and acceptance tests, production unconfigured identity remains closed.

### Task 4: shadcn ortak uygulama

Files: web/ React app and official shadcn components, tests form/API behavior.
Interface: real API client, connection/profile/settings dialogs, source selection, job progress and results.
- [x] RED: source-kind switch validation, frozen request/settings rendering, failed API request visible, server paging preserved.
- [x] GREEN: approved logo and Innova tokens, accessible responsive app, connection test, save/start, jobs and SQL detail, no demo success counters.
- [x] Verify npm tests/build and browser against actual local API.

### Task 5: Tam doğrulama ve devir

- [x] Full Python suite + contracts, frontend tests/build, local browser end-to-end with isolated fixture, independent whole-change review and necessary RED→GREEN fixes.
- [x] Runtime docs/optional dependencies/launch commands, updated ADR user scope extension, yz devir/status.
- [x] Production SSO/Jenkins archive deployment/live Oracle acceptance statuses reported separately, no claim without evidence.

## Teslim kanıtı

1053 Python testi, 3 UI testi, TS/Vite build ve 7schema/8example sözleşme doğrulaması geçti.
Bağımsız incelemedeki 7 önemli bulgu RED→GREEN ile düzeltildi. Tarayıcı gerçek API/SQL
akışı sentetik girdilerle doğrulandı. Ortak deployment/canlı Oracle NOT_RUN, bu planın
son maddesinde istendiği gibi ayrı raporlandı. Ayrıntı yz/DEVIR.md.
