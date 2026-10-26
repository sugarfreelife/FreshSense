import axios from "axios";
import { BUSINESS_WORKSPACE_STORAGE_KEY, WORKSPACE_MODE_STORAGE_KEY } from "../context/WorkspaceModeContext";

const LEGACY_TOKEN_KEY = "freshsense_token";
const CSRF_COOKIE_NAME = "freshsense_csrf";

// Remove bearer tokens created by older FreshSense versions. Browser sessions
// now use the API's HttpOnly cookie, which scripts cannot read from storage.
try {
  localStorage.removeItem(LEGACY_TOKEN_KEY);
} catch {
  // Storage can be unavailable in private browsing; cookie auth still works.
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
  timeout: 60000,
  withCredentials: true
});

function readCookie(name: string): string | null {
  try {
    const prefix = `${name}=`;
    const entry = document.cookie.split(";").map((cookie) => cookie.trim()).find((cookie) => cookie.startsWith(prefix));
    return entry ? decodeURIComponent(entry.slice(prefix.length)) : null;
  } catch {
    return null;
  }
}

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  const method = (config.method ?? "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const csrfToken = readCookie(CSRF_COOKIE_NAME);
    if (csrfToken) config.headers["X-CSRF-Token"] = csrfToken;
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
