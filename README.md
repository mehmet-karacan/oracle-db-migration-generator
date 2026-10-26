# Oracle DB Migration Generator

Kaynak Git DDL durumu veya salt okunur Oracle kaynağı ile Oracle hedefleri arasındaki farklardan SQL/JSON/HTML üreten Python CLI ve isteğe bağlı ortak UI.

**24 Ekim UI uygulaması:** Git/Oracle kaynak seçimi, bağlantı/profil yönetimi,
gerçek çalışma takibi/DDL ayrıntısı ve doğrulanan ayar ekranları eklendi.
Yerel geliştirme doğrulandı, kurumsal SSO/Jenkins UI kurulumu ve gerçek
Oracle→Oracle kabulü NOT_RUN. [Çalıştırma ve dağıtım](docs/UI_CALISTIRMA_VE_DAGITIM.md).

**Mevcut durum (20 Ekim 2026):** Yerel ve Jenkins karşılaştırması, güvenli DDL
kuralları, bağımlılık sırası ve SQL/JSON/HTML üretimi çalışır. Günlük varsayılan
`PROD / TTBP`, `INNOVA_ODI` yalnız manuel `SCHEMA_SCOPE` seçimiyle karşılaştırılır.
Jenkins her gün Türkiye saatiyle 08:00 başlar. Üretilen DDL ve raporlar yalnız
Jenkins artifact arşivinde, son 20 çalışma için tutulur. Source ve target her
zaman salt okunurdur, SQL uygulanmaz. Metadata eksikliği UNKNOWN/kısmi kapsam
olarak görünür, güvenli DDL alt kümesi tam migration onayı sayılmaz.

## Ürün Sınırı

| Ürün | Sorumluluk |
|---|---|
| Oracle DB DDL Sync | Oracle durumunu çıkarır, DDL dosyalarını Git'e taşır. |
| AI DB Change Analyzer | Kaynak Git değişikliklerini kanıta dayalı yorumlar. |
| Oracle DB Migration Generator | Seçili kaynak durumu ile her hedef arasındaki farktan migration planı ve SQL üretir. |

Generator, Sync'in veya Analyzer'ın yerine geçmez, bunları çalıştırma zorunluluğu da yoktur. Kaynakta yeni commit olmasa bile geride kalmış hedef için çalışır. Hedef veritabanına yazmaz, migration uygulamaz, model servisi çağırmaz.

## Başlangıç

Uygulayıcı `AGENTS.md` ve **AKTIF_GOREV.md** dosyalarını okur. Mimari kararlar `yz/MIMARI_KARARLAR.md`, teknik tasarım `docs/MIMARI.md`, birebir yeniden kullanım eşlemesi `docs/YENIDEN_KULLANIM.md` içindedir.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m oracle_db_migration_generator validate-config --source-profile .local/source-profile.sky.json --targets .local/targets.json
.\.venv\Scripts\python.exe -m oracle_db_migration_generator preflight
```

Lock, Python 3.13/Windows başlangıç ortamının sürüm sabitlemesidir. Nihai hash'li release lock ve platform matrisi A13'tedir.

Yerel endpoint/profile/credentials `.local/` altında ve Git dışında tutulur. Mevcut `.env.local` korunur. `LOCAL_INNOVA_ODI_USER` ve `LOCAL_INNOVA_ODI_PASSWORD`, `.local/credentials.env` veya environment üzerinden çözülür, environment önceliklidir. Parolayı komut satırına yazmayın.

Ön kontrol çıktısı `output/local-preflight.json` içindedir. Source'a yalnız `ls-remote`, target'a `SET TRANSACTION READ ONLY` ve sabit metadata SELECT sorguları gönderilir. Metadata erişim hatası boş şema sayılmaz. Bu komut karşılaştırma yapmaz, `difference_count=null` ve `comparison_status=NOT_RUN` döndürür. Başarısız erişim exit 20, geçersiz config exit 30'dur.

SSH kimliği için yalnız yerel `source.ssh_identity_file` alanına mevcut anahtarın yolu yazılır. HTTPS için `source.credential_id=LOCAL_SOURCE` ve yerel/env `LOCAL_SOURCE_USER` / `LOCAL_SOURCE_PASSWORD` kullanılır. Kimlik bilgileri URL/argv'ye girmez, HTTPS askpass dosyası yalnız environment değişken adları içerir ve silinir. TLS doğrulaması, BatchMode ve StrictHostKeyChecking açık kalır.

## Sabit Tasarım

Python CLI ve kütüphane, varsayılan Python 3.12, destek hedefi 3.11–3.13. Kaynak DDL ve hedef metadata aynı kanonik modele dönüştürülür. Deterministik karşılaştırma sonucundan işlem planı, aynı plandan SQL/JSON/HTML üretilir. İlgili mevcut Python bileşenleri kontrollü uyarlanır. Java web uygulaması runtime bağımlılığı yapılmaz.

## Belgeler

- [Mimari](docs/MIMARI.md), [Arayüzler](docs/CODEX_ARAYUZLERI.md), [Yeniden Kullanım](docs/YENIDEN_KULLANIM.md)
- [Kaynak Ve Hedef](docs/KAYNAK_HEDEF_SOZLESMESI.md), [DDL Kuralları](docs/DDL_KURALLARI.md)
- [Jenkins](docs/JENKINS.md), [HTML](docs/HTML_STANDARDI.md), [Artifact Sözleşmesi](docs/ARTIFACT_SOZLESMESI.md)
- [Güvenlik](docs/GUVENLIK.md), [Doğrulama](docs/DOGRULAMA.md), [Dış Kaynaklar](docs/DIS_KAYNAKLAR.md)

## Kullanım Sözleşmesi

Uygulanan komutlar: `validate-config`, `preflight`, `prepare-source`, `plan-offline`, `plan-target`, `aggregate`, `verify-bundle`. Yerel komut örnekleri [Yerel başlangıç](docs/YEREL_BASLANGIC.md) içindedir. `apply`, `deploy`, `rollback` ve `publish` komutu yoktur. Source ve target daima salt okunur kalır.

Üretilen SQL bir **uygulama önerisidir**. `READY` etiketi desteklenen kurallarla üretildiğini belirtir, DBA onayı, gerçek Oracle kabul testi veya deployment kaydı değildir.


### Taşınabilir Oracle metadata toplama

Production tarafında mevcut SQL*Plus veya SQLcl kullanılarak kurulum gerektirmeyen,
parametreli metadata paketi hazırlanabilir. Şema, nesne türü, kesin nesne adı ve
kolon veri tipi filtreleri CLI ve arayüzde aynı sözleşmeyi kullanır.
Bağlantılar > Taşınabilir Toplama sekmesinden paket indirilir veya oluşan dosya
seçili projeye aktarılır. Kaynak/hedef dosyaları yerel motorla karşılaştırılır.

Ayrıntılı parametreler ve örnekler:
[Taşınabilir Toplama README](src/oracle_db_migration_generator/portable/templates/README.md).
Canlı Oracle/SQL*Plus/SQLcl kabulü, offline testlerden ayrı izlenir.
