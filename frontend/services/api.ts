import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Authentication is held in an HttpOnly cookie issued by the backend. The
// browser can send it but JavaScript cannot read the credential itself.
export const api = axios.create({ baseURL: API_URL, withCredentials: true });

export function startSession() {
  // This is only a non-sensitive UI flag. It is never used as a credential.
  window.localStorage.setItem("medisense_session", "active");
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("medisense_session");
}

export function saveUser(user: any) {
  window.localStorage.setItem("medisense_user", JSON.stringify(user));
}

export function getUser(): any {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("medisense_user");
  return raw ? JSON.parse(raw) : null;
}

export function logout() {
  void api.post("/api/auth/logout");
  window.localStorage.removeItem("medisense_session");
  window.localStorage.removeItem("medisense_user");
}

// ---- Auth ----
export const registerUser = (data: any) => api.post("/api/auth/register", data);
export const loginUser = (data: any) => api.post("/api/auth/login", data);

// ---- Profile ----
export const getProfile = () => api.get("/api/user/profile");
export const updateProfile = (data: any) => api.put("/api/user/profile", data);
export const deleteAccount = () => api.delete("/api/user/account");

// ---- Health / Predictions ----
export const predictRisk = (answers: any, diseases?: string[]) =>
  api.post("/api/health/predict", { answers, diseases });
export const getHistory = () => api.get("/api/health/history");
export const getLatest = () => api.get("/api/health/latest");

// ---- Measurements ----
export const addMeasurement = (data: any) => api.post("/api/health/measurements", data);
export const listMeasurements = () => api.get("/api/health/measurements");
export const addSymptomCheckIn = (data: any) => api.post("/api/health/symptoms", data);
export const listSymptomCheckIns = () => api.get("/api/health/symptoms");
export const getLatestSymptomCheckIn = () => api.get("/api/health/symptoms/latest");

// ---- Assistant chat ----
export const sendChatMessage = (message: string, sessionId?: string) =>
  api.post("/api/assistant/chat", { message, session_id: sessionId });
