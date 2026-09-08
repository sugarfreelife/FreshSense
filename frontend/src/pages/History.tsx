import { Link } from "react-router-dom";
import { useScans } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";

export default function History() {
  const scansQuery = useScans();

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">History</h1>
        <Link
          to="/scan"
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700"
        >
          + New scan
        </Link>
      </div>

      <div className="mt-4">
        {scansQuery.isPending ? (
          <LoadingSkeleton lines={5} />
        ) : scansQuery.isError ? (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            Could not load history. Check your connection.
          </p>
        ) : !scansQuery.data || scansQuery.data.length === 0 ? (
          <EmptyState
            title="No history yet"
            message="Your analyzed scans will appear here."
            actionLabel="Start a scan"
            actionTo="/scan"
          />
        ) : (
          <ul className="space-y-2">
            {scansQuery.data.map((s) => {
              const label = s.freshness_label ?? s.freshness ?? "Unknown";
              const conf =
                s.confidence === undefined || s.confidence === null
                  ? "—"
                  : `${((s.confidence <= 1 ? s.confidence * 100 : s.confidence)).toFixed(0)}%`;
              return (
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
                        {s.created_at ? new Date(s.created_at).toLocaleString() : ""}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm text-slate-600">
                      {label} · {conf}
                      {s.expiry_date ? ` · exp ${s.expiry_date}` : ""}
                    </p>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Layout>
  );
}
