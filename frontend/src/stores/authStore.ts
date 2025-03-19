import { User, auth } from '../api/client';
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isLoading: false,
  error: null,

  loadUser: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ user: null });
      return;
    }

    try {
      set({ isLoading: true });
      const user = await auth.getCurrentUser();
      set({ user, isLoading: false });
    } catch (error) {
      console.error('Failed to load user:', error);
      // If we get an error loading the user, clear the token
      localStorage.removeItem('token');
      set({ user: null, token: null, isLoading: false });
    }
  },

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await auth.login(username, password);
      console.log('Login response:', response);
      set({ token: response.access_token, isLoading: false });
      
      // Get user info after successful login
      const user = await auth.getCurrentUser();
      console.log('User info:', user);
      set({ user });
    } catch (error) {
      console.error('Login error:', error);
      set({ error: 'Invalid username or password', isLoading: false });
      throw error;
    }
  },
  logout: () => {
    auth.logout();
    set({ user: null, token: null });
  },
  setToken: (token: string) => {
    localStorage.setItem('token', token);
    set({ token });
  },
})); 