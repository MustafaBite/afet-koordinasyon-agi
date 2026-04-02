import { useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { 
  validatePhone, 
  validateRequired,
  validateURL 
} from '../utils/validation';
import { USER_ROLES, EXPERTISE_AREAS, CITIES_DISTRICTS } from '../constants/formOptions';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import Button from '../components/common/Button';

export default function Profile({ user, onUpdateSuccess }) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    expertise_area: '',
    organization: '',
    city: '',
    district: '',
    profile_photo_url: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [availableDistricts, setAvailableDistricts] = useState({});

  // User bilgilerini form'a yükle
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        expertise_area: user.expertise_area || '',
        organization: user.organization || '',
        city: user.city || '',
        district: user.district || '',
        profile_photo_url: user.profile_photo_url || ''
      });

      // İlçeleri yükle
      if (user.city && CITIES_DISTRICTS[user.city]) {
        setAvailableDistricts(
          CITIES_DISTRICTS[user.city].reduce((acc, district) => {
            acc[district] = district;
            return acc;
          }, {})
        );
      }
    }
  }, [user]);

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
      if (formData.city !== user?.city) {
        setFormData(prev => ({ ...prev, district: '' }));
      }
    }
  }, [formData.city, user?.city]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
    setApiError(null);
    setSuccessMessage(null);
  };

  const validateForm = () => {
    const newErrors = {};
    
    const firstNameError = validateRequired(formData.first_name, 'Ad');
    if (firstNameError) newErrors.first_name = firstNameError;
    
    const lastNameError = validateRequired(formData.last_name, 'Soyad');
    if (lastNameError) newErrors.last_name = lastNameError;
    
    const phoneError = validatePhone(formData.phone);
    if (phoneError) newErrors.phone = phoneError;
    
    const needsExpertise = ['volunteer', 'coordinator'].includes(user?.role);
    if (needsExpertise) {
      const expertiseError = validateRequired(formData.expertise_area, 'Uzmanlık Alanı');
      if (expertiseError) newErrors.expertise_area = expertiseError;
      
      const orgError = validateRequired(formData.organization, 'Organizasyon');
      if (orgError) newErrors.organization = orgError;
    }
    
    const cityError = validateRequired(formData.city, 'Şehir');
    if (cityError) newErrors.city = cityError;
    
    const districtError = validateRequired(formData.district, 'İlçe');
    if (districtError) newErrors.district = districtError;
    
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
    setSuccessMessage(null);

    try {
      const token = authService.getToken();
      const response = await fetch('/auth/me', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Güncelleme başarısız');
      }

      const updatedUser = await response.json();
      authService.saveUser(updatedUser);
      setSuccessMessage('Profil başarıyla güncellendi!');
      
      if (onUpdateSuccess) {
        onUpdateSuccess(updatedUser);
      }
    } catch (error) {
      setApiError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const needsExpertise = ['volunteer', 'coordinator'].includes(user?.role);

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        
        {/* Başlık */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">Profil Ayarları</h1>
          <p className="text-slate-500 dark:text-slate-400">
            Kişisel bilgilerinizi görüntüleyin ve güncelleyin
          </p>
        </div>

        {/* Form Kartı */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8">
          
          {/* Başarı Mesajı */}
          {successMessage && (
            <div className="mb-6 bg-green-500/10 border border-green-500/30 text-green-600 dark:text-green-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">check_circle</span>
              {successMessage}
            </div>
          )}

          {/* Hata Mesajı */}
          {apiError && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">error</span>
              {apiError}
            </div>
          )}

          {/* Kullanıcı Bilgileri (Read-only) */}
          <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-slate-500 dark:text-slate-400">E-posta:</span>
                <p className="font-semibold">{user?.email}</p>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">TC Kimlik No:</span>
                <p className="font-semibold">{user?.tc_identity_no}</p>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Rol:</span>
                <p className="font-semibold">{USER_ROLES[user?.role]}</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Kişisel Bilgiler */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">person</span>
                Kişisel Bilgiler
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Ad"
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  error={errors.first_name}
                  required
                  autoComplete="given-name"
                />

                <Input
                  label="Soyad"
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  error={errors.last_name}
                  required
                  autoComplete="family-name"
                />
              </div>

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

            {/* Uzmanlık ve Organizasyon */}
            {needsExpertise && (
              <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">work</span>
                  Uzmanlık ve Organizasyon
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Select
                    label="Uzmanlık Alanı"
                    name="expertise_area"
                    value={formData.expertise_area}
                    onChange={handleChange}
                    options={EXPERTISE_AREAS}
                    error={errors.expertise_area}
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
              </div>
            )}

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
                Profil Fotoğrafı
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
                type="submit"
                variant="primary"
                fullWidth
                loading={loading}
                icon="save"
              >
                Değişiklikleri Kaydet
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
