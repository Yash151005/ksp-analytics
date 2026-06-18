import { create } from 'zustand';
import { authAPI } from '../services/api';

export const useAuthStore = create((set) => ({
  user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null,
  token: localStorage.getItem('token') || null,
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authAPI.login(username, password);
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      set({ 
        user, 
        token: access_token, 
        isLoading: false 
      });
      
      return user;
    } catch (error) {
      let errorMsg = 'Login failed';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // Handle both string errors and FastAPI validation errors (array)
        if (Array.isArray(detail)) {
          errorMsg = detail[0]?.msg || 'Login failed';
        } else if (typeof detail === 'string') {
          errorMsg = detail;
        }
      }
      set({ error: errorMsg, isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null });
  },

  refresh: async () => {
    try {
      const response = await authAPI.refresh();
      const { access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      set({ token: access_token });
      
      return access_token;
    } catch (error) {
      set({ user: null, token: null });
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      throw error;
    }
  },

  hasPermission: (permission) => {
    const { user } = useAuthStore.getState();
    if (!user) return false;
    
    const permissions = {
      admin: ['view_crimes', 'view_criminals', 'view_analytics', 'view_reports', 'create_reports', 'export_data', 'manage_users', 'view_audit_logs', 'manage_alerts'],
      analyst: ['view_crimes', 'view_criminals', 'view_analytics', 'view_reports', 'create_reports', 'export_data'],
      investigator: ['view_crimes', 'view_criminals', 'export_data', 'manage_alerts'],
      viewer: ['view_crimes'],
    };
    
    return (permissions[user.role] || []).includes(permission);
  },

  isAdmin: () => useAuthStore.getState().user?.role === 'admin',
  isAnalyst: () => useAuthStore.getState().user?.role === 'analyst',
  isInvestigator: () => useAuthStore.getState().user?.role === 'investigator',
  isViewer: () => useAuthStore.getState().user?.role === 'viewer',
}));

export default useAuthStore;
