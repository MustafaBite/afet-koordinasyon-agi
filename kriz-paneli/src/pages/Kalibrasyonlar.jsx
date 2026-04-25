import { useState } from 'react';

const NEED_TYPES = [
  { value: 'arama_kurtarma', label: 'Arama Kurtarma', baseScore: 100 },
  { value: 'medikal', label: 'Medikal', baseScore: 95 },
  { value: 'yangin', label: 'Yangın', baseScore: 90 },
  { value: 'enkaz', label: 'Enkaz', baseScore: 80 },
  { value: 'su', label: 'Su', baseScore: 60 },
  { value: 'barinma', label: 'Barınma (Çadır)', baseScore: 50 },
  { value: 'gida', label: 'Gıda', baseScore: 40 },
  { value: 'is_makinesi', label: 'İş Makinesi', baseScore: 35 },
  { value: 'ulasim', label: 'Ulaşım', baseScore: 25 },
];

const CONTEXT_BONUSES_INFO = [
  { name: 'soguk_hava', label: 'Soğuk Hava (< 0°C)', value: 30, color: 'blue' },
  { name: 'asiri_sicak', label: 'Aşırı Sıcak (> 35°C)', value: 15, color: 'red' },
  { name: 'arac_yok', label: 'Bölgede Araç Yok', value: 20, color: 'amber' },
  { name: 'yagisli_hava', label: 'Yağışlı Hava', value: 10, color: 'cyan' },
  { name: 'gece_vakti', label: 'Gece Operasyonu', value: 5, color: 'purple' },
];

const PRESET_SCENARIOS = [
  {
    title: 'Klasik: Çadır + Donma + Araç Yok',
    description: 'Barınma talebi, soğuk havada, bölgede araç bulunamadı',
    data: {
      need_type: 'barinma',
      wait_hours: 2,
      temperature_celsius: -5,
      vehicles_within_radius: 0,
      is_raining: false,
      is_night: false,
    },
  },
  {
    title: 'Yaz Sıcağında Su',
    description: '40°C sıcaklıkta su talebi',
    data: {
      need_type: 'su',
      wait_hours: 6,
      temperature_celsius: 40,
      vehicles_within_radius: 2,
      is_raining: false,
      is_night: false,
    },
  },
  {
    title: 'Gece Medikal Acil',
    description: 'Gece vakti, yağmurlu, kanamalı yaralı',
    data: {
      need_type: 'medikal',
      wait_hours: 0.5,
      temperature_celsius: 8,
      vehicles_within_radius: 1,
      is_raining: true,
      is_night: true,
    },
  },
  {
    title: 'Bekleyen Gıda Talebi',
    description: '24 saat bekleyen gıda talebi (queue starvation)',
    data: {
      need_type: 'gida',
      wait_hours: 24,
      temperature_celsius: 12,
      vehicles_within_radius: 3,
      is_raining: false,
      is_night: false,
    },
  },
];

export default function Kalibrasyonlar() {
  const [scenario, setScenario] = useState({
    need_type: 'barinma',
    wait_hours: 2,
    temperature_celsius: -5,
    vehicles_within_radius: 0,
    is_raining: false,
    is_night: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        'http://127.0.0.1:8000/requests/task-packages/priority-simulate',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            need_type: scenario.need_type,
            wait_hours: parseFloat(scenario.wait_hours) || 0,
            temperature_celsius:
              scenario.temperature_celsius === '' ||
              scenario.temperature_celsius === null
                ? null
                : parseFloat(scenario.temperature_celsius),
            vehicles_within_radius:
              scenario.vehicles_within_radius === '' ||
              scenario.vehicles_within_radius === null
                ? null
                : parseInt(scenario.vehicles_within_radius, 10),
            is_raining: !!scenario.is_raining,
            is_night: !!scenario.is_night,
          }),
        }
      );

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        const err = await res.json();
        setError(err.detail || 'Simülasyon başarısız');
        setResult(null);
      }
    } catch (e) {
      setError('Bağlantı hatası: ' + e.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (preset) => {
    setScenario(preset.data);
    setResult(null);
  };

  const update = (field, value) => {
    setScenario((prev) => ({ ...prev, [field]: value }));
  };

  const scoreColor = (score) => {
    if (score >= 80) return 'text-red-500';
    if (score >= 60) return 'text-orange-500';
    if (score >= 40) return 'text-amber-500';
    return 'text-slate-400';
  };

  const scoreLabel = (score) => {
    if (score >= 75) return 'KRİTİK';
    if (score >= 50) return 'YÜKSEK';
    if (score >= 25) return 'ORTA';
    return 'DÜŞÜK';
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-zinc-900">
      <div>
        <h1 className="text-2xl font-black text-white mb-1">
          🎚️ Puanlama Kalibrasyonu
        </h1>
        <p className="text-sm text-slate-400">
          Aciliyet algoritmasını farklı senaryolarda test et ve ağırlıkları
          doğrula
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SOL: Senaryo Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Hazır Senaryolar */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h2 className="text-sm font-bold text-white mb-3">
              ⚡ Hazır Senaryolar
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {PRESET_SCENARIOS.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => loadPreset(preset)}
                  className="text-left p-3 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-all"
                >
                  <p className="text-xs font-bold text-orange-400">
                    {preset.title}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {preset.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-white">
              🧪 Özel Senaryo Oluştur
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  İhtiyaç Tipi
                </label>
                <select
                  value={scenario.need_type}
                  onChange={(e) => update('need_type', e.target.value)}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700 focus:border-blue-500 focus:outline-none"
                >
                  {NEED_TYPES.map((nt) => (
                    <option key={nt.value} value={nt.value}>
                      {nt.label} (taban: {nt.baseScore})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Bekleme Süresi (saat)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={scenario.wait_hours}
                  onChange={(e) => update('wait_hours', e.target.value)}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Sıcaklık (°C)
                  <span className="text-slate-500 ml-1">— boş bırak: yok</span>
                </label>
                <input
                  type="number"
                  step="1"
                  value={scenario.temperature_celsius ?? ''}
                  onChange={(e) =>
                    update(
                      'temperature_celsius',
                      e.target.value === '' ? null : e.target.value
                    )
                  }
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  10 km İçindeki Araç Sayısı
                </label>
                <input
                  type="number"
                  min="0"
                  value={scenario.vehicles_within_radius ?? ''}
                  onChange={(e) =>
                    update(
                      'vehicles_within_radius',
                      e.target.value === '' ? null : e.target.value
                    )
                  }
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex gap-6 pt-2">
              <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={scenario.is_raining}
                  onChange={(e) => update('is_raining', e.target.checked)}
                  className="w-4 h-4 accent-blue-500"
                />
                🌧️ Yağışlı
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={scenario.is_night}
                  onChange={(e) => update('is_night', e.target.checked)}
                  className="w-4 h-4 accent-blue-500"
                />
                🌙 Gece
              </label>
            </div>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="w-full mt-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-sm font-bold py-3 rounded-lg transition-all shadow-md"
            >
              {loading ? '🧮 Hesaplanıyor...' : '🚀 SENARYOYU ÇALIŞTIR'}
            </button>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs px-3 py-2 rounded-lg">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* SAĞ: Sonuç + Bonus Listesi */}
        <div className="space-y-6">
          {/* Sonuç Kartı */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h2 className="text-sm font-bold text-white mb-3">📊 Sonuç</h2>
            {result ? (
              <div className="space-y-4">
                <div className="text-center py-4 bg-slate-800/50 rounded-xl">
                  <p className="text-xs text-slate-400 uppercase font-bold">
                    Final Aciliyet Skoru
                  </p>
                  <p className={`text-6xl font-black ${scoreColor(result.final_score)}`}>
                    {result.final_score}
                  </p>
                  <p className="text-xs font-bold text-slate-300 tracking-wider">
                    {scoreLabel(result.final_score)} ÖNCELİK
                  </p>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Temel Puan (Taban + Zaman):</span>
                    <span className="font-bold text-white">
                      {result.base_score}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Bağlamsal Bonus:</span>
                    <span className="font-bold text-orange-400">
                      +{result.context_bonus}
                    </span>
                  </div>
                  <div className="border-t border-slate-700 pt-1.5 flex justify-between">
                    <span className="text-slate-300 font-medium">Toplam:</span>
                    <span className={`font-black ${scoreColor(result.final_score)}`}>
                      {result.final_score} / 100
                    </span>
                  </div>
                </div>

                {result.applied_bonuses?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold text-slate-500 uppercase mb-1.5">
                      Uygulanan Bonuslar
                    </p>
                    <div className="space-y-1.5">
                      {result.applied_bonuses.map((b, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-orange-500/10 border border-orange-500/20 rounded p-2 text-xs"
                        >
                          <div className="flex-1">
                            <p className="font-bold text-orange-300">{b.name}</p>
                            <p className="text-[10px] text-slate-400">
                              {b.detail}
                            </p>
                          </div>
                          <span className="font-black text-orange-400 ml-2">
                            +{b.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-xs text-slate-500 py-8">
                Bir senaryo çalıştır — sonuç burada görüntülenir.
              </div>
            )}
          </div>

          {/* Tüm Bonus Tablosu */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h2 className="text-sm font-bold text-white mb-3">
              📚 Bonus Tablosu
            </h2>
            <div className="space-y-2">
              {CONTEXT_BONUSES_INFO.map((b) => (
                <div
                  key={b.name}
                  className="flex justify-between items-center text-xs bg-slate-800/50 rounded px-3 py-2"
                >
                  <span className="text-slate-300">{b.label}</span>
                  <span className="font-bold text-orange-400">+{b.value}</span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-slate-500 mt-3 italic">
              Bonuslar final skora mutlak olarak eklenir, üst sınır 100'dür.
              İhtiyaç tipine göre çarpan etkisi de uygulanabilir (örn: barınma ×
              soğuk hava = 1.5x).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
