# Taşınabilir Oracle toplama ve filtre sözleşmesi

25 Ekim kullanıcı onayı. SQL*Plus tabanlı, SQLcl ortak komut alt kümesi destekli
tek toplama script'i. Üretimde Python/web/parser kurulmaz. Seçili projeye ait
anlık görüntü import edilir, aynı Python motoruyla salt okunur karşılaştırılır.

Filtreler bağımsızdır: schemas, object_types (TABLE/VIEW...), object_names,
table_names kısayolu, data_types (NUMBER/VARCHAR2...), include_related ve teknik
nesne politikası. Adlar kesin eşleşir, joker varsayımı yoktur. Tablo adı kısa
yolu TABLE kökünü seçer. Veri tipi eşleşmesi tüm tablo/view yapısını seçer,
kolonları budamaz. Tablo closure kolon/kısıt ve mevcut indeks/trigger/comment
bilgisini içerir. Harici referans şemalara kendiliğinden genişlemez.

Güven: parametreler doğrudan SQL metnine substitution ile girmez. Uygulama/CLI
ve Windows PowerShell5.1+ launcher doğrulanmış değerleri hex kodlu bind script'e
çevirir, collector SET DEFINE OFF ile sadece kapalı SELECT/DBMS_METADATA okur.
Parola argv/config/paket içinde yoktur. Bağlantı açık SQL istemcisi oturumunda
veya /nolog + etkileşimli CONNECT ile yapılır. Kalıcı DB nesnesi oluşturulmaz.
Oracle19c referans hedeftir, client SQL*Plus19c+/SQLcl için canlı kabul ayrı.

Çıktı sürümlü, sadece ASCII taşıyan JSONL stream'dir. Uzun metinler AL32UTF8
Base64 parçalarıyla taşınır, CLOB/LONG kesilmez. Başlık/sorgu durumları/DDL/
ön-son envanter/footer zorunlu, sıra/limit/eksik/kesilme importta doğrulanır.
Kendi şeması ve doğrulanmış mevcut katalog yetkisi tam envanter sağlayabilir.
Görünür alt küme/ORA/eksik metadata UNKNOWN/PARTIAL kalır. Filtre dışındaki
DDL yokluğu nesne yokluğu sayılmaz, tam envanter ile varlık kaydı korunur.

Import aynı collector projection/enrichment bileşenlerini yeniden kullanır,
SQL yeniden yazmaz. İçe alınan tanım çalıştırılmaz. Snapshot bağlantısı parola
taşımaz, projeye bağlı ve değişmezdir. UI export/import + filtreler görünürdür.
Kaynak filtresi kök nesne kümesini belirler, hedefe aynı kimlik kümesi uygulanır.
Veri tipi hedefte değişmiş diye hedef nesne saklanmaz. Paket kapsamını aşan
istek eksik kapsam olarak reddedilir veya UNKNOWN ile açıkça sınırlandırılır.

Canlı Oracle/DDL/DML/Jenkins/SMTP/push bu tur kapsam dışı. Offline SQL grammar,
launcher prepare-only, adversarial stream, gerçek parser/planner üretimi ve UI
akışı doğrulanır. Client/Oracle gerçek kabul NOT_RUN kalır.


25 Ekim canlı kabul düzeltmesi: SQLcl2000-karakter VARCHAR2 bind sınırı nedeniyle
metin parametreleri CLOB bind ile taşınır ve collector yerel VARCHAR2 değerlerine
alır. Hex/DEFINE OFF ve4000 UTF8 bayt liste sınırı korunur. Blok DBMS_OUTPUT
buffer'ını NULL ile açar, kendi çıktı/değer/satır bütçesi değişmez. Ham envanter
oynarsa ORA-20011 ile başarısız biter, COMPLETE footer verilmez.

SQLcl oturumu metadata dönüşümlerini değiştirebildiğinden collector başlangıcında
DBMS_METADATA SESSION_TRANSFORM DEFAULT kullanılır. Nesne SQL'i ve veri export
ifadeleri çalıştırılmaz. İsteğe bağlı session_calendar query'si NLS_CALENDAR
kanıtını taşır. Eski dosyada bulunmuyorsa UNKNOWN kalır, takvim uydurulmaz.
