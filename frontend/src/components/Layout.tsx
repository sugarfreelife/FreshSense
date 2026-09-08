import { type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setToken } from "../api/client";
import { useToast } from "./Toast";
import BottomNav from "./BottomNav";

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
  const { push } = useToast();

  const handleLogout = () => {
    setToken(null);
    push("Signed out.", "info");
    navigate("/login");
  };

  return (
    <div className="flex min-h-dvh flex-col bg-slate-50">
      <OfflineBanner />
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-md items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2" aria-label="FreshSense AI home">
            <img src="/icons/icon-192.svg" alt="" className="h-7 w-7" />
            <span className="text-base font-bold text-green-700">FreshSense AI</span>
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-md px-2 py-1 text-sm text-slate-500 hover:text-slate-800"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto w-full max-w-md flex-1 px-4 pb-24 pt-4">{children}</main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
