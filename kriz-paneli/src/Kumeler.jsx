import React, { useState, useEffect, useCallback } from 'react';

const PRIORITY_COLORS = {
  'Kritik': { border: 'border-red-500/30', bg: 'bg-red-500/10', badge: 'bg-red-600 text-white', text: 'text-red-500', btn: 'bg-blue-600 hover:bg-blue-700' },
  'Yüksek': { border: 'border-orange-500/30', bg: 'bg-orange-500/10', badge: 'bg-orange-500 text-white', text: 'text-orange-400', btn: 'bg-blue-600 hover:bg-blue-700' },
  'Orta':   { border: 'border-amber-500/30',  bg: 'bg-amber-500/10',  badge: 'bg-amber-500 text-slate-900', text: 'text-amber-400', btn: 'bg-slate-700 hover:bg-slate-600' },
  'Düşük':  { border: 'border-slate-600/30',  bg: 'bg-slate-700/10',  badge: 'bg-slate-600 text-white', text: 'text-slate-400', btn: 'bg-slate-700 hover:bg-slate-600' },
};
const NEED_LABELS = {
  arama_kurtarma: 'Arama Kurtarma', medikal: 'Medikal', yangin: 'Yangın',
  enkaz: 'Enkaz', su: 'Su', barinma: 'Barınma', gida: 'Gıda',
  is_makinesi: 'İş Makinesi', ulasim: 'Ulaşım',
};

export default function Kumeler() {
  const [kumeler, setKumeler] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [bildirim, setBildirim] = useState(null);
  const [modal, setModal] = useState(null);
  const [araclar, setAraclar] = useState([]);
  const [seciliAracId, setSeciliAracId] = useState('');
  const [ataniyor, setAtaniyor] = useState(false);

  const fetchKumeler = useCallback(async () => {
    try {
      const r = await fetch('/requests/task-packages?status=active');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setKumeler(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKumeler();
  }, [fetchKumeler]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const r = await fetch('/requests/task-packages/generate', { method: 'POST' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setKumeler(data);
      setBildirim({ type: 'success', msg: `${data.length} küme oluşturuldu.` });
      setTimeout(() => setBildirim(null), 3000);
    } catch (e) {
      setBildirim({ type: 'error', msg: `Küme oluşturulamadı: ${e.message}` });
      setTimeout(() => setBildirim(null), 4000);
    } finally {
      setGenerating(false);
    }
  };

  const handleYonlendir = async (kume) => {
    // Araç listesini çek, modal aç
    try {
      const r = await fetch('/araclar');
      const data = await r.json();
      setAraclar(data);
    } catch {
      setAraclar([]);
    }
    setSeciliAracId('');
    setModal({ kume });
  };

  const handleAracAta = async () => {
    if (!seciliAracId || !modal) return;
    setAtaniyor(true);
    try {
      const r = await fetch(`/requests/task-packages/${modal.kume.cluster_id}/assign-vehicle?vehicle_id=${seciliAracId}`, {
        method: 'POST',
      });
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      setBildirim({ type: 'success', msg: `"${modal.kume.cluster_name}" için araç atandı. Bildirim gönderildi.` });
      setModal(null);
      setTimeout(() => setBildirim(null), 4000);
    } catch (e) {
      setBildirim({ type: 'error', msg: `Atama başarısız: ${e.message}` });
      setTimeout(() => setBildirim(null), 4000);
    } finally {
      setAtaniyor(false);
    }
  };

  const toplam = kumeler.length;
  const kritik = kumeler.filter(k => k.priority_level === 'Kritik').length;
  const toplamKisi = kumeler.reduce((s, k) => s + (k.total_persons_affected || 0), 0);
  const bekleyen = kumeler.reduce((s, k) => s + (k.status_summary?.pending || 0), 0);

  return (
    <div className="flex-1 overflow-y-auto bg-slate-900 text-white relative p-6">

      {/* ARAÇ ATAMA MODALI */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold mb-1">Araç Ata</h3>
            <p className="text-slate-400 text-sm mb-4">{modal.kume.cluster_name}</p>
            <div className="mb-4">
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-2">Araç Seç</label>
              {araclar.length === 0 ? (
                <p className="text-slate-500 text-sm">Kayıtlı araç bulunamadı.</p>
              ) : (
                <select
                  value={seciliAracId}
                  onChange={e => setSeciliAracId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                >
                  <option value="">-- Araç seçin --</option>
                  {araclar.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.vehicle_type} — Çadır: {a.tent_count ?? 0} | Kapasite: {a.capacity}
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div className="flex gap-3">
              <button onClick={() => setModal(null)} className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm font-bold">İptal</button>
              <button
                onClick={handleAracAta}
                disabled={!seciliAracId || ataniyor}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl text-sm font-bold"
              >
                {ataniyor ? 'Atanıyor...' : 'Onayla & Gönder'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-[1600px] mx-auto grid grid-cols-12 gap-6">

        {/* BAŞLIK */}
        <div className="col-span-12 flex justify-between items-end mb-2">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight text-white">İhbar Kümeleri ve Analiz</h2>
            <p className="text-slate-400 text-sm mt-1">
              {loading ? 'Yükleniyor...' : `${toplam} aktif küme — ${toplamKisi} etkilenen kişi`}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchKumeler}
              className="flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-slate-700 transition-colors border border-slate-700"
            >
              <span className="material-symbols-outlined text-lg">refresh</span>
              Yenile
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 bg-rose-600 px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-rose-600/20 hover:brightness-110 transition-all disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                {generating ? 'hourglass_empty' : 'emergency'}
              </span>
              {generating ? 'OLUŞTURULUYOR...' : 'KÜMELERİ GÜNCELLE'}
            </button>
          </div>
        </div>

        {/* BİLDİRİM */}
        {bildirim && (
          <div className={`col-span-12 px-4 py-3 rounded-xl text-sm font-semibold border ${
            bildirim.type === 'success' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
            bildirim.type === 'error'   ? 'bg-red-500/10 border-red-500/30 text-red-400' :
                                          'bg-blue-500/10 border-blue-500/30 text-blue-400'
          }`}>
            {bildirim.msg}
          </div>
        )}

        {/* HATA */}
        {error && (
          <div className="col-span-12 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
            Backend bağlantı hatası: {error}
          </div>
        )}

        {/* KÜME KARTLARI */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {loading && (
            <div className="text-center text-slate-400 py-16">Kümeler yükleniyor...</div>
          )}
          {!loading && kumeler.length === 0 && !error && (
            <div className="text-center text-slate-400 py-16 bg-slate-800 rounded-xl border border-slate-700">
              <span className="material-symbols-outlined text-4xl mb-3 block">hub</span>
              Henüz küme yok. "KÜMELERİ GÜNCELLE" butonuna basarak oluşturabilirsin.
            </div>
          )}
          {kumeler.map((kume) => {
            const c = PRIORITY_COLORS[kume.priority_level] || PRIORITY_COLORS['Düşük'];
            const adres = kume.location?.full_address || kume.location?.district || `${kume.center_latitude?.toFixed(3)}, ${kume.center_longitude?.toFixed(3)}`;
            return (
              <div key={kume.cluster_id} className={`bg-slate-800 border ${c.border} rounded-xl overflow-hidden shadow-sm`}>
                <div className={`${c.bg} p-4 border-b ${c.border} flex justify-between items-center`}>
                  <div className="flex items-center gap-3">
                    <span className={`${c.badge} text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter`}>
                      {kume.priority_level}
                    </span>
                    <h3 className="font-bold text-white">{kume.cluster_name}</h3>
                  </div>
                  <div className={`flex items-center gap-1 ${c.text} text-xs font-bold`}>
                    <span className="material-symbols-outlined text-sm">schedule</span>
                    {new Date(kume.generated_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>

                <div className="p-6 grid grid-cols-3 gap-6">
                  <div className="col-span-2 space-y-4">
                    <div className="flex gap-4">
                      <div className="flex-1 bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                        <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-1">ETKİLENEN NÜFUS</p>
                        <p className="text-2xl font-extrabold">~{kume.total_persons_affected} <span className="text-sm font-medium text-slate-400">kişi</span></p>
                      </div>
                      <div className={`flex-1 bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 ${c.text}`}>
                        <p className="text-[10px] uppercase font-bold tracking-widest mb-1 text-slate-400">İHTİYAÇ TÜRÜ</p>
                        <p className="text-xl font-extrabold">{NEED_LABELS[kume.need_type] || kume.need_type}</p>
                      </div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                      <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-2">KONUM & ÖZET</p>
                      <p className="text-sm leading-relaxed text-slate-300">
                        📍 {adres} — {kume.request_count} ihbar kümelendi.
                        Bekleyen: {kume.status_summary?.pending || 0} |
                        Atanan: {kume.status_summary?.assigned || 0} |
                        Çözülen: {kume.status_summary?.resolved || 0}
                      </p>
                    </div>
                  </div>

                  <div className="col-span-1 flex flex-col justify-between">
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 space-y-2">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">Ort. Öncelik Puanı</p>
                      <p className={`text-2xl font-extrabold ${c.text}`}>{kume.average_priority_score}</p>
                      <p className="text-[10px] text-slate-500">{kume.is_noise_cluster ? '⚠ Dağınık Küme' : '✓ Yoğun Küme'}</p>
                    </div>
                    <button
                      onClick={() => handleYonlendir(kume)}
                      className={`w-full ${c.btn} text-white py-3 rounded-xl font-bold mt-4 transition-colors active:scale-95 flex items-center justify-center gap-2`}
                    >
                      <span className="material-symbols-outlined">send</span>
                      EKİP YÖNLENDİR
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* SAĞ PANEL */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 sticky top-6">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-blue-500">analytics</span>
              <h3 className="text-lg font-bold uppercase tracking-tight">KÜME DETAY ANALİZİ</h3>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                <p className="text-[10px] text-slate-400 font-bold">TOPLAM KÜME</p>
                <p className="text-xl font-bold text-white">{toplam}</p>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                <p className="text-[10px] text-slate-400 font-bold">KRİTİK</p>
                <p className="text-xl font-bold text-red-500">{kritik}</p>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                <p className="text-[10px] text-slate-400 font-bold">BEKLEYEN İHBAR</p>
                <p className="text-xl font-bold text-white">{bekleyen}</p>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                <p className="text-[10px] text-slate-400 font-bold">ETKİLENEN KİŞİ</p>
                <p className="text-xl font-bold text-white">{toplamKisi}</p>
              </div>
            </div>

            {/* Son kümeler listesi */}
            <div>
              <label className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-3 block">AKTİF KÜMELER</label>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {kumeler.slice(0, 8).map(k => {
                  const c = PRIORITY_COLORS[k.priority_level] || PRIORITY_COLORS['Düşük'];
                  return (
                    <div key={k.cluster_id} className={`flex gap-3 text-xs border-l-2 ${c.text.replace('text', 'border')} pl-3 py-1 text-slate-300`}>
                      <span className={`font-bold ${c.text}`}>{k.priority_level}</span>
                      <p className="truncate">{k.cluster_name}</p>
                    </div>
                  );
                })}
                {kumeler.length === 0 && !loading && (
                  <p className="text-slate-500 text-xs">Küme bulunamadı.</p>
                )}
              </div>
            </div>
          </div>
        </aside>

      </div>

      {/* YÜZEN BUTON */}
      <div className="fixed bottom-8 right-8 z-50">
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-16 h-16 bg-blue-600 text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-90 transition-all disabled:opacity-60"
          title="Kümeleri Güncelle"
        >
          <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
            {generating ? 'hourglass_empty' : 'add_alert'}
          </span>
        </button>
      </div>
    </div>
  );
}
