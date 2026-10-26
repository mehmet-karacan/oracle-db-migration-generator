# Proje çalışma alanı ve sade arayüz uygulama planı

Kullanıcının onayladığı düzen ve son proje izolasyonu talimatı kapsamdır.
Uygulama adı Şema Karşılaştırma. Mevcut workspace korunur, commit/push yok.

- [x] Proje sınırı: ayarlar proje kimliğinde sürümlenir, legacy defaults yalnız
  SKY içindir. API liste/detail/test/artifact/save/start seçili projeyi doğrular.
  Proje değişimi eski istekleri ve form sonuçlarını yeni ekrana taşımaz.
  RED: test_control_workspace.py, GREEN: store/api/frontend kapsamı.
- [x] Parolalı oturum: mkaracan / Mehmet KARACAN, loopback ilk kurulum,
  salt+scrypt, süreli opaque HttpOnly cookie, çıkış/iptal ve deneme sınırı.
  Proxy modu korunur. RED: test_control_login.py, GREEN: password_auth/api,
  LoginScreen ve sunucu seçeneği. Varsayılan parola üretilmez.
- [x] Ortak ekran: tek başlık, bütünleşik sidebar, kompakt proje seçimi,
  ortalı alt bilgi, profil seçimi/adı tek bölüm, belirgin eşleştirme sekmeleri,
  anlamlı ikon renkleri ve gerçek sonuç sayıları. RED: WorkspaceFlow.test.tsx,
  GREEN: App/ComparisonForm/SchemaMappings/RunSummary/CSS/translations.
- [x] İlgili Python ve frontend testleri, build/lint, browser reflow ve iki
  proje geçişi, bağımsız son inceleme, devir.

Arayüz standartları docs/ARAYUZ_STANDARTLARI.md. Gerçek Oracle/Jenkins/SMTP yok.
Özetler yalnız doğrulanmış kanıttan, bilinmeyen sayı null kalır. SQL değişmez.
İnceleme odağı: cross-project ID erişimi, eski async işin yeni projede kaydı,
parola/session sızıntısı, ilk kurulum yarışı, forged proxy bypass, frozen spec,
eksik envanterin sıfır/tam diye gösterilmesi.

## Teslim kaydı

Pre-flight: yeni profile/settings project_id ve session kimliği mevcut kapalı
sözleşmeyle birlikte ele alındı. Ruling: mevcut kirli workspace korunur, bu
kullanıcı işi için commit/push veya temizlik yapılmaz. Aktif kullanıcı kapsamı
ADR-025 ile kayıtlıdır, motor mimarisi değişmez.

Task 1 complete: cross-project detail/save/test/artifact/start, proje ayarları,
late response ve unmount sonrası run/test davranışı test edildi.
Task 2 complete: parola kurulum/giriş/çıkış, no-secret storage, expiry/deneme
sınırı ve forged proxy senaryoları test edildi. Gerçek ilk parola kullanıcıya ait.
Task 3 complete: sade ekran ve gerçek #55 metadata özeti, 320 px ve iki dil/tema.
Final review: bağımsız read-only reviewer, Critical0/Important2/Minor0/Declined0.
Final fixed: terminal claimed kapasitesi COMPLETE ve FAILED testleri RED→GREEN.
Final fixed: reverse proxy ilk kurulumu açık yerel bootstrap flag'ine bağlandı,
network-service test RED→GREEN. review-green.log 9/9. Python tam suite1096/1096.
Frontend35/35, buildPASS, lint0error/4öncekiwarning. Son kanıt yz/DEVIR.md.
