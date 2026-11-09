# Şema Karşılaştırma Tema İkonları

Author: Mehmet KARACAN
Date: 2026-11-07

Kullanıcı sunum ikonlarının raporda fazla ayrıntılı kaldığını belirtti.
Son tercih tema, başlık ve renk anlamlarıyla uyumlu tek bir ikon ailesidir.
Arayüzde zaten kurulu Lucide React 1.61.0 kaynakları kullanılır. Sunum
ikonları bu rapor görünümünden çıkarılır. Eski önizleme ve kaynaklar özel
yerel arşivde korunur.

## Eşleme

| Alan | Lucide | Tema Rengi |
| --- | --- | --- |
| Hedef Ortam | database | Oracle mavisi |
| Bulunan Fark | file-diff | Sakin amber |
| Üretilen DDL | file-code-corner | Petrol yeşili |
| Taranan Nesne | scan-search | Bilgi mavisi |
| İnceleme | clipboard-list | Sakin amber |
| DDL Dosyası Eksik | file-exclamation-point | Hata kırmızısı |
| Süre | clock | Nötr gri |
| Değişiklik Detayları | list-tree | Bilgi mavisi |
| Kaynak ve İzlenebilirlik | workflow | Nötr gri |

## Uygulama

- [x] Dekoratif ve bağımsız görsel sözleşmesini yeni ikon eşlemeleriyle sına.
- [x] Kurulu Lucide paketinden kaynakları al, lisansı ve hash'leri kaydet.
- [x] 24 birimlik sade çizgileri hafif zeminli PNG'lere dönüştür.
- [x] Mail ikonlarını başlık satırına taşı, sayıları ayrı ve aynı hizada tut.
- [x] Bölüm ikonlarını aynı aileye geçir. Mobilde iki kolon kullan.
- [x] Son koşunun kayıtlarından ayrı önizleme oluştur. Metinleri ve sayıları koru.
- [x] İlgili ve tam offline testleri çalıştır, yerel HTML render ile görünümü kontrol et.
- [x] Devir kayıtlarını güncelle ve önizleme bağlantısını paylaş.

Yeni karşılaştırma, Oracle, Jenkins ve mail gönderimi yoktur. Kaynak koşu
arşivi değiştirilmez. Mailde PNG gömülür, webde paket içi varlık kullanılır.
200 KiB HTML sınırı ve açıklamaların tamlığı korunur. Önceki Browser Use
file:// engeli devam eder. Otomatik açma başka araçla zorlanmaz.

## Doğrulama

İlgili rapor grubu 52 PASS. Tam test 1.328 PASS, 222,82 saniye.
Komut PYTHONPATH=src ile python -m pytest -q --tb=short
--junitxml=.local/lucide-report-icons-tests-final.xml. Son boşluk ve hizalama
düzeltmesinden sonra ilgili 18 test de geçti. Tek uyarı mevcut Starlette/AnyIO
kullanım dışı kalma bildirimidir. git diff --check geçti.

Önizleme .local/lucide-icons-preview-20261107/report-email.preview.html.
Mail 88.821 byte. İkon yerleşimi nedeniyle kart içinde önce başlık sonra
sayı görünür. Her kartın metinleri ve sayıları aynı. Kartlar dışındaki
görünür metin de aynı. Kaynak koşunun 36.736 dosyası hash kontrolünde
değişmedi. Yeni karşılaştırma veya mail gönderilmedi. Tarayıcı yerine yerel
HTML renderer ile görsel kontrol yapıldı. Gerçek mail istemcisi ve tarayıcı
mobil görünüm kontrolü NOT_RUN kalır.
