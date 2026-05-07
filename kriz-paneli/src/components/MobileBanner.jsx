import { useState } from 'react';

const APK_URL = 'https://qr.bilalabic.com/afet-apk';
const DISMISS_KEY = 'resq_mobile_banner_dismissed';

function isMobile() {
  return (
    /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
    window.innerWidth < 768
  );
}

export default function MobileBanner() {
  // Lazy init — ilk render'da zaten doğru değerle başlar, flash olmaz
  const [visible, setVisible] = useState(
    () => isMobile() && !sessionStorage.getItem(DISMISS_KEY)
  );

  const dismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, '1');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">

        {/* Başlık */}
        <div className="flex items-center gap-3 px-5 py-4 bg-slate-800 dark:bg-slate-950">
          <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-white text-xl">smartphone</span>
          </div>
          <div className="flex-1">
            <p className="text-white font-bold text-sm">RESQ Mobil Uygulama</p>
            <p className="text-slate-400 text-xs mt-0.5">Android için ücretsiz</p>
          </div>
          <button
            onClick={dismiss}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1"
            aria-label="Kapat"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* İçerik */}
        <div className="px-5 py-4">
          {/* Uyarı */}
          <div className="flex items-start gap-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-xl p-3 mb-4">
            <span className="material-symbols-outlined text-amber-500 text-lg mt-0.5 shrink-0">info</span>
            <p className="text-amber-800 dark:text-amber-300 text-xs leading-relaxed">
              Bu panel <span className="font-semibold">masaüstü koordinatörler</span> için tasarlanmıştır.
              Afet bildirimi yapmak için mobil uygulamamızı kullanın.
            </p>
          </div>

          {/* Özellikler */}
          <ul className="space-y-2 mb-5">
            {[
              ['location_on', 'GPS ile anlık konum tespiti'],
              ['add_alert',   '4 adımda hızlı yardım talebi'],
              ['wifi_off',    'Çevrimdışı mod — internet kesilse bile çalışır'],
            ].map(([icon, text]) => (
              <li key={icon} className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300 text-xs">
                <span className="material-symbols-outlined text-sm text-red-600">
                  {icon}
                </span>
                {text}
              </li>
            ))}
          </ul>

          {/* İndir butonu */}
          <a
            href={APK_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-semibold text-sm transition-colors"
            onClick={dismiss}
          >
            <span className="material-symbols-outlined text-lg">download</span>
            Mobil Uygulamayı İndir
          </a>

          <button
            onClick={dismiss}
            className="w-full mt-2 py-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 text-xs transition-colors"
          >
            Yine de masaüstü versiyonu kullan
          </button>
        </div>
      </div>
    </div>
  );
}
