import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex flex-1 flex-col items-center gap-0.5 rounded-lg px-2 py-2 text-xs font-medium ${
    isActive ? "text-green-700" : "text-slate-500 hover:text-slate-700"
  }`;

export default function BottomNav() {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur"
    >
      <div className="mx-auto flex max-w-md items-stretch justify-between px-2 pb-[env(safe-area-inset-bottom)]">
        <NavLink to="/dashboard" className={linkClass} aria-label="Dashboard">
          <span aria-hidden="true" className="text-lg leading-none">⌂</span>
          Home
        </NavLink>
        <NavLink to="/scan" className={linkClass} aria-label="Start scan">
          <span aria-hidden="true" className="text-lg leading-none">◉</span>
          Scan
        </NavLink>
        <NavLink to="/history" className={linkClass} aria-label="Scan history">
          <span aria-hidden="true" className="text-lg leading-none">≡</span>
          History
        </NavLink>
      </div>
    </nav>
  );
}
