# Nesne bazlı sonuç ekranı uygulama planı

> For agentic workers: superpowers:executing-plans ile bu oturumda uygula, sonunda tek bağımsız inceleme.

**Goal:** Kendi shadcn bileşenlerimizle tablo/nesne seçimi, kaydedilmiş kaynak–hedef alan farkları ve bağlı işlem/DDL gerekçeleri.

**Architecture:** Mevcut kanonik planın sunum izdüşümü, motor/SQL kararları değişmez. Kaynak=after, hedef=before. Yapısal metadata özel control state'e aktarılabilir, gerçek SQL gövdeleri Jenkins'te kalır. Eski arşivlerdeki fark kayıtları kullanılır, kaydedilmemiş eşit alanlar uydurulmaz. Mevcut #55 sonucu yeni Oracle/Jenkins koşusu olmadan gösterilir.

**Tech Stack:** Mevcut FastAPI/SQLite, React/TypeScript, shadcn Table/Sheet/Tabs/Badge/Input/Button. Yeni framework/servis yok.

**Spec:** 24 Ekim kullanıcı isteği: tablo seçildiğinde kaynak ve hedef farkları, Schema Compare Platform'u kopyalamadan kendi komponentlerimiz/yöntemlerimiz. Önceki 1→N, UNKNOWN, ortak proje, Jenkins-only SQL kuralları sürer.

## Global constraints

- Diğer repo salt okunur. Oracle/SMTP/Jenkins job değişikliği ve push yapılmaz.
- Nesne/alan farkları kanonik plan kimliğiyle eşleşir, UI yeniden karşılaştırma yapmaz.
- UNKNOWN, ABSENT, KNOWN null ve NOT_APPLICABLE ayrı gösterilir.
- Yalnız kaydedilmiş farklar listelenir, tüm snapshot veya eşit alanlar varmış gibi gösterilmez.
- Kaynak/target/plan/run eşleşmesi import sırasında denetlenir, import idempotent ve değişmezdir.
- SQL tanım gövdeleri metadata izdüşümüne alınmaz, ilgili SQL yetkili Jenkins bağlantısından açılır.

## Review focus

Kaynak/hedef yönü, ilişkili operation/change ID'ler, bilinmeyen veya kırpılmış değerlerin eşit/null görünmemesi, hedef/proje izolasyonu, SQL path traversal, stale UI yanıtı, farklı planı aynı build'e bağlama, eksik sonuçların sıfır fark diye sunulmaması.

### Task 1: Güvenilir sonuç metadata'sı ve API

- [x] RED: source/target yönü, üç durum/null, nesne gruplama/operation ilişkisi, sayfalama, yanlış plan/target reddi, gövde dışlama.
- [x] GREEN: control/results.py normalize/validate/import/read, SQLite immutable comparison view, /results/objects ve /results/objects/{key} API.
- [x] Local CLI import ve tarayıcıdan yalnız metadata çıkaran export, #55 nesne verisi bağlantısı.

### Task 2: Kendi sonuç bileşenlerimiz

- [x] RED: tablo seçimi, kolon kaynak/hedef değerleri, bilinmiyor/NULL ayrımı, hedef değişiminde geciken yanıt reddi.
- [x] GREEN: ObjectResults, ObjectDifferenceSheet, result labels/types, mevcut yerel/Jenkins RunDetail bağlantısı.
- [x] Filtre/nesne ve ayrıntı sayfalaması, işlem gerekçesi ve SQL linkleri, masaüstü taşma kontrolü. 390px tarayıcı override uygulanmadığından mobil kabul NOT_RUN, geçici ayar resetlendi.

### Task 3: Teslim

- [x] #55 gerçek kayıtlarıyla tarayıcı kontrolü/screenshot, yeni Oracle bağlantısı/SQL indirme yok.
- [x] İlgili testler, frontend build/lint, tek inceleme ve gerekli RED→GREEN düzeltme.
- [x] yz durum/devir ve kurulum/sonuç sözleşmesi belgesi, eksik canlı/ortak dağıtım kapıları ayrı.
