🛰️ RESQ - Afet Otonom Asistanı Kriz Merkezi Paneli
RESQ, afet anlarında saha verilerini, otonom araç (İHA/İDRONE) lokasyonlarını ve vatandaşlardan gelen ihbarları tek bir merkezden yönetmeyi amaçlayan profesyonel bir kriz yönetim panelinin önyüz (frontend) projesidir.

Bu proje, otonom sürüş ve afet yönetimi ekosisteminin görsel yüzü olarak tasarlanmıştır.

✨ Öne Çıkan Özellikler
📍 Gerçek Zamanlı Harita Görünümü: Saha robotları (SDR), İHA'lar ve mobil komuta merkezlerinin konumlarını arayüz üzerinden canlı takip edebilme.

🚨 Doğrulanmamış İhbar Yönetimi: Vatandaşlardan gelen verileri listeleme, doğrulama veya reddetme arayüzleri.

📊 Dinamik İstatistik Paneli: Aktif ihbar sayılarını ve ekip dağılımlarını anlık gösteren modern UI.

🎮 Operasyonel Kontrol: "Sürüyü Başlat" gibi otonom görevleri tek tıkla tetikleyen arayüz bileşenleri.

🌙 Modern Karanlık Tema: Kriz anlarında göz yormayan, yüksek kontrastlı Tailwind tabanlı profesyonel tasarım.

🛠️ Kullanılan Teknolojiler
React: Kullanıcı arayüzü inşası ve bileşen (component) mimarisi.

Vite: Yeni nesil, ultra hızlı frontend geliştirme ve derleme aracı.

Tailwind CSS: Utility-first yaklaşımıyla hızlı ve duyarlı (responsive) tasarım.

Lucide React: Kriz paneli konseptine uygun, minimalist ikon seti.

🚀 Kurulum ve Çalıştırma
Projeyi yerel bilgisayarınızda çalıştırmak için bilgisayarınızda Node.js kurulu olmalıdır. Ardından aşağıdaki adımları izleyin:
# Proje klasörüne gidin
cd kriz-paneli

# Gerekli kütüphaneleri (bağımlılıkları) kurun
npm install

# Geliştirici sunucusunu başlatın
npm run dev
Proje varsayılan olarak http://localhost:5173 adresinde çalışacaktır.
🔗 Backend Bağlantısı Hakkında Not
Bu frontend projesi, gerçek verileri çekmek ve aksiyonları (ihbar doğrulama, sürü başlatma vb.) gerçekleştirmek için ayrı bir FastAPI backend servisi ile haberleşecek şekilde tasarlanmıştır. Tam sistem testi için ilgili backend servisinin de yerel ortamda (http://localhost:8000) çalışır durumda olması gerekmektedir.

📸 Ekran Görüntüleri
