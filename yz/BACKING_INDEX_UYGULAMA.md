# Adlandırılmış backing index — kısa uygulama kaydı

Kapsam: A06–A08'de tanımlı yeni boş heap tablo PK/UK `USING INDEX owner.name`
olumlu yolunu tamamlamak. Kaynak/target salt okunur; fixture yalnız sentetik.
Jenkins, TTBP ve canlı DDL kabulü bu işin parçası değildir.

1. Kırmızı: ayrı CREATE INDEX + USING INDEX PK/UK, adlandırılmış/quoted owner,
   eksik veya yanlış kolonlu index ve bloklu index önkoşulu için kısa regresyonlar.
2. Tam kaynak AST index kimliği/table/kolon/durum kanıtını doğrula. Yeni tablonun
   yokluğu kanıtlanmış target'ta aynı parent'a ait index bulunduğu iddiası
   tutarsızdır; bu çelişkide otomatik reuse yapılmaz. Mevcut tabloya constraint
   eklenmesi ve dictionary association kabulü V1 REVIEW yolunda kalır.
3. TABLE CREATE → CREATE INDEX → ADD CONSTRAINT kenarlarını kur; SQL yalnız bir
   index CREATE içerir. Eksik/yanlış/uygunsuz index'e bağlı constraint hazır olamaz.
4. Üretilen bundle'ı grammar/kimlik/hash ile doğrula. Yeni kod hash'iyle yeni yerel
   rapor dizini üret; eski paketleri değiştirme. Kısa pytest ve wheel doğrulaması.

Oracle 19c resmi kaynak:
https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-indexes.html
(Specifying the Index Associated with a Constraint).

Uygulama kanıtı: ilk 6 hedefli test kırmızı, ardından yeşil. Bağımsız incelemenin
CREATE INDEX tail UNUSABLE ve inline USING INDEX sıralama bulguları da kırmızı
regresyonlarla kapatıldı. Inline key doğrulanmış ANTLR spanlarından ayrı constraint
haline alınır; kalan DEFAULT/NOT NULL/CHECK metni ve anonim kimliği korunur.
STORAGE parantezi function-based index key'i sayılmaz; yalnız key grubu incelenir.
İncelemeci son 10 dar testi ve önceki iki reproyu tekrar doğruladı.

A09'da belgelenmiş `tools/check_contracts.py` komutunun eksik olduğu görüldü.
Komut paket/root schema byte eşitliğini, 7 örneği, config semantiğini ve plan
hash/kanıt bağlantılarını ağsız doğrular. Drift ve schema-valid yanlış plan hash'i
regresyonlarla reddedilir. Bu komut paket başlangıç manifestini yeniden yazmaz.
