import { useState, useEffect } from 'react';

const VEHICLE_ICONS = {
  ambulans: 'medical_services',
  itfaiye: 'local_fire_department',
  kamyon: 'local_shipping',
  default: 'directions_car',
};

export default function Ekipler() {
  const [araclar, setAraclar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [yeniArac, setYeniArac] = useState({ latitude: '', longitude: '', vehicle_type: 'kamyon', capacity: '10' });
  const [formAcik, setFormAcik] = useState(false);
  const [kaydediliyor, setKaydediliyor] = useState(false);
  const [bildirim, setBildirim] = useState(null);

  const fetchAraclar = async () => {
    try {
      const r = await fetch('/araclar');
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

  const handleEkle = async (e) => {
    e.preventDefault();
    setKaydediliyor(true);
    try {
      const r = await fetch('/arac-ekle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: parseFloat(yeniArac.latitude),
          longitude: parseFloat(yeniArac.longitude),
          vehicle_type: yeniArac.vehicle_type,
          capacity: yeniArac.capacity,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      await fetchAraclar();
      setFormAcik(false);
      setYeniArac({ latitude: '', longitude: '', vehicle_type: 'kamyon', capacity: '10' });
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

  return (
    <div className="text-on-surface p-8 w-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">

        {/* BAŞLIK */}
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-on-surface mb-2">Saha Ekipleri & Araçlar</h1>
            <p className="text-slate-400 max-w-lg">
              {loading ? 'Yükleniyor...' : `${aktif} araç kayıtlı — ${toplamCadir} çadır, ${toplamGida} gıda, ${toplamSu} su stoku`}
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
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Araç Tipi</label>
              <select
                value={yeniArac.vehicle_type}
                onChange={e => setYeniArac(p => ({ ...p, vehicle_type: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                <option value="kamyon">Kamyon</option>
                <option value="ambulans">Ambulans</option>
                <option value="itfaiye">İtfaiye</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Kapasite</label>
              <input
                type="text"
                value={yeniArac.capacity}
                onChange={e => setYeniArac(p => ({ ...p, capacity: e.target.value }))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="10"
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
            const icon = VEHICLE_ICONS[arac.vehicle_type?.toLowerCase()] || VEHICLE_ICONS.default;
            return (
              <div key={arac.id} className="bg-surface-container rounded-xl p-6 border border-outline-variant shadow-sm hover:border-primary/50 transition-all">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined text-2xl">{icon}</span>
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-on-surface capitalize">{arac.vehicle_type}</h3>
                      <span className="text-[10px] uppercase tracking-widest text-slate-500">Kapasite: {arac.capacity}</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest rounded-full border border-primary/20">
                    Aktif
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
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
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 pb-12">
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
          </div>
        )}

      </div>
    </div>
  );
}
