# Afet Yönetimi ve Kriz İletişiminde Bilgi Kirliliğinin Yapay Zeka ve Mekansal Algoritmalarla Tespiti

> **Not:** Bu dokümantasyon, literatür taraması ve algoritmik analiz süreçleri kapsamında **Gemini Deep Research** kullanılarak oluşturulmuştur.

## 1. Giriş
Doğal afetler, toplumların fiziksel, ekonomik ve psikolojik altyapılarını derinden sarsan, ani ve yıkıcı olaylardır. Özellikle deprem, sel, kasırga ve orman yangını gibi büyük çaplı afetlerin hemen sonrasında ortaya çıkan ilk 72 saat, arama-kurtarma operasyonlarının başarısı ve can kayıplarının en aza indirilmesi açısından kritik bir öneme sahiptir. Bu zaman diliminde kriz yönetim merkezlerinin en çok ihtiyaç duyduğu unsur, sahadan gelen doğru, kesintisiz ve eyleme dönüştürülebilir veridir. 

Vatandaşların akıllı telefonlar ve sosyal ağlar üzerinden anlık durum bildirimleri yapabilmesi kitle kaynaklı (crowdsourced) bir nitelik kazanmıştır. Ancak bu durum, "bilgi kirliliği" (information pollution) ve dezenformasyon adı verilen devasa bir risk ekosistemini de beraberinde getirmiştir. 

Büyük veri analitiği, yapay zeka (AI) tabanlı anomali tespiti ve mekansal (spatial) kümeleme algoritmalarının afet yönetim sistemlerinin çekirdeğine entegre edilmesi zorunlu bir mühendislik gereksinimi haline gelmiştir. Sistemin temel amacı, yalnızca bir harita üzerinde veri listelemek değil, yetkililere rafine, doğrulanmış ve eyleme geçirilebilir "görev paketleri" sunmaktır.

## 2. Afet Krizlerinde Dezenformasyon ve Bilgi Kirliliği Ekolojisi
Afetler sırasında bilgi kirliliği; "misenformasyon" (yanlış anlama), "dezenformasyon" (kasıtlı üretilen) ve "malenformasyon" (bağlamdan koparılan) olmak üzere farklı formlarda tezahür eder. Sosyal ağ algoritmaları, içeriklerin doğruluğundan ziyade kullanıcı etkileşimini maksimize edecek şekilde optimize edilmiştir.

| Dezenformasyon Türü | Tanım ve Örnekler | Operasyonel Sonuçları |
| :--- | :--- | :--- |
| **Sahte İhbarlar ve Adresler** | Hiç var olmayan enkaz veya yaralı bildirimleri; alakasız koordinatlara acil durum çağrıları. | Arama-kurtarma kaynaklarının israfı, kritik vakalara müdahalenin gecikmesi. |
| **Komplo Teorileri** | Afetin doğaüstü veya düşman teknolojileri tarafından yapay olarak yaratıldığı iddiaları (Örn: HAARP). | Otoriteye güvensizlik, tahliye süreçlerinin aksaması. |
| **Dolandırıcılık (Scam)** | Afetzedelere yardım kisvesi altında sahte IBAN paylaşımı; sahte yıkım görselleri. | Toplumsal dayanışmanın suistimali, finansal kaynakların engellenmesi. |
| **Bağlamdan Koparılmış Bilgi** | Eski afetlere ait fotoğraf veya videoların yeniymiş gibi paylaşılması. | Hasarın boyutunun yanlış algılanması, yanlış kaynak tahsisi planlaması. |

## 3. Kitle Kaynaklı Verilerin (Crowdsourcing) Doğrulanması ve Resmi API Entegrasyonu
Kitle kaynaklı sistemler, dağıtık konumdaki sıradan vatandaşların anlık gözlemlerini dijital ortama aktarması esasına dayanır. Ancak, eğitim almamış kitlelerden sağlanan veriler doğası gereği yüksek oranda "gürültülü"dür (noisy).

### Resmi Veri Akışları (API) ile Çapraz Kontrol (Cross-Check) Algoritmaları
Sisteme dış dünyadan alınan güvenilir veri kaynaklarının (AFAD, Kandilli vb.) Uygulama Geliştirme Arayüzleri (API) aracılığıyla gerçek zamanlı olarak çekilmesi sarsılmaz bir bariyer oluşturur. Kullanıcıdan gelen ihbar JSON verisi, son 24-48 saat içindeki resmi deprem merkez üsleri ve etki yarıçaplarıyla (buffer zone) coğrafi olarak karşılaştırılır. Eğer ihbar edilen konum sismik alanın dışındaysa, karar motoru talebi geçersiz sayar (`is_verified = False`).

## 4. Mekansal Kümeleme ve Anomali Tespiti ile Sahte İhbarların Filtrelenmesi
Kriz yönetim ekranında binlerce bağımsız noktanın görüntülenmesi devasa bir bilişsel yük yaratır. Koordinasyonun sağlanabilmesi için birbirine yakın ihbarların tek bir "görev paketine" dönüştürülmesi şarttır.

### K-Means Algoritması ve Sınırlılıkları
* **Küme Sayısının (K) Önceden Bilinmesi:** Deprem anında kaç küme oluşacağını tahmin etmek imkansızdır.
* **Küresel Şekil Bağımlılığı:** K-Means dairesel sınırlar çizer; fay hattı boyunca uzanan çizgisel hasarları kümeleyemez.
* **Aykırı Değerlere Hassasiyet:** Sahte bir ihbarı (outlier) zorla bir kümeye dahil ederek rotayı kaydırır.

### DBSCAN Algoritmasının Üstünlüğü ve Gürültü Filtreleme
Yoğunluk tabanlı DBSCAN, iki hiper-parametre ile çalışır: Epsilon ($\epsilon$) ve MinPts. Eğer bir bölgedeki ihbar sayısı MinPts eşiğine ulaşırsa kümeyi oluşturur. 

**Anomali Tespiti:** Sabotajcı botların yoğunluk bölgesinden uzak sahte ihbarları MinPts yoğunluğuna ulaşamayacağı için DBSCAN tarafından dışlanır ve `-1` etiketi ile **"Gürültü" (Noise)** olarak sınıflandırılır.

| Özellik / Algoritma Özeti | K-Means Kümeleme | DBSCAN Kümeleme (Önerilen) |
| :--- | :--- | :--- |
| **Küme Sayısı Belirleme** | Algoritma başlamadan manuel olarak girilmelidir. | Otonom olarak veri yoğunluğuna göre kendisi belirler. |
| **Desteklenen Geometri** | Sadece küresel (yuvarlak) bölgeler oluşturur. | Fay hattı gibi düzensiz, doğrusal, asimetrik şekillere uyum sağlar. |
| **Gürültü/Sahte Veri** | Her sahte veriyi zorla kümeye dahil eder. | Sahte/seyrek verileri matematiksel olarak dışlar. |

## 5. Siber Güvenlik Katmanı: Sybil Saldırıları ve Hız Sınırlandırma (Rate Limiting)
Bir Sybil saldırısı, tek bir kaynaktan binlerce sahte kimlikle sahte ihbar gönderilmesi şeklinde yaşanabilir. FastAPI altyapısına gömülen bir **Rate Limit** algoritması (örneğin Token Bucket), "1 IP adresinden 1 dakikada en fazla 3 talep gelebilir" kuralı ile siber saldırıları reddeder (HTTP 429).

## 6. Yüksek Erişilebilirlikli Sistem Altyapısı: PostGIS, WebSocket ve ACID
* **PostGIS İndeksleme (GiST):** Coğrafi mesafe sorguları (spatial queries), geleneksel tam tablo taraması yerine R-Tree mimarisiyle milisaniyeler içinde çözülür.
* **ACID ve Rollback:** Enerji kesintilerinde, yarım kalan bir yönlendirme işlemi veritabanında Transaction Rollback ile geri alınarak stok bozulmaları engellenir.
* **WebSocket:** Geleneksel HTTP istekleri (F5) yerine tam çift yönlü WebSocket altyapısı ile Kriz Ekranı anlık (real-time) güncellenir.
