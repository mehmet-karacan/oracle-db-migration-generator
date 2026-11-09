# Şema Karşılaştırma Kurumsal Rapor İkonları

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

Author: Mehmet KARACAN
Date: 2026-11-07

**Goal:** Kullanıcının seçtiği İnnova kurumsal sunum ikonlarını mevcut rapora eklemek ve kayıtlı sonuçlarla yerel önizlemeyi açmak.

**Architecture:** Kurumsal sunum skill'indeki reference.pptx dosyasının 53–59 sayfalarından anlamı uygun özgün SVG'ler alınır. Kaynak hash ve sayfa bilgisi kaydedilir. Mailde saydam PNG türevleri gömülür. Web raporu kendi paketindeki PNG dosyalarını kullanır. Sayılar, DDL ve karşılaştırma metadata kayıtları değişmez.

**Tech Stack:** Mevcut Python, Jinja2 ve statik PNG görselleri. Yeni runtime bağımlılığı yoktur.

**Spec:** Kullanıcı ikon uygulamasını onayladı, ardından kurumsal sunum skill'indeki ikonları tercih etti. Bu seçim önceki Font Awesome seçiminin yerini alır. Yeni karşılaştırma ve mail gönderimi yasak. Kurumsal vurgu #ED3340 olur. Mevcut metinler korunur. Şablonda anlamı uygun ikon yoksa nesne türüne ilgisiz ikon eklenmez.

## Global Constraints

- Yeni Oracle, Git kaynak okuması, karşılaştırma, Jenkins veya SMTP çalıştırması yoktur.
- Eski koşu arşivi değişmez. Önizleme ayrı .local dizininde hazırlanır.
- İkonlar sayıları veya metinleri tekrar etmez. Dekoratif görsellerin alt metni boştur.
- İkon için dış URL, font veya JavaScript yüklenmez. HTML boyut sınırı korunur.
- Lisans ve üçüncü taraf sahipliği korunur. SVG asılları değiştirilmez.

## Review Focus

- Mail görselleri internet olmadan çözülebilmeli.
- Kurumsal kaynaktan alınan özgün SVG hash'leri ve PNG boyutları doğrulanmalı.
- Nesne türünün anlamına uymayan ikon eklenmemeli.
- Mevcut görünür metin, sayılar, süre, hedef ve SQL dosyaları aynı kalmalı.
- Masaüstü ve dar görünümde ikonlar yazıları veya sayıları taşırmamalı.

## Task 1 Rapor İkonları Ve Önizleme

- [x] Kırmızı testte raporun gömülü, dekoratif kurumsal ikonlarını arat.
- [x] reporting/icons.py ve kaynak bilgili statik varlıkları ekle.
- [x] Mail, ortak dağılım başlıkları ve web özetine aynı ikon eşlemesini bağla.
- [x] İlgili rapor testlerini ve tam test paketini çalıştır.
- [x] Son koşuyu yeniden çalıştırmadan kayıtlı JSON'lardan ayrı önizleme üret.
- [x] Önceki görünür metinleri ve arşivin dosya hash'lerini karşılaştır.
- [x] Önizlemeyi çevrimdışı HTML render ile görsel olarak kontrol et.
- [ ] Tarayıcıda otomatik açılış dosya protokolü güvenlik ilkesi nedeniyle engellendi. Kullanıcı dosya bağlantısından açabilir.

## Karar Kaydı

Kullanıcının son tercihi kurumsal sunum ikonlarıdır. Font Awesome için bu
turda hazırlanan kullanılmamış varlıklar kaldırıldı. SVG asılları korunur,
yalnız PNG türevleri renklendirilir. İkonlar özet, süre ve bölüm başlıklarında
kullanılır. Nesne türleri kendi açık adlarıyla gösterilir.

## Kontrol Kaydı

Sekiz özgün SVG ve 16 PNG türevi var. Kaynak PPTX hash'i
443b6fc0d2f3fd8f5b468fce4cf73edc71f363517505163b51f1e3213f12edf6.
Kaynak sahipliği ve dosyaları korundu. Önizleme
.local/corporate-icons-preview-20261107/report-email.preview.html dosyasıdır.
Görünür metinler aynı ve eski arşivdeki 36.736 dosya değişmedi.

Taze kapsam incelemesinde mobil karttaki nowrap taşması bulundu. Sabit
nowrap kaldırıldı ve dar ekranda ikon sayıdan ayrı satıra alınır. Tam testte
uzun açıklamalı ayrıntı sayfasının 200 KiB sınırına takıldığı da görüldü.
Web ikonları paket içi dosyalara bağlandı. Açıklama kırpılmadan mevcut boyut
testi ve ilgili rapor grubu geçti. Mail gömülü görselleri kullanmayı sürdürür.
Bu grubun son sonucu 51 PASS. Nihai tam test 1.327 PASS, 202,81 saniye.
Komut PYTHONPATH=src ile python -m pytest -q --tb=short
--junitxml=.local/corporate-report-icons-tests-final.xml. Tek uyarı mevcut
Starlette/AnyIO kullanım dışı kalma bildirimidir. git diff --check geçti.

Yeni karşılaştırma, Oracle, Jenkins, SMTP, commit veya push yoktur.
Browser Use file:// protokolüne izin vermedi. Protokol engelini aşmak için
başka tarayıcı yüzeyi veya ara sunucu kullanılmadı. Görsel kontrol tarayıcı
kullanmayan yerel HTML render ile yapıldı. Gerçek mail istemcisi kontrolü
bu görevde NOT_RUN kalır.
