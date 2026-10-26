import { NavLink } from "react-router-dom";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex flex-1 flex-col items-center gap-0.5 rounded-lg px-2 py-2 text-xs font-medium ${
    isActive ? "text-green-700" : "text-slate-500 hover:text-slate-700"
  }`;

function NavIcon({ name }: { name: "home" | "scan" | "inventory" | "history" }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5" {...common}>
      {name === "home" && <><path d="m3.5 10 8.5-7 8.5 7" /><path d="M5.5 9v11h13V9M9 20v-6h6v6" /></>}
      {name === "scan" && <><path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M3 16v3a2 2 0 0 0 2 2h3" /><circle cx="12" cy="12" r="4" /></>}
      {name === "inventory" && <><rect x="3.5" y="4" width="17" height="16" rx="2" /><path d="M3.5 10h17M9 4v16M15 10v10" /></>}
      {name === "history" && <><path d="M4 7h16M4 12h16M4 17h16" /><circle cx="2.8" cy="7" r=".5" fill="currentColor" stroke="none" /><circle cx="2.8" cy="12" r=".5" fill="currentColor" stroke="none" /><circle cx="2.8" cy="17" r=".5" fill="currentColor" stroke="none" /></>}
    </svg>
  );
}

export default function BottomNav() {
  const { mode } = useWorkspaceMode();
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur"
    >
      <div className="mx-auto flex max-w-5xl items-stretch justify-between px-2 pb-[env(safe-area-inset-bottom)]">
        <NavLink to="/dashboard" className={linkClass} aria-label="Dashboard">
          <NavIcon name="home" />
          Home
        </NavLink>
        <NavLink to="/scan" className={linkClass} aria-label="Start scan">
          <NavIcon name="scan" />
          Scan
        </NavLink>
        <NavLink to="/inventory" className={linkClass} aria-label={mode === "business" ? "Seller stock" : "Pantry inventory"}>
          <NavIcon name="inventory" />
          {mode === "business" ? "Stock" : "Pantry"}
        </NavLink>
        <NavLink to="/history" className={linkClass} aria-label="Scan history">
          <NavIcon name="history" />
          History
        </NavLink>
      </div>
    </nav>
  );
}
