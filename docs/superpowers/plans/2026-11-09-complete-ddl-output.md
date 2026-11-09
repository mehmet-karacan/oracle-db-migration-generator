# Schema Compare Eksik DDL Üretimi

Author: Mehmet KARACAN
Date: 2026-11-09

Goal: 105 karşılaştırmasındaki 238 eksik DDL kaydını gerçek SQL dosyalarıyla tamamlamak.
Architecture: Bağımlılık kontrolü hazırlanmış SQL'i öneri olarak korur.
Eksik üretim yolları kaynak tanımından türüne uygun DDL önerisi hazırlar.
READY kararı, metadata belirsizliği ve uygulanmama bilgisi ayrı korunur.
Tech Stack: Mevcut Python CLI, SqlIntent, Oracle SQL ve Jenkins HTML ailesi.
Spec: Kullanıcının farklı bütün nesneler için DDL ve yalnız kendisine mail talimatı.

Sınır Oracle DDL ve DML uygulamamaktır. Kayıtlı 105 kaynak ve hedefi kullanılır.
Ekip gönderimi onay bekler. Yeni branch, commit veya dış Git push yoktur.
Eksik kaynak tanımı uydurulmaz. Hazır SQL gövdeleri korunur.

- [x] 105 kayıtlarını neden, tür ve kaynak tanımıyla incele.
- [x] Hazır SQL'in bağımlılık engelinde kaybolmasını kırmızı testle göster.
- [x] Kolon, kısıt, indeks, bölüm, özel tablo ve eksik projection senaryolarını test et.
- [x] graph.py içinde hazırlanmış SqlIntent'i öneride koru.
- [x] planning/ddl_proposals.py ile tamamlanan DDL yollarını uygula.
- [x] Kayıtlı gerçek girdilerde bütün eksik kayıtları ve eski SQL eşitliğini doğrula.
- [x] Paket ve ilgili testleri doğrula, Jenkins kurulu sürümünü güncelle.
- [x] Gerçek 105 girdilerinden yeni arşiv üret, SQL dosyalarını ve HTML sayımını kontrol et.
- [x] Güncel maili yalnız mkaracan@innova.com.tr adresine gönder ve devir kaydını yaz.

Canlı tanı 107 SUCCESS. 238 kaydın tümünde kaynak nesnesi ve ham tanım var.
96 tablo, 43 indeks, 53 paket, 22 prosedür, 10 görünüm, 9 açıklama,
3 fonksiyon, 1 tetikleyici ve 1 maddi görünüm kaydı incelendi.
Oracle ALTER TABLE 19c belgesindeki modify_to_partitioned ve constraint
kuralları üretim sözdizimi için birincil referanstır.

112 kabulü tamamlandı. 238 yeni DDL ve eksik 0 doğrulandı. Önceki 1783
hazır SQL gövdesi aynı. Toplam 2120 DDL dosyası var. Kaynak ve hedef 105
kaydıyla sabit. Oracle bağlantısı sıfır. SQL uygulanmadı. Mail yalnız
kullanıcıya gönderildi. 64 kurulu paket testi geçti. Son tam test 1417 PASS
ve eski paketle de tekrarlanan 1 Git publication hatası verdi.

Birincil sözdizimi kaynağı
[Oracle 19c ALTER TABLE](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/ALTER-TABLE.html).
