# Uygulama Dosyaları Ve Arayüz Sözleşmeleri

Bu dosyadaki isimler uygulanacak arayüzdür; mevcut çalışan API olarak sunulmaz. İşlevler test edilebilir saf katmanlara ayrılır. Gerçek DB/Git bağlantısı dependency injection ile sınırlandırılır.

## Paket Ağacı

`src/oracle_db_migration_generator/`: `__init__.py`, `__main__.py`, `cli.py`; `config/{models,loader}.py`; `model/{identity,snapshot,difference,plan,evidence}.py`; `source/{git_reader,layout,sidecars}.py`; `parsing/{adapter,statements,canonicalize}.py`; `oracle/{connection,queries,collector,capabilities}.py`; `compare/{snapshots,projection_adapter}.py`; `planning/{rules,graph,policy}.py`; `sql/{emit,validate}.py`; `reporting/{view,render}.py`; `artifacts/{bundle,publisher,catalog}.py`; `runtime/{worker,aggregate,checkpoint}.py`; `_vendor/`.

Ek kök dosyaları: `pyproject.toml`, `Jenkinsfile`, `requirements.lock`, platform bazlı `requirements/`, `tools/{check_contracts,verify_references,check_release,prepare_wheelhouse}.py`; `tests/{unit,contracts,integration,acceptance}`. Uygulama template'leri `src/oracle_db_migration_generator/templates/`, schema'ları package data olarak `schemas/` kaynağından dağıtılır.

## Domain Tipleri

`Identifier(effective_name:str, raw_name:str, quoted:bool)`; `ObjectIdentity(profile_id:str, owner:Identifier, object_type:str, name:Identifier, parent_key:str|None)`.

`KnownValue(state:Literal['KNOWN','ABSENT','UNKNOWN','NOT_APPLICABLE'], value:JSONValue, evidence_ids:tuple[str,...])`.

`SchemaSnapshot` immutable: schema_version, synthetic, side(SOURCE/TARGET), profile_id, schemas, source_commit veya target_id, object collection, completeness, capabilities, semantic_digest. Capture zamanı runtime receipt'tedir.

`Difference` immutable: difference_id, object_key, property_path, before(KnownValue), after(KnownValue), kind, evidence_ids. `DifferenceSet`: source/target fingerprint + tuple differences + scope coverage + diagnostics.

`Operation`: operation_id, object identity, kind, decision, risk, rule_id, reason codes/TR metin, change_ids, evidence_ids, dependencies, ön/son koşullar, emission intent. `TargetPlan`: schema_version, plan_id, source, target, snapshot_digest, status, counts, operations, evidence, validation, warnings.

Aynı kimlik türleri schema JSON sözleşmeleriyle uyumludur; uygulama içi dataclass dönüşümleri açık ve testlidir. `Unknown` Python None'a indirgenmez. Domain modeline DB credential veya live connection nesnesi eklenmez.

## Kesin Fonksiyon Sınırları

| Dosya | Arayüz |
|---|---|
| config/loader.py | `load_source_profile(path: Path) -> SourceProfile`; `load_targets(path: Path, selected: tuple[str,...]) -> tuple[TargetConfig,...]` |
| source/git_reader.py | `resolve_source(repo: RepositoryReader, ref: str) -> SourceRevision`; `read_source(revision: SourceRevision, profile: SourceProfile) -> SourceInput` |
| source/layout.py | `collect_layout(entries: tuple[GitEntry,...], profile: SourceProfile) -> tuple[SourceArtifact,...]` |
| parsing/adapter.py | `parse_source(inputs: SourceInput, profile: SourceProfile) -> SchemaSnapshot`; `parse_ddl(raw: bytes, identity_hint: ObjectIdentity|None) -> ParseResult` |
| source/sidecars.py | `merge_sidecars(snapshot: SchemaSnapshot, sidecars: tuple[SourceArtifact,...]) -> SchemaSnapshot` |
| oracle/collector.py | `collect_target(config: TargetConfig, credentials: CredentialResolver, profile: SourceProfile) -> TargetObservation` |
| compare/snapshots.py | `compare_snapshots(desired: SchemaSnapshot, actual: SchemaSnapshot, policy: Policy) -> DifferenceSet` |
| planning/rules.py | `plan_target(diff: DifferenceSet, context: PlanningContext) -> TargetPlan` |
| planning/graph.py | `order_operations(operations: tuple[Operation,...], evidence: EvidenceRegistry) -> OrderedOperations` |
| sql/emit.py | `emit_sql(plan: TargetPlan) -> SqlBundle` |
| sql/validate.py | `validate_sql(bundle: SqlBundle, plan: TargetPlan) -> ValidationResult` |
| reporting/view.py | `build_report_view(run: RunResult, plans: tuple[TargetPlan,...], limits: ReportLimits) -> ReportView` |
| reporting/render.py | `render_reports(view: ReportView, output: Path) -> RenderManifest` |
| artifacts/bundle.py | `write_bundle(plan: TargetPlan, sql: SqlBundle, output: Path) -> BundleManifest`; `verify_bundle(path: Path) -> VerificationResult` |
| artifacts/publisher.py | `publish_bundle(bundle: Path, destination: ArtifactDestination, git: GitClient) -> PublicationResult` |
| runtime/worker.py | `run_target(source: SchemaSnapshot, target: TargetConfig, context: RunContext) -> TargetResult` |
| runtime/aggregate.py | `aggregate_run(results: tuple[TargetResult,...], context: RunContext) -> RunResult` |
| runtime/checkpoint.py | `save_checkpoint(state: Checkpoint, path: Path) -> None`; `load_verified_checkpoint(path: Path, inputs: InputFingerprint) -> Checkpoint` |

RepositoryReader, CredentialResolver, GitClient protokolleri external I/O'yu soyutlar; unit testler fake implementasyon kullanır. `credentials` resolve sonucu asla repr/log'a girmez.

## CLI

Aşağıdaki komutlar AKTIF_GOREV uygulandıktan sonra çalışacaktır:

- `oracle-db-migration-generator validate-config --source-profile PATH --targets PATH`: schema + semantic config kontrolü, hedeflere bağlanmaz.
- `oracle-db-migration-generator prepare-source --repo PATH --ref REF --source-profile PATH --output DIR`: sabit SHA'dan source snapshot; Git'e yazmaz.
- `oracle-db-migration-generator plan-target --source-snapshot PATH --targets PATH --target-id ID --output DIR`: yalnız seçili target worker. Secret'lar env/credential resolver'dan, argv'den değil.
- `oracle-db-migration-generator plan-offline --source-snapshot PATH --target-snapshot PATH --source-profile PATH --output DIR`: ağsız kabul/örnek akışı; aynı compare/planning/emission kodu.
- `oracle-db-migration-generator aggregate --run-root DIR`: target sonuçları + standart rapor.
- `oracle-db-migration-generator verify-bundle --bundle DIR`: schema/hash/link/integrity; ağsız.
- `oracle-db-migration-generator publish --bundle DIR --destination PATH`: yetkili artifact Git publication; varsayılan CLI akışında çağrılmaz.

`apply`, `deploy`, `execute-ddl`, `rollback` alt komutları **yoktur**. Test-only Oracle integration harness runtime CLI'dan ayrı durur.

## Kaynak Ve Ağ Erişimi

`prepare-source` Jenkins'in sabitlediği yerel checkout'u okuyabilir; projeyi Git blob API'siyle de güvenli tarayabilir. Kullanıcının çalışma repo'sunda checkout/ref değiştirip dirty dosya kaybetmez. Secrets env'den okunsa da tüm environment dump edilmez. Jenkins job yalnız güvenilir koddan çalışır.

## Development Commands

Varsayılan doğrulama komutları (uygulama aşamasında oluşturulacak testler): `python -m pytest tests/unit tests/contracts tests/acceptance -q`; `python tools/check_contracts.py`; `python tools/verify_references.py`; `python tools/check_release.py`; `python -m build` ve ayrı temiz env'de wheel kurup CLI `--help` + offline fixture koşusu. Dependency çözümlenemezse ilgili environment engeli kaydedilir, test başarısı yazılmaz.

## JSON Alan Adları Ve Destek Tipleri

JSON sözleşmesi kanoniktir: Python `operation_id` → JSON `id`; `difference_id` → `id`; `dependencies` → `depends_on`; Python `completeness` → JSON `coverage`; `snapshot_digest` → `target_snapshot_digest`. Diğer alanlar şema adıyla aynı yazılır. Serialization round-trip testi zorunludur; aliases gizli farklı format yaratmaz.

`TargetPlan` ayrıca `input_fingerprint` ve `differences` listesi taşır. Her `change_ids` elemanı bu difference listesinde çözülür. `Operation` JSON'unda `preconditions`/`postconditions` açık condition record'larıdır; postcheck dosyası varsa güvenli `check_path` ile bağlanır. Satır aralığı 1-based inclusive, byte aralığı 0-based half-open; elde edilmeyen byte konumu null olur, tahmin edilmez.

`KnownValue(ABSENT, null, evidence)` yalnız tam envanter/parse kapsamıyla doğrulanmış yokluktur. `KNOWN` ve null, örneğin gerçek SQL NULL/default yokluğu gibi açık bilinen değeri anlatabilir. `UNKNOWN` ve `NOT_APPLICABLE` değerleri null taşır, birbirleriyle veya ABSENT ile eşit sayılmaz. Canonical owner/name etkin adlarıdır; `quoted` gösterim bilgisi mantıksal identity eşitliğini değiştirmez.

`TargetObservation = snapshot + receipt`; `receipt` capture zamanı ve örnekleme kontrolünü taşır. Snapshot `observed_consistency` capture'ın kanıt düzeyini gösterir, atomik Oracle snapshot garantisi değildir. `InputFingerprint`, plan input_fingerprint alanları + source/target digest'lerinden oluşur. `RunContext` run_id/limits/output-root/credential-resolver/timeout ile sabit kaynak parmak izini taşır; secrets model repr'e girmez. `PlanningContext` source/target snapshot, profile policy, capabilities ve EvidenceRegistry'yi taşır. `SqlBundle` operation-id → statement bytes/kind/relative path koleksiyonudur. `ParseResult` occurrences/projections/diagnostics/coverage döndürür. `ReportLimits` varsayılanları HTML_STANDARDI'ndedir. IO protokolleri sadece bu sınırları sağlar; yeni servis veya veri tabanı gerektirmez.
