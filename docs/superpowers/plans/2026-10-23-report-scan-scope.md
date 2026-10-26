# HTML tarama kapsamı uygulama planı

Kullanıcı, DDL Sync raporundaki toplam nesne ve tür dağılımını istedi.
Mevcut HTML ailesinde KPI şeridinin altında Tarama Kapsamı bölümü eklenir.
Kullanıcının son düzeltmesiyle toplam ve tür dağılımı yalnız seçili kaynak
şemalarına aittir, değişmeyen nesneler de dahildir. Kaynak hedef sayısıyla
çarpılmaz. Teknik nesne politikası korunur, COMMENT/GRANT metadata kayıtları
nesne toplamına eklenmez. Paket tanım/gövdeleri ayrı nesnelerdir. Hedef
envanteri yalnız teknik özet kanıtında kalır, görünür toplamda kullanılmaz.

Plan ve SQL kararları değişmez. Snapshot'tan türetilen küçük scan-summary.json
bundle manifestine girer, web/mail aynı özeti okur. Eski arşivde özet yoksa
sayı Bilinmiyor olur. Eksik envanter tam tarama diye sunulmaz.
Yeni Oracle bağlantısı, Jenkins değişikliği veya mail gönderimi bu işte yoktur.

- [x] Kırmızı test: aynı nesneler dahil tam envanter, tür dağılımı, kaynak
  tekilleştirme, boş/eksik/eski hedef ve sunum.
- [x] Snapshot özetini üret, bundle bütünlüğü ve plan bağlantısını doğrula.
- [x] Genel web/mail ve hedef web sayfasına mevcut stile uygun bölüm ekle.
- [x] İlgili testler, tüm pytest ve sözleşme kapısı, sentetik görsel kontrol.
- [x] Devir/durum belgelerine kanıt ve NOT_RUN sınırlarını yaz.
