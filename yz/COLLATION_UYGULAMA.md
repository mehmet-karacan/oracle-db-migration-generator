# Etkin collation SQL korunumu - 19 Ekim 2026

CREATE/ADD üretimi, Git DDL'de örtük olan fakat kolon metadata'sıyla doğrulanan
collation'ı gelecekteki execution session varsayılanına bırakmaz. BYTE/CHAR
üretimi ve ham literal/comment içerikleri korunur, PL/SQL gövdeleri değişmedi.

- oracle/queries.py: sabit COLLATION_PARAMETERS sorgusu compatible ve
  max_string_size okur. CDB root için effective STANDARD kuralı uygulanır.
- oracle/capabilities.py: gerçek gözlemden data_bound_collation_enabled çıkar.
  Oracle major sürümü ve 4000-byte konservatif sınırı destek kanıtı değildir.
- oracle/collector.py: opsiyonel sorgu izni yoksa capability UNKNOWN, güvenli
  hata kodu receipt.capability_errors içindedir. Dictionary coverage bağımsızdır.
- planning/table_ddl.py: destek doğrulanınca etkin kolon COLLATE değeri datatype
  sonuna eklenir. Açık kaynak değeri korunur, çelişki bloklanır.
- Destek kapalıysa yalnız örtük USING_NLS_COMP, Oracle'ın zorunlu user-object
  semantiğiyle korunur. Başka değer veya açık declaration bloklanır. Destek
  UNKNOWN ise gereken işlem bloklanır. DEFAULT COLLATION suffix'i de denetlenir.
- Örtük CLOB/NCLOB intrinsic USING_NLS_COMP korunur, explicit LOB syntax aynı
  kapıdan geçer. NUMBER/DATE/RAW üzerinde COLLATE daima bloke edilir.
- table_rules.py ve builder.py yalnız etkilenen CREATE/ADD işlemini bloklar,
  capability kanıt ID'sini işlem ve precondition'a bağlar.

Dayanak: [Oracle 19c collation kuralları](https://docs.oracle.com/en/database/oracle/oracle-database/19/nlspg/linguistic-sorting-and-matching.html),
5.10.3–5.10.4. Özellik kapalıyken user-defined nesneler USING_NLS_COMP taşır,
COLLATE ve session DEFAULT_COLLATION declaration'ı kullanılamaz.

## Doğrulama

İlk testler 8 kırmızı/1 yeşil: eksik emission ve capability bloklaması gerçek SQL
üzerinden görüldü. Context yeniden üretimi ve tablo DEFAULT COLLATION ayrıca
kırmızı görüldü. Bağımsız incelemedeki explicit LOB/noncharacter early-return
bypass ailesi de önce kırmızı testle gösterilip tek fix pass içinde kapatıldı.

Son dar kapı 19 passed / 3.27s, bağımsız teyit 19 passed / 3.36s. Tam kısa kapı
176 passed / 24.80s, output/pytest-collation-final.xml, skip/failure yok.
check_contracts.py: 6 schema/7 örnek VERIFIED. Dist-v6 ve wheel-smoke-v6 import/
config kontrolü geçti, kurulu kod hash'i planla aynı. İlk no-isolation build,
venv'de setuptools olmadığı için başarısız oldu, önceki standart izole build
ile başarı sağlandı. Release/wheelhouse/platform matrisi çalıştırılmadı.

## Gerçek gözlem ve güncel paket

Önceki yerel source yardımcıda aynı-transaction inventory kontrolü tazeliği
kanıtlamıyordu. Kaynak metadata yeniden alındı: source-oracle-observation-v2.
Arada rollback ve yeni READ ONLY transaction ile 830 nesne envanteri eşit,
17456 kolon metadata kaydı. 405 Git tablosunda 16560 kolon yine eşleşti,
10088 BYTE ve 10379 collation tamamlandı. Source-v8 yeni, v6/v7 korundu.

Hedefte yalnız capability parametreleri yeni salt okunur oturumda okundu:
compatible=19.0.0.0.0, max_string_size=STANDARD. Örtük USING_NLS_COMP bu kanıtla
korunur. Target DDL yeniden alınmadı, capture-v2 zamanı ve eski DDL/properties/
coverage aynı kaldı. Target-reparsed-v7 ek capability kanıtıyla türetildi.
Endpoint, credentials ve ham source gözlemi .local altında, Git dışındadır.

local-report-v6: plan BLOCKED, run PARTIAL, NOT_EXECUTED. 2353 gözlenen fark,
447 READY, 119 REVIEW_REQUIRED, 69 BLOCKED, 1020 INFORMATIONAL. UNKNOWN 0,
beş kısmi INVALID target tanımı nedeniyle tam difference_count=null. Bloklar:
49 bağımlılık, 14 desteklenmeyen tablo özelliği, 4 iç nesne, 2 index tanımı.

472 bundle dosyası VERIFIED, run arşivi 482 dosya. 19 HTML, max 92560 byte,
0 kırık link, 0 gerçek endpoint/parola eşleşmesi. 180 Git adayında da 0 eşleşme.
Kanıt output/local-report-v6-verification.json. Tarayıcıda güncel sayılar ve
NOT_EXECUTED doğrulandı, Innova görünümü korundu. Eski v5'e yazılmadı.

Source/target DDL/DML, Jenkins job/build değişikliği, mail veya Git push yok.
TTBP/Jenkins kurulumu ertelendi. INVALID hedefler burada onarılmaz. Kaynak
bağlantısı için kullanıcıdan tekrar bilgi gerekmez.
