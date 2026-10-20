# Sentetik Sözleşme Örnekleri

Bu dosyalar çalışan ürün çıktısı değil, Codex'in uygulayacağı JSON/SQL sözleşmesinin geçerli örnekleridir. Hiçbir gerçek bağlantı bilgisi veya kurumsal DDL içermez. Target hostları `.invalid` alanındadır; bağlantı kurulmaz. Kaynak SHA yalnız sentetik değerdir.

Örnek fark: APP.DEMO_NOTE.TITLE target'ta40CHAR, source'ta80CHAR. plan.example.json before=40/after=80 yönünü ve tek MODIFY operation'ını gösterir. Şema uyumu kontrol edilir; Oracle çalıştırma doğrulaması yapılmamıştır. `READY` burada örnek rule kararını temsil eder, uygulama onayı değildir.

Snapshot properties örneği kasıtlı olarak tek kolona odaklıdır. Tam ürün, DOGRULAMA ve DDL_KURALLARI belgelerindeki diğer özellikleri de gerçek parser/dictionary'den üretmelidir; sadece bu beş alanı destekleyerek görevi kapatamaz.
