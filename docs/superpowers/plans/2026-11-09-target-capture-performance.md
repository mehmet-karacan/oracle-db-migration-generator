# Hedef Toplama Süresi

Author: Mehmet KARACAN
Date: 2026-11-09

120 koşusunda hedef toplama 333,507 saniye, toplam süre 634,126 saniyedir.
Kaynak önbelleği doğrulanmış olarak kullanılmıştır. Hedef metadata her koşuda
yeniden salt okunur toplanır. Sabah alıcısı ve zamanlaması korunur.

- [x] Hedef makbuzundaki sorgu ve uygulama sürelerini ayır.
- [x] Aynı SQL'in tekrar çözümlemesini kırmızı testle göster.
- [x] Büyük paketlerdeki parser beklemesini kayıtlı girdilerle ölç.
- [x] Sonucu koruyan düzeltmeleri ve ilgili regresyon testlerini tamamla.
- [x] Kayıtlı aynı kaynak ve hedefle DDL içeriğini karşılaştır.
- [x] Tam testleri ve kurulan paketin dosya bütünlüğünü doğrula.
- [x] Canlı testi tekrarla ve toplam süreyi ölç.
- [x] Mailin yalnız Mehmet KARACAN'a gittiğini ve SKY ayarının korunduğunu doğrula.

Veritabanında DDL veya DML uygulanmaz. Yeni branch oluşturulmaz.
Önceki kaynak önbelleği düzeltmesi korunur.

129 kayıtlı kabulünde 2416 SQL dosyası yalnız oluşturulan plan kimliği
yorumları dışında birebir aynıdır. İşlem kimlikleri ve kararlar aynıdır.
2120 DDL vardır, eksik DDL sıfırdır. Son yerel tam test 1471 passed,
kurulan paket kontrolü 102 passed. Hedef çözümlemesinin toplu kontrolü
devam eder. Bu aşama Oracle bağlantısı açmaz ve mail göndermez.

137 canlı tekrarında toplam 287,179 saniye ve hedef toplama 99,630 saniye
ile aynı kaynak ve doğrulanmış önbellekte beş dakika hedefi sağlandı.
136 ilk yeni sürüm koşusu 310,443 saniyedir. Soğuk kaynak veya yeni parser
sürümü için beş dakika garantisi değildir. Oracle metadata yeniden okundu.
2120 DDL ve sıfır eksik DDL vardır. 138 SQL kanıtında 2416 dosya eski 120
ile yalnız plan kimliği yorumları dışında aynıdır. Sabah SKY ayarı korundu.
Test mailleri yalnız Mehmet KARACAN'a gitti. SQL uygulanmadı.
