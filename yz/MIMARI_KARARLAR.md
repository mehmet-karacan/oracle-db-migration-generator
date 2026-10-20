# Mimari Kararlar

Sürüm: 1.0 · 19 Ekim 2026. Bu kararlar bu paket için tasarım otoritesi tarafından verilmiştir; Codex’e yeniden seçim konusu olarak bırakılmaz. Kapsamı değiştiren yeni karar kullanıcıya ait ayrı talimat gerektirir.

## ADR-001 — Bağımsız Üçüncü Ürün

**Durum:** Uygulama için bağlayıcı.

Sync gözlemler, Analyzer yorumlar, Generator hedefe özgü SQL üretir. İlk ikisi değiştirilmez; yeni ürün yalnız onların onaylı saf bileşenlerini kullanır.

## ADR-002 — Python CLI

**Durum:** Uygulama için bağlayıcı.

İki mevcut pipeline ürününün Python bileşenlerinden yararlanılır. Python 3.12 varsayılan; 3.11–3.13 destek hedefi. Yeni Java web runtime veya Maven bağımlılığı yoktur.

## ADR-003 — 1 Kaynak Ve N Target

**Durum:** Uygulama için bağlayıcı.

Kaynak SHA her run bir kez sabitlenir. Jenkins managed registry kaç enabled target içeriyorsa ALL o kadar target üretir. Her target schema mapping listesiyle birden fazla owner taşıyabilir.

## ADR-004 — Tam Durum Karşılaştırması

**Durum:** Uygulama için bağlayıcı.

Son Git commit diff’i migration değildir. Target source’un kaç sürüm gerisindeyse tamamı hesaba katılır. V1 changed-files-only modu eklenmez.

## ADR-005 — DDL Repo Tek Kaynak

**Durum:** Uygulama için bağlayıcı.

Kaynak canlı DB yeniden okunmaz, kaynak DDL ara DB’de çalıştırılmaz. Git ref/profile/layout doğrulanır. Boş hedef desteklenir fakat Oracle instance/user oluşturulmaz.

## ADR-006 — Ortak Kanonik Model

**Durum:** Uygulama için bağlayıcı.

Source SQL parse ve target DDL+dictionary aynı immutable modele çevrilir. before=target, after=source. Unknown ve absent birbirine dönüştürülemez.

## ADR-007 — Kontrollü Kaynak Uyarlaması

**Durum:** Uygulama için bağlayıcı.

Minimum Python import kapanışı _vendor alanında provenance ile uyarlanır. Eski repolara yazılmaz; runtime C:\ import veya source workflow bağımlılığı yoktur.

## ADR-008 — Schema Compare Referans Rolü

**Durum:** Uygulama için bağlayıcı.

Java karşılaştırma alanları/test senaryoları referanstır; OracleDdlGenerator’ın eksikleri aynen alınmaz. Migration planner yeni ürünün gerçek katma değeridir.

## ADR-009 — Hedefte Kalıcı Yazma Yok

**Durum:** Uygulama için bağlayıcı.

Allowlist metadata okumaları dışında SQL yok. Üründe apply/deploy/rollback komutu bulunmaz. SQL üretimi execution değildir.

## ADR-010 — Varsayılan Silmeme

**Durum:** Uygulama için bağlayıcı.

Target-only nesneler ve kolonlar korunur/raporlanır. Rename tahmini, drop-recreate, sequence reset, gizli data migration ve blanket exception swallowing yoktur.

## ADR-011 — Kural Bazlı Güvenli Üretim

**Durum:** Uygulama için bağlayıcı.

DDL_KURALLARI matrisi zorunludur. READY pozitif senaryolar gerçekten SQL üretir; belirsizlikte REVIEW/BLOCKED. Tüm türleri unsupported yaparak görev bitirilemez.

## ADR-012 — Bağımlılık Grafı

**Durum:** Uygulama için bağlayıcı.

Topolojik sıra gerçek edge’lerle kurulur. FK cycle ertelenmiş FK fazıyla çözülür; diğer cycle’lar gizli FORCE/stub yerine bloklanır. Bloke prerequisite dependent’a taşınır.

## ADR-013 — Owner Remap Yok

**Durum:** Uygulama için bağlayıcı.

İlk sürüm aynı owner adlarıyla çalışır; farklı schema mapping açık engel üretir. Metin içinde global isim değiştirme yapılmaz.

## ADR-014 — Sırların Jenkins Yönetimi

**Durum:** Uygulama için bağlayıcı.

Bağlantı bilgileri managed config, kullanıcı/parola/key Credentials. Job trusted code/host allowlist ile sınırlıdır. Aktif target listesi koddan bağımsızdır.

**19 Ekim 2026 kullanıcı güncellemesi:** İlk çalışma yereldir. Credentials
`.local/credentials.env` veya environment'tan okunabilir; `.local/` Git'e
alınmaz ve raporlarda sır gösterilmez. Jenkins credential entegrasyonu ancak
yerel INNOVA_ODI karşılaştırmasından sonra yapılır.

## ADR-015 — Worker İzolasyonu

**Durum:** Uygulama için bağlayıcı.

Varsayılan 2, en fazla 8 target eşzamanlı. Her worker ayrı process; target schema okumaları sırayla, iç paralellik 1. Hatalı target diğerlerini iptal etmez.

## ADR-016 — Mevcut Kurumsal HTML

**Durum:** Uygulama için bağlayıcı.

Ana aile innova-db-report/1.0; 820px shell ve onaylı logo. V5 veya yeni renk paleti değil. İlk 5 önemli DDL, 30 satır/2048 karakter sınırı; tamamı ayrı SQL.

## ADR-017 — Web Ve Mail Ayrımı

**Durum:** Uygulama için bağlayıcı.

V1 web/Jenkins raporu, yerel CSS/logo ve script’siz yapı. SMTP gönderimi yok. Mail gerekirse ayrı renderer; web’de CID kullanılmaz.

## ADR-018 — Tek Plan Ve Ayrı Run Kaydı

**Durum:** Uygulama için bağlayıcı.

SQL/JSON/HTML aynı plandan. Timestamp/build ayrı run.json; aynı plan girdisi byte-identical artifact. Plan ID/SQL hash döngüsü kurulmaz.

## ADR-019 — İki Depo Ve Yetkili Yayın

**Durum:** Uygulama için bağlayıcı.

Generator code repo, artifact data repo ayrı. Jenkins archive temel; private/kurum onayıyla opt-in Git publication. Source repo’ya push ve public veri yayını yok.

## ADR-020 — Modelden Bağımsız Devir

**Durum:** Uygulama için bağlayıcı.

AGENTS+tek AKTIF_GOREV, mimari kararlar, proje belleği ve kanıtlı ilerleme kalıcıdır. Uygulayıcı model mimariyi baştan araştırmaz; scope dışına çıkmaz.

## ADR-021 — Harici Lisans Motoru Yok

**Durum:** Uygulama için bağlayıcı.

Liquibase, DBMS_METADATA_DIFF ve başka ticari karşılaştırıcı runtime zorunluluğu değildir. Mevcut ANTLR lisans/provenance korunur; yayın yetkisi varsayılmaz.

## ADR-022 — Kabul Düzeylerini Ayırma

**Durum:** Uygulama için bağlayıcı.

Offline fixture testi, gerçek Oracle kabulü ve Jenkins kurulum testi ayrı. Ortam/credential yokluğunda live NOT_RUN kalır; offline uygulama devam eder.
