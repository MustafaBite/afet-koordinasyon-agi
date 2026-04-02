// Form validasyon fonksiyonları

export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) return 'E-posta adresi gereklidir';
  if (!emailRegex.test(email)) return 'Geçerli bir e-posta adresi giriniz';
  return null;
};

export const validatePassword = (password) => {
  if (!password) return 'Şifre gereklidir';
  if (password.length < 8) return 'Şifre en az 8 karakter olmalıdır';
  if (!/[A-Z]/.test(password)) return 'Şifre en az bir büyük harf içermelidir';
  if (!/[a-z]/.test(password)) return 'Şifre en az bir küçük harf içermelidir';
  if (!/[0-9]/.test(password)) return 'Şifre en az bir rakam içermelidir';
  return null;
};

export const validatePhone = (phone) => {
  const phoneRegex = /^05[0-9]{9}$/;
  if (!phone) return 'Telefon numarası gereklidir';
  if (!phoneRegex.test(phone)) return 'Geçerli bir telefon numarası giriniz (05xxxxxxxxx)';
  return null;
};

export const validateTCIdentity = (tc) => {
  if (!tc) return 'TC Kimlik No gereklidir';
  if (!/^[0-9]{11}$/.test(tc)) return 'TC Kimlik No 11 haneli olmalıdır';
  return null;
};

export const validateRequired = (value, fieldName) => {
  if (!value || value.trim() === '') return `${fieldName} gereklidir`;
  return null;
};

export const validateURL = (url) => {
  if (!url) return null; // Opsiyonel alan
  try {
    new URL(url);
    if (!url.toLowerCase().endsWith('.png')) {
      return 'Sadece PNG formatında resim linki kabul edilir';
    }
    return null;
  } catch {
    return 'Geçerli bir URL giriniz';
  }
};
