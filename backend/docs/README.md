# 🌍 Afet Koordinasyon Ağı - Teknik Dokümantasyon Merkezi

> **🤖 Araştırma ve Geliştirme Notu:** > Bu klasörde yer alan teknik mimari, literatür taraması, matematiksel modellemeler ve algoritmik analizler **Gemini Deep Research** yapay zeka modeli kullanılarak sentezlenmiş ve oluşturulmuştur.

Afet Koordinasyon Ağı, kriz anlarında sahadan gelen kitle kaynaklı (crowdsourced) verileri yapay zeka ve mekansal algoritmalarla filtreleyen, otonom önceliklendirme yapan ve kısıtlı lojistik kaynakları en optimum şekilde sahaya sevk eden çok katmanlı bir karar destek sistemidir.

Bu klasör, sistemin arka planında çalışan algoritmik modellerin, matematiksel formüllerin ve siber güvenlik mimarilerinin detaylı teknik analizlerini içermektedir.

## 📚 Dokümantasyon İçeriği ve Modüller

Sistem mimarimiz birbiriyle entegre çalışan üç temel algoritmik motordan oluşmaktadır. İlgili modüllerin derinlemesine analizleri için aşağıdaki bağlantıları inceleyebilirsiniz:

### 1. [Bilgi Kirliliği Tespiti ve Mekansal Kümeleme (DBSCAN)](https://docs.google.com/document/d/1zHhF_6-0OCiZWdV9WGj8Y75FVM5v2kKnxjNXJhPzg7s/edit?usp=sharing)
Afet anında sosyal ağlardan ve ihbar kanallarından akan verilerdeki asılsız çağrıların ve manipülasyonların filtrelenmesi modülü.
* **Resmi API Çapraz Doğrulaması:** AFAD, Kandilli gibi sismik ağlarla gelen ihbarların lokasyon bazlı otonom teyidi.
* **Mekansal Anomali Tespiti:** K-Means yerine **DBSCAN** algoritması kullanılarak sahte/seyrek ihbarların "Gürültü" (Noise) olarak dışlanması ve organik hasar kümelerinin oluşturulması.
* **Siber Güvenlik Katmanı:** Sybil ve DDoS saldırılarına karşı IP/Oturum bazlı Rate Limiting ve anomali tespiti.
* **Gerçek Zamanlı Veri Akışı:** PostGIS uzamsal indeksleme (GiST) ve WebSocket üzerinden düşük gecikmeli veri senkronizasyonu.

### 2. [Otonom Önceliklendirme ve Triyaj Motoru](https://docs.google.com/document/d/1BdAMHpEGyv_WbslJ7ysQ6LxKDYFSQd_VBGNX3WtlsBE/edit?usp=sharing)
Doğrulanmış ihbarların, insan fizyolojisi ve zaman kritikliğine göre otonom olarak sıralanması modülü.
* **Triyaj Standartları:** START, ESI ve WFP 72-Saat değerlendirme kriterlerinin algoritmik adaptasyonu.
* **Çok Kriterli Karar Verme (AHP):** İhbar tiplerinin (Medikal, Arama Kurtarma, Gıda, Barınma vb.) AHP özvektörleri ile matematiksel ağırlıklarının (Base Score) hesaplanması.
* **Zaman Sönümleme (Time Decay) Algoritması:** Kuyruk açlığını (queue starvation) önlemek amacıyla, bekleme süresi artan düşük öncelikli taleplerin aciliyet puanını doğrusal/üstel fonksiyonlarla dinamik olarak artıran puanlama mimarisi.

### 3. [Lojistik Optimizasyon ve Araç Atama Algoritması](https://docs.google.com/document/d/1qFLlPwUhtDCFxuvn3nz2j-9tw1NU_eQV3GGwK1FxFuk/edit?usp=sharing)
Sistemde oluşan görev paketlerine en uygun müdahale araçlarının ve lojistik kaynakların yönlendirilmesi modülü.
* **MCDM ile Araç Seçimi:** AHP ve **TOPSIS** algoritmalarının hibrid kullanımıyla; talep aciliyeti, varış süresi ve kapasite tatmini kriterlerine göre en ideal aracın seçilmesi.
* **Stokastik ETA Hesabı:** Sismik yol hasar indeksleri ve araç süspansiyon hassasiyetleri (Ambulans vs. Paletli İş Makinesi) kullanılarak tahmini varış süresinin (ETA) dinamik düzeltme katsayılarıyla hesaplanması.
* **Kapasite ve Stok Yönetimi:** Sphere standartları ve TÜBER normlarına dayalı olarak kalori, su (WASH) ve barınma ihtiyaçlarının Çok Boyutlu Sırt Çantası (Knapsack) algoritması ile araçlara yüklenmesi.

---

## 🛠 Mimari Prensipler
* **ACID Uyumluluğu:** Lojistik atamalarda ağ kesintilerine karşı "Transaction Rollback" ile veri bütünlüğünün korunması.
* **Graceful Degradation:** Aşırı siber saldırı veya veri seli (tsunami) anlarında sistemin çökmesini engellemek için karmaşık analizleri askıya alarak temel listeleme moduna geçiş yapabilme yeteneği.
* **Yüksek Erişilebilirlik:** Ön yüz (Frontend) ile Kriz Merkezi Taktik Ekranının, sahadaki ekiplere sıfır bilişsel yük yaratacak şekilde WebSocket ile anlık haberleşmesi.
