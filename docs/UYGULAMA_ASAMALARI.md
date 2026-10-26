# Ürün yol haritası ve sonraki aşama kapıları

Bu belge başlangıç paketindeki ayrıntılı A00–A13 planını korur. Aktif çalışma
önceliği AKTIF_GOREV.md içindedir, buradaki geniş kabul/dağıtım kapıları yerel
başlangıcın ön koşulu değildir.

---

# AKTİF GÖREV - Oracle DB Migration Generator

**Görev kimliği:** ODMG-001 · **Sürüm:** 1.0 · **Durum:** Uygulamaya hazır.

**Amaç:** Mevcut iki Python ürününün kanıtlı extraction/parser/compare/HTML bileşenlerinden yararlanarak, tek source Git DDL durumunu N hedefe göre değerlendiren ve hedefe özel güvenli SQL/JSON/HTML paketleri üreten bağımsız Generator'ı uygulamak.

**Uygulama:** Mimari bu pakette tanımlıdır. Kullanıcı bu dosyayı uygulama görevi olarak verdiğinde aşağıdaki aşamaları uygula, yeni araştırma promptu, framework seçimi veya ek mimari tasarım turu açma.

## Önce Oku

`AGENTS.md` → `yz/MIMARI_KARARLAR.md` → `docs/MIMARI.md` → `.local/session-context.json` → `reference-lock.json` → `docs/YENIDEN_KULLANIM.md` → `docs/CODEX_ARAYUZLERI.md` → `docs/KAYNAK_HEDEF_SOZLESMESI.md` → `docs/DDL_KURALLARI.md`. Sonra aşamaya ilişkin HTML/Jenkins/artifact/güvenlik/doğrulama belgeleri.

Bu dosya tek başına mimariyi kayıpsız taşıma iddiasında değildir, **paketin tamamı proje kökünde** bulunmalıdır. Eksik bir zorunlu belge varsa uydurma planla devam etme, eksik dosyayı bildir, güvenli referans/env doğrulamasını yap. Birden fazla aktif görev yaratma.

## Değişmez Kurallar

- Kaynak DDL deposu, Generator kod deposu ve Artifact deposu ayrı. Adres/dizinler `.local` bağlamında, genel kaynaklara gerçek endpoint yazılmaz.
- Sync ve Analyzer kaynakları salt okunur. Yeni ürüne taşınan sınırlı bileşenlerin provenance/lisansı korunur. Eski projelerde refactor yok.
- Python CLI/kütüphane, 1→N Jenkins registry, aynı source SHA, tam durum karşılaştırması, SQL üretimi ama DB'de execution yok.
- Source desired, target actual, before=target, after=source. Eksik metadata boş liste veya NO_CHANGE değildir.
- DDL_KURALLARI matrisindeki pozitif üretimler **gerçekten çalışacak**. TODO/stub, hep boş SQL veya her şeye unsupported cevabı kabul edilmez.
- Varsayılan DROP, RENAME tahmini, sequence reset, production/data mutation, schema string replacement yok.
- HTML mevcut `innova-db-report/1.0` ailesi. İlk5 DDL preview, tüm SQL ayrı, kanıtlı artifact.
- Key/token/parola sohbet veya dosyaya yazılmaz. Gerçek Git push/Jenkins job değişikliği/DB DDL için ayrı izin gerekir. Offline/fake Git tests serbest.

## İnceleme Bulgularını Tekrar Keşfetme

DDL extraction'ın kullanılacağı dosyalar Sync `oracle_client.py`/`metadata.py`, by_object/flat yerleşimi `layout.py`/`writer.py`, parser ve structured diff Analyzer `oracle/*` ve `changes.py`, HTML Analyzer `innova_v1`, kapsam referansı Schema Compare `TableMetadataComparator.java`. Tam eşleme ve bilinen tehlikeli davranışlar YENIDEN_KULLANIM belgesindedir.

SKY kaynak profili adayı master + ttbp/innova_odi by_object v1'dir, bu **yüklenen yapılandırmanın kanıtıdır**, uzak repo erişim iddiası değildir. Gerçek repo erişildiğinde doğrula. Mevcut Analyzer HTML'inde aktif aile v5 değil innova-db-report/1.0'dır.

## Her Aşamanın Çalışma Döngüsü

İlgili kabul testinin anlamlı kırmızı sonucunu yaz/çalıştır, uygulamayı ekle, testleri tekrar çalıştır, yalnız gerçek geçti sonucunu kaydet. Aşama sonunda `yz/GELISTIRME_DURUMU.md` ve `yz/DEVIR.md` güncellenir. Git commit/push otomatik yapılmaz. Bir sonraki aşama öncekinin tanımlı arayüzünü tüketir, yeni sözleşme icat edilmez.

## İnceleme Odağı

Yön tersliği, unknown→absent dönüşümü, metadata çıkarımında hata yutma, PL/SQL semicolon splitting, default/string/identifier semantiği kaybı, N target credential karışması, generated SQL ile execution başarı kaydının karışması, HTML kısaltması nedeniyle tam artifact kaybı, source/project dosyalarının silinmesi. Aşağıdaki test kapıları bunları ölçer.

## Uygulama Aşamaları


### A00 - Çalışma Alanı Ve Referansları Sabitle

**Dosyalar:** tools/verify_references.py, vendor/PROVENANCE.json, yz/GELISTIRME_DURUMU.md

**Uygulama:** Kökteki origin/status ve .local yollarını oku, reference-lock.json hash’lerini kıyasla. Referanslarda hiçbir dosya değiştirmeden gerekli sembolleri aç. Schema Compare commit’ine sadece ihtiyaç duyulan dosyalar için bak. Dolu dizini temizleme. source-profile için master/ttbp/innova_odi adaylarını doğrulanacak bağlam olarak kaydet.

**Arayüz/çıktı:** A01 için mevcut kaynak yolu/hash ve uyarlama provenance başlangıcı. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_reference_paths_are_read_only`, `test_wrong_or_dirty_project_root_is_not_deleted`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python tools/verify_references.py --report output/reference-check.json` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A01 - Çekirdek Konfigürasyon Ve Domain

**Dosyalar:** pyproject.toml, src/oracle_db_migration_generator/{cli.py,config/,model/}, tests/unit/test_config.py, tests/contracts/test_schemas.py

**Uygulama:** Python CLI paketini kur, schemas/ dosyalarını API ile bağla. Target registry1-N/multi-schema/secrets sınırları, KnownValue/identity modelleri, source-profile ve exit code sözleşmesini uygula. Mevcut örnekleri sessiz gevşetmeden doğrula.

**Arayüz/çıktı:** load_source_profile/load_targets ve immutable domain tipleri. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_registry_all_discovers_three_targets`, `test_registry_unknown_id_fails`, `test_registry_requires_exactly_one_service_or_sid`, `test_registry_duplicate_target_and_mapping_rejected`, `test_empty_registry_is_not_success`, `test_secrets_are_not_serialized`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_config.py tests/contracts/test_schemas.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A02 - Git Kaynak Ve Yerleşim Okuyucusu

**Dosyalar:** src/oracle_db_migration_generator/source/{git_reader,layout,sidecars}.py, tests/unit/test_source.py

**Uygulama:** Git SHA’yı bir kez sabitle, by_object v1/flat keşfi, nested child ve sidecar toplama, duplicate/conflict, LFS/symlink/missing-root kurallarını uygula. Source’a yazma ve SQL execution yok.

**Arayüz/çıktı:** SourceRevision ve SourceInput kanıtlı dosya koleksiyonu. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_pinned_source_is_shared_by_all_targets`, `test_by_object_nested_children_and_sidecars`, `test_flat_combined_package_spec_body`, `test_missing_source_root_is_not_empty_schema`, `test_duplicate_conflicting_definitions_block`, `test_symlink_submodule_and_lfs_are_not_sql`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_source.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A03 - Mevcut Parser Bileşenlerini Uyarla

**Dosyalar:** src/oracle_db_migration_generator/{_vendor/,parsing/}, vendor/PROVENANCE.json, tests/unit/test_parsing.py

**Uygulama:** YENIDEN_KULLANIM haritasındaki saf parser/import kapanışını taşı, generated parser/runtime4.13.2/license/hash koru. Token/spans, source sidecar merge, unknown fields ve diagnostics adaptörünü yaz. Whole Analyzer/LLM/SMTP workflow’u taşıma.

**Arayüz/çıktı:** parse_source/parse_ddl/merge_sidecars, tamlık kaydı olan source snapshot. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_utf8_bom_crlf_quoted_names_and_qquote`, `test_comment_semicolon_does_not_split_package`, `test_unknown_syntax_blocks_only_affected_object`, `test_sidecar_grant_without_create_is_collected`, `test_literal_whitespace_case_is_not_normalized_away`, `test_parser_timeout_is_not_parse_success`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_parsing.py tests/contracts -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A04 - Salt Okunur Oracle Target Çıkarımı

**Dosyalar:** src/oracle_db_migration_generator/oracle/, tests/unit/test_collector.py

**Uygulama:** Sync extraction/sorgu yaklaşımını allowlist adapter’a uyarla, error→empty davranışını kaldır. Dictionary coverage, metadata izinleri, sürüm probe, target capture consistency, schema credential izolasyonu ve timeout ekle. Hiçbir gerçek hedefte DDL veya iş verisi okuma yok.

**Arayüz/çıktı:** collect_target → TargetObservation(snapshot, coverage, receipt). İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_ora01031_is_not_absence`, `test_dependent_ddl_unexpected_error_propagates`, `test_empty_visible_schema_requires_complete_inventory`, `test_snapshot_changes_during_capture`, `test_collector_uses_no_business_data_or_nextval`, `test_multi_schema_target_uses_isolated_credentials`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_collector.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A05 - Hedefe Doğru Semantik Karşılaştırma

**Dosyalar:** src/oracle_db_migration_generator/compare/, tests/unit/test_compare.py

**Uygulama:** Analyzer compare_projections adaptörünü old=target/new=source yönünde kullan, Schema Compare alan kapsamını tamamla. Identity, field missing/unknown, sequence runtime, logical/physical fark ayrımını uygula. Son Git diff’ine değil tüm snapshot’a bak.

**Arayüz/çıktı:** compare_snapshots → DifferenceSet. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_before_is_actual_after_is_desired`, `test_target_lag_is_not_limited_to_last_commit`, `test_unknown_field_diff_is_not_same`, `test_uppercase_quoted_identity_matches_unquoted`, `test_same_name_different_owner_or_type_no_collision`, `test_sequence_runtime_counter_is_informational`, `test_format_only_change_emits_no_sql`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_compare.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A06 - DDL Kural Ve Policy Motoru

**Dosyalar:** src/oracle_db_migration_generator/planning/{rules,policy}.py, tests/unit/test_rules.py

**Uygulama:** DDL_KURALLARI matrisi için olumlu READY kuralları ve olumsuz/review/block sınıfları uygula. Sadece missing object CREATE değil, mevcut tablo ADD/MODIFY, default, package body, index/constraint ownership, comments/grants ve no-drop akışları çalışsın.

**Arayüz/çıktı:** plan_target → gerekçeli TargetPlan operation listesi. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_empty_target_generates_complete_table_definition`, `test_existing_table_adds_only_missing_nullable_column`, `test_safe_varchar_widening_emits_modify`, `test_numeric_scale_or_shrink_requires_review`, `test_not_null_on_existing_table_requires_review`, `test_package_body_change_does_not_recreate_spec`, `test_unique_index_on_populated_unknown_table_review`, `test_backing_index_not_emitted_twice`, `test_target_only_object_is_preserved`, `test_missing_grantee_is_not_auto_granted`, `test_unsupported_partition_not_silently_removed`, `test_schema_remap_is_not_global_replace`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_rules.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A07 - Bağımlılık Ve İşlem Sıralaması

**Dosyalar:** src/oracle_db_migration_generator/planning/graph.py, tests/unit/test_graph.py

**Uygulama:** AST/sidecar/dictionary kanıtını derecelendir, stabil topolojik sıra, FK phase splitting, blocked dependency propagation uygula. View/type cycle için FORCE/stub yok. Tamlığı bilinmeyen dış referansları hazır sayma.

**Arayüz/çıktı:** order_operations → sıralanmış/engellenmiş operation set’i. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_fk_cycle_is_resolved_by_deferred_fk_phase`, `test_package_spec_and_sequence_dependencies`, `test_blocked_prerequisite_blocks_dependent`, `test_view_cycle_is_blocked`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_graph.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A08 - SQL Üretimi Ve Offline Doğrulama

**Dosyalar:** src/oracle_db_migration_generator/sql/, tests/unit/test_sql.py

**Uygulama:** Operation’lardan gerçek SQL üret, raw PL/SQL koru, table özellik kaybı için reparse kontrolü ekle. SQLPlus directives/terminator, tek ve kısmi plan dosya adları, postcheck önerileri, secret scan ve safe filename uygula. apply alt komutu ekleme.

**Arayüz/çıktı:** emit_sql/validate_sql → tam hash’lenebilir SqlBundle. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_sqlplus_delimiter_policy`, `test_partial_plan_is_not_named_migration`, `test_unchanged_target_has_no_migration_file`, `test_emission_reparse_preserves_features`, `test_secret_or_dblink_candidate_is_not_published`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_sql.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A09 - Deterministik Artifact Paketi

**Dosyalar:** src/oracle_db_migration_generator/artifacts/{bundle,catalog}.py, tests/unit/test_bundle.py, tools/check_contracts.py

**Uygulama:** Plan-core hash zinciri, timestamps ayrı run kaydı, atomik write, bütünlüğü doğrulanan dosya kataloğu ve self-describing target README üret. Hatalı planı no-change olarak yayımlama. Şema/semantic validation birlikte.

**Arayüz/çıktı:** write_bundle/verify_bundle → BundleManifest. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_same_inputs_have_identical_payload`, `test_hash_tamper_and_extra_file_rejected`, `test_windows_reserved_and_unicode_filenames_safe`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_bundle.py tests/contracts -q && python tools/check_contracts.py` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A10 - Mevcut HTML Standardını Uygula

**Dosyalar:** src/oracle_db_migration_generator/{reporting/,templates/,assets/}, tests/unit/test_reporting.py, tests/acceptance/test_html.py

**Uygulama:** innova-db-report/1.0 layout/token/logo’yu uyarla. AI-specific ifadeleri çıkar, ilk5 DDL30satır/2048karakter, target/fark pagination, relative CSS/logo/SQL/JSON linkleri ve 200KiB sınırı uygula. Full SQL’i görünmez HTML’e koyma. Mevcut görüntüyle tarayıcıda görsel karşılaştır.

**Arayüz/çıktı:** standart index.html ve target sayfaları, RenderManifest. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_five_previews_are_bounded`, `test_full_sql_not_hidden_in_html`, `test_approved_style_and_web_logo`, `test_html_escape_and_relative_links`, `test_target_and_changes_pagination`, `test_error_target_counts_are_unknown`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_reporting.py tests/acceptance/test_html.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A11 - Runtime Worker Ve Jenkins Pipeline

**Dosyalar:** src/oracle_db_migration_generator/runtime/, Jenkinsfile, tests/unit/test_runtime.py, tests/acceptance/test_jenkins_contract.py

**Uygulama:** Bağımsız worker, bounded parallel batches, schema credential scope, checkpoint/input verification ve always-archive aggregate uygula. Kaynak aynı SHA. One target failure diğerlerini kesmez. Managed config/credentials ve gerekli plugin contract testleri yaz, canlı job upload etme.

**Arayüz/çıktı:** 1→N pipeline/run API ve hata/no-change/partial ayrımı. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_one_failed_target_does_not_cancel_others`, `test_checkpoint_mismatch_rejects_reuse`, `test_jenkins_credential_scopes_and_bounded_parallelism`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_runtime.py tests/acceptance/test_jenkins_contract.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A12 - Yetkili Artifact Git Yayınlayıcısı

**Dosyalar:** src/oracle_db_migration_generator/artifacts/publisher.py, templates/artifact_repo/, tests/unit/test_publisher.py

**Uygulama:** Ayrı output repo, private/kurum allowlist gate, generated namespace ownership, content dedupe, katalog/pointer ve 3 kontrollü non-fast-forward retry uygula. Fake/local bare Git ile test et, gerçek GitHub/Bitbucket push yok. Runtime yayın varsayılan kapalı.

**Arayüz/çıktı:** publish_bundle → ayrı PublicationResult. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_publish_duplicate_payload_is_noop`, `test_public_or_unapproved_destination_rejected`, `test_non_fast_forward_retry_never_force_push`, `test_source_repo_never_receives_push`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit/test_publisher.py -q` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


### A13 - Bütünleşik Kabul, Dağıtım Paketi Ve Devir

**Dosyalar:** tests/acceptance/test_end_to_end.py, tests/integration/, tools/{check_release,prepare_wheelhouse}.py, requirements.lock, yz/

**Uygulama:** 1 source+boş/geride/aynı target fixture’ı ile uçtan uca gerçek SQL çıktısını doğrula, fake başarısız target ekleyerek sonuç koruma testini tamamla. Wheel ve temiz env offline kullanımını test et. Gerçek Oracle/Jenkins koşusu izin/ortam yoksa NOT_RUN, bu engeli gizleme. Son dosya/provenance/security taraması ve devir kaydı oluştur.

**Arayüz/çıktı:** test kanıtlı offline ürün paketi + gerçek ortama hazırlık/engel raporu. İmzalar için docs/CODEX_ARAYUZLERI.md esas alınır.

**Zorunlu testler:** `test_installed_wheel_works_without_reference_paths`, `test_project_acceptance_one_source_three_targets`. Assertions docs/DOGRULAMA.md içinde sabittir.

- [ ] İlgili testleri anlamlı assertion'larla yaz, önce başarısızlığını doğrula.
- [ ] Tanımlı modülü ve minimum gerekli adaptasyonları uygula.
- [ ] `python -m pytest tests/unit tests/contracts tests/acceptance -q && python tools/check_contracts.py && python tools/check_release.py && python -m build` komutunu çalıştır ve return code/özetini kaydet.
- [ ] Aşamanın çıktısını ve değişen dosyaları gözden geçir, sonraki adıma devir kaydı yaz.


## Tamamlanma Kriterleri

Bütün A00–A13 offline aşamaları test kanıtlarıyla tamamlanmış, desteklenen pozitif migration senaryoları gerçek SQL üretmiş, N target ayrı sonuçları ve hata izolasyonu doğrulanmış, hazır/inceleme/blok sınırı doğru, artifact hash/link/schema ve rapor bütçesi kontrol edilmiş, temiz wheel kurulumu referans klasörsüz çalışmış olmalıdır.

Kapanış raporunda şu alanlar ayrı bulunur: `implementation_status`, `offline_verification`, `oracle_integration`, `jenkins_installation`, `artifact_publication`, `remaining_environment_requirements`. Gerçek Oracle/Jenkins/PAT yoksa ilgili değer NOT_RUN/ENVIRONMENT_BLOCKED olur, offline ürünün uygulanmasını engellemek için tüm görevi araştırma fazına geri döndürme.

**Görev dışı:** Deployment executor, Liquibase changeset, rollback motoru, yeni web uygulaması, AI/model çağrısı, mevcut repoların değiştirilmesi, yeni ortak repo, GitHub Actions, production SQL çalıştırması.

## Hata Ve Kesintiden Devam

Devam ederken önce current workspace diff'i, aktif aşama, source/ref/vendor hash ve son doğrulama kaydını kontrol et. Önceki log 'başarılı' dedi diye bozuk artifact kullanma. Checkpoint input fingerprint'i değişmişse runtime işi güvenli yeniden snapshot/plan yapar, mevcut başarılı dosyaları silmez. Kullanıcının son açık düzeltmesi varsa yalnız o kapsam değişikliği bu göreve işlenir, başka yeni iş eklenmez.

## Son Sözleşme Bağlama Notu

A01: `test_absent_unknown_and_sql_null_are_distinct`, A09: `test_change_ids_resolve_and_counts_match` ve `test_plan_fingerprint_changes_for_parser_or_policy`, A11: `test_informational_only_is_no_action_not_no_change` ek testleri zorunludur. Assertion'lar docs/DOGRULAMA.md son bölümündedir. `input_fingerprint`, `differences`, condition kayıtları, evidence byte spans ve `NO_ACTION` bu paketin V1 sözleşmesine dahildir, sonradan düşünülecek özellik değildir.

A00 ek başlangıç: Paket köke açılmış fakat `.git` yoksa AGENTS.md son bölümündeki manifest kontrollü yerel `git init`/origin protokolünü uygula. Nonempty dizini temizleme, yeniden clone ile üzerine yazma. Bu işlem commit/push içermez.
