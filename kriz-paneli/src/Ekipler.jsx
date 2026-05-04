import { useEffect, useMemo, useRef, useState } from 'react';
import { apiFetch } from './services/apiFetch';

const VEHICLE_ICONS = {
  ambulans: 'medical_services',
  itfaiye: 'local_fire_department',
  kamyon: 'local_shipping',
  panelvan: 'airport_shuttle',
  'su tankeri': 'water_drop',
  'iş makinesi': 'construction',
  'is makinesi': 'construction',
  default: 'directions_car',
};

const SUGGESTED_VEHICLE_TYPES = [
  'Kamyon',
  'Ambulans',
  'İtfaiye',
  'Panelvan',
  'Su Tankeri',
  'İş Makinesi',
];

const normalizeVehicleType = (vehicleType = '') => vehicleType.trim().toLocaleLowerCase('tr-TR');
const VEHICLE_TYPE_LABELS = {
  ambulans: 'Ambulans',
  ambulance: 'Ambulans',
  itfaiye: 'İtfaiye',
  'fire truck': 'İtfaiye',
  firetruck: 'İtfaiye',
  'fire engine': 'İtfaiye',
  kamyon: 'Kamyon',
  truck: 'Kamyon',
  lorry: 'Kamyon',
  panelvan: 'Panelvan',
  'panel van': 'Panelvan',
  'su tankeri': 'Su Tankeri',
  'water tanker': 'Su Tankeri',
  'iş makinesi': 'İş Makinesi',
  'is makinesi': 'İş Makinesi',
  excavator: 'İş Makinesi',
  'construction vehicle': 'İş Makinesi',
};
const getVehicleTypeLabel = (vehicleType = '') => (
  VEHICLE_TYPE_LABELS[normalizeVehicleType(vehicleType)] || vehicleType.trim()
);
const getUniqueVehicleTypes = (vehicleTypes) => {
  const seen = new Set();
  return vehicleTypes.filter((vehicleType) => {
    const normalized = normalizeVehicleType(getVehicleTypeLabel(vehicleType));
    if (!normalized || seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
};

const EMPTY_VEHICLE_FORM = {
  plate_number: '',
  latitude: '',
  longitude: '',
  vehicle_type: '',
  capacity: '',
  base_speed_kmh: '60',
  tent_count: '0',
  food_count: '0',
  water_count: '0',
  medical_count: '0',
  blanket_count: '0',
};

const STOCK_FIELDS = [
  { key: 'tent_count', label: 'Çadır' },
  { key: 'food_count', label: 'Gıda' },
  { key: 'water_count', label: 'Su (lt)' },
  { key: 'medical_count', label: 'Tıbbi' },
  { key: 'blanket_count', label: 'Battaniye' },
];

export default function Ekipler() {
  const [araclar, setAraclar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [yeniArac, setYeniArac] = useState({ ...EMPTY_VEHICLE_FORM });
  const [formAcik, setFormAcik] = useState(false);
  const [kaydediliyor, setKaydediliyor] = useState(false);
  const [bildirim, setBildirim] = useState(null);
  const [aracTipiPanelAcik, setAracTipiPanelAcik] = useState(false);
  const aracTipiAlanRef = useRef(null);
  const aracTipiOnerileri = useMemo(
    () => getUniqueVehicleTypes([
      ...SUGGESTED_VEHICLE_TYPES,
      ...araclar.map((arac) => getVehicleTypeLabel(arac.vehicle_type)).filter(Boolean),
    ]).map(getVehicleTypeLabel),
    [araclar],
  );
  const aracTipiArama = yeniArac.vehicle_type.trim();
  const filtreliAracTipleri = useMemo(() => {
    const normalizedSearch = normalizeVehicleType(aracTipiArama);
    const normalizedCanonicalSearch = normalizeVehicleType(getVehicleTypeLabel(aracTipiArama));
    return aracTipiOnerileri.filter((tip) => (
      !normalizedSearch
      || normalizeVehicleType(tip).includes(normalizedSearch)
      || normalizeVehicleType(tip).includes(normalizedCanonicalSearch)
    ));
  }, [aracTipiArama, aracTipiOnerileri]);
  const yeniTipOnerisi = useMemo(() => {
    if (!aracTipiArama) return '';
    const eslesmeVar = aracTipiOnerileri.some(
      (tip) => normalizeVehicleType(tip) === normalizeVehicleType(getVehicleTypeLabel(aracTipiArama)),
    );
    return eslesmeVar ? '' : getVehicleTypeLabel(aracTipiArama);
  }, [aracTipiArama, aracTipiOnerileri]);

  const fetchAraclar = async () => {
    try {
      const r = await apiFetch('/api/vehicles');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setAraclar(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAraclar(); }, []);

  useEffect(() => {
    const handlePointerDown = (event) => {
      if (aracTipiAlanRef.current && !aracTipiAlanRef.current.contains(event.target)) {
        setAracTipiPanelAcik(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, []);

  const selectVehicleType = (vehicleType) => {
    setYeniArac((prev) => ({ ...prev, vehicle_type: vehicleType }));
    setAracTipiPanelAcik(false);
  };

  const handleEkle = async (e) => {
    e.preventDefault();
    const vehicleType = getVehicleTypeLabel(yeniArac.vehicle_type);
    const plateNumber = yeniArac.plate_number.trim();
    const capacity = yeniArac.capacity.trim();
    if (!vehicleType) {
      setBildirim({ type: 'error', msg: 'Araç tipi boş bırakılamaz.' });
      setTimeout(() => setBildirim(null), 4000);
      return;
    }
    if (!plateNumber) {
      setBildirim({ type: 'error', msg: 'Araç kodu veya plaka bilgisi gereklidir.' });
      setTimeout(() => setBildirim(null), 4000);
      return;
    }
    if (!capacity) {
      setBildirim({ type: 'error', msg: 'Araç kapasitesi boş bırakılamaz.' });
      setTimeout(() => setBildirim(null), 4000);
      return;
    }
    setKaydediliyor(true);
    try {
      const r = await apiFetch('/api/vehicles/', {
        method: 'POST',
        body: JSON.stringify({
          plate_number: plateNumber,
          latitude: parseFloat(yeniArac.latitude),
          longitude: parseFloat(yeniArac.longitude),
          vehicle_type: vehicleType,
          capacity,
          base_speed_kmh: Number.parseInt(yeniArac.base_speed_kmh || '60', 10),
          tent_count: Number.parseInt(yeniArac.tent_count || '0', 10),
          food_count: Number.parseInt(yeniArac.food_count || '0', 10),
          water_count: Number.parseInt(yeniArac.water_count || '0', 10),
          medical_count: Number.parseInt(yeniArac.medical_count || '0', 10),
          blanket_count: Number.parseInt(yeniArac.blanket_count || '0', 10),
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      await fetchAraclar();
      setFormAcik(false);
      setYeniArac({ ...EMPTY_VEHICLE_FORM });
      setBildirim({ type: 'success', msg: 'Araç başarıyla eklendi.' });
      setTimeout(() => setBildirim(null), 3000);
    } catch (e) {
      setBildirim({ type: 'error', msg: `Araç eklenemedi: ${e.message}` });
      setTimeout(() => setBildirim(null), 4000);
    } finally {
      setKaydediliyor(false);
    }
  };

  const aktif = araclar.length;
  const toplamCadir = araclar.reduce((s, a) => s + (a.tent_count || 0), 0);
  const toplamGida = araclar.reduce((s, a) => s + (a.food_count || 0), 0);
  const toplamSu = araclar.reduce((s, a) => s + (a.water_count || 0), 0);
  const toplamTibbi = araclar.reduce((s, a) => s + (a.medical_count || 0), 0);
  const toplamBattaniye = araclar.reduce((s, a) => s + (a.blanket_count || 0), 0);

  return (
    <div className="text-on-surface p-8 w-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">

        {/* BAŞLIK */}
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-on-surface mb-2">Saha Ekipleri & Araçlar</h1>
            <p className="text-slate-400 max-w-lg">
              {loading ? 'Yükleniyor...' : `${aktif} araç kayıtlı — ${toplamCadir} çadır, ${toplamGida} gıda, ${toplamSu} su, ${toplamTibbi} tıbbi, ${toplamBattaniye} battaniye stoku`}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchAraclar}
              className="bg-surface-container hover:bg-surface-container-high text-slate-300 px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 border border-slate-800 transition-all"
            >
              <span className="material-symbols-outlined text-sm">refresh</span> Yenile
            </button>
            <button
              onClick={() => setFormAcik(!formAcik)}
              className="bg-primary hover:opacity-90 text-white px-6 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all"
            >
              <span className="material-symbols-outlined text-sm">{formAcik ? 'close' : 'add'}</span>
              {formAcik ? 'İptal' : 'Yeni Araç Ekle'}
            </button>
          </div>
        </div>

        {/* BİLDİRİM */}
        {bildirim && (
          <div className={`mb-6 px-4 py-3 rounded-xl text-sm font-semibold border ${
            bildirim.type === 'success' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
                                          'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {bildirim.msg}
          </div>
        )}

        {/* HATA */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
            Backend bağlantı hatası: {error}
          </div>
        )}

        {/* YENİ ARAÇ FORMU */}
        {formAcik && (
          <form onSubmit={handleEkle} className="mb-8 bg-slate-800 border border-slate-700 rounded-xl p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Araç Kodu / Plaka</label>
              <input
                type="text"
                required
                value={yeniArac.plate_number}
                onChange={e => setYeniArac(p => ({ ...p, plate_number: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="34 ABC 123"
              />
            </div>
            <div ref={aracTipiAlanRef} className="col-span-2 md:col-span-1 relative">
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Araç Tipi</label>
              <div className={`flex items-center rounded-xl border bg-slate-900 pr-2 transition-all ${
                aracTipiPanelAcik ? 'border-primary/40 ring-1 ring-primary/20' : 'border-slate-700'
              }`}>
                <input
                  type="text"
                  required
                  value={yeniArac.vehicle_type}
                  onFocus={() => setAracTipiPanelAcik(true)}
                  onChange={(e) => {
                    setYeniArac((p) => ({ ...p, vehicle_type: e.target.value }));
                    setAracTipiPanelAcik(true);
                  }}
                  className="w-full bg-transparent px-3 py-2 text-sm text-white outline-none"
                  placeholder="Kamyon, İtfaiye, İş Makinesi..."
                />
                <button
                  type="button"
                  onClick={() => setAracTipiPanelAcik((prev) => !prev)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white"
                  aria-label="Araç tipi önerilerini aç"
                >
                  <span className="material-symbols-outlined text-base">
                    {aracTipiPanelAcik ? 'expand_less' : 'expand_more'}
                  </span>
                </button>
              </div>
              {aracTipiPanelAcik && (
                <div className="absolute inset-x-0 z-20 mt-2 rounded-xl border border-slate-700 bg-slate-950/98 p-2 shadow-2xl backdrop-blur">
                  <div className="mb-2 flex items-center justify-between px-2">
                    <span className="text-[10px] uppercase tracking-widest text-slate-500">Önerilen Araç Tipleri</span>
                    <span className="text-[10px] text-slate-500">Türkçe giriş serbest</span>
                  </div>
                  <div className="max-h-56 space-y-1 overflow-y-auto pr-1">
                    {filtreliAracTipleri.map((tip) => {
                      const secili = normalizeVehicleType(tip) === normalizeVehicleType(yeniArac.vehicle_type);
                      return (
                        <button
                          key={tip}
                          type="button"
                          onClick={() => selectVehicleType(tip)}
                          className={`group flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-all ${
                            secili
                              ? 'border-primary/30 bg-primary/10 text-white'
                              : 'border-transparent text-slate-200 hover:border-slate-700 hover:bg-slate-800/70'
                          }`}
                        >
                          <span className={`flex h-5 w-5 items-center justify-center rounded-md border transition-all ${
                            secili
                              ? 'border-primary bg-primary text-white'
                              : 'border-slate-600 bg-slate-900 text-transparent group-hover:border-slate-400'
                          }`}>
                            <span className="material-symbols-outlined text-[14px] leading-none">check</span>
                          </span>
                          <span className="flex-1 font-medium">{tip}</span>
                        </button>
                      );
                    })}

                    {yeniTipOnerisi && (
                      <button
                        type="button"
                        onClick={() => selectVehicleType(yeniTipOnerisi)}
                        className="flex w-full items-center gap-3 rounded-lg border border-dashed border-primary/30 bg-primary/5 px-3 py-2 text-left text-sm text-slate-100 transition-all hover:bg-primary/10"
                      >
                        <span className="flex h-5 w-5 items-center justify-center rounded-md bg-primary text-white">
                          <span className="material-symbols-outlined text-[14px] leading-none">add</span>
                        </span>
                        <span className="flex-1">
                          <span className="block font-medium">{yeniTipOnerisi}</span>
                          <span className="text-[10px] uppercase tracking-widest text-slate-400">Yeni araç tipi olarak kullan</span>
                        </span>
                      </button>
                    )}

                    {!filtreliAracTipleri.length && !yeniTipOnerisi && (
                      <div className="rounded-lg border border-dashed border-slate-700 px-3 py-3 text-xs text-slate-400">
                        Eşleşen öneri yok. Araç tipini Türkçe olarak yazarak devam edebilirsin.
                      </div>
                    )}
                  </div>
                </div>
              )}
              <p className="mt-1 text-[10px] text-slate-500">
                Açılır listeden seçebilir veya araç tipini Türkçe olarak yazabilirsin.
              </p>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Kapasite</label>
              <input
                type="text"
                required
                value={yeniArac.capacity}
                onChange={e => setYeniArac(p => ({ ...p, capacity: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="10 ton"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Standart Hız (km/s)</label>
              <input
                type="number"
                min="1"
                step="1"
                required
                value={yeniArac.base_speed_kmh}
                onChange={e => setYeniArac(p => ({ ...p, base_speed_kmh: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="60"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Enlem</label>
              <input
                type="number"
                step="any"
                required
                value={yeniArac.latitude}
                onChange={e => setYeniArac(p => ({ ...p, latitude: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="41.01"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Boylam</label>
              <input
                type="number"
                step="any"
                required
                value={yeniArac.longitude}
                onChange={e => setYeniArac(p => ({ ...p, longitude: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="29.02"
              />
            </div>
            <div className="col-span-2 md:col-span-4 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Başlangıç Yükü</p>
                  <p className="text-xs text-slate-400">Araç sahaya çıkmadan önce içindeki temel stokları gir.</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
                {STOCK_FIELDS.map((field) => (
                  <div key={field.key}>
                    <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">{field.label}</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={yeniArac[field.key]}
                      onChange={e => setYeniArac(p => ({ ...p, [field.key]: e.target.value }))}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                      placeholder="0"
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="col-span-2 md:col-span-4 flex justify-end">
              <button
                type="submit"
                disabled={kaydediliyor}
                className="bg-primary text-white px-8 py-2 rounded-xl font-bold text-sm disabled:opacity-60"
              >
                {kaydediliyor ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </form>
        )}

        {/* ARAÇ KARTLARI */}
        {loading && <div className="text-center text-slate-400 py-16">Araçlar yükleniyor...</div>}

        {!loading && araclar.length === 0 && !error && (
          <div className="text-center text-slate-400 py-16 bg-slate-800 rounded-xl border border-slate-700">
            <span className="material-symbols-outlined text-4xl mb-3 block">local_shipping</span>
            Henüz araç yok. "Yeni Araç Ekle" butonuyla ekleyebilirsin.
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {araclar.map((arac) => {
            const icon = VEHICLE_ICONS[normalizeVehicleType(arac.vehicle_type)] || VEHICLE_ICONS.default;
            const vehicleTypeLabel = getVehicleTypeLabel(arac.vehicle_type);
            return (
              <div key={arac.id} className="bg-surface-container rounded-xl p-6 border border-outline-variant shadow-sm hover:border-primary/50 transition-all">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined text-2xl">{icon}</span>
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-on-surface">{arac.plate_number || vehicleTypeLabel}</h3>
                      <p className="text-xs text-slate-400 capitalize">{vehicleTypeLabel}</p>
                      <span className="text-[10px] uppercase tracking-widest text-slate-500">
                        Kapasite: {arac.capacity} · Hız: {arac.base_speed_kmh ?? 60} km/s
                      </span>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest rounded-full border border-primary/20">
                    Aktif
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                  <div className="bg-surface-container-low p-3 rounded-lg border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Çadır</p>
                    <p className="text-sm font-bold text-on-surface">{arac.tent_count ?? 0}</p>
                  </div>
                  <div className="bg-surface-container-low p-3 rounded-lg border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Gıda</p>
                    <p className="text-sm font-bold text-on-surface">{arac.food_count ?? 0}</p>
                  </div>
                  <div className="bg-surface-container-low p-3 rounded-lg border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Su</p>
                    <p className="text-sm font-bold text-on-surface">{arac.water_count ?? 0}</p>
                  </div>
                  <div className="bg-surface-container-low p-3 rounded-lg border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Tıbbi</p>
                    <p className="text-sm font-bold text-on-surface">{arac.medical_count ?? 0}</p>
                  </div>
                  <div className="bg-surface-container-low p-3 rounded-lg border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Battaniye</p>
                    <p className="text-sm font-bold text-on-surface">{arac.blanket_count ?? 0}</p>
                  </div>
                </div>

                <p className="text-[10px] text-slate-500 font-mono">
                  📍 {arac.latitude?.toFixed(4)}, {arac.longitude?.toFixed(4)}
                </p>
              </div>
            );
          })}
        </div>

        {/* ÖZET İSTATİSTİKLER */}
        {!loading && araclar.length > 0 && (
          <div className="mt-8 grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 pb-12">
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Araç</p>
              <p className="text-2xl font-black text-on-surface">{aktif}</p>
            </div>
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Çadır</p>
              <p className="text-2xl font-black text-blue-500">{toplamCadir}</p>
            </div>
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Gıda</p>
              <p className="text-2xl font-black text-on-surface">{toplamGida}</p>
            </div>
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Su</p>
              <p className="text-2xl font-black text-on-surface">{toplamSu}</p>
            </div>
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Tıbbi</p>
              <p className="text-2xl font-black text-emerald-400">{toplamTibbi}</p>
            </div>
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/50">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Toplam Battaniye</p>
              <p className="text-2xl font-black text-amber-300">{toplamBattaniye}</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
