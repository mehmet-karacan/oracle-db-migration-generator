# Mevcut Kaynakların Kesin Kullanım Haritası

## İnceleme Dayanağı

DDL Sync: yüklenen `gpu-db-ddl-sync-master@87c867aa5ba (1)(1).zip`.

Analyzer: yüklenen `gpu-ai-db-change-analyzer-master@30012f17d1d(1).zip`.

Schema Compare: GitHub `main` okumasından sabitlenen `fdfd1c804a12764d2d6b7aad6ada9d172f9011bc` (16 Ekim 2026 tarihli commit). ZIP dosya adlarındaki kısa ref'ler tam Git commit doğrulaması değildir; gerçek byte hash'leri `reference-lock.json` içindedir.

Kullanıcının yerel dizinleri `.local/session-context.json` içindedir. Codex bu dizinleri okur, değiştirmez. Runtime sırasında bu dizinlere dependency verilmez.

## Dosya Ve Sembol Eşlemesi

| Kaynak | Sembol/Bölüm | Yeni Üründeki Kullanım |
|---|---|---|
| Sync `src/oracle_ddl_sync/oracle_client.py` | DdlObject, ObjectRef, list_objects, _get_ddl, _set_transform_params, connect, init_thick_mode | `oracle/collector.py`, `oracle/connection.py`: target nesne listeleme ve DDL retrieval yaklaşımı. |
| Sync aynı dosya | _get_dependent_ddl | Çağrı biçimi alınır; **tüm DatabaseError'ı None yapma davranışı alınmaz**. |
| Sync `src/oracle_ddl_sync/metadata.py` | SchemaMetadata, load, _rows | Sorgu/alan bilgisi alınır; _rows error→[] yerine coverage/error result modeli uygulanır. |
| Sync `src/oracle_ddl_sync/layout.py` | TYPE_DIRS, plan, manifest, write_schema, dependencies_json | `source/layout.py` by_object v1 keşfi ve sidecar yerleşimi. Yazma/prune akışı çalıştırılmaz. |
| Sync `src/oracle_ddl_sync/writer.py` | _FLAT_TYPE_DIRS, _PAIRED_GROUPS, _write_atomic | Eski flat layout desteği, birleşik spec/body tanıma, atomik yazma yaklaşımı. prune_stale/remove_objects alınmaz. |
| Sync `config/sky-db.toml` | layout, schemas, branch | İlk runtime profile için .local altındaki doğrulanacak bağlam. Endpoint/credential asla genel örneğe kopyalanmaz. |
| Analyzer `identities.py` | canonical_identifier, object_key, stable_id | Oracle effective name + hash kimlik adaptasyonu; delimiter çakışmaları düzeltilir. |
| Analyzer `oracle/scanner.py` | scan, ScanOccurrence, mask_sql_code | Byte/satır/object boundary kanıtları. Regex scanner, parser yerine geçmez. |
| Analyzer `oracle/ddl_tokens.py` | code_tokens, top_level_items, enclosed, source_span | Token/span tabanlı güvenilir statement ve clause işlemleri. |
| Analyzer `oracle/generated/` | ANTLR Python lexer/parser/visitor/base | Runtime 4.13.2 ile sabitlenmiş parser; grammar manifest/license korunur. |
| Analyzer `oracle/table.py` | extract_table, table_context_statements, constraint_properties | Kolon/tip/default/constraint/context çıkarımı; kaynak-target ortak representation. |
| Analyzer `oracle/index.py`, `sequence.py`, `view.py`, `package.py` | extract_index, extract_sequence_options, extract_view, extract_package, extract_standalone_routine | İlgili nesne projections; parser/projection diagnostics policy'ye aktarılır. |
| Analyzer `oracle/projections.py` | Projection, project | Diff için typed projection adaptörü; parse_ok=True hardcode edilmez. |
| Analyzer `oracle/changes.py` | compare_projections | old=target, new=source olarak temel structured diff. old_scope/new_scope yokluk kanıtı korunur. |
| Analyzer `taxonomy/catalog.py`, `change-catalog.json`, `object-catalog.json` | change_catalog, supported_types | Kaynak diff taxonomy kapanışı; desteklenmeyenler yeni plannerda açık reason. |
| Analyzer `inventory.py` | inventory_bytes ve worker mantığı | Kaynak tarama/parse timeout sözleşmesi referansı. Fonksiyonun sidecar skip davranışı aynen alınmaz, inventory_revision/workflow orchestration taşınmaz. |
| Analyzer `dependencies.py` | DependencyEdge/aday çözümleme yaklaşımı | Kanıtlı ve candidate dependency ayrımı; AI risk sonucu import edilmez. |
| Analyzer `innova_rendering.py` + `templates/innova_v1` | render_innova_view, html/email ayrımı, StrictUndefined | `reporting/` için görünüm + escaping + sınırlama. AI-specific view model ayrı tutulur. |
| Analyzer `assets/innova-logo-approved.png` | Değişmeyen logo | Yerel/onaylı deployment asset; farklı logo veya font uydurulmaz. |
| Schema Compare `.../compare/TableMetadataComparator.java` | compareColumns, compareConstraints, compareIndexes | Python canonical comparator'da alan kapsamı ve test kuralı referansı. Java runtime bağımlılığı yok. |
| Schema Compare `.../compare/OracleSnapshotComparators.java` | Comparator tip kayıtları | Nesne coverage envanteri referansı; engine'de olanın UI'de/SQL'de de tamam olduğu varsayılmaz. |
| Schema Compare `.../ddl/OracleDdlGenerator.java` | generate/createTable/createSequence | **Anti-regression referansı**: CHANGED TABLE atlama, datatype detail kaybı, sequence min=start ve kontrolsüz DROP alınmaz. |

Schema Compare yollarındaki `...`, `schema-provider-oracle/src/main/java/com/schemacompare/provider/oracle` köküdür. Tam adresler `reference-lock.json` içindedir.

## Bağımlılık Kararı

Yeniden kullanılacak saf Python birimler yeni repo içinde `src/oracle_db_migration_generator/_vendor/analyzer_core/` ve `_vendor/ddl_sync_core/` altında gerekli minimum import kapanışıyla tutulur. Package path'leri uyarlanır; orijinal hash + adapted hash + lisans + değişiklik gerekçesi `vendor/PROVENANCE.json` dosyasına kaydedilir. Hedef eski projelerin Python namespace'ine runtime import bırakılmaz.

`oracle/table.py`, index/view/sequence, scanner, ddl_tokens, package, parser_worker, dynamic_sql, identities ve grammar kapanışı zorunlu başlangıç kümesidir. `compare_projections` için taxonomy kapanışı eklenir. Migration'a özgü güvenlik/alan eşleştirme `compare/` adaptöründedir. Yeni functionality gerektiğinde vendor'a rastgele patch değil adaptör katmanına ekleme; vendor patch zorunluysa provenance'ta açık gerekçe.

Analyzer'ın workflow, LLM HTTP client, SMTP, SQLite geçmişi, model prompt'ları, örnek şirket DDL corpus'u ve Jenkins bildirim akışı taşınmaz. Sync'in git push/prune/state orchestrator'ı alınmaz. Yeni Git publisher artifact sözleşmesine göre yazılır; source DDL'ye push yapamaz.

## Referans Sürümü Değiştiğinde

Dosya hash'i aynıysa tanımlı alım uygulanır. Farklıysa ilgili sembol+regression test karşılaştırılır ve `yz/DEVIR.md` içine fark yazılır. Yerel değişmiş dosya geri alınmaz, referans repo checkout'u zorla eski ref'e geçirilmez. Anlam aynıysa adapte et; güvenlik/arayüz çelişkisi varsa sadece etkilenen import aşamasını durdur. Yeni mimari tasarlama.

## Gerçekte Çalıştırılmış Referans Testleri

`test_table_extraction.py`, `test_index_extraction.py`, `test_innova_rendering.py`: **60 passed** (paket hazırlama ortamında, ANTLR 4.13.2 izole bağımlılık diziniyle). İlk denemede ortam ANTLR 4.9.3 olduğu için collection durmuş; pakette bulunan 4.13.2 wheel'i izole dizinde kullanılarak tekrar doğrulanmıştır. Orijinal kod değiştirilmemiştir.

Bunlar yalnız seçilmiş referans testleridir. Tüm Analyzer regression suite'i, Sync suite'i, yeni ürün veya Oracle/Jenkins kabulü tamamlandı iddiası değildir.

## 20 Ekim 2026 — Teknik nesne kapsamı

Kullanıcı talimatıyla Sync `oracle_client.py` içindeki
`_SYSTEM_GENERATED_PATTERNS` / `_is_system_generated` güncel karşılığı salt
okunur incelendi. Dosya SHA-256:
`1b20f0ffc5e57b55307cb6bd1154d73cb6851f7fe527fb350f96ed8f49c016c2`.
Bu, eski paket lock'undaki `8d809b...` sürümünden farklı mevcut yerel sürümdür;
referans dosyası veya lock geriye zorlanmadı. On dört teknik önek saf
`compare/scope.py` uyarlamasında kullanılır; eski runtime import edilmez.
Doğrulanmış parent ilişkileriyle index/COMMENT/GRANT kapsamı yeni modelde
çözülür. İş nesnesinin bağımlılık kenarı filtreyi o iş nesnesine yaymaz;
meşru `$` adı ve gerçek materialized view log korunur. GRANT dışlama ayrıca
kullanıcının açık daraltmasıdır; Sync'in tüm grant desteği kaldırılmış değildir.
