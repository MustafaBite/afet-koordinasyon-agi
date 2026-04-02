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
      setApiError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        
        {/* Logo ve Başlık */}
        <div className="text-center mb-8">
          <div className="afad-logo-container scale-125 justify-center mb-4">
            <span className="afad-text text-4xl text-afad-blue dark:text-white">AFAD</span>
            <div className="turk-flag-circle"></div>
          </div>
          <h1 className="text-2xl font-bold mt-6 mb-2">Kriz Yönetim Sistemi</h1>
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
          © 2026 AFAD - Afet ve Acil Durum Yönetimi Başkanlığı
        </p>
      </div>
    </div>
  );
}
