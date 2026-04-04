const API_BASE_URL = '/auth'; 

export const authService = {
  // SAHTE LOGİN (Backend'i atlar)
  async login(credentials) {
    console.warn("DİKKAT: Şu an sahte (mock) login kullanılıyor!");
    
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          access_token: "sahte_jwt_token_12345",
          token_type: "bearer",
          user: { 
            id: "fake-uuid-123", 
            email: credentials.email, 
            first_name: "Test", 
            role: "volunteer" 
          }
        });
      }, 500); // Gerçekçi olması için yarım saniye gecikme ekledik
    });
  },

  // SAHTE KAYIT (Backend'i atlar)
  async register(userData) {
    console.warn("DİKKAT: Şu an sahte (mock) register kullanılıyor!");
    
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          access_token: "sahte_jwt_token_12345",
          token_type: "bearer",
          user: { 
            id: "fake-uuid-123", 
            email: userData.email, 
            first_name: userData.first_name || "Yeni", 
            role: "volunteer" 
          }
        });
      }, 500);
    });
  },

  async getMe() {
    // ... (Bu kısım aynı kalabilir veya buraya da sahte dönüş ekleyebilirsin)
    const token = this.getToken();
    if (!token) throw new Error('Token bulunamadı');
    return { id: "fake-uuid-123", email: "test@test.com", first_name: "Test" };
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