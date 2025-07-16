import { create } from 'zustand';
import { auth } from '@/lib/firebase';
import { useJobStore } from './useJobStore';

interface AuthState {
  user: any;
  token: string | null;
  setUser: (user: any) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  logout: async () => {
    try {
      await auth.signOut();
      useJobStore.getState().clearJobs();
      set({ user: null, token: null });
    } catch (error) {
      console.error("Error during sign-out:", error);
    }
  },
}));