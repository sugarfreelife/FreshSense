import axios from "axios";
import { BUSINESS_WORKSPACE_STORAGE_KEY, WORKSPACE_MODE_STORAGE_KEY } from "../context/WorkspaceModeContext";

const TOKEN_KEY = "freshsense_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // storage unavailable (private mode); ignore
  }
}

export function isOnline(): boolean {
  if (typeof navigator !== "undefined" && typeof navigator.onLine === "boolean") {
    return navigator.onLine;
  }
  return true;
}

const baseURL =
  (import.meta.env.VITE_API_URL as string | undefined) ||
  "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL,
  timeout: 60000
});

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  try {
    const mode = localStorage.getItem(WORKSPACE_MODE_STORAGE_KEY) === "business" ? "business" : "personal";
    config.headers["X-Workspace-Mode"] = mode;
    const workspaceId = mode === "business" ? localStorage.getItem(BUSINESS_WORKSPACE_STORAGE_KEY) : null;
    if (workspaceId) config.headers["X-Workspace-Id"] = workspaceId;
    else delete config.headers["X-Workspace-Id"];
  } catch {
    config.headers["X-Workspace-Mode"] = "personal";
    delete config.headers["X-Workspace-Id"];
  }
  return config;
});

export { TOKEN_KEY };
