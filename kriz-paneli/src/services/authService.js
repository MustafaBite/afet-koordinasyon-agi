// Authentication API servisleri

const API_BASE_URL = '/auth'; // Vite proxy üzerinden backend'e gidecek

export const authService = {
  async login(credentials) {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Giriş başarısız' }));
      throw new Error(error.detail || 'Giriş başarısız');
    }
    
    return response.json();
  },

  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Kayıt başarısız' }));
      throw new Error(error.detail || 'Kayıt başarısız');
    }
    
    return response.json();
  },

  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      throw new Error('Token bulunamadı');
    }

    const response = await fetch(`${API_BASE_URL}/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        throw new Error('Oturum süresi doldu');
      }
      const error = await response.json().catch(() => ({ detail: 'Kullanıcı bilgisi alınamadı' }));
      throw new Error(error.detail || 'Kullanıcı bilgisi alınamadı');
    }

    return response.json();
  },

  async updateProfile(userData) {
    const token = this.getToken();
    if (!token) {
      throw new Error('Token bulunamadı');
    }

    const response = await fetch(`${API_BASE_URL}/me`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        throw new Error('Oturum süresi doldu');
      }
      const error = await response.json().catch(() => ({ detail: 'Profil güncellenemedi' }));
      throw new Error(error.detail || 'Profil güncellenemedi');
    }

    const updatedUser = await response.json();
    this.saveUser(updatedUser);
    return updatedUser;
  },

  // Token ile API çağrısı yapmak için yardımcı fonksiyon
  async fetchWithAuth(url, options = {}) {
    const token = this.getToken();
    if (!token) {
      throw new Error('Token bulunamadı');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok && response.status === 401) {
      this.logout();
      window.location.reload();
      throw new Error('Oturum süresi doldu');
    }

    return response;
  },

  saveToken(token) {
    localStorage.setItem('access_token', token);
  },

  getToken() {
    return localStorage.getItem('access_token');
  },

  saveUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  isAuthenticated() {
    return !!this.getToken();
  }
};
