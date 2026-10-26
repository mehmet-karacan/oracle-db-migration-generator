# Proje seçimi, ortak kullanım ve canlı koşu uygulama planı

> For agentic workers: superpowers:executing-plans ile aynı oturumda uygula.

**Goal:** Ortak kullanıcıyla proje bazlı UI, mevcut bağlantıları kaydet, UI'den canlı Git→PROD/TTBP karşılaştırmasını başlat, gerçek süreyi ve yalnız izinli alıcıya maili doğrula.

**Architecture:** Mevcut motor korunur. SQLite kayıtlarında project_id, eski kayıtlar varsayılan SKY projesine aittir. Uygulamaya erişenler ortak çalışma yetkisini kullanır, UI kullanıcı/rol rozeti göstermez. Normal proxy kimlik doğrulaması korunur. Proje seçimi bağlantı/profil/geçmişi filtreler, çapraz proje çalışma reddedilir.

**Tech Stack:** Mevcut React/shadcn/FastAPI/SQLite, yeni framework/model yok.

**Spec:** 24 Ekim kullanıcı talimatı: mevcut bağlantılar, canlı UI karşılaştırması, toplam süre, mail yalnız mkaracan@innova.com.tr, tek ortak kullanıcı, SKY yerine proje seçimi, model bilgisi gösterilmez.

## Global Constraints

- Oracle daima READ ONLY, mevcut karşılaştırma/SQL kuralları ve günlük TTBP08:00 korunur.
- Bağlantılar .local içinden okunur, UI vault'a şifreli kaydedilir, sırlar log/Git/argv'ye yazılmaz.
- Mevcut branch/diff korunur, commit/push yok.
- Kullanıcı Jenkins servis hesabının bulunmadığını bildirdi. Bu koşu UI'nin açıkça gösterdiği Jenkins oturumu devriyle başlatılır. Tamamlanan Jenkins run.json ve tarayıcı kanıtı doğrulanıp UI'ye bağlanır, otomatik servis hesabı entegrasyonu yapılmış gibi sunulmaz.
- Gerçek SQL Jenkins arşivinde kalır, UI'de rapor bağlantısı ve sanitised çalışma metadata'sı tutulur. Onaylı Jenkins profilinden farklı seçim sessizce çalıştırılmaz.

## Review Focus

- Proje değiştirme önceki projenin bağlantı/profil/çalışmasını göstermemeli, source-target çapraz proje seçimi reddedilmeli.
- Ortak kullanım anonim ağ erişimi veya parola görüntüleme hakkı anlamına gelmez, normal proxy doğrulaması sürer.
- Sadece arayüz etiketi değiştirilmez: yetkili bütün oturumlar aynı çalışma kayıtlarını görüp başlatabilmeli.
- Jenkins devri gerçek queued/running sanılmamalı, yalnız tamamlanan, yeni timestamp'li, eşleşen iş sonucu bağlanmalı.
- Süre gerçek başlangıç/bitişten, eksik/başarısız canlı koşu hızlanma başarısı değildir.

### Task1: Proje ve ortak çalışma sözleşmesi
Files: control/models.py, store.py, api.py, tests/unit/test_control_projects.py.
- [x] RED: default SKY/legacy scope, project isolation, cross-project rejection, shared authenticated viewer can start/read, anonymous still denied.
- [x] GREEN: ProjectInput/CRUD, connection/profile/run project binding, shared workspace role, immutable project membership.
- [x] Focused control tests pass.

### Task2: Proje seçimi ve sade UI
Files: web/src/{App,ComparisonForm,Connections,RunDetail,ProjectSwitcher,api}, tests.
- [x] RED: switching project requests scoped data, role/user/model copy absent, new project persisted.
- [x] GREEN: top project selector/create dialog, reset selected profile/details on switch, scoped forms, common workspace copy.
- [x] Frontend tests/build/browser pass.

### Task3: Bağlantı importu ve Jenkins oturum devri
Files: control/jenkins_browser.py, api.py, tools/ui_import_connections.py, ui_link_jenkins_run.py, tests.
- [x] RED: approved fingerprint only, handoff status does not start local worker, closed metadata validation rejects stale/wrong target/source, credentials not public.
- [x] GREEN: server-managed binding, visible Jenkins launch link, validated completed run metadata with report URL and timing, local import uses existing credential resolver.
- [x] Import existing SKY Git and Oracle connection metadata from verified local/Jenkins config, no secret output.

### Task4: Canlı koşu ve teslim
- [x] UI üzerinden onaylı SKY Git→PROD/TTBP profili, mevcut Jenkins oturumunda başlat.
- [x] Gerçek başlangıç/bitiş/toplam/kaynak hazırlama süresi, source/target freshness, yalnız mkaracan@innova.com.tr mail kanıtı.
- [x] Full tests/contracts/build, tek bağımsız inceleme ve gerekli düzeltmeler, yz durum/devir güncelle.
