import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Initialize Auth State: Attempt silent token refresh on application load
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const data = await authService.refreshToken();
        if (data && data.user) {
          setUser(data.user);
        }
      } catch (err) {
        // Cookie missing or expired - silent failure expected for unauthenticated state
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    setAuthError(null);
    try {
      const data = await authService.login(credentials);
      setUser(data.user);
      return data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Authentication failed. Please check credentials.';
      setAuthError(message);
      throw new Error(message);
    }
  };

  const register = async (userData) => {
    setAuthError(null);
    try {
      const newUserData = await authService.register(userData);
      return newUserData;
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed.';
      setAuthError(message);
      throw new Error(message);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
    }
  };

  const updateProfile = async (profileData) => {
    const updated = await authService.updateProfile(profileData);
    setUser(updated);
    return updated;
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    authError,
    login,
    register,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
