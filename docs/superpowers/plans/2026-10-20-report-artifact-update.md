# ODMG-RPT-UPDATE-001 - Onaylı rapor ve artifact güncellemesi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Kullanıcı mevcut görev bitince bu ZIP'in uygulanmasını açıkça yetkilendirdi, inline uygulama ve sonda tek bağımsız inceleme.

**Goal:** Onaylı iki HTML referansını gerçek run/plan verilerine bağlamak, benzersiz plan + ayrı build/run kayıtları, nesne klasörleri, güvenli sabit yayın linkleri üretmek.

**Architecture:** Mevcut compare/planner korunur. Artifact layout/store/publisher ve report view/template katmanları tamamlanır. Plan immutable, run gözlemseldir. Aynı plan iki build'de bir kez saklanır, SQL veya tarih planı değiştirerek dedup bozulmaz.

**Tech Stack:** Mevcut Python/Jinja2/jsonschema, stdlib dosya/Git/HTTP adaptörleri. SMTP veya yeni web servis yok.

**Spec:** AKTIF_GOREV.md (ZIP görevi), reference-ui/{artifact-browser,report-email}.preview.html, ARTIFACT_SOZLESMESI/HTML_STANDARDI/GUVENLIK.

## Global Constraints

- Source ve target daima READ ONLY. Bu aşamada yeni Oracle bağlantısı yok, doğrulanmış source-review130-v2 / target-reparsed-backend-v2 kullanılır.
- Parser/compare/karar/DDL gövdeleri yeniden yazılmaz. Önceki motor paketi/kanıtları değişmez.
- Onaylı web 1.100 px, mail 820 px referans, renk/logo/inline mail stilleri korunur. Sentetik demo sayıları/indirmeleri üretime kopyalanmaz.
- Gerçek push, SMTP, Jenkins ayarı ve code repo commit yok. Publisher yalnız açık çağrılan opt-in API, gerçek iş bu tur NOT_REQUESTED.
- JSON ekleri kapalı schema ve eski örneklerle geriye uyumlu. Tarih/build plan hash'ine girmez.

## Review Focus

1. Aynı plan ID altında farklı bytes veya mevcut kullanıcı dosyası: overwrite değil INTEGRITY_CONFLICT/ownership hatası.
2. Uzun/quoted/zararlı object name dosya yolu veya HTML/Markdown injection olamaz, hash tabanlı güvenli bileşen ve escaping.
3. ERROR target hiçbir KPI'da sıfır fark gibi gösterilmez, 5 target/10 benzersiz nesne sınırı gerçek toplamı değiştirmez.
4. Başarısız/public/kanıtsız push ve retention linki mailde başarı gibi görünmez, SHA ve allowlist URL doğrulanır.
5. Plan ve run commit SHA öz-referans döngüsü: run.json artifact_git_sha planı içeren commit, e-posta linki run README'yi içeren son commit. İki commit tek başarılı push ile tutarlı yayımlanır.

## Task 1 - Nesne klasörleri ve hazır SQL sözleşmesi

Files: artifacts/layout.py, artifacts/bundle.py, emission/sql.py, test_report_artifact_update.py.
Interface: object_sql_path(operation) → güvenli objects/schema/type/name/op-id.sql, review kanıtı/README aynı nesneye bağlı.

- [x] Kırmızı test: nested gerçek SQL, review kanıtı, hazır/kısmi SQL ayrılığı, eski flat bundle doğrulanabilir.
- [x] Ham SQL/operation sırası/hash korunarak dosya layout ve README bağlantılarını uygula.
- [x] Uzun/reserved/path-traversal isimler ve aynı object'te çoklu operasyon negatiflerini doğrula.

## Task 2 - Yerel run/plan store ve katalog

Files: artifacts/store.py, artifacts/catalog.py, CLI, run/catalog schemas ve örnekler.
Interface: archive_run(run_root, store, build_number=None) → run_path, plan refs, yeni/reused plan sayısı.

- [x] İki build/ayrı run ID/aynı plan bir kez, ERROR target, ownership ve integrity conflict kırmızı testleri.
- [x] plans/profile/target/id, runs/date/build-id, latest ve hafif catalog/README üret, plan/run önce, katalog en son atomik yaz.
- [x] Sır taraması, path/symlink ve başarısız transaction sınırlarını doğrula, kullanıcı dosyaları korunur.

## Task 3 - Opt-in publisher ve sabit link

Files: artifacts/publisher.py ve Git adapter, reporting/links.py.
Interface: publish_run(store, run_path, destination, git) → doğrulanmış publication receipt, render link yalnız receipt'den.

- [x] Private/storage-policy/host ve başarısız push/404/retention/commit-SHA link kırmızı testleri.
- [x] Generated namespace dışında stage/commit yok, no force, bounded fail, kimlik bilgisi argv/log'a girmez. Gerçek remote çağrısı bu tur yok.
- [x] Plan commit + yeni run commit ayrımı, dedup ve son commit URL'si, başarısızlıkta Jenkins arşivi yalnız erişilebilir kanıtı varsa alternatif.

## Task 4 - Onaylı web/e-posta görünümü

Files: reporting/{view,render,links}.py, templates/assets, runtime/aggregate.py.
Interfaces: build_run_view(run, plans, publication=None), render_email(view, preview=False), render_run_reports(view).

- [x] 0/100+ target, 1.000+ nesne, çok hedefte aynı nesne, ERROR/UNKNOWN, escaping ve sayı ayıracı kırmızı testleri.
- [x] 5 kritik target/10 benzersiz önemli nesne, gerçek KPI ve bağımlılık/reason bilgisi, SQL gövdesi mailde yok.
- [x] Statik web + inline/CID mail, Run→Target→Plan→Object ve JSON/manifest/DDL gerçek dosya linkleri, 200 KiB bütçe ve pagination.

## Task 5 - Gerçek veriyle offline teslim

- [x] Mevcut source/target snapshot ile yeni plan/bundle/run/store üret, motor sayıları 2.353/559/123/5/1.038 korunmalı.
- [x] İki run aynı plan dedup, tüm hash/link/aggregate kontrolleri, sır/endpoint scan, kısa tam pytest ve schema kapısı.
- [x] Onaylı referans ile 390/820/1.440 px browser kontrolü, tek bağımsız kod incelemesi ve gereken kırmızı→yeşil düzeltmeler.
- [x] Devir/durum/doğrulama, Jenkins taslak entegrasyon gereksinimlerini somut bırak. Gerçek yayın, SMTP, Jenkins NOT_RUN.

Ruling: Onaylı ZIP spec + doğrudan kullanıcı uygulama yetkisi ek tasarım turunu gerektirmez. Eski task ve ZIP orijinali output/report-update-original altında, active task'ta sadece bağlantı URI .local'a yönlendirilmiştir. Yeni worktree/commit yok, aynı workspace kullanıcı tarafından yetkilendirildi.
