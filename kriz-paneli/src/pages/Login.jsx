import { useState } from 'react';
import { authService } from '../services/authService';
import { validateEmail, validateRequired } from '../utils/validation';
import Input from '../components/common/Input';
import Button from '../components/common/Button';

export default function Login({ onLoginSuccess, onSwitchToRegister }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Kullanıcı yazmaya başladığında hatayı temizle
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
    setApiError(null);
  };

  const validateForm = () => {
    const newErrors = {};
    
    const emailError = validateEmail(formData.email);
    if (emailError) newErrors.email = emailError;
    
    const passwordError = validateRequired(formData.password, 'Şifre');
    if (passwordError) newErrors.password = passwordError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setApiError(null);

    try {
      const response = await authService.login({
        email: formData.email,
        password: formData.password
      });

      authService.saveToken(response.access_token);
      authService.saveUser(response.user);
      
      onLoginSuccess(response.user);
    } catch (error) {
      console.error('Login error:', error);
      setApiError(error.message || 'Giriş sırasında bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        
        {/* Logo ve Başlık */}
        <div className="text-center mb-8">
          {/* RESQ LOGOSU */}
          <div className="flex flex-col items-center justify-center select-none scale-[0.65] origin-center mb-4">
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
          
          <h1 className="text-2xl font-bold mb-2">Kriz Yönetim Sistemi</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Hesabınıza giriş yapın
          </p>
        </div>

        {/* Form Kartı */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8">
          
          {apiError && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">error</span>
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="E-posta Adresi"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="ornek@email.com"
              required
              icon="mail"
              autoComplete="email"
            />

            <Input
              label="Şifre"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              placeholder="••••••••"
              required
              icon="lock"
              autoComplete="current-password"
            />

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={loading}
              icon="login"
            >
              Giriş Yap
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Hesabınız yok mu?{' '}
              <button
                onClick={onSwitchToRegister}
                className="text-primary font-semibold hover:underline"
              >
                Kayıt Ol
              </button>
            </p>
          </div>
        </div>

        {/* Alt Bilgi */}
        <p className="text-center text-xs text-slate-500 dark:text-slate-400 mt-6">
          © 2026 RESQ - Afet ve Acil Durum Yönetimi Sistemi
        </p>
      </div>
    </div>
  );
}
