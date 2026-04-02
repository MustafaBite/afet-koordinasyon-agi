export default function Header({ user, onLogout }) {
  return (
    <header className="h-20 bg-white dark:bg-slate-900/50 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-8 shrink-0">
      
      {/* Sol Taraf: Logo ve Başlık */}
      <div className="flex items-center gap-6">
        <div className="afad-logo-container scale-90">
          <span className="afad-text text-2xl text-afad-blue dark:text-white">AFAD</span>
          <div className="turk-flag-circle"></div>
        </div>
        <div className="h-8 w-px bg-slate-200 dark:bg-slate-800"></div>
        <h2 className="text-xl font-bold tracking-tight">Kriz Merkezi Paneli</h2>
      </div>
      
      {/* Sağ Taraf: Arama ve Butonlar */}
      <div className="flex items-center gap-6">
        <div className="relative group">
          <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
            <span className="material-symbols-outlined text-xl">search</span>
          </span>
          <input className="w-80 pl-10 pr-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 border-none focus:ring-2 focus:ring-primary text-sm placeholder:text-slate-500" placeholder="İhbar no, bölge veya ekip ara..." type="text"/>
        </div>
        
        <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-6">
          <button className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 relative">
            <span className="material-symbols-outlined">notifications</span>
            <span className="absolute top-2 right-2 size-2 bg-emergency-red rounded-full ring-2 ring-white dark:ring-slate-900"></span>
          </button>
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 font-semibold text-sm"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            <span>Çıkış Yap</span>
          </button>
        </div>
      </div>

    </header>
  );
}