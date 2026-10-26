# Taşınabilir Oracle Şema Toplama

Bu paket yalnız metadata ve özgün DDL okur. Mevcut SQL*Plus 19c+ veya SQLcl,
Oracle 19c+ hedeflenir. Python, web uygulaması veya parser production'a kurulmaz.
Gerçek SQL*Plus/SQLcl/Oracle kabulü ayrıca yapılmalıdır. Dosya ithalatında SQL
çalıştırılmaz. Eksik yetki, boş veya eşit şema anlamına gelmez.

## Çalıştırma

1. Paketi yazılabilir, yeni bir çalışma klasörüne çıkarın.
2. Mevcut SQL*Plus/SQLcl istemcisini başlatın ve normal yönteminizle bağlanın.
3. Paketin klasöründe `@run_export.sql` çalıştırın.
4. `capture.odmg.jsonl` dosyasını uygulamada seçili projeye içe aktarın.

```text
sqlplus /nolog
CONNECT kullanici@baglanti
@run_export.sql
```

SQLcl kullanılıyorsa `sql /nolog` ile aynı adımlar izlenir. Parolayı istemcinin
kendi gizli isteminde girin. Parola argv, selection.json veya çıktıda tutulmaz.
Script sonunda mevcut transaction rollback edilip istemci kapanır. Bu nedenle
ayrı ve temiz bir toplama oturumu kullanın. Mevcut işlem yapılan oturumu kullanmayın.

## Bağımsız parametreler

Windows PowerShell5.1+ hazırsa aynı collector ile yeni parametre paketi hazırlanır.
Bu komut veri tabanına bağlanmaz, yalnız bind request dosyasını üretir:

```powershell
.\New-Capture.ps1 -Schemas APP -ObjectTypes TABLE,VIEW -OutputDirectory C:\Temp\tum-yapi
.\New-Capture.ps1 -Schemas APP -TableNames ORDERS -OutputDirectory C:\Temp\orders
.\New-Capture.ps1 -Schemas APP -ObjectTypes TABLE -DataTypes NUMBER,VARCHAR2 -OutputDirectory C:\Temp\veri-tipleri
.\New-Capture.ps1 -Schemas APP,TTBP -ObjectTypes PACKAGE_SPEC,PACKAGE_BODY -ObjectNames PCK_JOB -Environment PROD -OutputDirectory C:\Temp\paketler
```

| Parametre | Davranış |
|---|---|
| Schemas | En fazla20 şema. Boşsa bağlanılan hesap. Unquoted adlar büyük harfe çevrilir. |
| ObjectTypes | TABLE, VIEW, INDEX, SEQUENCE, PACKAGE_SPEC, PACKAGE_BODY, FUNCTION, PROCEDURE, TYPE_SPEC, TYPE_BODY, TRIGGER, SYNONYM ve ilgili metadata türleri. |
| ObjectNames | Seçili türlerde kesin ad eşleşmesi. Joker/LIKE uygulanmaz. |
| TableNames | ObjectTypes=TABLE + ObjectNames kısayolu. ObjectNames ile birlikte verilmez. |
| DataTypes | NUMBER/VARCHAR2 gibi kolon tipleri. Eşleşen tablonun/view'ın tamamı alınır. Kolonlar budanmaz. |
| NoRelated | Varsayılan tabloya ait indeks/trigger/comment closure'ını kapatır. Harici şemalara genişleme yoktur. |
| IncludeTechnicalObjects | Varsayılan teknik nesne filtresini kaldırır. |
| FilterSide | SOURCE veya TARGET. Hedefte veri tipi değişmiş nesneleri kaçırmamak için TARGET seçin. |
| ReaderMode | AUTO, OWN, CATALOG, VISIBLE. Yeni yetki verilmez. |
| Environment | Bilgilendirme etiketi, en fazla80 karakter. |
| TimeoutSeconds | 30–7200, varsayılan900. Çağrılar arasında denetlenen süre bütçesi. Bloklanan tek Oracle çağrısını kesme garantisi yoktur. |
| MaxObjects | Seçilen DDL nesneleri için1–100000, varsayılan10000. |

DataTypes tek başına verilirse TABLE/VIEW/MATERIALIZED_VIEW seçilir. Diğer türlerle
birlikte veri tipi filtresi reddedilir. SOURCE için filtreler AND ile birleşir. TARGET modunda DataTypes DDL okumayı daraltmaz, diğer filtreler aynı kalır. Aynı listedeki
adlar OR'dur. Tablo seçimi kolon/kısıt ve ilgili indeks/trigger bilgisini kapsar.
Filtre dışı nesneler için DDL okunmaz, tam envanter varlık kanıtı korunur. Bu,
hedefte tipi değişmiş bir tablonun yanlışlıkla yok sayılmasını engeller.

Quoted adlar için örnek `-ObjectNames '"Mixed Case"'`. Tek tırnak ve & karakterleri
hex bind ile taşınır, SQL substitution yapılmaz. CSV ayıracı nedeniyle adında
virgül bulunan filtre değeri bu sürümde kabul edilmez. Nesne DDL'sindeki Türkçe,
Unicode, çift tırnak ve literal içeriği korunur.

## Yetki ve kapsam

OWN yalnız hesabın kendi şemasıdır. CATALOG, mevcut SELECT_CATALOG_ROLE ve DBA
owner erişimi doğrulanırsa kullanılır. AUTO bunu dener, aksi durumda VISIBLE
kısmi görünürlüğü açıkça kaydeder. VISIBLE hiçbir zaman tam envanter kanıtı değildir.
ORA-01031, ORA-00942 ve okunamayan metadata ayrı durumdur. Boş ALL_* sonucu tek
başına nesne yokluğu kanıtı sayılmaz. Başlangıç/bitiş envanteri farklıysa durum
kararsızdır, tam karşılaştırma sayılmaz. Grant/User güvenlik nesneleri otomatik
oluşturulmaz, tabloların iş verisi ve sequence NEXTVAL okunmaz.

## Çıktı ve sınırlar

JSONL dış taşıması ASCII/Base64'tür. Mesaj parçalarında SHA256, sıra ve bitiş
kaydı bulunur. Uzun CLOB/LONG parçalanır, kesilmez. Maksimum64 MiB dış dosya,
2 MiB UTF8 değer ve sorgu başına200000 satır vardır. Sınır aşımı sessiz budama
yapmaz. Eksik footer veya parça sırası importta reddedilir. DBMS_OUTPUT tamponu
nedeniyle çıktı oturum belleğinde tutulur ve blok sonunda istemciye gelir.
Büyük şemalarda parametrelerle kapsamı daraltın. Filtreli çıktı tam şema DDL
paketi değildir. İnternet veya otomatik yayın yoktur.

Çıkış0: toplama tamamlandı,10: metadata hatalarıyla kısmi çıktı,20: toplama
başarısız, diğer SQL*Plus/SQLcl bağlantı ve OS hataları istemci tarafından döner.
Çıktının aktarımına kurumunuzun kod/metadata erişim kuralları uygulanır.

## Kaynak ve hedef için örnek

Kaynakta NUMBER içeren ORDERS tablosunu karşılaştırmak için:

```powershell
.\New-Capture.ps1 -Schemas APP -TableNames ORDERS -DataTypes NUMBER -FilterSide SOURCE -Environment UAT -OutputDirectory C:\Temp\kaynak
.\New-Capture.ps1 -Schemas APP -TableNames ORDERS -DataTypes NUMBER -FilterSide TARGET -Environment PROD -OutputDirectory C:\Temp\hedef
```

TARGET, PROD tablosunda NUMBER artık VARCHAR2 olmuşsa da DDL'yi okur.
Karşılaştırmada hangi nesnelerin seçildiği kaynak üzerinden belirlenir.
Kaynaktan bağımsız bir hedef topluyorsanız DataTypes alanını boş bırakmanız da
aynı korumayı sağlar. Eksik DDL varsa motor tahmin yapmaz, belirsizliği gösterir.

COMMENT ve GRANT ayrı GET_DDL kökü değildir. Tabloya bağlı açıklama ve yetki
metadata grupları ayrıca taşınır. MATERIALIZED_VIEW_LOG mevcut motorun metadata
sözleşmesiyle değerlendirilir. Yalnız bu türlerden oluşan toplama isteği reddedilir.

## Generator CLI

Uygulamanın kurulu olduğu bilgisayarda, veri tabanına bağlanmadan paket üretimi:

```text
oracle-db-migration-generator prepare-capture --schema APP --table-name ORDERS --data-type NUMBER --output capture-source
oracle-db-migration-generator prepare-capture --schema APP --table-name ORDERS --filter-side TARGET --output capture-target
oracle-db-migration-generator import-capture --input capture.odmg.jsonl --source-profile source-profile.json --side SOURCE --connection-id uat-file --output imported-source
oracle-db-migration-generator import-capture --input target.odmg.jsonl --source-profile source-profile.json --side TARGET --connection-id prod-file --output imported-target
oracle-db-migration-generator plan-offline --source-snapshot imported-source/source-snapshot.json --target-snapshot imported-target/target-snapshot.json --source-profile source-profile.json --output comparison
```

`--schema`, `--object-type`, `--object-name`, `--table-name`, `--data-type`
parametreleri birden fazla kez verilebilir. Diğer seçenekler `--no-related`,
`--include-technical`, `--reader-mode`, `--filter-side`, `--environment`,
`--timeout-seconds` ve `--max-objects` biçimindedir. Import profilindeki şemalar
pakette bulunmalıdır. Kaynak/hedef yönü `--side` ile açıkça seçilir.

## Arayüz

Bağlantılar > Taşınabilir Toplama sekmesinde paket hazırlayın veya dosya aktarın.
Ardından Şema Eşleştirmeleri sekmesinde dosyayı kaynak/hedef seçin. Yeni
Karşılaştırma ekranında eşleştirmeyi ve nesne filtrelerini seçerek Bu Bilgisayar
üzerinde çalıştırın. Dosyalar ve çalışma sonuçları seçili projeye bağlıdır.
Bu sürümde Jenkins'e dosya karşılaştırması gönderilmez. Gerçek SQL yerel özel
arşivdedir. Import SQL çalıştırmaz ve mail göndermez.

Dosya ve mesaj hash değerleri aktarım bütünlüğünü denetler, üretici kimliğini
imzalamaz. Dosya kaynağını kurumun normal aktarım/onay yöntemiyle doğrulayın.
Salt okunur export için SELECT_CATALOG_ROLE gibi geniş yetkiler otomatik verilmez.
Aynı metadata erişim sınırı dosya üzerinde açıkça korunur.

İstemci davranışı için Oracle belgeleri:
[SQL*Plus SET komutları](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqpug/SET-system-variable-summary.html),
[DBMS_METADATA oturum dönüşümleri](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_METADATA.html),
[PL/SQL JSON tipleri](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/json-types.html).


## Bu sürümün bilinen sınırları

- SQL*Plus/SQLcl parametreleri CLOB bind olarak taşınır, collector içinde yerel
  VARCHAR2 değerlerine alınır. Her CSV parametre listesi en fazla4000 UTF8
  bayttır. Sınır aşılırsa paket hazırlanmaz. Gerekirse birden çok paket hazırlayın.
- CSV filtresine ek olarak bu sürümün import okuyucusu da adında virgül bulunan
  quoted şema/nesneleri kabul etmez. Bu tür bir nesne envanterdeyse dosya reddedilir.
- Collector64 MiB sayacı satır sonu ve bitiş satırı ek yükünü kapsamaz. Üst sınıra
  yakın bir çıktı import sınırını aşabilir. Nesne/tür/ad filtresiyle paketi küçültün.
- Aynı adda farklı owner'a bağlı indeks/tetikleyici collector closure'ına fazladan
  girebilir. Dictionary parent owner kanıtı bulunduğunda karşılaştırma dışında kalır.

Genişletilmiş VARCHAR2/DB ayarı veya yeni Oracle yetkisi bu paket için açılmaz.
Partition alt nesneleri root envanterine eklenmez, mevcut partition metadata
sorgularındaki ayrıntılar korunur.


SQLcl bazı sürümlerde VARCHAR2 bind değerlerini2000 karakterle sınırlar.
CLOB parametre aktarımı bu istemci sınırını aşarken kapalı filtre boyutu denetimi
korunur. SQLcl'in varsayılan DBMS_OUTPUT tamponuna güvenilmez, blok içinde
DBMS_OUTPUT.ENABLE(NULL) çağrılır. Paket/değer/satır bütçeleri ayrıca uygulanır.
Başlangıç ve bitiş ham envanterleri farklıysa export ORA-20011 ile başarısız
biter. Bu çıktı tam snapshot olarak içe aktarılmaz, yeniden toplama gerekir.

Toplama başında DBMS_METADATA oturum dönüşümleri DEFAULT değerine alınır.
Böylece SQLcl'in DDL dışa aktarma tercihleri tablo çıktısına veri aktarım SQL'i
ekleyemez. Bu işlem yalnız metadata çıktısının biçimini ayarlar, nesne veya veri
değiştirmez. Oturumun NLS_CALENDAR değeri de kaydedilir. Bu kayıt bulunmayan
eski dosyalarda tarih ifadeli indeks için takvim kanıtı UNKNOWN kalır.

Mevcut şemanın ALL_DEPENDENCIES kayıtlarında geçen harici nesnelerin yalnız
owner/ad/tür/durum bilgisi alınır. Bu işlem diğer şemaların DDL'ini veya verisini
okumaz, ek yetki tanımlamaz. Dosyada bulunmayan yeni bir harici referans, synonym
zinciri veya kolon/anahtar yapısı doğrulanmış sayılmaz. Gerekli kanıt yoksa ilgili
işlem engelli kalır. Eski dosyalarda bu ek sorgunun olmaması UNKNOWN anlamındadır.

## Doğrulanan İstemci Kabulü

25 Ekim 2026 SQLcl 26.2/Oracle 19c INNOVA_ODI kabulü PASS. Gerçek dosya UI üzerinden
aktarıldı. Aynı kaynakla canlı hedef gözlemi ve dosya hedefi1743 fark/542 hazır SQL/
71 inceleme/5 engeli aynı üretti.542 SQL gövdesi byte düzeyinde eşit. SQL*Plus canlı
kabulü NOT_RUN. Kendi ortamınızdaki yetki ve metadata kapsamını ayrıca doğrulayın.
