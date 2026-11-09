# Schema Compare Başarısız Toplama Maili

Author: Mehmet KARACAN
Date: 2026-11-09

Amaç, kullanıcıya giden 97 mailindeki kaybolan kaynak bilgisini düzeltmek
ve başlığı yalnız Schema Compare yapmaktır. Hedef iki okumada da değiştiği
için bu çalışmada karşılaştırma oluşmadı. Sayı veya başarı uydurulmaz.

Kaynak envanteri hedef toplamadan önce hazırlanmış snapshot üzerinden
sayılır. reporting/context.py yalnız adları, şemaları ve sayımları tutar.
inventory.py mevcut sayım kuralını paylaşır. view.py başarısız hedefte
aynı kaynak SHA ve hedef listesiyle doğrulanan bağlamı kullanır.
jenkins_run.py bu bağlamı hedef okumadan önce yazar. jenkins_notification.py
aynı çalışmanın bağlamını okuyarak son mail ve HTML görünümünü oluşturur.

- [x] Sabahki 97 kaydında CHANGED_DURING_CAPTURE nedenini doğrula.
- [x] Onaya kadar canlı alıcıyı yalnız mkaracan@innova.com.tr yap.
- [x] Başarısız hedef, çok hedef ve eski SHA testlerini kırmızı çalıştır.
- [x] Bağımsız kaynak bağlamını ve açık hata metnini uygula.
- [x] Başarılı karşılaştırmanın sayımlarını koruyan testleri tamamla.
- [x] Aynı motorla yeni rapor paketini oluştur ve test et.
- [x] Jenkins ortam kontrolüyle paketi kur. Yeni karşılaştırma başlatma.
- [x] 97 kaynak snapshot dosyasını salt okunur kullanarak yeni önizleme üret.
- [x] Özgün arşivleri koru. Test mailini yalnız kullanıcıya gönder.
- [x] Devir kaydını tamamla. Ekip gönderimi için kullanıcı onayını bekle.

Kabulde eski SHA, yanlış hedef, negatif sayaç, tekrar sayılan kaynak ve
başarısız toplamanın sıfır fark gibi sunulması reddedilir. SQL gövdeleri,
bağlantılar, motor, tutarlılık kontrolü, özgün logo ve tek mail bağlantısı
korunur. Commit, push ve Oracle DDL veya DML yoktur.
