import { useState, useEffect } from 'react';

const NEED_LABELS = {
  arama_kurtarma: 'Arama Kurtarma', medikal: 'Medikal', yangin: 'Yangın',
  enkaz: 'Enkaz', su: 'Su', barinma: 'Barınma', gida: 'Gıda',
  is_makinesi: 'İş Makinesi', ulasim: 'Ulaşım',
};

const PRIORITY_BADGE = (score) => {
  if (score >= 80) return { label: 'Kritik', cls: 'bg-red-500/10 text-red-500 border-red-500/20' };
  if (score >= 50) return { label: 'Yüksek Öncelik', cls: 'bg-orange-500/10 text-orange-500 border-orange-500/20' };
  if (score >= 25) return { label: 'Orta Öncelik', cls: 'bg-amber-500/10 text-amber-500 border-amber-500/20' };
  return { label: 'Düşük Öncelik', cls: 'bg-blue-500/10 text-blue-500 border-blue-500/20' };
};

export default function DogrulanmamisIhbarlar() {
  const [ihbarlar, setIhbarlar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [islemler, setIslemler] = useState({}); // { id: 'loading' | 'done' }
  const [filtre, setFiltre] = useState('hepsi'); // 'hepsi' | 'kritik'

  const fetchIhbarlar = async () => {
    try {
      const r = await fetch('/requests/prioritized');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      // Sadece doğrulanmamışları al
      setIhbarlar(data.filter(i => !i.is_verified));
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchIhbarlar(); }, []);

  const handleDurum = async (id, yeniDurum) => {
    setIslemler(p => ({ ...p, [id]: 'loading' }));
    try {
      const r = await fetch(`/requests/${id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: yeniDurum }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setIslemler(p => ({ ...p, [id]: 'done' }));
      // Listeden kaldır
      setTimeout(() => {
        setIhbarlar(p => p.filter(i => i.id !== id));
        setIslemler(p => { const n = { ...p }; delete n[id]; return n; });
      }, 800);
    } catch (e) {
      setIslemler(p => ({ ...p, [id]: 'error' }));
      setTimeout(() => setIslemler(p => { const n = { ...p }; delete n[id]; return n; }), 2000);
    }
  };

  const gorunenler = filtre === 'kritik'
    ? ihbarlar.filter(i => i.dynamic_priority_score >= 80)
    : ihbarlar;

  return (
    <div className="text-on-surface p-8 w-full relative overflow-y-auto">
      <div className="max-w-7xl mx-auto">

        {/* BAŞLIK */}
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-on-surface">Doğrulanmamış İhbarlar</h1>
            <p className="text-slate-400 mt-2 max-w-2xl">
              {loading ? 'Yükleniyor...' : `${ihbarlar.length} doğrulanmamış ihbar — deprem bölgesi dışından geldi`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex bg-surface-container p-1 rounded-xl">
              <button
                onClick={() => setFiltre('hepsi')}
                className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors ${filtre === 'hepsi' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'}`}
              >
                Tümü ({ihbarlar.length})
              </button>
              <button
                onClick={() => setFiltre('kritik')}
                className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors ${filtre === 'kritik' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'}`}
              >
                Yüksek Öncelik ({ihbarlar.filter(i => i.dynamic_priority_score >= 80).length})
              </button>
            </div>
            <button onClick={fetchIhbarlar} className="bg-surface-container-high p-2.5 rounded-xl border border-slate-700/30 hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined text-slate-300">refresh</span>
            </button>
          </div>
        </div>

        {/* HATA */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
            Backend bağlantı hatası: {error}
          </div>
        )}

        {/* YÜKLENİYOR */}
        {loading && <div className="text-center text-slate-400 py-16">Yükleniyor...</div>}

        {/* BOŞ DURUM */}
        {!loading && ihbarlar.length === 0 && !error && (
          <div className="text-center text-slate-400 py-16 bg-surface-container rounded-xl border border-slate-700/20">
            <span className="material-symbols-outlined text-4xl mb-3 block text-green-500">check_circle</span>
            Tüm ihbarlar doğrulanmış durumda.
          </div>
        )}

        {/* KARTLAR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {gorunenler.map((ihbar) => {
            const badge = PRIORITY_BADGE(ihbar.dynamic_priority_score);
            const durum = islemler[ihbar.id];
            return (
              <div
                key={ihbar.id}
                className={`bg-surface-container border border-slate-700/20 rounded-xl p-6 transition-all relative overflow-hidden ${durum === 'done' ? 'opacity-40 scale-95' : ''}`}
              >
                <div className="flex justify-between items-start mb-6">
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20">
                      <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase tracking-widest block mb-1">
                        Puan: {ihbar.dynamic_priority_score}
                      </span>
                      <h3 className="text-lg font-bold text-on-surface">
                        {NEED_LABELS[ihbar.need_type] || ihbar.need_type}
                      </h3>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-[10px] font-bold uppercase tracking-tighter rounded-full border ${badge.cls}`}>
                    {badge.label}
                  </span>
                </div>

                <div className="space-y-3 mb-6">
                  <div className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-slate-400 text-lg">location_on</span>
                    <span className="text-sm font-medium text-slate-300">
                      {ihbar.latitude?.toFixed(4)}, {ihbar.longitude?.toFixed(4)}
                    </span>
                  </div>
                  {ihbar.description && (
                    <div className="flex items-start gap-3">
                      <span className="material-symbols-outlined text-slate-400 text-lg">description</span>
                      <p className="text-sm text-slate-400 leading-relaxed">{ihbar.description}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-slate-400 text-lg">schedule</span>
                    <span className="text-xs text-slate-400">
                      {new Date(ihbar.created_at).toLocaleString('tr-TR')}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-slate-400 text-lg">person</span>
                    <span className="text-xs text-slate-400">{ihbar.person_count ?? 1} kişi etkilendi</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-4 border-t border-slate-700/30">
                  {durum === 'loading' ? (
                    <div className="flex-1 text-center text-slate-400 text-sm">İşleniyor...</div>
                  ) : durum === 'done' ? (
                    <div className="flex-1 text-center text-green-400 text-sm font-bold">✓ Tamamlandı</div>
                  ) : durum === 'error' ? (
                    <div className="flex-1 text-center text-red-400 text-sm">Hata oluştu</div>
                  ) : (
                    <>
                      <button
                        onClick={() => handleDurum(ihbar.id, 'assigned')}
                        className="flex-1 py-2.5 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-bold flex items-center justify-center gap-2 transition-all"
                      >
                        <span className="material-symbols-outlined text-lg">check_circle</span> Doğrula
                      </button>
                      <button
                        onClick={() => handleDurum(ihbar.id, 'resolved')}
                        className="flex-1 py-2.5 bg-surface-container-high hover:bg-red-500/10 hover:text-red-500 text-slate-300 rounded-lg text-sm font-bold flex items-center justify-center gap-2 transition-all border border-slate-700/30"
                      >
                        <span className="material-symbols-outlined text-lg">cancel</span> Reddet
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* DAHA FAZLA */}
        {!loading && gorunenler.length > 0 && (
          <div className="mt-12 flex justify-center pb-12">
            <button
              onClick={fetchIhbarlar}
              className="group flex items-center gap-2 px-8 py-3 bg-surface-container hover:bg-surface-container-high border border-slate-700/30 rounded-xl transition-all"
            >
              <span className="text-sm font-bold uppercase tracking-widest text-slate-400 group-hover:text-on-surface">Yenile</span>
              <span className="material-symbols-outlined text-slate-400 group-hover:text-on-surface">refresh</span>
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
