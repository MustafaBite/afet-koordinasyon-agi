import 'leaflet/dist/leaflet.css';
import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

const kirmiziPin = L.divIcon({
  className: 'custom-icon',
  html: `<div style="width:14px;height:14px;background:#ef4444;border-radius:50%;box-shadow:0 0 0 6px rgba(239,68,68,0.25);animation:pulse 1.5s infinite;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

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
  const [ihbarlar, setIhbarlar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/talepler/oncelikli')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => { setIhbarlar(data); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const verified = ihbarlar.filter(i => i.is_verified).length;

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8">

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

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

        {/* Harita */}
        <div className="xl:col-span-2 space-y-4">
          <h3 className="text-lg font-bold">Harita Canlı İzleme</h3>
          <div className="relative h-[420px] w-full rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-inner">
            <MapContainer
              center={[39.0, 35.0]}
              zoom={6}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              />
              {ihbarlar.map((ihbar) => (
                <Marker
                  key={ihbar.id}
                  position={[ihbar.latitude, ihbar.longitude]}
                  icon={kirmiziPin}
                >
                  <Popup>
                    <b>Tür:</b> {NEED_TYPE_LABELS[ihbar.need_type] || ihbar.need_type}<br />
                    <b>Aciliyet:</b> {ihbar.dynamic_priority_score}<br />
                    <b>Doğrulandı:</b> {ihbar.is_verified ? 'Evet' : 'Hayır'}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Canlı İhbar Akışı */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold">Canlı İhbar Akışı</h3>
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-y-auto max-h-[420px] divide-y divide-slate-100 dark:divide-slate-800">
            {loading && (
              <div className="p-6 text-center text-slate-400 text-sm">Yükleniyor...</div>
            )}
            {!loading && ihbarlar.length === 0 && (
              <div className="p-6 text-center text-slate-400 text-sm">Kayıt bulunamadı.</div>
            )}
            {ihbarlar.slice(0, 50).map((ihbar) => (
              <div key={ihbar.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer">
                <div className="flex justify-between items-start">
                  <p className="text-sm font-bold text-slate-900 dark:text-white capitalize">
                    {NEED_TYPE_LABELS[ihbar.need_type] || ihbar.need_type}
                  </p>
                  <span className="text-[10px] text-slate-500">
                    {new Date(ihbar.created_at).toLocaleDateString('tr-TR')}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  📍 {ihbar.latitude.toFixed(3)}, {ihbar.longitude.toFixed(3)}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[10px] bg-red-500/10 text-red-500 px-2 py-0.5 rounded-full font-bold">
                    🔥 {ihbar.dynamic_priority_score}
                  </span>
                  {ihbar.is_verified && (
                    <span className="text-[10px] bg-green-500/10 text-green-500 px-2 py-0.5 rounded-full font-bold">
                      ✓ Doğrulandı
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
