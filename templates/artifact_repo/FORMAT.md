# Artifact Formatı

Kanonik JSON sürümleri: plan/1.0, bundle-manifest/1.0. Run observation kaydı Jenkins tarafında run/1.0 olarak tutulur.

`plans/<profile>/<target>/<plan-id>/`: immutable payload. `catalog.json`: bilinen planların target/profile bazlı dizini. `latest/<profile>/<target>.json`: son geçerli plan pointer'ı. Payload'ın bundle-manifest.json dosyası listedeki dosyaların SHA-256 ve byte sayısını taşır, kendisini hash'lemez.

Aynı kaynak SHA, target canonical snapshot, scope/policy ve generator/parser/rule sürümünde aynı payload yeniden commit edilmez. Planı açıklarken timestamp'i uygulama tarihi sanma. Kanonik before=actual target, after=desired source.

Target migration.sql yalnız tam hazır plan içindir. partial-ready.sql kısmi hazır bağımsız işlemlerdir, review/ otomatik uygulama dışında kalır. Hedefte hiçbir fark yoksa SQL dosyası bulunmayabilir, NO_CHANGE yalnız coverage tamlığıyla birlikte anlamlıdır.
