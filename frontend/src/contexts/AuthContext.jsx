// Authentication Context - ITEM 90: Global auth state management
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../lib/apiClient';
import apiClient from '../lib/apiClient';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize auth state from stored token
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    const token = apiClient.getAuthToken();

    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // Verify token and fetch user data
      const userData = await authAPI.me();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      // Token invalid or expired
      console.error('Auth initialization failed:', error);
      apiClient.removeAuthToken();
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      const response = await authAPI.login(credentials);

      // Store tokens
      apiClient.setAuthToken(response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }

      // Set user data
      setUser(response.user);
      setIsAuthenticated(true);

      toast.success('Login successful!');
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      toast.error(error.message || 'Login failed');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      const response = await authAPI.register(userData);

      // Auto-login after registration
      if (response.access_token) {
        apiClient.setAuthToken(response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        setUser(response.user);
        setIsAuthenticated(true);
      }

      toast.success('Registration successful!');
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      toast.error(error.message || 'Registration failed');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      // Call logout endpoint
      await authAPI.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear local state
      apiClient.removeAuthToken();
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    }
  }, []);

  const updateProfile = useCallback(async (data) => {
    try {
      setLoading(true);
      const updatedUser = await authAPI.updateProfile(data);
      setUser(updatedUser);
      toast.success('Profile updated successfully');
      return updatedUser;
    } catch (error) {
      console.error('Profile update failed:', error);
      toast.error(error.message || 'Profile update failed');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const changePassword = useCallback(async (data) => {
    try {
      setLoading(true);
      await authAPI.changePassword(data);
      toast.success('Password changed successfully');
    } catch (error) {
      console.error('Password change failed:', error);
      toast.error(error.message || 'Password change failed');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await authAPI.refreshToken(refreshToken);
      apiClient.setAuthToken(response.access_token);

      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }

      return response.access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Logout if refresh fails
      await logout();
      throw error;
    }
  }, [logout]);

  const setupMFA = useCallback(async () => {
    try {
      const response = await authAPI.setupMFA();
      toast.success('MFA setup initiated');
      return response;
    } catch (error) {
      console.error('MFA setup failed:', error);
      toast.error(error.message || 'MFA setup failed');
      throw error;
    }
  }, []);

  const verifyMFA = useCallback(async (data) => {
    try {
      const response = await authAPI.verifyMFA(data);
      toast.success('MFA verified successfully');
      return response;
    } catch (error) {
      console.error('MFA verification failed:', error);
      toast.error(error.message || 'MFA verification failed');
      throw error;
    }
  }, []);

  const hasRole = useCallback((role) => {
    if (!user || !user.role) return false;
    return user.role === role;
  }, [user]);

  const hasAnyRole = useCallback((roles) => {
    if (!user || !user.role) return false;
    return roles.includes(user.role);
  }, [user]);

  const hasPermission = useCallback((permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
  }, [user]);

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    refreshToken,
    setupMFA,
    verifyMFA,
    hasRole,
    hasAnyRole,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Protected Route Component
export const ProtectedRoute = ({ children, requiredRole = null, requiredPermission = null }) => {
  const { isAuthenticated, loading, hasRole, hasPermission } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Access Denied</h2>
          <p className="text-gray-600 dark:text-gray-400">You do not have the required role to access this page.</p>
        </div>
      </div>
    );
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Access Denied</h2>
          <p className="text-gray-600 dark:text-gray-400">You do not have permission to access this page.</p>
        </div>
      </div>
    );
  }

  return children;
};

export default AuthContext;
