import { useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { 
  validateEmail, 
  validatePassword, 
  validatePhone, 
  validateTCIdentity, 
  validateRequired,
  validateURL 
} from '../utils/validation';
import { USER_ROLES, EXPERTISE_AREAS, CITIES_DISTRICTS } from '../constants/formOptions';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import Button from '../components/common/Button';

export default function Register({ onRegisterSuccess, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    tc_identity_no: '',
    phone: '',
    role: '',
    expertise_area: '',
    organization: '',
    city: '',
    district: '',
    profile_photo_url: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [availableDistricts, setAvailableDistricts] = useState({});

  // Şehir değiştiğinde ilçeleri güncelle
  useEffect(() => {
    if (formData.city) {
      setAvailableDistricts(
        CITIES_DISTRICTS[formData.city]?.reduce((acc, district) => {
          acc[district] = district;
          return acc;
        }, {}) || {}
      );
      // Şehir değiştiğinde ilçeyi sıfırla
      setFormData(prev => ({ ...prev, district: '' }));
    }
  }, [formData.city]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
    setApiError(null);
  };

  const validateForm = () => {
    const newErrors = {};
    
    // Temel bilgiler
    const emailError = validateEmail(formData.email);
    if (emailError) newErrors.email = emailError;
    
    const passwordError = validatePassword(formData.password);
    if (passwordError) newErrors.password = passwordError;
    
    if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'Şifreler eşleşmiyor';
    }
    
    // Kişisel bilgiler
    const firstNameError = validateRequired(formData.first_name, 'Ad');
    if (firstNameError) newErrors.first_name = firstNameError;
    
    const lastNameError = validateRequired(formData.last_name, 'Soyad');
    if (lastNameError) newErrors.last_name = lastNameError;
    
    const tcError = validateTCIdentity(formData.tc_identity_no);
    if (tcError) newErrors.tc_identity_no = tcError;
    
    const phoneError = validatePhone(formData.phone);
    if (phoneError) newErrors.phone = phoneError;
    
    // Rol
    const roleError = validateRequired(formData.role, 'Rol');
    if (roleError) newErrors.role = roleError;
    
    // Uzmanlık ve organizasyon (volunteer/coordinator için zorunlu)
    const needsExpertise = ['volunteer', 'coordinator'].includes(formData.role);
    if (needsExpertise) {
      const expertiseError = validateRequired(formData.expertise_area, 'Uzmanlık Alanı');
      if (expertiseError) newErrors.expertise_area = expertiseError;
      
      const orgError = validateRequired(formData.organization, 'Organizasyon');
      if (orgError) newErrors.organization = orgError;
    }
    
    // Lokasyon
    const cityError = validateRequired(formData.city, 'Şehir');
    if (cityError) newErrors.city = cityError;
    
    const districtError = validateRequired(formData.district, 'İlçe');
    if (districtError) newErrors.district = districtError;
    
    // Profil fotoğrafı (opsiyonel)
    if (formData.profile_photo_url) {
      const urlError = validateURL(formData.profile_photo_url);
      if (urlError) newErrors.profile_photo_url = urlError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setApiError(null);

    try {
      // password_confirm'i backend'e gönderme
      const { password_confirm, ...dataToSend } = formData;
      
      const response = await authService.register(dataToSend);

      authService.saveToken(response.access_token);
      authService.saveUser(response.user);
      
      onRegisterSuccess(response.user);
    } catch (error) {
      setApiError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const needsExpertise = ['volunteer', 'coordinator'].includes(formData.role);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4 py-12">
      <div className="w-full max-w-4xl">
        
        {/* Logo ve Başlık */}
        <div className="text-center mb-8">
          <div className="afad-logo-container scale-125 justify-center mb-4">
            <span className="afad-text text-4xl text-afad-blue dark:text-white">AFAD</span>
            <div className="turk-flag-circle"></div>
          </div>
          <h1 className="text-2xl font-bold mt-6 mb-2">Kriz Yönetim Sistemi</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Yeni hesap oluşturun
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

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Temel Bilgiler */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">account_circle</span>
                Temel Bilgiler
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  label="Telefon"
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  error={errors.phone}
                  placeholder="05xxxxxxxxx"
                  required
                  icon="phone"
                  autoComplete="tel"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Şifre"
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  error={errors.password}
                  placeholder="En az 8 karakter"
                  required
                  icon="lock"
                  autoComplete="new-password"
                />

                <Input
                  label="Şifre Tekrar"
                  type="password"
                  name="password_confirm"
                  value={formData.password_confirm}
                  onChange={handleChange}
                  error={errors.password_confirm}
                  placeholder="Şifrenizi tekrar girin"
                  required
                  icon="lock"
                  autoComplete="new-password"
                />
              </div>
            </div>

            {/* Kişisel Bilgiler */}
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">badge</span>
                Kişisel Bilgiler
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Ad"
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  error={errors.first_name}
                  placeholder="Adınız"
                  required
                  icon="person"
                  autoComplete="given-name"
                />

                <Input
                  label="Soyad"
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  error={errors.last_name}
                  placeholder="Soyadınız"
                  required
                  icon="person"
                  autoComplete="family-name"
                />

                <Input
                  label="TC Kimlik No"
                  type="text"
                  name="tc_identity_no"
                  value={formData.tc_identity_no}
                  onChange={handleChange}
                  error={errors.tc_identity_no}
                  placeholder="11 haneli"
                  required
                  icon="fingerprint"
                />
              </div>
            </div>

            {/* Rol ve Yetki */}
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">shield</span>
                Rol ve Yetki
              </h3>
              
              <Select
                label="Rol"
                name="role"
                value={formData.role}
                onChange={handleChange}
                options={USER_ROLES}
                error={errors.role}
                placeholder="Rolünüzü seçin"
                required
                icon="admin_panel_settings"
              />

              {needsExpertise && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Select
                    label="Uzmanlık Alanı"
                    name="expertise_area"
                    value={formData.expertise_area}
                    onChange={handleChange}
                    options={EXPERTISE_AREAS}
                    error={errors.expertise_area}
                    placeholder="Uzmanlık alanınızı seçin"
                    required
                    icon="medical_services"
                  />

                  <Input
                    label="Organizasyon/Kurum"
                    type="text"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    error={errors.organization}
                    placeholder="Örn: Kızılay, AFAD"
                    required
                    icon="business"
                  />
                </div>
              )}
            </div>

            {/* Lokasyon */}
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">location_on</span>
                Lokasyon
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Şehir"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  options={Object.keys(CITIES_DISTRICTS).reduce((acc, city) => {
                    acc[city] = city;
                    return acc;
                  }, {})}
                  error={errors.city}
                  placeholder="Şehir seçin"
                  required
                  icon="location_city"
                />

                <Select
                  label="İlçe"
                  name="district"
                  value={formData.district}
                  onChange={handleChange}
                  options={availableDistricts}
                  error={errors.district}
                  placeholder={formData.city ? "İlçe seçin" : "Önce şehir seçin"}
                  required
                  icon="map"
                />
              </div>
            </div>

            {/* Profil Fotoğrafı */}
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">image</span>
                Profil Fotoğrafı (Opsiyonel)
              </h3>
              
              <Input
                label="Profil Fotoğrafı URL"
                type="url"
                name="profile_photo_url"
                value={formData.profile_photo_url}
                onChange={handleChange}
                error={errors.profile_photo_url}
                placeholder="https://example.com/photo.png"
                icon="link"
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Sadece PNG formatında resim linki kabul edilir
              </p>
            </div>

            {/* Butonlar */}
            <div className="flex gap-4 pt-6">
              <Button
                type="button"
                variant="ghost"
                onClick={onSwitchToLogin}
                fullWidth
              >
                Geri Dön
              </Button>
              
              <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={loading}
                icon="person_add"
              >
                Kayıt Ol
              </Button>
            </div>
          </form>
        </div>

        {/* Alt Bilgi */}
        <p className="text-center text-xs text-slate-500 dark:text-slate-400 mt-6">
          © 2026 AFAD - Afet ve Acil Durum Yönetimi Başkanlığı
        </p>
      </div>
    </div>
  );
}
