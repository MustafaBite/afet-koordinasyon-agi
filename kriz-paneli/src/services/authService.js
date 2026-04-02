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
      const error = await response.json();
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
      const error = await response.json();
      throw new Error(error.detail || 'Kayıt başarısız');
    }
    
    return response.json();
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
  }
};
