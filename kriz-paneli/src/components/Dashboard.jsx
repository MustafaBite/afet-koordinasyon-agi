import 'leaflet/dist/leaflet.css';
import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

const kirmiziPin = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});


function MapController({ flyTo }) {
  const map = useMap();
  useEffect(() => {
    if (flyTo) map.flyTo(flyTo, 13, { duration: 1.5 });
  }, [flyTo, map]);
  return null;
}

const NEED_TYPE_LABELS = {
  arama_kurtarma: 'Arama Kurtarma',
  medikal: 'Medikal',
  yangin: 'Yangın',
  enkaz: 'Enkaz',
  su: 'Su',
  barinma: 'Barınma',
  gida: 'Gıda',
  is_makinesi: 'İş Makinesi',
  ulasim: 'Ulaşım',
};

export default function Dashboard() {
  const mapRef = useRef(null);
  
  // --- STATE BÖLÜMÜ ---
  const [flyTo, setFlyTo] = useState(null);
  const [ihbarlar, setIhbarlar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [secilenGorev, setSecilenGorev] = useState(null);

  // MOCK VERİ (Senin eklediğin)
  const [clusters, setClusters] = useState([
    {
      "cluster_id": "fake-uuid-1",
      "need_type": "yangin",
      "cluster_name": "Kadıköy Osmanağa Mahallesi - Yangın Söndürme Kümesi",
      "center_latitude": 40.990743,
      "center_longitude": 29.028482,
      "location": {
        "district": "Kadıköy",
        "neighborhood": "Osmanağa Mahallesi",
        "street": "Kuşdili Caddesi",
        "full_address": "Kuşdili Caddesi, Osmanağa Mahallesi, Kadıköy"
      },
      "request_count": 30,
      "total_persons_affected": 280,
      "priority_level": "Yüksek Aciliyet",
      "status": "active"
    }
  ]);

  const musaitAraclar = [
    { id: 1, isim: "1 Nolu AFAD Arama Kurtarma", mesafe: "2 km" },
    { id: 2, isim: "İtfaiye Ekibi - Merkez", mesafe: "4 km" },
    { id: 3, isim: "Ambulans (Acil)", mesafe: "1.5 km" }
  ];

  // --- API VERİ ÇEKME (Birleştirilmiş Mantık) ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/talepler/oncelikli');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setIhbarlar(data);
        setLoading(false);
      } catch (e) {
        setError(e.message);
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 3000); // 3 saniyede bir canlı günceller
    return () => clearInterval(interval);
  }, []);

  const konumaGit = (lat, lng) => setFlyTo([lat, lng]);

  // --- HARİTA YENİDEN BOYUTLANDIRMA (Senin Kodun) ---
  useEffect(() => {
    const haritayiGuncelle = () => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
      }
    };

    const timer1 = setTimeout(haritayiGuncelle, 100);
    const timer2 = setTimeout(haritayiGuncelle, 500);
    const timer3 = setTimeout(haritayiGuncelle, 1000);
    window.addEventListener('resize', haritayiGuncelle);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      window.removeEventListener('resize', haritayiGuncelle);
    };
  }, []);

  // Uygulama çökmesin diye eklenen örnek atama fonksiyonu
  const aracıAta = (arac) => {
    alert(`${arac.isim} başarıyla görevlendirildi!`);
    setIsModalOpen(false);
  };

  // --- HESAPLANAN VERİLER ---
  const verified = ihbarlar.filter(i => i.is_verified).length;
  const normalIhbarlar = ihbarlar.filter(i => i.dynamic_priority_score < 80);

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 relative bg-zinc-900">
      
      {/* İstatistik Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800">
          <p className="text-slate-500 dark:text-slate-400 font-medium">Aktif İhbarlar</p>
          <h3 className="text-3xl font-bold mt-1">{loading ? '...' : ihbarlar.length}</h3>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800">
          <p className="text-slate-500 dark:text-slate-400 font-medium">Doğrulanmış</p>
          <h3 className="text-3xl font-bold mt-1 text-green-500">{loading ? '...' : verified}</h3>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800">
          <p className="text-slate-500 dark:text-slate-400 font-medium">Doğrulanmamış</p>
          <h3 className="text-3xl font-bold mt-1 text-yellow-500">{loading ? '...' : ihbarlar.length - verified}</h3>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800">
          <p className="text-slate-500 dark:text-slate-400 font-medium">En Yüksek Puan</p>
          <h3 className="text-3xl font-bold mt-1 text-red-500">
            {loading ? '...' : ihbarlar.length > 0 ? ihbarlar[0].dynamic_priority_score : '-'}
          </h3>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
          Backend bağlantı hatası: {error}
        </div>
      )}

      {/* --- ANA YERLEŞİM (Senin Tasarımın) --- */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* SOL TARAF: LİSTELER */}
        <div className="xl:col-span-2 space-y-8">
          
          {/* OTONOM GÖREV PAKETLERİ ALANI */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-red-600 flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              Otonom Görev Paketleri
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto pr-2">
             {clusters.map((cluster) => (
                <div 
                  key={cluster.cluster_id}
                  onClick={() => konumaGit(cluster.center_latitude, cluster.center_longitude)}
                  className={`border-l-[6px] p-4 rounded-r-xl shadow-md cursor-pointer transition-all duration-500 ease-in-out transform hover:-translate-y-1 flex flex-col justify-between ${
                    cluster.status === 'yolda' 
                      ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-500' 
                      : 'bg-red-50 dark:bg-red-900/20 border-red-600'    
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-2">
                        <h4 className={`font-black uppercase text-[13px] transition-colors duration-500 ${cluster.status === 'yolda' ? 'text-amber-700 dark:text-amber-500' : 'text-red-800 dark:text-red-500'}`}>
                          {cluster.status === 'yolda' ? '⏳' : '🚨'} {cluster.cluster_name}
                        </h4>
                        <span className={`text-[10px] text-white px-2 py-1 rounded font-bold tracking-wider transition-colors duration-500 ${cluster.status === 'yolda' ? 'bg-amber-500 animate-pulse' : 'bg-red-600'}`}>
                          {cluster.status === 'yolda' ? 'YOLDA' : cluster.priority_level}
                        </span>
                    </div>

                    <p className="text-[11px] text-slate-600 dark:text-slate-300 font-medium">
                      📍 {cluster.location?.district} / {cluster.location?.neighborhood}
                    </p>

                    <div className="flex gap-2 mt-3 mb-4">
                      <span className="bg-purple-100 text-purple-800 text-[10px] font-bold px-2.5 py-1 rounded-md border border-purple-200">
                        👥 {cluster.total_persons_affected} Kişi
                      </span>
                      <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2.5 py-1 rounded-md border border-blue-200">
                        🔗 {cluster.request_count} İhbar
                      </span>
                    </div>
                  </div>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setSecilenGorev(cluster);
                      setIsModalOpen(true);
                    }}
                    disabled={cluster.status === 'yolda'}
                    className={`w-full py-2.5 mt-auto rounded-lg text-xs font-bold transition-all duration-500 shadow-sm ${
                      cluster.status === 'yolda' 
                        ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed border border-slate-300 dark:border-slate-700' 
                        : 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white hover:shadow-md'
                    }`}
                  >
                    {cluster.status === 'yolda' ? '✔️ YÖNLENDİRİLDİ' : '🚐 EKİP YÖNLENDİR'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* DOĞRULANMAMIŞ İHBARLAR */}
          <div className="space-y-4 opacity-75">
            <h3 className="text-sm font-bold italic text-slate-900 dark:text-white">Doğrulanmamış İhbarlar</h3>
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800 max-h-[300px] overflow-y-auto">
              {normalIhbarlar.length === 0 ? (
                 <div className="p-4 text-center text-xs text-slate-500">Şu an doğrulanmamış ihbar bulunmuyor.</div>
              ) : (
                normalIhbarlar.map((ihbar) => (
                  <div key={ihbar.id} onClick={() => konumaGit(ihbar.latitude, ihbar.longitude)} className="p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer flex justify-between items-center">
                    <span className="text-xs text-slate-600 dark:text-slate-400">📍 {NEED_TYPE_LABELS[ihbar.need_type] || ihbar.need_type}</span>
                    <span className="text-[10px] bg-slate-200 dark:bg-slate-700 px-2 py-0.5 rounded text-slate-900 dark:text-white">Şüpheli</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div> 

        {/* SAĞ TARAF: HARİTA ALANI (Taktiksel Görünüm) */}
        <div className="xl:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
             <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-xl text-blue-500">radar</span>
                Taktiksel Harita
             </h3>
             <span className="text-[10px] px-2 py-1 bg-green-500/20 text-green-400 rounded-full font-bold border border-green-500/30">Canlı</span>
          </div>
          
          <div className="relative h-[600px] w-full rounded-2xl overflow-hidden shadow-xl border border-slate-700/50">
            <MapContainer ref={mapRef} center={[40.990, 29.020]} zoom={12} style={{ height: '100%', width: '100%' }} zoomControl={false}>
              
              {/* Haritanın tıklanan yere uçmasını sağlayan bileşeni ekledik */}
              <MapController flyTo={flyTo} /> 
              
              <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
              {ihbarlar.map((ihbar) => (
                <Marker key={ihbar.id} position={[ihbar.latitude, ihbar.longitude]} icon={kirmiziPin}>
                  <Popup>
                    <b>Tür:</b> {NEED_TYPE_LABELS[ihbar.need_type] || ihbar.need_type} <br/>
                    <b>Puan:</b> {ihbar.dynamic_priority_score}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
            
            {/* Harita Overlay */}
            <div className="absolute bottom-4 left-4 right-4 bg-slate-900/80 backdrop-blur-md p-3 rounded-xl border border-slate-700 z-[400] text-xs">
                <div className="flex justify-between items-center text-slate-300">
                    <span>Toplam İşaret: <strong className="text-white">{ihbarlar.length}</strong></span>
                    <span>Mod: <strong className="text-red-400">Kriz (Acil)</strong></span>
                </div>
            </div>
          </div>
        </div>

      </div>

      {/* MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl w-[400px] shadow-2xl border border-slate-200 dark:border-slate-700">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Müsait Ekipler</h2>
            <p className="text-xs text-slate-500 mb-4">Hedef: {secilenGorev?.cluster_name}</p>
            
            <div className="space-y-3">
              {musaitAraclar.map((arac) => (
                <div key={arac.id} className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div>
                    <p className="font-bold text-sm text-slate-800 dark:text-slate-200">{arac.isim}</p>
                    <p className="text-xs text-slate-500">📍 {arac.mesafe} uzaklıkta</p>
                  </div>
                  <button 
                    onClick={() => aracıAta(arac)}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-1.5 px-4 rounded"
                  >
                    Görevlendir
                  </button>
                </div>
              ))}
            </div>

            <button 
              onClick={() => setIsModalOpen(false)}
              className="mt-6 w-full py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-sm font-bold rounded"
            >
              İptal Et Kapat
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
