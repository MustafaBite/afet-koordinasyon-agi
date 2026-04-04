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
import { authService } from './services/authService';

function App() {
  // --- KULLANICI VE GİRİŞ DURUMU YÖNETİMİ ---
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState('Login'); // Sadece giriş yapılmadıysa 'login' veya 'register'

  // --- ARAYÜZ (MENÜ) DURUMU YÖNETİMİ (Senin Kodun) ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("aktif");

  // Sayfa yüklendiğinde token kontrolü (Backend bağlantısı)
  useEffect(() => {
    const token = authService.getToken();
    const savedUser = authService.getUser();
    
    if (token && savedUser) {
      setUser(savedUser);
      setActiveTab('aktif'); // Giriş başarılıysa varsayılan olarak Dashboard'u aç
    }
  }, []);

  // --- YETKİLENDİRME FONKSİYONLARI ---
  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setActiveTab('aktif');
  };

  const handleRegisterSuccess = (userData) => {
    setUser(userData);
    setActiveTab('aktif');
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
        <Login
          onLoginSuccess={handleLoginSuccess}
          onSwitchToRegister={() => setAuthView('Register')}
        />
      );
    }
    if (authView === 'Register') {
      return (
        <Register
          onRegisterSuccess={handleRegisterSuccess}
          onSwitchToLogin={() => setAuthView('Login')}
        />
      );
    }
  }

  // --- KULLANICI GİRİŞ YAPMIŞSA (Ana Panel Arayüzü) ---
  return (
    <div className="flex h-screen overflow-hidden">
      
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
        />
        
        {/* İÇERİK BÖLÜMÜ: Sol menüden hangi sekmeye tıklandıysa o ekran */}
        {activeTab === "aktif" && <Dashboard />}
        {activeTab === "kumeler" && <Kumeler />}
        {activeTab === "harita" && <HaritaGorunumu />}
        {activeTab === "ekipler" && <Ekipler />}
        {activeTab === 'dogrulanmamislar' && <Dogrulanmamisİhbarlar />}
        
        {/* Profil sayfası eklemesi (Üstten profile tıklandığında menüden tetiklenebilir) */}
        {activeTab === 'profile' && <Profile user={user} onUpdateSuccess={handleProfileUpdate} />}
        
      </main>
    </div>
  );
}

export default App;