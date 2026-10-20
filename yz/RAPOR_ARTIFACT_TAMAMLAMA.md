# Rapor/artifact güncellemesi — 20 Ekim 2026

ODMG-RPT-UPDATE-001 yerel uygulaması tamamlandı. Onaylı ZIP'in iki tasarımı gerçek
Run → Target → Plan → Object modeline bağlandı. Source ve target daima salt okunur;
bu aşamada Oracle bağlantısı dahi açılmadı. Parser/compare/karar motoru değiştirilmedi.

2.353 fark; 559 hazır DDL; 123 inceleme; 5 kaynak/sözleşme koşulu; 1.038 bilgi.
559 SQL gövdesi önceki tamamlanmış motor paketiyle byte karşılaştırmasında aynı;
yalnız plan kimliği header'ı ve dosya yolları yeni rapor build'iyle değişti.
Birleşik SQL sıra/hash kontrolü ve eski flat bundle doğrulaması başarılı.
Beş gerçek koşul yz/MOTOR_TAMAMLAMA.md içinde; rapor üretimi için engel değiller.

313 passed / 51,22 sn; skip 0. 7 şema / 8 örnek VERIFIED.
İki farklı run aynı tek immutable planı kullanıyor. 14.346 statik bağlantı doğrulandı.
En büyük HTML 115.129 byte (<200 KiB). Web/target/email 390/820/1.440 px olmak üzere
9 browser kontrolü, yatay taşma 0. Onaylı logo SHA'sı iki ZIP referansıyla birebir aynı.
Mail 5 kritik target / 10 benzersiz nesne, CID ve ayrı gömülü preview; SQL body mailde yok.
Nesne README/review kanıtları, binlik ayraçlar ve gerçek dosya yolları tamamlandı.

Arşiv sahiplik/kilit/atomik yazma/rollback/dedup ve integrity conflict kontrolleri var.
Opt-in publisher private kurum deposu, izinli host/SSH remote, storage ve push yetkisi,
literal generated pathspec, bütün payload sır taraması ve doğrulanmış sabit son SHA linki ister.
Başarısız push/404/retention/yanlış run/yanlış Jenkins build için olmayan link çizilmez.
Bağımsız incelemedeki 3 bulgu kırmızı→yeşil kapandı; yeniden incelemede yeni önemli bulgu yok.

Plan: `1c5950cc93efb9d9420bbf94743ef8e9112038bef627cdb130775d503f8e078f`
Generator: `4912b9ea900f5670551106003b9983500232a4a9ca1d8be1b9c6b7bdeed932d1`
Source SHA: `3b028ebaa8c0c0b15d3095810f6a5e4f910c939f`
Wheel SHA: `97d09db658f72e59ba361c62f43c2086fff1c7edef865e5d52f01a61517ba1f3`

Kanıt: output/report-update-final-verification.json. Rapor: output/report-update-final/run/index.html.
Mail: output/report-update-final/run/report-email.preview.html.
Arşiv: output/report-update-final/store/README.md; her run ayrı, plan tek kopya.
Teslim ZIP'leri: output/report-update-final-run.zip ve output/report-update-final-store.zip.
Test: output/pytest-report-update-final.xml. Patch: output/report-update-code.patch.
Reference hash değişimi 0; eski 7 drift korunuyor. Git adaylarında sır/endpoint eşleşmesi 0.
Kod repo unborn/untracked olduğu için git diff boş; önceki dosya baseline'ından patch/hash listesi üretildi.

Offline uygulama: VERIFIED. Wheel build/ayrı dizine kurulum/installed import + archive smoke: VERIFIED.
Canlı Oracle DDL/compile kabulü: NOT_RUN. Gerçek artifact push/SMTP/Jenkins: NOT_RUN.
Eski belgede adı geçen tools/check_release.py mevcut değil: NOT_AVAILABLE; uygulanmış kapı sayılmadı.
Sonraki somut iş Jenkins geçişidir: docs/JENKINS_GECIS_HAZIRLIGI.md.
Önceki backend kanıtları ve ZIP görev orijinalleri korunuyor; v1/v2 rapor çıktıları ara kanıttır,
son teslim output/report-update-final'dır. Otomatik code commit/push yapılmadı.

## Değişen ürün/sözleşme dosyaları

- `src/oracle_db_migration_generator/artifacts/bundle.py` — MODIFIED
- `src/oracle_db_migration_generator/artifacts/layout.py` — ADDED
- `src/oracle_db_migration_generator/artifacts/publisher.py` — ADDED
- `src/oracle_db_migration_generator/artifacts/store.py` — ADDED
- `src/oracle_db_migration_generator/cli.py` — MODIFIED
- `src/oracle_db_migration_generator/emission/sql.py` — MODIFIED
- `src/oracle_db_migration_generator/reporting/assets/report.css` — MODIFIED
- `src/oracle_db_migration_generator/reporting/links.py` — ADDED
- `src/oracle_db_migration_generator/reporting/render.py` — MODIFIED
- `src/oracle_db_migration_generator/reporting/templates/email.html.j2` — ADDED
- `src/oracle_db_migration_generator/reporting/templates/report.html.j2` — MODIFIED
- `src/oracle_db_migration_generator/reporting/templates/run.html.j2` — ADDED
- `src/oracle_db_migration_generator/reporting/view.py` — ADDED
- `src/oracle_db_migration_generator/runtime/aggregate.py` — MODIFIED
- `src/oracle_db_migration_generator/schemas/catalog.schema.json` — ADDED
- `src/oracle_db_migration_generator/schemas/run.schema.json` — MODIFIED
- `schemas/catalog.schema.json` — ADDED
- `schemas/run.schema.json` — MODIFIED

## Uygulanan komutlar

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=output/pytest-report-update-final.xml
.\.venv\Scripts\python.exe tools/check_contracts.py
.\.venv\Scripts\python.exe tools/verify_references.py --report output/reference-report-update-final.json
.\.venv\Scripts\python.exe -m build --wheel --outdir output/dist-report-update
.\.venv\Scripts\python.exe output/export-report-update.py output/report-update-final
.\.venv\Scripts\python.exe output/verify-report-update-final.py
```

Reference komutu eski 7 drift nedeniyle nonzero döner; önceki motor kapanışıyla actual SHA'lar aynı.
Test değişiklikleri: test_report_artifact_update.py, test_publication.py, test_report_views.py;
test_runtime.py hata receipt negatif testi; test_bundle.py recursive SQL dosyaları; test_schemas.py yeni katalog.
Yeni catalog.example.json ve tools/check_contracts.py katalog kapısını içerir.
docs/HTML_STANDARDI.md, ARTIFACT_SOZLESMESI.md ve JENKINS_GECIS_HAZIRLIGI.md güncellendi.
Kullanıcı kaynak/ref checkout'ları ve Oracle snapshot'ları değiştirilmedi.

