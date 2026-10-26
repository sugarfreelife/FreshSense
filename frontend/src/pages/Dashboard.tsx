import { Link } from "react-router-dom";
import { useInventory, useScans } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";

function freshnessLabel(s: { freshness?: string | null; freshness_label?: string | null }) {
  return s.freshness_label ?? s.freshness ?? "Unknown";
}

function needsAttention(label: string): boolean {
  const v = label.toLowerCase();
  return (
    v.includes("spoil") ||
    v.includes("unsafe") ||
    v.includes("expired") ||
    v.includes("stale") ||
    v.includes("caution") ||
    v.includes("moderate")
  );
}

export default function Dashboard() {
  const { mode, workspaceId } = useWorkspaceMode();
  const business = mode === "business";
  const scansQuery = useScans(mode, workspaceId);
  const inventoryQuery = useInventory(mode, workspaceId);
  const pantryItems = inventoryQuery.data ?? [];
  const nextAction = pantryItems.find((item) => item.status === "unknown")?.product_name
    ?? pantryItems.find((item) => ["expired", "urgent", "soon"].includes(item.status))?.product_name
    ?? (pantryItems.length ? (business ? "No batches need a date check" : "Dates look clear") : (business ? "Record your first stock batch" : "Scan your first food"));
  const units = pantryItems.reduce((sum, item) => sum + item.quantity, 0);
  const expiringItems = pantryItems.filter((item) => item.status === "urgent" || item.status === "soon");
  const expiredItems = pantryItems.filter((item) => item.status === "expired");
  const expiringUnits = expiringItems.reduce((sum, item) => sum + item.quantity, 0);
  const expiredUnits = expiredItems.reduce((sum, item) => sum + item.quantity, 0);

  const scans = scansQuery.data?.pages.flatMap((page) => page.items) ?? [];
  const total = scansQuery.data?.pages[0]?.total ?? 0;
  const recent = scans.slice(0, 5);
  const attention = recent.filter((s) => needsAttention(freshnessLabel(s))).length;
  const fresh = recent.length - attention;

  return (
    <Layout>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl bg-slate-950 px-5 py-6 text-white shadow-lg sm:px-7">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">FreshSense / {business ? "Stock intelligence" : "Food intelligence"}</p>
          <h1 className="mt-2 text-2xl font-bold sm:text-3xl">{business ? "Stock & expiry dashboard" : "Your freshness command center"}</h1>
          <p className="mt-1 text-sm text-slate-300">{business ? "Track received batches, stock on hand, and package dates that need a check." : "Scans, package dates, and pantry batches in one place."}</p>
        </div>
        <Link
          to="/scan"
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700"
        >
          {business ? "+ Receive stock" : "+ Scan a purchase"}
        </Link>
      </div>

      <section className="mt-4 grid gap-3 sm:grid-cols-3" aria-label={business ? "Stock overview" : "Pantry overview"}>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{business ? "Units on hand" : "Pantry units"}</p>
          <p className="mt-1 text-3xl font-bold tabular-nums text-slate-950">{inventoryQuery.isError ? "—" : inventoryQuery.isPending ? "…" : units}</p>
          <p className="mt-1 text-xs text-slate-500">Across {inventoryQuery.isPending ? "…" : pantryItems.length} {business ? "received" : "purchase"} batches</p>
        </div>
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-900">{business ? "Units with dates due" : "Date watch"}</p>
          <p className="mt-1 text-3xl font-bold tabular-nums text-amber-950">{inventoryQuery.isError ? "—" : inventoryQuery.isPending ? "…" : business ? expiringUnits : expiringItems.length + expiredItems.length}</p>
          <p className="mt-1 text-xs text-amber-900">{business ? `${expiringItems.length} batches within 7 days; ${expiredUnits} units past label date` : "Batches within seven days or past label date"}</p>
        </div>
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-900">Next action</p>
          <p className="mt-1 text-sm font-semibold text-emerald-950">{inventoryQuery.isPending ? (business ? "Loading stock…" : "Loading pantry…") : nextAction}</p>
          <Link to="/inventory" className="mt-2 inline-block text-sm font-semibold text-emerald-800 underline">{business ? "Open stock ledger" : "Open batch tracker"}</Link>
        </div>
      </section>

      {scansQuery.isPending ? (
        <div className="mt-4">
          <LoadingSkeleton lines={4} />
        </div>
      ) : scansQuery.isError ? (
        <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not load scans. Check your connection and sign-in status.
        </p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center" aria-label="Scan statistics">
            <div className="rounded-xl border border-slate-200 bg-white p-3">
              <p className="text-2xl font-bold">{total}</p>
              <p className="text-xs text-slate-500">Total scans</p>
            </div>
            <div className="rounded-xl border border-green-200 bg-green-50 p-3">
              <p className="text-2xl font-bold text-green-700">{fresh}</p>
              <p className="text-xs text-slate-500">Fresh (recent)</p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
              <p className="text-2xl font-bold text-amber-700">{attention}</p>
              <p className="text-xs text-slate-500">Review (recent)</p>
            </div>
          </div>

          <h2 className="mt-6 text-base font-semibold">Recent scans</h2>
          {recent.length === 0 ? (
            <div className="mt-2">
              <EmptyState
                title="No scans yet"
                message="Take a photo of food to get a freshness assessment."
                actionLabel="Start your first scan"
                actionTo="/scan"
              />
            </div>
          ) : (
            <ul className="mt-2 space-y-2">
              {recent.map((s) => (
                <li key={String(s.id)}>
                  <Link
                    to={`/result/${String(s.id)}`}
                    className="block rounded-xl border border-slate-200 bg-white p-3 hover:border-green-400"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-slate-800">
                        {s.tracked_item_label ?? s.food_type ?? "Food scan"}
                      </span>
                      <span className="text-xs text-slate-500">
                        {s.created_at ? new Date(s.created_at).toLocaleDateString() : ""}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm text-slate-600">
                      {freshnessLabel(s)}
                      {s.confidence !== undefined && s.confidence !== null
                        ? ` · ${((s.confidence <= 1 ? s.confidence * 100 : s.confidence)).toFixed(0)}%`
                        : ""}
                      {s.expiry_date ? ` · exp ${s.expiry_date}` : ""}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {total > 5 && (
            <Link
              to="/history"
              className="mt-3 inline-block text-sm text-green-700 underline"
            >
              View full history
            </Link>
          )}
        </>
      )}
    </Layout>
  );
}
