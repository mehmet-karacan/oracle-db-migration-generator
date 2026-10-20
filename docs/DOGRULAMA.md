# Doğrulama Ve Kabul Stratejisi

## Şimdiki kısa kapı

Yerel başlangıçta `python -m pytest -q` çalışır: konfigürasyon/kimlik,
referans koruma, secret/argv sınırı, salt okunur Oracle ön kontrolü ve sağlanan
JSON sözleşmeleri. Testler sentetiktir; ağ veya Oracle fixture kurulumu yapmaz.
`preflight` ayrıca yetkili salt okuma erişimini ölçer, semantic karşılaştırma
başarısı sayılmaz. Aşağıdaki geniş ürün matrisi ilgili uygulama aşamasına kadar
ertelenir; başlangıcın ön koşulu veya tamamlanmış test listesi değildir.

## Sonraki ürün aşamalarının doğrulaması

Aşağıdaki test adları aktif görevde uygulanacaktır. Her satır gerçek assertion gerektirir; test dosyasının varlığı yeterli değildir. Offline testler sentetik verilerle, gerçek kaynak/hedef verisine erişmeden çalışmalıdır.

| Aşama | Zorunlu Test | Assertion / Beklenen Sonuç |
|---|---|---|
| A00 | `test_reference_paths_are_read_only` | Referans iki dizinin stat/diff/hash değerleri uygulama sonunda değişmez. |
| A00 | `test_wrong_or_dirty_project_root_is_not_deleted` | Dolu/yanlış origin dizini temizlenmez; açık engel. |
| A01 | `test_registry_all_discovers_three_targets` | 3 enabled tanım → 3 target; kodda sabit liste yok. |
| A01 | `test_registry_unknown_id_fails` | Bilinmeyen TARGET_IDS → code 30, ALL fallback yok. |
| A01 | `test_registry_requires_exactly_one_service_or_sid` | service_name+sid ikisi birden veya ikisi yok → reject. |
| A01 | `test_registry_duplicate_target_and_mapping_rejected` | Duplicate ID, aynı owner mapping duplicate → reject. |
| A01 | `test_empty_registry_is_not_success` | 0 enabled target → INPUT_ERROR. |
| A01 | `test_secrets_are_not_serialized` | password/token alanı JSON schema tarafından reddedilir. |
| A02 | `test_pinned_source_is_shared_by_all_targets` | Source branch ilerlese de N target ilk resolved SHA kullanır. |
| A02 | `test_by_object_nested_children_and_sidecars` | Nested index/trigger/synonym + comments/grants doğru owner’a bağlanır. |
| A02 | `test_flat_combined_package_spec_body` | Flat Packages tek dosyada 2 identity oluşturur. |
| A02 | `test_missing_source_root_is_not_empty_schema` | Eksik root → SOURCE_SCOPE_MISSING; empty plan yok. |
| A02 | `test_duplicate_conflicting_definitions_block` | Aynı identity farklı DDL → BLOCKED, last-write-wins yok. |
| A02 | `test_symlink_submodule_and_lfs_are_not_sql` | Dış path takip edilmez; pointer SQL kabul edilmez. |
| A03 | `test_utf8_bom_crlf_quoted_names_and_qquote` | Türkçe, quoted virgüllü ad, q-quote, ; literal doğru span/parse. |
| A03 | `test_comment_semicolon_does_not_split_package` | Body tek mantıksal unit; noktalı virgülle split edilmez. |
| A03 | `test_unknown_syntax_blocks_only_affected_object` | İlgili nesne UNKNOWN/BLOCKED; bağımsız nesne gerçeği korunur. |
| A03 | `test_sidecar_grant_without_create_is_collected` | CREATE içermeyen grant/comment veri olarak alınır. |
| A03 | `test_literal_whitespace_case_is_not_normalized_away` | String ve quoted identifier içerik farkı gerçek fark kalır. |
| A03 | `test_parser_timeout_is_not_parse_success` | Parser timeout → UNKNOWN, parse_ok=True fallback yok. |
| A04 | `test_ora01031_is_not_absence` | Metadata izin hatası boş nesne listesine dönüşmez. |
| A04 | `test_dependent_ddl_unexpected_error_propagates` | ORA-31608 dışı hata veya görünürlük belirsizliği coverage kaybı. |
| A04 | `test_empty_visible_schema_requires_complete_inventory` | Boş hedef ancak tam scope kanıtıyla CREATE planına izin verir. |
| A04 | `test_snapshot_changes_during_capture` | Ön/son envanter farkı → retry bir kez, sonra INCONSISTENT. |
| A04 | `test_collector_uses_no_business_data_or_nextval` | Fake cursor’da iş tablosu SELECT, NEXTVAL, DDL/DML yok. |
| A04 | `test_multi_schema_target_uses_isolated_credentials` | İki schema credentials karışmaz; sırlar dump edilmez. |
| A05 | `test_before_is_actual_after_is_desired` | Target width40, source80 → before40 after80; yön tersine dönmez. |
| A05 | `test_target_lag_is_not_limited_to_last_commit` | Target iki sürüm gerideyse son commit dışında eksik kolon da bulunur. |
| A05 | `test_unknown_field_diff_is_not_same` | Bilinmeyen metadata → NO_CHANGE verilmez. |
| A05 | `test_uppercase_quoted_identity_matches_unquoted` | "FOO" ve FOO aynı, "Foo" farklı. |
| A05 | `test_same_name_different_owner_or_type_no_collision` | Hash identity parent/owner/type içerir. |
| A05 | `test_sequence_runtime_counter_is_informational` | START WITH değişmesi reset SQL’i üretmez. |
| A05 | `test_format_only_change_emits_no_sql` | Yalnız güvenle tanımlı biçim farkı → 0 SQL + açık bilgi. |
| A06 | `test_empty_target_generates_complete_table_definition` | VARCHAR2(100 CHAR), NUMBER(12,2), default, nullability kaybolmaz. |
| A06 | `test_existing_table_adds_only_missing_nullable_column` | CREATE TABLE/DROP yok; tek ALTER ADD. |
| A06 | `test_safe_varchar_widening_emits_modify` | Metadata uygun width40→80 → tek ALTER MODIFY. |
| A06 | `test_numeric_scale_or_shrink_requires_review` | Precision daraltma/scale değiştirme READY değil. |
| A06 | `test_not_null_on_existing_table_requires_review` | Veri taraması yapmadan uygun denmez. |
| A06 | `test_package_body_change_does_not_recreate_spec` | Sadece body farkı → sadece body + postcheck metadata. |
| A06 | `test_unique_index_on_populated_unknown_table_review` | Mevcut tablo row durumu bilinmiyor → review. |
| A06 | `test_backing_index_not_emitted_twice` | PK backing index tek oluşturma intent’i. |
| A06 | `test_target_only_object_is_preserved` | Target-only tablo → informational; DROP SQL yok. |
| A06 | `test_missing_grantee_is_not_auto_granted` | Allowlist dışı grant → review/block. |
| A06 | `test_unsupported_partition_not_silently_removed` | Partition clause desteklenmiyorsa normal CREATE üretilmez. |
| A06 | `test_schema_remap_is_not_global_replace` | Owner farklı mapping → SCHEMA_REMAP_NOT_SUPPORTED. |
| A07 | `test_fk_cycle_is_resolved_by_deferred_fk_phase` | Tablolar önce FK sonra; cycle gizli FORCE ile çözülmez. |
| A07 | `test_package_spec_and_sequence_dependencies` | Sequence default’tan, spec body’den önce. |
| A07 | `test_blocked_prerequisite_blocks_dependent` | Bloklu type/table’a bağımlı operation READY değil. |
| A07 | `test_view_cycle_is_blocked` | View cycle → DEPENDENCY_CYCLE; stub yok. |
| A08 | `test_sqlplus_delimiter_policy` | Düz SQL tek ;, PL/SQL tek /; sql iki kez çalışmaz. |
| A08 | `test_partial_plan_is_not_named_migration` | Review varsa partial-ready.sql, tam migration.sql yok. |
| A08 | `test_unchanged_target_has_no_migration_file` | No-change JSON/HTML var, boş migration dosyası yok. |
| A08 | `test_emission_reparse_preserves_features` | AST → SQL → AST kıyaslaması kolon/constraint/default kaybı yok. |
| A08 | `test_secret_or_dblink_candidate_is_not_published` | Şüpheli secret → security block; maskeli SQL executable değil. |
| A09 | `test_same_inputs_have_identical_payload` | Farklı run zamanı aynı plan ID/bytes. |
| A09 | `test_hash_tamper_and_extra_file_rejected` | Bir SQL byte değiştirme veya fazla dosya → verify fail. |
| A09 | `test_windows_reserved_and_unicode_filenames_safe` | CON, slash, Unicode, case conflict güvenli hash path. |
| A10 | `test_five_previews_are_bounded` | 6 büyük body → en çok5 önizleme; her biri30 satır/2048 karakter. |
| A10 | `test_full_sql_not_hidden_in_html` | Tam body display:none/script/JSON içinde de bulunmaz. |
| A10 | `test_approved_style_and_web_logo` | 820px aile/palette/logo korunur, web’de CID yok. |
| A10 | `test_html_escape_and_relative_links` | Script comment escape; bütün relative linkler mevcut ve root içinde. |
| A10 | `test_target_and_changes_pagination` | 51 target/101 fark devam sayfaları; toplamlar eksiksiz. |
| A10 | `test_error_target_counts_are_unknown` | Connection-error → fark count null; yeşil 0 fark yok. |
| A11 | `test_one_failed_target_does_not_cancel_others` | Fake3 target:ready/nochange/error sonuçlarının tümü korunur. |
| A11 | `test_checkpoint_mismatch_rejects_reuse` | SHA/policy/target digest değiştiyse checkpoint reuse yok. |
| A11 | `test_jenkins_credential_scopes_and_bounded_parallelism` | N worker, en çok2 concurrent default; secret cross-talk yok. |
| A12 | `test_publish_duplicate_payload_is_noop` | Aynı plan ikinci publication → commit/push sayısı artmaz. |
| A12 | `test_public_or_unapproved_destination_rejected` | Private/kurum izin kanıtı olmadan push yok. |
| A12 | `test_non_fast_forward_retry_never_force_push` | Concurrent publisher fetch/merge-only retry; user file korunur. |
| A12 | `test_source_repo_never_receives_push` | Git fake call log’da source dest push yok. |
| A13 | `test_installed_wheel_works_without_reference_paths` | Temiz env, C dizinleri olmadan offline CLI başarılı. |
| A13 | `test_project_acceptance_one_source_three_targets` | Biri boş, biri geride, biri aynı target farklı doğru paketler. |

## Gerçek Oracle Kabulü

İzole ve ayrıca yetkilendirilmiş Oracle test şemasında: fixture source/target kur → Generator'ı salt okumayla çalıştır → üretilen READY SQL'i yalnız test harness/DBA uygulasın → yeniden snapshot/compare → beklenen yönetilen farklar sıfır. Aynı test mevcut veri için kayıp olmadığını ayrıca ölçer. DDL implicit commit nedeniyle cleanup/rollback varsayımı yapılmaz; test şeması açıkça atılabilir olmalıdır.

Oracle 19c ilk canlı kabul hedefidir; 11g, 12c, 21c, 23ai/26ai aynı ürünün otomatik sertifikalı kapsamı ilan edilmez. Thin/Thick, dictionary kolonları ve kullanılan syntax sürüme göre doğrulanır. Kurum Oracle sürümü bilinmiyorsa capability probe kısıt kaydı üretir. Gerçek sürüm test edilmemişse NOT_RUN.

## Paket Ve Yayın Kabulü

Wheel kurulumunda parser generated dosyaları, manifest/license, JSON schema, report template ve gerekli assets bulunmalıdır. Dış referans dizinini sys.path'e ekleyerek test geçirmek yasaktır. Python/OS matrisi için en az Windows geliştirme yolu ve Linux Jenkins ortamı hedeflenir; yalnız çalıştırılan matris satırı passed işaretlenir.

Lint/static analiz, unit/contract/acceptance, HTML viewport/screenshot ve güvenlik negative test sonuçları ayrı raporlanır. Coverage ölçülebilir fakat anlamsız assertion, exclusion veya skip ile yükseltilemez. READY rule matrix'in her satırının en az bir pozitif ve bir olumsuz testi olmalıdır.

## Bu Teslimatta Yapılan Kontrol

Paket hazırlığında yalnız seçili mevcut Analyzer testleri (60 passed), şema/örnek uyumu, belge dosya linkleri, paket hash'leri ve referans HTML render kontrolü yapılır. Yeni Generator bu dosyalarda henüz uygulanmadığı için onun unit/live/Jenkins sonucu verilmez. Son dosya kontrolünün sonucu `PAKET_DOGRULAMA.json` içindedir.

## Sözleşme Tutarlılığı İçin Ek Kabul Testleri

A01 `test_absent_unknown_and_sql_null_are_distinct`: ABSENT yalnız scope evidence ile; UNKNOWN/NOT_APPLICABLE non-null value şema hatası; KNOWN(null) korunur.

A09 `test_change_ids_resolve_and_counts_match`: Her operation change_id/evidence_id/condition referansı var, difference sayısı ve decision count'ları eşleşiyor; dangling ID fail.

A09 `test_plan_fingerprint_changes_for_parser_or_policy`: Aynı girdide aynı plan ID; policy/parser artifact digest değişirse plan ID değişir; run timestamp değişirse değişmez; SQL hash'i kendini referanslamaz.

A11 `test_informational_only_is_no_action_not_no_change`: Target-only korunmuş nesne → NO_ACTION, fark sayısı>0, SQL yok. Tam eşit snapshot → NO_CHANGE; incomplete → ikisi de değil.
