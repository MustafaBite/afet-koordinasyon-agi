import { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import { authService } from './services/authService';

function App() {
  const [currentView, setCurrentView] = useState('login'); // 'login', 'register', 'dashboard', 'profile'
  const [user, setUser] = useState(null);

  // Sayfa yüklendiğinde token kontrolü
  useEffect(() => {
    const token = authService.getToken();
    const savedUser = authService.getUser();
    
    if (token && savedUser) {
      setUser(savedUser);
      setCurrentView('dashboard');
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setCurrentView('dashboard');
  };

  const handleRegisterSuccess = (userData) => {
    setUser(userData);
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentView('login');
  };

  const handleProfileUpdate = (updatedUser) => {
    setUser(updatedUser);
  };

  // Login sayfası
  if (currentView === 'login') {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToRegister={() => setCurrentView('register')}
      />
    );
  }

  // Register sayfası
  if (currentView === 'register') {
    return (
      <Register
        onRegisterSuccess={handleRegisterSuccess}
        onSwitchToLogin={() => setCurrentView('login')}
      />
    );
  }

  // Dashboard veya Profile (giriş yapılmışsa)
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar user={user} currentView={currentView} onNavigate={setCurrentView} />
      
      <main className="flex-1 flex flex-col overflow-hidden bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100">
        <Header user={user} onLogout={handleLogout} />
        
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'profile' && <Profile user={user} onUpdateSuccess={handleProfileUpdate} />}
      </main>
    </div>
  );
}

export default App;