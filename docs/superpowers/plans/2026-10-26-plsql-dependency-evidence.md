# PL/SQL Bağımlılık Kanıtı Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Yerel kirli dal korunur, commit/push yapılmaz.

**Goal:** Kalan 59 incelemeyi izleyerek, salt okunur tamamlanan metadata ile güvenliği kanıtlanan PL/SQL birimlerini otomatik SQL üretimine açmak.

**Architecture:** Mevcut Python parser/planner korunur. Sınırlı sözlük sorguları güncel derleme, tanım, bağımlılık, synonym ve doğrudan yetki kanıtını toplar. Derleyici kanıtı exporter envanterinden ayrı tutulur ve kapalı güvenlik koşullarıyla kullanılır.

**Tech Stack:** Python, python-oracledb, mevcut snapshot/plan/yerel UI arşivi.

**Spec:** AGENTS.md, docs/KAYNAK_HEDEF_SOZLESMESI.md, docs/DDL_KURALLARI.md ve son kullanıcı talimatı.

## Global Constraints

- DENEME tablosu korunur, hiçbir DDL/DML/COMPILE uygulanmaz.
- Yalnız metadata SELECT ve salt okunur transaction. İş verisi okunmaz.
- Kaynak gövdeleri korunur, UNKNOWN yokluk veya başarı sayılmaz.
- Önceki 559 hazır SQL ve 59 inceleme kimliği tek tek izlenir.
- Sırlar ve gerçek SQL yalnız özel yerel arşivde. Jenkins/SMTP/push yok.

## Review Focus

- VALID kaydın eski/farklı tanıma ait olması, toplama sırasında değişim.
- Dinamik SQL, uzak bağ, invoker rights, koşullu derleme ve gizli çağrılar.
- Synonym gölgeleme, yanlış owner ve rol yetkisini doğrudan yetki sanma.
- Eksik/farklı hedef kolon veya paket imzası, bağlı inceleme işlemini atlama.
- Önceki dosya gözlemini güncel canlı metadata diye sunma veya eski SQL'i değiştirme.

## Task 1: Salt Okunur Kanıt ve Kök Neden

- [x] 59 kaydı ve 15 envanter incelemesini sabitle. Önceki dosyaları değiştirme.
- [x] Kaynak/hedefte yalnız ilgili birim ve referans metadata'sını oku. Kimlik, hata, süre, hash kaydet. DENEME kapsam dışında.
- [x] Kaynak/target kanıtları eşleşmiyorsa yalnız etkilenen birimi tut. Doğrudan yetki, synonym ve imza koşullarını belirle.

## Task 2: Kapalı Derleyici Kanıtı

- [x] Yeni sentetik RED testleri: gerçek statik READY/SQL ve INVALID, hash/dependency drift, dynamic/remote/invoker/privilege/shape olumsuzları.
- [x] oracle/routine_metadata.py kanıt okuyucusu ve parsing/planning entegrasyonu. Mevcut exporter yolunu gevşetme.
- [x] Metadata hatalarını UNKNOWN olarak koru. Bağımlılık grafı ve sırayı koru.
- [x] İlgili testler, ardından tüm offline testler PASS.

## Task 3: Gerçek Kayıtlarda Yeniden Planlama ve Teslim

- [x] 59/59 işlemi önce/sonra eşleştir, yeni engelleri açıkça belirt.
- [x] Eski 559 SQL gövdesi, kaynak/target ham DDL ve 1743 fark korunur. Aynı kanıt iki hedefte aynı sonuç verir. Dosya yolu için yeni ek kanıt kökeni açıkça etiketlenir.
- [x] Yeni özel yerel UI koşusu, manifest/bundle/SQL doğrulaması.
- [x] Tek bağımsız son inceleme, önemli bulgular RED -> GREEN. Belgeler ve yz devir güncellenir.

## Çalışma Kaydı

Başlangıç: baseline 13a6dbe5c2aa4b03be417f10763a02a2. Pre-flight: metadata kanıt biçimi -> parser kapısı -> graf referansları -> immutable arşiv ortak arayüzdür. Derleyici kanıtı yalnız doğrulanmış aynı gövde ve hedef uyumu ile geçerlidir. Aktif tarihsel görev yeniden yazılmaz.

Kapanış: yerel UI koşusu c0f45c8ca18848988968bafd90943e5c. 59/59 izleme,
559 eski SQL gövdesi ve iki hedef eşdeğerliği `verification.json` içinde PASS.
Bağımsız incelemenin bağlantı gözlemi, hedef kök sapması ve etkin çağrı imzası
bulguları negatif testlerle RED -> GREEN kapatıldı. 1209 birim testi PASS.
Otomatik yerel UI metadata toplama entegrasyonu sonraki iş olarak ayrıldı.
