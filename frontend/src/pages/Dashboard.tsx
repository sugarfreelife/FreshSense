import { Link } from "react-router-dom";
import { useScans } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";

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
  const scansQuery = useScans();

  const scans = scansQuery.data ?? [];
  const total = scans.length;
  const attention = scans.filter((s) => needsAttention(freshnessLabel(s))).length;
  const fresh = total - attention;
  const recent = scans.slice(0, 5);

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link
          to="/scan"
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700"
        >
          + New scan
        </Link>
      </div>

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
              <p className="text-xs text-slate-500">Fresh</p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
              <p className="text-2xl font-bold text-amber-700">{attention}</p>
              <p className="text-xs text-slate-500">Needs attention</p>
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
                        {s.food_type ?? "Food scan"}
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
