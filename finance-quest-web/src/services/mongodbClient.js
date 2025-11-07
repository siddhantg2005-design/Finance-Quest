import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Token storage helpers
const TOKEN_KEY = "access_token";
const USER_KEY = "auth_user";

const getToken = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));
const setUser = (u) => (u ? localStorage.setItem(USER_KEY, JSON.stringify(u)) : localStorage.removeItem(USER_KEY));
const getStoredUser = () => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

// Recurring helpers
export const Recurring = {
  async list() {
    const { data } = await api.get('/api/recurring/');
    return data;
  },
  async create(payload) {
    const { data } = await api.post('/api/recurring/create/', payload);
    return data;
  },
  async runNow(id) {
    const { data } = await api.post(`/api/recurring/${id}/run-now/`);
    return data;
  },
  async runDue() {
    const { data } = await api.post('/api/recurring/run-due/');
    return data;
  }
};

// Savings helpers
export const Savings = {
  async list() {
    const { data } = await api.get('/api/savings/');
    return data;
  },
  async create(payload) {
    const { data } = await api.post('/api/savings/create/', payload);
    return data;
  },
  async runNow(id) {
    const { data } = await api.post(`/api/savings/${id}/run-now/`);
    return data;
  },
  async runDue() {
    const { data } = await api.post('/api/savings/run-due/');
    return data;
  }
};

// Axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach Authorization automatically
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Simple subscriber model for auth change events
const subscribers = new Set();
const notifyAuthChange = (payload) => subscribers.forEach((cb) => cb(payload));

// Auth API
export async function signUp(email, password) {
  const { data } = await api.post("/api/auth/signup/", { email, password });
  return data;
}

export async function signIn(email, password) {
  const { data } = await api.post("/api/auth/login/", { email, password });
  const token = data.access_token || data.token;
  if (!token) throw new Error("Token missing in response");
  setToken(token);
  if (data.user) setUser(data.user);
  notifyAuthChange({ event: "SIGNED_IN", token, user: data.user || null });
  return data;
}

export function signOut() {
  setToken(null);
  setUser(null);
  notifyAuthChange({ event: "SIGNED_OUT" });
}

export async function getSession() {
  const token = getToken();
  if (!token) return { user: null, token: null };
  try {
    const { data } = await api.get("/api/profile/");
    if (data) setUser(data);
    return { user: data || getStoredUser(), token };
  } catch {
    signOut();
    return { user: null, token: null };
  }
}

export function onAuthChange(callback) {
  subscribers.add(callback);
  return () => subscribers.delete(callback);
}

export default {
  signUp,
  signIn,
  signOut,
  getSession,
  onAuthChange,
};

// Domain API helpers
export const Transactions = {
  async list() {
    const { data } = await api.get('/api/transactions/');
    return data;
  },
  async create(payload) {
    const { data } = await api.post('/api/transactions/', payload);
    return data;
  },
  async remove(id) {
    const { data } = await api.delete(`/api/transactions/${id}/`);
    return data;
  },
};

export const Goals = {
  async list() {
    const { data } = await api.get('/api/goals/');
    return data;
  },
  async create(payload) {
    const { data } = await api.post('/api/goals/', payload);
    return data;
  },
};

export async function getProfile() {
  const { data } = await api.get('/api/profile/');
  return data;
}

export async function awardXP(user_id, reason, xp_amount) {
  const { data } = await api.post('/api/xp/award/', { user_id, reason, xp_amount });
  return data;
}

// Analytics helpers
export const Analytics = {
  async spendByCategory(month) {
    const params = month ? { month } : undefined;
    const { data } = await api.get('/api/analytics/spend-by-category/', { params });
    return data;
  },
  async incomeVsExpense(range) {
    const params = range || {};
    const { data } = await api.get('/api/analytics/income-vs-expense/', { params });
    return data;
  },
  async goalProgress() {
    const { data } = await api.get('/api/analytics/goal-progress/');
    return data;
  },
};
