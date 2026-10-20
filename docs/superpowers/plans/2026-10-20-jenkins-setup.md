# Jenkins Generator işi kurulum planı

> **For agentic workers:** Use superpowers:executing-plans inline. Kullanıcı Jenkins'e girip işi oluşturmayı açıkça yetkilendirdi; ek tasarım/onay turu yok.

**Goal:** sky klasöründe ayrı Generator Pipeline işi, ilk kapsam yalnız INNOVA_ODI; kaynak/hedef salt okunur.
**Architecture:** Doğrulanmış immutable wheel + SHA'lı offline release bundle + workspace'e özel CPython 3.12. Mevcut Jenkins Stashed File Parameter ve Credentials kullanılır. Generator remote henüz boş olduğundan code push yapılmadan release yüklenir. Sonraki çalışmalarda hash'i doğrulanmış yerel release cache kullanılabilir.
**Tech Stack:** Mevcut Python CLI, stdlib bootstrap/runner, Jenkins Pipeline, mevcut JGit ve credentials/file-parameters eklentileri.
**Spec:** docs/JENKINS.md ve doğrudan kullanıcı Jenkins kurulum talimatı.

- [x] Bootstrap/runner için kırmızı test: paket SHA/path, desteklenen Python, yalnız INNOVA_ODI, credentials yalnız env, sonuç/exit kodları ve arşiv sınırı.
- [x] En küçük runner/Pipeline, sabitlenmiş offline Linux wheel lock + resmi CPython archive hash; yerel test/kurulum paketi doğrulama.
- [x] Jenkins'te ayrı iş oluştur; eski DDL Sync/diğer işler değişmez. Credential kimlikleri mevcut sky scope'undan; tetikleme/push/SQL uygulama yok; Jenkins bildirimi yalnız kullanıcının belirttiği mkaracan@innova.com.tr adresine.
- [x] Release upload ve salt ortam kontrolü; mümkünse gerçek read-only ilk karşılaştırma, çıktı arşivi ve UI kanıtı. Ortam yokluğu somut raporlanır.
- [x] Devir, test ve job/build URL kanıtları. Gerçek Git push/Oracle DDL yetkisi bu talimata dahil değildir. Jenkins bildirimi için yalnız mkaracan@innova.com.tr yetkilidir.

Kurulum dayanağı: Jenkins 2.492.3; sky-db-ddl-sync #62 agent jenkins-2/Python3.10.12; stashedFile eklentisi görünür. Yeni runtime sistem Python'ını değiştirmez.

20 Ekim kullanıcı mail düzeltmesi: ek dosya yerine genel HTML gövdesi; konu GPU | Oracle DB Migration Generator | DURUM | Build #N. #5 kaynak örtük BYTE/collation kanıtının CI portunu eksik buldu; önceki yerel read-only column correspondence guardları tool runner içine taşındı. Kaynak Git DDL değişmez. Raw column set/duplicate ve plan zamanı determinizm regresyonları da eklendi. #6 yeni release ile doğrulanıyor.

Tamamlandı: #4ENV SUCCESS; #6COMPARE UNSTABLE_BY_REAL_PLAN, UNKNOWN0,2.352fark/559READY/123REVIEW/5BLOCKED. Kaynak405tablo/0reject canlı eşleşti. Genel HTML body mail izinli tek alıcıya gönderildi; link gerçek arşivi açtı.332test geçti. Kanıt output/jenkins-setup/live-verification.json. OracleDDL/DML ve dışGitpush NOT_RUN.
