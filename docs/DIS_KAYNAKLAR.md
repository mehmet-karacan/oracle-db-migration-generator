# Teknik Kaynaklar Ve Kararlara Etkileri

19 Ekim 2026 tarihinde birincil dokümanlar üzerinden kontrol edildi. Aşağıdaki açıklamalar ürün tasarım kararlarıyla birlikte okunmalıdır, kurum kurulumu/sürümü/izinleri doğrulanmış değildir.

| Kod | Kaynak | Bu Tasarımda Kullanıldığı Yer |
|---|---|---|
| K01 | Oracle 19c DBMS_METADATA - https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_METADATA.html | GET_DDL/dependent DDL ve görünürlük. Object SELECT izni ile metadata çıkarımı aynı değildir, boş sonuç tamlık kanıtı sayılmaz. |
| K02 | Oracle 19c ALTER TABLE - https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/ALTER-TABLE.html | Kolon dönüşümlerinde boyut/semantik, mevcut veri, constraint ve partition kısıtları, koşulsuz güvenli ALTER varsaymama. |
| K03 | Jenkins Credentials Binding - https://www.jenkins.io/doc/pipeline/steps/credentials-binding/ | Sırları dar scope'da bağlama, Groovy interpolation ve log masking sınırları. |
| K04 | Jenkins Artifact Content Security Policy - https://www.jenkins.io/doc/book/security/configuring-content-security-policy/ | Web raporunda yerel CSS/logo, script gerektirmeme, global CSP gevşetmeme. |
| K05 | Config File Provider - https://plugins.jenkins.io/config-file-provider/ | Merkezi JSON profile/target registry seçimi. |
| K06 | HTML Publisher - https://plugins.jenkins.io/htmlpublisher | publishHTML ve standart Jenkins artifact fallback. |
| K07 | Oracle python-oracledb kurulumu - https://github.com/oracle/python-oracledb/blob/main/doc/src/user_guide/installation.rst | Thin/Thick sürüm ve platform kontrolü, varsayılan driver modu. |
| K08 | Oracle python-oracledb initialization - https://github.com/oracle/python-oracledb/blob/main/doc/src/user_guide/initialization.rst | Bir process içindeki bağlantıların mod ortaklığı, target worker izolasyonu. |
| K09 | Oracle 19c DBMS_METADATA_DIFF - https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_METADATA_DIFF.html | Nesne/SXML karşılaştırma API'si, her nesne türüne genellememek, Git SQL girişine doğrudan çözüm varsaymamak. V1 dependency değildir. |
| K10 | Oracle object names - https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Database-Object-Names-and-Qualifiers.html | Oracle identifier case/quoting/namespace kuralları, OS dosya adıyla ayırma. |

## Lisans Ve Sürüm Sınırı

DBMS_METADATA_DIFF veya ticari Liquibase yeteneğinin kullanım hakkı bu incelemeyle sağlanmış değildir. Zorunlu lisans bağımlılığı oluşturulmadı. Mevcut Analyzer'ın `LicenseRef-Proprietary` ve parser'ın `vendor/antlr-plsql/LICENSE-and-NOTICE.txt` kayıtları korunacak, kodun public repoda görünmesi yeniden lisanslama yetkisi anlamına gelmez.

Dokümanlarda görülen güncel bir Oracle patch sözdizimi, kurumun aynı patch'i kullandığını kanıtlamaz. Örneğin `IF EXISTS` gibi sürüme bağlı kolaylıklar patch bilinmeden üretilmez. Runtime capability probe ve test matrisi esas alınır.

## Yerel Birincil Kaynaklar

Yüklenen iki arşiv için dosya yolları, SHA-256 değerleri ve fonksiyon konumları `reference-lock.json` içindedir. Schema Compare GitHub yolları aynı dosyada commit'e sabitlenmiştir. Kaynak referansı olmayan özellik 'mevcut yetenek' sayılmaz, yeni planner kuralları bu paketin tasarım kararlarıdır.
