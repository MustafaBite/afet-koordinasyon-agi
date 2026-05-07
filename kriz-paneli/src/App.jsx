import { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import Kumeler from './Kumeler';
import HaritaGorunumu from './HaritaGorunumu';
import Ekipler from './Ekipler';
import Dogrulanmamisİhbarlar from "./Dogrulanmamisİhbarlar.jsx";
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Kalibrasyonlar from './pages/Kalibrasyonlar';
import { authService } from './services/authService';
import MobileBanner from './components/MobileBanner';

const ROLE_TABS = {
  admin:       ['aktif', 'kumeler', 'harita', 'ekipler', 'kalibrasyon', 'dogrulanmamislar', 'profile'],
  coordinator: ['aktif', 'kumeler', 'harita', 'ekipler', 'dogrulanmamislar', 'profile'],
  volunteer:   ['aktif', 'harita', 'profile'],
  citizen:     ['profile'],
};

const canAccessTab = (role, tab) => (ROLE_TABS[role] ?? ROLE_TABS.citizen).includes(tab);

const defaultTabForRole = (role) => role === 'citizen' ? 'profile' : 'aktif';

function AccessDenied() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-400 dark:text-slate-500">
      <span className="material-symbols-outlined text-6xl">lock</span>
      <h2 className="text-xl font-semibold text-slate-600 dark:text-slate-300">Erişim Kısıtlı</h2>
      <p className="text-sm">Bu sayfayı görüntülemek için yeterli yetkiniz yok.</p>
    </div>
  );
}

function App() {
  // --- KULLANICI VE GİRİŞ DURUMU YÖNETİMİ ---
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState('Login'); // Sadece giriş yapılmadıysa 'login' veya 'register'

  // --- ARAYÜZ (MENÜ) DURUMU YÖNETİMİ (Senin Kodun) ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("aktif");

  // Sayfa yüklendiğinde token kontrolü (Backend bağlantısı)
  useEffect(() => {
    const checkAuth = async () => {
      const token = authService.getToken();
      const savedUser = authService.getUser();
      
      if (token && savedUser) {
        try {
          // Token'ın geçerliliğini kontrol et
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          setActiveTab(defaultTabForRole(currentUser.role));
        } catch (error) {
          // Token geçersizse logout yap
          console.error('Token doğrulama hatası:', error);
          authService.logout();
          setUser(null);
          setAuthView('Login');
        }
      }
    };

    checkAuth();
  }, []);

  // --- YETKİLENDİRME FONKSİYONLARI ---
  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setActiveTab(defaultTabForRole(userData.role));
  };

  const handleRegisterSuccess = (userData) => {
    setUser(userData);
    setActiveTab(defaultTabForRole(userData.role));
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setAuthView('Login');
  };

  const handleProfileUpdate = (updatedUser) => {
    setUser(updatedUser);
  };

  // --- KULLANICI GİRİŞ YAPMAMIŞSA (Giriş / Kayıt Ekranları) ---
  if (!user) {
    if (authView === 'Login') {
      return (
        <>
          <MobileBanner />
          <Login
            onLoginSuccess={handleLoginSuccess}
            onSwitchToRegister={() => setAuthView('Register')}
          />
        </>
      );
    }
    if (authView === 'Register') {
      return (
        <>
          <MobileBanner />
          <Register
            onRegisterSuccess={handleRegisterSuccess}
            onSwitchToLogin={() => setAuthView('Login')}
          />
        </>
      );
    }
  }

  // --- KULLANICI GİRİŞ YAPMIŞSA (Ana Panel Arayüzü) ---
  return (
    <div className="flex h-screen overflow-hidden">
      <MobileBanner />
      
      {/* SOL MENÜ: Senin propların + kimlik bilgisi */}
      <Sidebar 
        isOpen={isSidebarOpen} 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        user={user}
      />
      
      {/* SAĞ TARAF: Ana İçerik Alanı */}
      <main className="flex-1 flex flex-col overflow-hidden bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100">
        
        {/* Üst Çubuk: Sidebar'ı aç/kapat, profili göster ve çıkış yap */}
        <Header 
          toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} 
          user={user} 
          onLogout={handleLogout}
          onProfileClick={() => setActiveTab('profile')}
        />
        
        {/* İÇERİK BÖLÜMÜ: rol kontrolü yapıldıktan sonra sekme render edilir */}
        {!canAccessTab(user?.role, activeTab) ? (
          <AccessDenied />
        ) : (
          <>
            {activeTab === "aktif" && <Dashboard />}
            {activeTab === "kumeler" && <Kumeler />}
            {activeTab === "harita" && <HaritaGorunumu />}
            {activeTab === "ekipler" && <Ekipler />}
            {activeTab === 'dogrulanmamislar' && <Dogrulanmamisİhbarlar />}
            {activeTab === 'kalibrasyon' && <Kalibrasyonlar />}
            {activeTab === 'profile' && <Profile user={user} onUpdateSuccess={handleProfileUpdate} />}
          </>
        )}
        
      </main>
    </div>
  );
}

export default App;