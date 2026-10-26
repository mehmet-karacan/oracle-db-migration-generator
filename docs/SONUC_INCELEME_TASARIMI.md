# Nesne odaklı karşılaştırma tasarımı

25 Ekim 2026 kullanıcı onayı: nesne → fark özeti → gruplanmış ayrıntı → SQL.
Mevcut React/shadcn ve Python motoru korunur. Ayrı tasarım onayı gerekmez.

Sol liste hedef/tür/ad/fark türü filtrelerini sunar. Fark durumu ve DDL kararı
ayrı etiketlenir. Filtreler sunucuda sayfalama öncesi uygulanır, eski yanıtlar
ve seçim diğer hedef/projeye taşınmaz. Kaydırarak25 kayıt ekleme korunur.

Sağ başlık nesne kimliğini, kaynak/hedef bağlantı ve şema bağlamını, tüm nesne
kayıtlarından hesaplanan yapısal özeti gösterir. Kolon ve kısıtlar JSON pointer
kimliğiyle gruplanır, isimler tekrarlı satır olarak sunulmaz. Gruplar tamdır,
sayfa sınırında bölünmez. Varlık yalnız kanıtlı presence/exists ile özetlenir.
Kısmi/UNKNOWN bilgiden tam eşitlik veya nesne yokluğu çıkarılmaz. İşlemler
change_ids ile gruba bağlanır, SQL düğmesi gerekçe ile aynı alanda kalır.

Yerel özgün DDL karşılaştırması özel run source/observation snapshot'ından
nesne kimliği, safe_path, SHA256 ve varsa byte span ile okunur. Yalnız seçili
nesne, seçili target ve proje yetkisi kullanılır. UTF8 özgün metin değiştirilmez,
no-store yanıt verilir. Jenkins ham SQL'i bu endpoint'ten yerelleştirilmez,
arşiv erişimi sınırı görünür. Kaydı olmayan tanım uydurulmaz. Satır farkı
yalnız sunumdur, motor/SQL kararlarını değiştirmez. Büyük içerik sınırlı DOM
ile gösterilir, quote/literal ve kaynak biçimi korunur.

Kabul: 22 alan/2 FK örneği iki tam grup ve doğru özet verir. Varlık/UNKNOWN/
NULL ayrıdır. Filtre/tam sayılar, 1→N hedef ve proje izolasyonu, stale yanıt,
uzun/escaped kimlik, arşiv/yerel SQL, kaynak biçimi ve boş/hatalı durumlar
regression testindedir. TR/EN, iki tema, geniş ve dar ekran tarayıcıda görülür.
5 saniyede nesne/hedef/özetin anlaşılabilirliği görünür hiyerarşiyle incelenir,
gerçek kullanıcı kullanılabilirlik ölçümü yapılmış gibi raporlanmaz.
