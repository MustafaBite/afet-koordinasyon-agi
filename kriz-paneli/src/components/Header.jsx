import React from 'react';

export default function Header({ toggleSidebar, user, onLogout }) {
  return (
    <header className="h-20 bg-white dark:bg-slate-900/50 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-8 shrink-0">
      
      {/* Sol Taraf: Menü Butonu + Logo + Başlık */}
      <div className="flex items-center gap-6">
        
        {/* Menü Butonu */}
        <button 
          onClick={toggleSidebar} 
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all active:scale-95"
          title="Menüyü Aç/Kapat"
        >
          <span className="material-symbols-outlined text-2xl flex items-center justify-center">menu</span>
        </button>

        {/* RESQ LOGOSU */}
        <div className="flex flex-col items-center justify-center select-none cursor-pointer scale-[0.50] origin-center -my-6 z-10">
            {/* Kalkan İkonu */}
            <div className="relative w-16 h-[72px] -mb-3 z-10">
                <div className="w-full h-full rounded-[20%_20%_50%_50%/10%_10%_40%_40%] bg-gradient-to-br from-slate-100 to-slate-300 dark:from-slate-200 dark:to-slate-400 border-[3px] border-slate-400 shadow-lg transform scale-y-105"></div>
                <svg className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-10 h-auto" viewBox="0 0 100 60">
                    <path d="M5,30 h35 L45,15 L50,45 L55,15 L60,30 h35" stroke="#1e293b" strokeWidth="6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </div>
            {/* RESQ Metni */}
            <div className="font-extrabold text-[55px] leading-none tracking-tighter flex items-baseline font-sans drop-shadow-sm">
                <span className="text-slate-800 dark:text-slate-100">RES</span><span className="text-red-600">Q</span>
            </div>
            {/* Alt Çizgi */}
            <div className="w-[120%] h-5 -mt-2 flex justify-center">
                <svg className="w-full h-full drop-shadow-md" viewBox="0 0 250 20">
                    <path d="M0,10 h185 L190,5 L195,15 L200,5 L205,10 h45" stroke="#dc2626" strokeWidth="6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </div>
        </div>

        {/* Dikey Ayırıcı */}
        <div className="h-10 w-px bg-slate-200 dark:bg-slate-700"></div>
        
        {/* Başlık ve Slogan */}
        <div className="flex flex-col justify-center gap-1">
            <h2 className="text-xl font-black tracking-tight text-slate-900 dark:text-white leading-tight">Kriz Merkezi Paneli</h2>
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 italic tracking-wide uppercase">
                &quot;Zamana Karşı Otonom Yarış&quot;
            </p>
        </div>
      </div>
      
      {/* Sağ Taraf: Arama ve Profil/Aksiyonlar */}
      <div className="flex items-center gap-6">
        
        {/* Arama */}
        <div className="relative group">
          <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
            <span className="material-symbols-outlined text-xl">search</span>
          </span>
          <input 
            className="w-80 pl-10 pr-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 border-none focus:ring-2 focus:ring-blue-500 text-sm placeholder:text-slate-500" 
            placeholder="İhbar no, bölge veya ekip ara..." 
            type="text"
          />
        </div>
        
        {/* --- YENİ EKLENEN PROFİL VE BUTONLAR KISMI --- */}
        <div className="flex items-center gap-4 border-l border-slate-200 dark:border-slate-800 pl-6">
          
          {/* Bildirim Zili */}
          <button className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 relative transition-all">
            <span className="material-symbols-outlined">notifications</span>
            <span className="absolute top-2 right-2 size-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-slate-900 animate-pulse"></span>
          </button>

          {/* Profil İsmi ve Ünvan (Dinamik hale getirildi) */}
          <div className="hidden md:flex flex-col items-end">
            <span className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
              {user && user.firstName ? `${user.firstName} ${user.lastName}` : "Zehra Dağaşan"}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wide">
              {user && user.role ? user.role : "Kriz Merkezi Yöneticisi"}
            </span>
          </div>

          {/* Profil Resmi */}
          <img 
            src={user && user.avatarUrl ? user.avatarUrl : "https://ui-avatars.com/api/?name=Zehra+Dağaşan&background=2563eb&color=fff&bold=true"} 
            alt="Profil" 
            className="h-10 w-10 rounded-full border-2 border-slate-200 dark:border-slate-700 shadow-sm cursor-pointer hover:border-blue-500 transition-colors" 
          />

          {/* Çıkış Yap Butonu */}
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 font-semibold text-sm transition-all ml-2"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            <span className="hidden sm:block">Çıkış</span>
          </button>
          
        </div>
        {/* --------------------------------------------- */}

      </div>

    </header>
  );
}