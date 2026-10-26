import { type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useToast } from "./Toast";
import BottomNav from "./BottomNav";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";

function OfflineBanner() {
  const online = typeof navigator === "undefined" ? true : navigator.onLine;
  if (online) return null;
  return (
    <div
      role="alert"
      className="bg-amber-100 px-4 py-2 text-center text-sm text-amber-900"
    >
      You are offline. Connection required for AI analysis — browsing cached
      pages is available, but new scans need internet.
    </div>
  );
}

export default function Layout({
  children,
  hideNav = false
}: {
  children: ReactNode;
  hideNav?: boolean;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { push } = useToast();
  const { mode, setMode } = useWorkspaceMode();

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      push("Could not sign out. Check your connection and try again.", "error");
      return;
    }
    queryClient.clear();
    push("Signed out.", "info");
    navigate("/login");
  };

  return (
    <div className="flex min-h-dvh flex-col bg-slate-50">
      <OfflineBanner />
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link to="/" className="flex items-center gap-2" aria-label="FreshSense AI home">
            <img src="/icons/icon-192.svg" alt="" className="h-7 w-7" />
            <span className="text-base font-bold text-green-700">FreshSense AI</span>
          </Link>
          {!hideNav && <div className="flex items-center gap-3">
            <div className="flex items-center gap-2" aria-label="Workspace view">
              <span className="hidden text-xs font-medium text-slate-500 sm:inline">View as</span>
              <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
                {([ ["personal", "Personal"], ["business", "Seller"] ] as const).map(([value, label]) => (
                  <button key={value} type="button" aria-pressed={mode === value} onClick={() => setMode(value)} className={`rounded-md px-2.5 py-1.5 text-xs font-semibold transition ${mode === value ? "bg-white text-emerald-800 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <button type="button" onClick={() => void handleLogout()} className="rounded-md px-2 py-1 text-sm text-slate-600 hover:text-slate-900">Sign out</button>
          </div>}
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-24 pt-4">{children}</main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
