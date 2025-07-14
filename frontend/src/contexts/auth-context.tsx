"use client";

import React, { createContext, useEffect, useState } from "react";
import type { User } from "firebase/auth";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useAuthStore } from "@/stores/useAuthStore";

interface AuthContextType {
  user: User | null;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { setToken } = useAuthStore();

  useEffect(() => {
    // onAuthStateChanged might not be a function if firebase is not configured.
    if (auth && typeof auth.onAuthStateChanged === 'function') {
      const unsubscribe = onAuthStateChanged(auth, async (user) => {
        setUser(user);
        if (user) {
          const idToken = await user.getIdToken();
          setToken(idToken);
        } else {
          setToken(null);
        }
        setLoading(false);
      });
      return () => unsubscribe();
    } else {
        // If firebase is not configured, we are not loading and there is no user.
        setLoading(false);
        setUser(null);
        setToken(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
