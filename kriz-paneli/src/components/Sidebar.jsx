import { USER_ROLES } from '../constants/formOptions';

export default function Sidebar({ user }) {
  const userRole = user ? USER_ROLES[user.role] : 'Kullanıcı';
  const userName = user ? `${user.first_name} ${user.last_name}` : 'Kullanıcı';
  const userPhoto = user?.profile_photo_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=136dec&color=fff`;
  
  return (
    <aside className="w-72 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col shrink-0 h-screen">
      <div className="p-6 flex items-center gap-4">
        <div className="afad-logo-container">
          <span className="afad-text text-3xl text-afad-blue dark:text-white">AFAD</span>
          <div className="turk-flag-circle"></div>
        </div>
        <div className="ml-2">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Kriz Yönetimi</p>
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-4 space-y-1">
        <a className="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary text-white font-medium transition-all" href="#">
          <span className="material-symbols-outlined">warning</span>
          <span>Aktif İhbarlar</span>
        </a>
        <a className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 font-medium transition-all" href="#">
          <span className="material-symbols-outlined">map</span>
          <span>Harita Görünümü</span>
        </a>
        <a className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 font-medium transition-all" href="#">
          <span className="material-symbols-outlined">groups</span>
          <span>Ekipler</span>
        </a>
        <a className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 font-medium transition-all" href="#">
          <span className="material-symbols-outlined">pending_actions</span>
          <span>Doğrulanmamışlar</span>
          <span className="ml-auto bg-emergency-red text-white text-[10px] px-2 py-0.5 rounded-full">12</span>
        </a>
      </nav>

      <div className="p-4 mt-auto border-t border-slate-200 dark:border-slate-800">
        <a className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 font-medium transition-all" href="#">
          <span className="material-symbols-outlined">settings</span>
          <span>Ayarlar</span>
        </a>
        <div className="mt-4 p-4 rounded-xl bg-slate-200 dark:bg-slate-800 flex items-center gap-3">
          <div className="size-8 rounded-full bg-slate-400 overflow-hidden">
            <img alt={userName} className="w-full h-full object-cover" src={userPhoto} />
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-semibold truncate">{userName}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{userRole}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}