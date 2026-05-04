import 'leaflet/dist/leaflet.css';
import { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { apiFetch } from './services/apiFetch';

const NEED_LABELS = {
  arama_kurtarma: 'Arama Kurtarma', medikal: 'Medikal', yangin: 'Yangın',
  enkaz: 'Enkaz', su: 'Su', barinma: 'Barınma', gida: 'Gıda',
  is_makinesi: 'İş Makinesi', ulasim: 'Ulaşım',
};

const pinByScore = (score) => {
  const color = score >= 80 ? 'red' : score >= 50 ? 'orange' : score >= 25 ? 'gold' : 'blue';
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
  });
};

function FlyController({ flyTo }) {
  const map = useMap();
  useEffect(() => {
    if (flyTo) map.flyTo(flyTo, 14, { duration: 1.2 });
  }, [flyTo, map]);
  return null;
}

export default function HaritaGorunumu() {
  const mapRef = useRef(null);
  const [ihbarlar, setIhbarlar] = useState([]);
  const [kumeler, setKumeler] = useState([]);
  const [loading, setLoading] = useState(true);
  const [flyTo, setFlyTo] = useState(null);
  const [secili, setSecili] = useState(null); // seçili ihbar detay

  const fetchData = useCallback(async () => {
    try {
      const [rReq, rCluster] = await Promise.all([
        apiFetch('/api/ihbarlar/prioritized'),
        apiFetch('/requests/task-packages'),
      ]);
      if (rReq.ok) setIhbarlar(await rReq.json());
      if (rCluster.ok) setKumeler(await rCluster.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    const t1 = setTimeout(() => mapRef.current?.invalidateSize(), 150);
    const t2 = setTimeout(() => mapRef.current?.invalidateSize(), 600);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  // İstatistikler
  const toplam     = ihbarlar.length;
  const dogrulanan = ihbarlar.filter(i => i.is_verified).length;
  const bekleyen   = toplam - dogrulanan;
  const enYuksek   = ihbarlar[0]?.dynamic_priority_score ?? 0;
  const kritik     = ihbarlar.filter(i => i.dynamic_priority_score >= 80).length;

  // Son 5 ihbar (en yeni)
  const sonIhbarlar = [...ihbarlar]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden flex flex-col">

      {/* Harita */}
      <div className="flex-1 relative">
        <MapContainer
          ref={mapRef}
          center={[40.990, 29.020]}
          zoom={11}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <FlyController flyTo={flyTo} />
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />

          {/* Küme çember overlay */}
          {kumeler.map((k) => (
            <Circle
              key={k.cluster_id}
              center={[k.center_latitude, k.center_longitude]}
              radius={800}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.08, weight: 1 }}
            />
          ))}

          {/* İhbar pin'leri */}
          {ihbarlar.map((ihbar) => (
            <Marker
              key={ihbar.id}
              position={[ihbar.latitude, ihbar.longitude]}
              icon={pinByScore(ihbar.dynamic_priority_score)}
              eventHandlers={{ click: () => {
                setSecili(ihbar);
                setFlyTo([ihbar.latitude, ihbar.longitude]);
              }}}
            >
              <Popup>
                <div className="text-xs min-w-[160px]">
                  <p className="font-bold mb-1">{NEED_LABELS[ihbar.need_type] || ihbar.need_type}</p>
                  <p>Puan: <strong>{ihbar.dynamic_priority_score}</strong></p>
                  <p>{ihbar.person_count ?? 1} kişi</p>
                  {ihbar.description && <p className="mt-1 text-slate-500">{ihbar.description}</p>}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Zoom butonları */}
        <div className="absolute top-4 right-4 z-[400] flex flex-col gap-1">
          <button
            onClick={() => mapRef.current?.zoomIn()}
            className="w-9 h-9 bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center border border-white/10 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">add</span>
          </button>
          <button
            onClick={() => mapRef.current?.zoomOut()}
            className="w-9 h-9 bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center border border-white/10 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">remove</span>
          </button>
          <button
            onClick={fetchData}
            className="w-9 h-9 bg-slate-800/90 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center justify-center border border-white/10 transition-colors mt-1"
            title="Yenile"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
          </button>
        </div>

        {/* Sol üst — İstatistik paneli */}
        <div className="absolute top-4 left-4 z-[400] w-56 space-y-2">
          <div className="bg-slate-900/90 backdrop-blur border border-white/10 rounded-xl p-4 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Canlı Durum</span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                <span className="text-[10px] font-bold text-green-400">CANLI</span>
              </span>
            </div>
            {loading ? (
              <p className="text-xs text-slate-400">Yükleniyor...</p>
            ) : (
              <div className="space-y-2.5">
                <StatRow label="Toplam İhbar"  value={toplam}     color="text-white" />
                <StatRow label="Doğrulanmış"   value={dogrulanan} color="text-green-400" />
                <StatRow label="Doğrulanmamış" value={bekleyen}   color="text-yellow-400" />
                <StatRow label="Kritik (≥80)"  value={kritik}     color="text-red-400" />
                <div className="pt-1 border-t border-white/10">
                  <StatRow label="En Yüksek Puan" value={enYuksek} color="text-orange-400" />
                </div>
              </div>
            )}
          </div>

          {/* Küme sayacı */}
          <div className="bg-slate-900/90 backdrop-blur border border-white/10 rounded-xl px-4 py-3 shadow-xl">
            <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Görev Paketleri</p>
            <p className="text-2xl font-black text-white">{kumeler.length}</p>
            <p className="text-[10px] text-slate-400">aktif küme</p>
          </div>
        </div>

        {/* Seçili ihbar detay kutusu */}
        {secili && (
          <div className="absolute bottom-4 right-4 z-[400] w-72 bg-slate-900/95 backdrop-blur border border-white/10 rounded-xl p-4 shadow-2xl">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-bold text-orange-400 uppercase tracking-wide">
                {NEED_LABELS[secili.need_type] || secili.need_type}
              </span>
              <button onClick={() => setSecili(null)} className="text-slate-500 hover:text-white text-base leading-none">✕</button>
            </div>
            <div className="space-y-1.5 text-xs text-slate-300">
              <p>Puan: <strong className="text-white">{secili.dynamic_priority_score}</strong></p>
              <p>Kişi: <strong className="text-white">{secili.person_count ?? 1}</strong></p>
              <p>Doğrulanmış: <strong className={secili.is_verified ? 'text-green-400' : 'text-yellow-400'}>{secili.is_verified ? 'Evet' : 'Hayır'}</strong></p>
              <p className="text-slate-500 font-mono text-[10px]">{secili.latitude?.toFixed(5)}, {secili.longitude?.toFixed(5)}</p>
              {secili.description && <p className="text-slate-400 pt-1 border-t border-white/10">{secili.description}</p>}
              <p className="text-slate-600 text-[10px]">{new Date(secili.created_at).toLocaleString('tr-TR')}</p>
            </div>
          </div>
        )}
      </div>

      {/* Alt şerit — son ihbarlar */}
      <div className="bg-slate-900/95 border-t border-white/10 px-4 py-3 flex gap-3 overflow-x-auto shrink-0">
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-400 font-bold whitespace-nowrap pr-3 border-r border-white/10">
          <span className="material-symbols-outlined text-sm text-blue-400">list_alt</span>
          Son İhbarlar
        </div>
        {loading ? (
          <span className="text-xs text-slate-500 self-center">Yükleniyor...</span>
        ) : sonIhbarlar.length === 0 ? (
          <span className="text-xs text-slate-500 self-center">İhbar yok</span>
        ) : (
          sonIhbarlar.map((ihbar) => (
            <button
              key={ihbar.id}
              onClick={() => { setSecili(ihbar); setFlyTo([ihbar.latitude, ihbar.longitude]); }}
              className={`min-w-[200px] text-left p-3 rounded-xl border transition-all shrink-0 ${
                ihbar.dynamic_priority_score >= 80
                  ? 'bg-red-500/10 border-red-500/20 hover:border-red-500/50'
                  : ihbar.dynamic_priority_score >= 50
                    ? 'bg-orange-500/10 border-orange-500/20 hover:border-orange-500/50'
                    : 'bg-slate-800 border-white/5 hover:border-white/20'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className={`text-[10px] font-bold uppercase ${
                  ihbar.dynamic_priority_score >= 80 ? 'text-red-400' :
                  ihbar.dynamic_priority_score >= 50 ? 'text-orange-400' : 'text-slate-400'
                }`}>
                  {NEED_LABELS[ihbar.need_type] || ihbar.need_type}
                </span>
                <span className="text-[10px] font-mono text-slate-500">
                  {new Date(ihbar.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-xs text-slate-200 font-medium">Puan: {ihbar.dynamic_priority_score}</p>
              <p className="text-[10px] text-slate-500">{ihbar.person_count ?? 1} kişi</p>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function StatRow({ label, value, color }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[11px] text-slate-400">{label}</span>
      <span className={`text-sm font-black ${color}`}>{value}</span>
    </div>
  );
}
