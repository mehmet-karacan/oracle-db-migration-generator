# Şema Karşılaştırma Ortam Adları Ve Tür İkonları

Author: Mehmet KARACAN
Date: 2026-11-07

Kaynak TTBP - UAT, hedef TTBP - PROD olarak gösterilir. Bu adlar
kullanıcının seçili rapor için verdiği sunum bilgisidir. Bağlantılar, şema
kimlikleri ve eski koşu arşivi değiştirilmez. Sunum bağlamı run_id ve kaynak
commit'iyle bağlıdır. Başka bir koşuya veya projeye uygulanamaz.

Tarama ve DDL toplam kutularına ikon eklenir. Tür satırları tablo, kolon,
görünüm, paket ve diğer türlere uygun Lucide ikonlarını kullanır. Küçük tür
ikonları aynı nötr tondadır. Mevcut başlık ve özet renkleri korunur.

- [x] Ortam bağlamı ve tablo, kolon gibi tür ikonları için kırmızı testleri çalıştır.
- [x] Yalnız sunum alanlarına ortam adlarını bağla ve ikon eşlemesini ekle.
- [x] Toplam kutuları ve tür satırlarını mevcut şablonlarda güncelle.
- [x] Offline testleri, görünür içerik kontrolünü ve arşiv hash kontrolünü yap.
- [x] Ayrı yerel önizleme üret, görsel kontrol et ve devir kayıtlarını güncelle.

Yeni Oracle, karşılaştırma, Jenkins veya mail gönderimi yok. HTML boyut
sınırı ve tam açıklamalar korunur. Önceki file:// tarayıcı engeli aşılmaz.

## Sonuç

build_run_view isteğe bağlı display_context alır. Bu bağlam yalnız kendi
run_id, kaynak commit'i ve hedef kimlikleriyle kullanılabilir. Ortam adları
sunum alanlarında uygulanır. Bağlam verilmeyen diğer projelerde önceki
görünüm korunur. Kalıcı bağlantı adı veya şema eşlemesi değişmez.

Önizleme .local/schema-type-icons-preview-20261107/report-email.preview.html.
Sunum bağlamı aynı dizindeki report-display-context.json dosyasındadır.
Toplam kutularında ve tür satırlarında yeni ikonlar var. Küçük tür ikonları
48 x 48, özet ikonları 96 x 96 PNG olarak saklanır.

İlgili 49 test PASS. Tam test 1.333 PASS, 282,36 saniye. Komut PYTHONPATH=src
ile python -m pytest -q --tb=short --junitxml=.local/schema-type-icons-tests-final.xml.
Tek uyarı mevcut Starlette/AnyIO kullanım dışı kalma bildirimidir.
git diff --check geçti. HTML 132.341 byte ve boyut sınırı içinde.
36.736 kaynak arşiv dosyası aynı. Yalnız istenen ortam etiketleri değişti,
rakamlar ve diğer metinler korundu. Yerel HTML render ile görsel kontrol
yapıldı. Tarayıcı ve gerçek mail istemcisi kontrolü NOT_RUN.

## Tür Renkleri Revizyonu

Kullanıcı küçük tür ikonlarının renkli ve karanlık zeminde görünür olmasını
istedi. 19 tür simgesine renk grupları ve açık rozet zemini uygulandı.
report_type_icon artık semantic PNG kullanır. Kaynak yolları ve ikon
kimlikleri değişmedi. Tablo mavi, kolon turkuaz, görünüm mor, paket indigo,
fonksiyon ve prosedür petrol yeşili, tetikleyici turuncudur.

Kontrast testi önce arka plan eksikliğiyle kırmızı oldu. Yeni varlıklarla
çizgi/rozet kontrastı en az 4.75, rozet/koyu zemin kontrastı en az 7 olarak
doğrulandı. İlgili ikon, boyut ve rapor grubu 31 PASS. Renk revizyonunda
tam test paketi tekrar çalıştırılmadı. Önceki tam sonuç 1.333 PASS olarak
korunur. git diff --check geçti.

Yeni önizleme .local/color-type-icons-preview-20261107/report-email.preview.html.
138.034 byte. icons-light-dark.png gerçek PNG'lerin açık ve koyu zemin
kontrolüdür. TTBP - UAT ve TTBP - PROD etiketleri korundu. Korunan 36.736
arşiv dosyası aynı. Yeni karşılaştırma, bağlantı veya mail gönderimi yok.
