import { Link, useParams } from "react-router-dom";
import { useTrackedItem } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";

function title(value?: string | null) {
  return value ? value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Unknown";
}

export default function TrackedItemPage() {
  const { id } = useParams<{ id: string }>();
  const itemQuery = useTrackedItem(id);
  const scans = itemQuery.data?.scans ?? [];
  const first = scans[0];
  const latest = scans[scans.length - 1];
  const sensorScans = scans.filter((scan) => scan.temperature_c != null || scan.humidity_pct != null || scan.voc_index != null).length;
  const expiryScans = scans.filter((scan) => scan.expiry_date).length;

  return (
    <Layout>
      <Link to="/history" className="text-sm text-green-700 underline">← Back to history</Link>
      {itemQuery.isPending ? (
        <div className="mt-4"><LoadingSkeleton lines={6} /></div>
      ) : itemQuery.isError || !itemQuery.data ? (
        <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not load this Freshness Passport.
        </p>
      ) : (
        <>
          <header className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Longitudinal Freshness Passport</p>
            <h1 className="mt-1 text-2xl font-bold text-slate-900">{itemQuery.data.label}</h1>
            <p className="mt-1 text-sm text-slate-700">
              {scans.length} recorded scan{scans.length === 1 ? "" : "s"} · storage readings on {sensorScans} · expiry evidence on {expiryScans}
            </p>
          </header>

          {first && latest && scans.length > 1 && (
            <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-900">What changed in the record?</h2>
              <p className="mt-1 text-sm text-slate-700">
                The recorded assessment changed from <strong>{title(first.freshness_label)}</strong> to <strong>{title(latest.freshness_label)}</strong> across {scans.length} scans.
              </p>
              <p className="mt-2 text-xs text-slate-500">
                These are prototype estimates captured at different times, not a validated deterioration rate or food-safety determination.
              </p>
            </section>
          )}

          <section className="mt-5">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-base font-semibold text-slate-900">Evidence over time</h2>
              <Link to={`/scan?item=${itemQuery.data.id}`} className="text-sm font-semibold text-green-700 underline">
                Add scan
              </Link>
            </div>
            <ol className="mt-3 space-y-3">
              {[...scans].reverse().map((scan) => (
                <li key={String(scan.id)} className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <time className="text-xs text-slate-500" dateTime={scan.created_at}>
                        {new Date(scan.created_at).toLocaleString()}
                      </time>
                      <p className="mt-1 font-semibold text-slate-900">{title(scan.freshness_label)}</p>
                    </div>
                    <Link to={`/result/${String(scan.id)}`} className="text-sm text-green-700 underline">Passport</Link>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    Evidence used: {scan.sources.length ? scan.sources.join(", ") : "no reliable modality"}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {[
                      scan.temperature_c != null ? `${scan.temperature_c} °C` : null,
                      scan.humidity_pct != null ? `${scan.humidity_pct}% RH` : null,
                      scan.voc_index != null ? `VOC ${scan.voc_index}` : null,
                      scan.expiry_date ? `label date ${scan.expiry_date}` : null
                    ].filter(Boolean).join(" · ") || "No storage or expiry readings recorded"}
                  </p>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}
    </Layout>
  );
}
