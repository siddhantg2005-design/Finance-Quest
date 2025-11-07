import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import client from "../services/mongodbClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const session = await client.getSession();
        if (!mounted) return;
        setUser(session.user);
        setToken(session.token);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    const unsub = client.onAuthChange((evt) => {
      if (evt.event === "SIGNED_IN") {
        setUser(evt.user || null);
        setToken(evt.token || null);
      } else if (evt.event === "SIGNED_OUT") {
        setUser(null);
        setToken(null);
      }
    });
    return () => {
      mounted = false;
      unsub();
    };
  }, []);

  const signIn = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const res = await client.signIn(email, password);
      setUser(res.user || null);
      setToken(res.access_token || res.token || null);
      return res;
    } finally {
      setLoading(false);
    }
  }, []);

  const signUp = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const res = await client.signUp(email, password);
      return res;
    } finally {
      setLoading(false);
    }
  }, []);

  const signOut = useCallback(() => {
    client.signOut();
    setUser(null);
    setToken(null);
  }, []);

  const value = { user, token, loading, signIn, signUp, signOut };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
