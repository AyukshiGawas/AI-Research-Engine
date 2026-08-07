import api, { setAccessToken } from './api';

export const authService = {
  async register(userData) {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  async login(credentials) {
    const response = await api.post('/auth/login', credentials);
    if (response.data.access_token) {
      setAccessToken(response.data.access_token);
    }
    return response.data;
  },

  async refreshToken() {
    const response = await api.post('/auth/refresh');
    if (response.data.access_token) {
      setAccessToken(response.data.access_token);
    }
    return response.data;
  },

  async logout() {
    try {
      await api.post('/auth/logout');
    } finally {
      setAccessToken(null);
    }
  },

  async getCurrentUser() {
    const response = await api.get('/users/me');
    return response.data;
  },

  async updateProfile(profileData) {
    const response = await api.put('/users/me', profileData);
    return response.data;
  },
};
