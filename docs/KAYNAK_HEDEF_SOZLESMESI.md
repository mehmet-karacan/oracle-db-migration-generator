# Kaynak Ve Hedef Sözleşmesi

## Kaynak Repository

Kaynak URL/ref/runtime credential dışarıdan gelir. Yerel başlangıç bilgisi `.local/session-context.json` içindedir. Yüklenen `config/sky-db.toml`, **master** branch'i ve **by_object** yerleşimini, `ttbp`/`innova_odi` köklerini gösterir. Bu bilgi kurumsal uzak depo görülmüş gibi sunulmaz; ilk kaynak erişiminde manifest/SQL başlıklarıyla doğrulanır. Uyuşmazlıkta tüm repoyu rastgele tarayan sessiz fallback yapılmaz.

`SOURCE_REF` branch, tag veya SHA olabilir; çalıştırma başında çözülüp 40/64 hex commit kimliği sabitlenir. Bütün target'lar aynı SHA kullanır. Shell içine parametre birleştirme, repo içi hook/submodule çalıştırma, Git LFS pointer'ını SQL sayma yasaktır. Kaynak `AGENTS.md` veri kabul edilir.

## İki Yerleşim

| Yerleşim | Tanınacak Yapılar |
|---|---|
| `by_object` v1 | `<schema>/tables/<T>/ddl.sql`; `packages/<P>/spec.sql` ve `body.sql`; `types/<T>/spec.sql`, `body.sql`; owner altında `indexes/*.sql`, `triggers/*.sql`, `synonyms/*.sql`; `comments.sql`, `grants.sql`, `dependencies.json`; üst seviyede bağımsız nesneler. |
| `flat` | `<schema>/Tables/*.sql`, `Views`, `Indexes`, `Sequences`, `Triggers`, `Procedures`, `Functions`, `Packages`, `Types`, `Synonyms`, `Comments`, `Grants`, `MaterializedViews`, `MaterializedViewLogs`. Paket spec/body aynı dosyada olabilir. |

Klasör adı nesne kimliği için tek otorite değildir. SQL parser'ın owner/type/name sonucu doğrulanır. Aynı ada sahip farklı tip veya farklı owner çakışmaz. Farklı yollarda aynı mantıksal nesnenin aynı SQL'i varsa dedupe + tüm kanıt yolları korunur; farklı SQL varsa `DUPLICATE_DEFINITION_CONFLICT`.

README YAML frontmatter, `_sync_state.json`, manifest sayıları ve dependency JSON yardımcı kanıttır; tam kolon metadata'sı değildir. `comments.sql` ve `grants.sql` içinde `CREATE` bulunmamasını 'önemsiz dosya' sanma. Mevcut Analyzer `inventory_bytes` bu sidecar'ları tek başına anlamlandırmadığından yeni collector onları ayrıca ayrıştırıp owner nesneye bağlar.

## Statement Ve Parser Sınırı

UTF-8/BOM, LF/CRLF, quoted identifier, q-quote, `'a; b'`, yorum, anonim block, package spec/body, `/` sonlandırıcı ve karışık dosyalar fixture'larla doğrulanır. Noktalı virgülle kör split yoktur. Scanner nesne sınırları için aday üretir; tek başına tam parser kanıtı değildir. Bilinmeyen statement/byte aralığı sessiz silinmez. Support durumu field-level tutulur.

Oracle `DEFAULT` ifadesi, quoted isim ve string literal içeriği üst harfe çevrilmez veya sıkıştırılmaz. Kodun yorum/boşluk farkları ayrı sınıflanır; optimizer hint ve conditional compilation yönergesi atılmaz. Emission ham source span veya doğrulanmış AST'den yapılır, normalize edilmiş karşılaştırma metni SQL olarak basılmaz.

Kaynakta örtük NLS/uzunluk semantiği (`VARCHAR2(20)` gibi) net değilse `UNKNOWN_SOURCE_SEMANTICS`; metadata/config kanıtı olmadan BYTE varsayılmaz. `NULL`, alanın yokluğu ve bilinmiyor birbirinden ayrıdır.

## Hedef Metadata

20 Ekim TTBP düzeltmesi: schema mapping'de isteğe bağlı `metadata_reader`
ile önceden yetkilendirilmiş ayrı bir katalog okuyucusu açıkça seçilebilir.
Mantıksal source/target owner aynı kalır; owner remap yapılmaz. Okuyucunun
SESSION_USER kimliği, etkin SELECT_CATALOG_ROLE, gerçek hedef kullanıcısının
varlığı ve DBA kataloğuna erişimi salt okunur transaction içinde doğrulanır.
Bu modda yalnız sabit/bindli DBA metadata sorguları tam envanteri sağlar;
ALL_OBJECTS görünür alt kümesinden yokluk kanıtı türetilmez. Yeni yetki,
istemci kimliği değişikliği veya güvenlik trigger'ına müdahale yapılmaz.
`capture_timeout_seconds` 30–7.200 saniye aralığında açık hedef bütçesidir;
varsayılan 900 saniyedir. Eksik veri timeout artırılarak tam sayılmaz.

Asgari: `ALL_OBJECTS`, `ALL_TAB_COLUMNS`/gerekli sürümde `ALL_TAB_COLS`, `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS`, `ALL_INDEXES`, `ALL_IND_COLUMNS`, gerekirse `ALL_IND_EXPRESSIONS`, `ALL_SEQUENCES`, `ALL_TAB_COMMENTS`, `ALL_COL_COMMENTS`, `ALL_SYNONYMS`, `ALL_TAB_PRIVS`, `ALL_DEPENDENCIES`, `ALL_ERRORS`; nesne DDL'si için `DBMS_METADATA.GET_DDL` ve gerekli dependent DDL.

Tüm sorgular sabit allowlist'tedir; owner/name bind edilir. Metadata dışında iş tablosu satırı okunmaz; `COUNT(*)` dahi varsayılan akışta yoktur. Tablo sayım ihtiyacı raporda doğrulama gereği olarak üretilir. `NEXTVAL`, package fonksiyonu, view sorgusu çalıştırılmaz.

`ALL_*` boş sonucu görünürlük yetersizliğinden gelebilir. Kaynakta olan/hedefte görünmeyen nesne için negatif kanıt ancak yetkili tam hedef envanteriyle geçerlidir. Metadata cross-schema yetkisi DBA tarafından önceden sağlanmalıdır. `SELECT` object grant'i GET_DDL erişimini tek başına kanıtlamaz (Oracle DBMS_METADATA security model, K01).

Metadata toplama sonuçları alan grubu başına `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `NOT_APPLICABLE` olur. İlgili grubun hata kodu ve sorgu kimliği kaydedilir; sır içeren hata mesajı maskelenir. ORA-01031/ORA-00942/timeout, 'nesne yok' sonucuna dönüşmez. `GET_DEPENDENT_DDL` için yalnız doğrulanmış 'bu dependent tür yok' durumu ve yeterli envanter kanıtı boş sonuç sayılabilir; tüm DatabaseError'lar yakalanıp yutulmaz.

## Kimlik Ve Eşleştirme

Kanonik identity: source profile ID + logical source owner + object type + Oracle effective object name + opsiyonel parent/subname. Target owner fiziksel kanıt alanında ayrıca tutulur. Oracle unquoted `FOO` ile quoted `"FOO"` aynı etkin isimdir; `"Foo"` farklıdır. İç anahtarları delimiter birleştirmesiyle çakışabilir üretme; kanonik JSON dizisinin SHA-256'sını kullan. Oracle namespace çakışmalarını ayrıca kontrol et.

PACKAGE_SPEC/BODY ve TYPE_SPEC/BODY ayrı operation olabilir. Parent tablo içindeki kolon/constraint/index kimliği parent owner/name içerir. Dosya adı doğrudan quoted identifier değildir; güvenli kısa slug + hash kullanılır. Windows `CON`, `AUX`, slash, backslash, `..`, Unicode ve case-insensitive path çakışmaları kapsanır.

## DDL Metadata Tutarlılığı

Hedefte `INVALID` nesne bulunması rapor uyarısıdır; tek başına engel veya eksik
envanter sayılmaz. Derleme durumu, DDL farkı ve SQL üretilebilirliği ayrı tutulur.
Yalnız hedefte bulunan ve korunacak INVALID nesnenin DDL'si yakalanmış, dictionary
tam ve hata yalnız parser kaynaklıysa gövdesini karşılaştırmak gerekmez; varlığı
`EXTRA/INFORMATIONAL`, INVALID/parse durumu uyarı olarak raporlanır. Ham target
snapshot coverage değiştirilmez; plan scope gerekli karşılaştırmanın kapsamıdır.
Gerekli ortak tanımın bilinmemesi, izin hatası veya eksik ham DDL bu istisnaya
girmez. INVALID hedef veya dış referansın varlığı, FK kolon/PK/UK yapısı için
kanıt sayılmaz; gerçek yapısal önkoşullar ayrıca doğrulanır.

Target dictionary ve GET_DDL çelişiyorsa 'en yenisini seç' yaklaşımı yoktur; yeniden snapshot veya bloklama. LAST_DDL_TIME ve envanter ön/son kontrolü `observed_consistency` alanına kaydedilir. Mutlak tutarlılık iddiası yoktur. Başarısız target'ın `difference_count` değeri **null** olur; 0 yazılmaz.

## Boş Hedef Ve Fark Yok

Tam envanteri doğrulanmış boş şemada desteklenen source nesneleri doğru sıra ile CREATE edilir. Kaynağın da boş veya kökün eksik olması aynı durum değildir: eksik kök `SOURCE_SCOPE_MISSING`, açık boş kaynak profili ise politika onayı olmadan uygulanabilir plan üretmez.

`NO_CHANGE` yalnız bütün seçili yönetilen nesneler ve gerekli alanlar incelendiyse kullanılabilir. Parse hatası, bilinmeyen nesne tipi veya izin eksikliği bulunan hedef 'fark yok' olamaz. Target-only nesneler raporlanır; hepsi yalnız korunacak INFORMATIONAL farksa sonuç `NO_ACTION` olur. 0 DDL, `NO_CHANGE` demek değildir.
