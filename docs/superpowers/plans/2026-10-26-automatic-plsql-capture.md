# PL/SQL Kanıtını Normal Karşılaştırmaya Bağlama

Amaç: Oracle kaynak seçilen yerel UI karşılaştırmasında, eksik exporter envanteri
olan sınırlı statik PL/SQL birimlerinin metadata'sını salt okunur toplamak. Kaynak
ve hedef kanıtları kayıtlı snapshot'a bağlanır; kanıt yoksa mevcut REVIEW kuralı
korunur. Git kaynağı, TTBP günlük işi ve SQL uygulama sınırı değişmez.

1. Önce sentetik kırmızı test: uygun Oracle kaynak birimi seçilir, ikinci salt
   okunur oturumda metadata toplanır, kanıt ham blobuyla özel arşivde saklanır.
   Kaynak filtresi kanıt bağını bozmaz. Hedef, kaynak dependency kayıtlarının
   aynı sürümünü tamamlar. Eksik yetki/kimlikte READY çıkmaz.
2. En küçük entegrasyon: `collect_source` sonrası kaynak, `collect_target` sonrası
   hedef ek kanıtı. Yalnız tek kendi hesabı şeması ve en çok 64 aday birim. Diğer
   durumlarda eski karşılaştırma davranışı ve somut `UNAVAILABLE` kaydı.
3. İlgili testler, tüm birim takımı, ardından SKY yerel UI üzerinden yeni Oracle
   kaynak ve gerçek Oracle hedef canlı karşılaştırması. Önceki gerçek hedefin
   1743 fark, 567 READY, 51 REVIEW, 1 BLOCKED ve SQL gövdesiyle eşdeğerliği
   doğrulanır. Dosya hedefinin mevcut SQLcl paketi yeni ek metadata'yı taşımadığı
   için aynı otomatik genişleme bu dosya yoluna mal edilmez; ayrı iş kaydedilir.
4. Sonuç/süre, açık 51/1, sınırlar ve sonraki kararlar devir belgelerine yazılır.
   Oracle DDL/DML/COMPILE, SMTP, Jenkins iş değişikliği ve Git push yok.

## 26 Ekim durum

Ürün entegrasyonu ve ilgili RED -> GREEN regresyonlar tamamlandı. Kaynak/target
ek kanıtı kendi hesabı için ayrı salt okunur işlemde, en çok 64 aday birimle
toplanır. Kanıt özel source/observation arşivine yazılır. Filtre yalnız nesne
çıkardığında korunmuş nesnelerin hash'i sınanır. Ek oturum kapanış hatası ana
karşılaştırmayı düşürmez. Tüm birim takımı 1213 PASS.

Canlı kabul çalışması 4e0d515fcf004849817b4c6f7b1094b2 kaynak toplamada
SOURCE_CAPTURE_ERROR ile kapandı. Bağımsız bağlantı testi DPY-6005; kaynak ve
hedef TCP uçları erişilemiyordu. Çalışmada source snapshot, karşılaştırma veya SQL
oluşmadı. Bu ilk denemenin sonucu BLOCKED olarak korunur. Dosya hedefinin SQLcl paketi yeni ek metadata'yı
taşımıyor, bu yolun genişletilmiş eşdeğerliği ayrı iş.

## 26 Ekim ağ erişimi sonrası canlı kabul

VPN/kurum ağı açıldıktan sonra kaynak ve hedef TCP, ayrıca kaynak salt okunur
envanter testi geçti. Olağan yerel worker ile gerçek Oracle kaynak ve tek gerçek
Oracle hedefte yeni koşu `77f5933fa91841239ae3e892ee429277` tamamlandı:
`PARTIAL`, 1743 fark, 567 READY SQL, 51 REVIEW, 1 BLOCKED, 610 bilgilendirme.
Toplam 478.760 sn (7 dk 59 sn), kaynak hazırlama 176.166 sn (2 dk 56 sn).
Kaynak 432, hedef 422 ek metadata sorgusu kaydetti; sekiz statik PL/SQL terfisi
canlı worker akışında yeniden oluştu. Mail gönderilmedi, DDL uygulanmadı.

Önceki doğrulanmış gerçek hedef planına göre tüm 567 SQL gövdesi, karar sayıları
ve kaynak DDL hash'leri aynı. İki sequence'in `START WITH`/sayaç gözlemi
ilerledi; bu nedenle iki farkın değerleri ve iki işlemin ayrıntısı byte düzeyinde
aynı değildir. Hedefte eski kayıttaki 12 `C$_/I$_` adlı nesne artık yok,
aynı ad deseninde iki yeni nesne var; karşılaştırma kapsamı ve DDL kararı etkilenmedi.
Özel `.local/auto-capture-live-verification.json` kanıtı
`PASS_WITH_RUNTIME_DRIFT`. Tam snapshot eşitliği iddia edilmez. `DENEME`
fonksiyonu BLOCKED ve SQL'siz kaldı. Dosya hedefi ek metadata taşıma işi ve
Jenkins otomatik kabulü halen ayrı `NOT_RUN` kapsamındadır.
