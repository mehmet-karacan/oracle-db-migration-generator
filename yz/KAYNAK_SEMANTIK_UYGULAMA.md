# Kaynak uzunluk semantiği — kısa düzeltme kaydı

Önceki goal turu ilerleme idi: named backing index yolu ve A09 contract komutu
tamamlandı, 145 kısa test geçti. Şimdi A06–A08 özellik koruma gereği kontrol edildi.

Bulgu: source profili BYTE/CHAR bilirken CREATE TABLE ve ADD COLUMN ham kolon
metnini aynen basıyor; örtük VARCHAR2/CHAR uzunluğu execution oturumundan etkilenir.
Kaynak/target'a SQL çalıştırılmadan sentetik reparse ile gösterilecek.

1. CREATE ve ADD için profilin CHAR/BYTE değerinin SQL ve yeniden parse sonucunda
   korunduğu kırmızı regresyonlar; explicit kaynak BYTE/CHAR önceliği.
2. Yalnız örtük karakter tipi uzunluğuna doğrulanmış semantik token'ı ekle;
   DEFAULT, literal, yorum, inline constraint ve diğer ham metin korunur.
3. Kısa testler, wheel ve yeni immutable rapor; kaynak/target sürekli salt okuma.

Collation ayrı gerçek veri ihtiyacıdır. Oracle'da karakter kolonları explicit
COLLATE, foreign-key parent veya oluşturma anındaki tablo varsayılanından
etkilenebilir; güncel şema/oturum varsayılanı geçmiş kolon değerini tek başına
kanıtlamaz. Hedeften veya varsayılan dokümantasyon değerinden source değeri atanmaz.
Kaynak kayıtlarında etkin kolon semantiği veya tüm örtük kolonlar için geçerli
olduğu yetkili olarak doğrulanmış export sözleşmesi gerekir.

Resmi kaynak:
https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-TABLE.html
(column COLLATE / DEFAULT COLLATION);
https://docs.oracle.com/en/database/oracle/oracle-database/19/nlspg/linguistic-sorting-and-matching.html
(Specifying Data-Bound Collation for a Column).

Sonuç: 156 kısa test / 19.45s; bağımsız son dar kontrol 11 passed / 3.88s.
Kaynak semantik değerleri bilinmiyorsa UNKNOWN kalır. Source profile'e veya
canlı source/target'a tahmini değer yazılmadı. V5 yerel paket yeni program hash'iyle
üretildi; eski paketler korunur. Parser değişmediği için gereksiz tam source/target
reparse yapılmadı. VARCHAR eş adı ve CLOB/NCLOB sabit collation davranışı resmi
Oracle 19c Data Types / CREATE TABLE belgeleriyle kontrol edildi.
