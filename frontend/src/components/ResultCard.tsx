import type { Scan } from "../api/hooks";

function freshnessTone(freshness?: string | null): string {
  const v = (freshness ?? "").toLowerCase();
  if (v.includes("fresh")) return "bg-green-100 text-green-800";
  if (v.includes("stale") || v.includes("use caution") || v.includes("moderate"))
    return "bg-amber-100 text-amber-900";
  if (v.includes("spoil") || v.includes("unsafe") || v.includes("expired"))
    return "bg-red-100 text-red-800";
  return "bg-slate-100 text-slate-700";
}

function formatPct(conf?: number | null): string {
  if (conf === undefined || conf === null || Number.isNaN(conf)) return "—";
  const pct = conf <= 1 ? conf * 100 : conf;
  return `${pct.toFixed(0)}%`;
}

export default function ResultCard({ scan }: { scan: Scan }) {
  const label = scan.freshness_label ?? scan.freshness ?? "Unknown";
  const sources = scan.sources ?? [];
  const warnings = scan.warnings ?? [];

  return (
    <article aria-label="Scan result" className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <span
            className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${freshnessTone(label)}`}
          >
            {label}
          </span>
          <span className="text-sm text-slate-600">
            Confidence <strong>{formatPct(scan.confidence)}</strong>
          </span>
        </div>
        {scan.food_type && (
          <p className="mt-2 text-sm text-slate-600">
            Food: <strong className="text-slate-800">{scan.food_type}</strong>
          </p>
        )}
        {scan.image_url && (
          <img
            src={scan.image_url}
            alt={scan.food_type ? `Photo of ${scan.food_type}` : "Scanned food photo"}
            className="mt-3 max-h-64 w-full rounded-xl object-cover"
            loading="lazy"
          />
        )}
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Expiry</p>
          <p className="mt-1 text-sm font-semibold text-slate-800">
            {scan.expiry_date ?? "Not detected"}
          </p>
          {scan.shelf_life_days !== undefined && scan.shelf_life_days !== null && (
            <p className="text-xs text-slate-500">
              ≈ {scan.shelf_life_days} day(s) shelf life
            </p>
          )}
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Environment</p>
          <p className="mt-1 text-sm text-slate-800">
            {scan.temperature_c !== undefined && scan.temperature_c !== null
              ? `${scan.temperature_c} °C`
              : "Temp —"}
            {" · "}
            {scan.humidity_pct !== undefined && scan.humidity_pct !== null
              ? `${scan.humidity_pct}% RH`
              : "RH —"}
          </p>
          <p className="text-xs text-slate-500">
            VOC index:{" "}
            {scan.voc_index !== undefined && scan.voc_index !== null
              ? String(scan.voc_index)
              : "—"}
          </p>
        </div>
      </section>

      {scan.recommendation && (
        <section className="rounded-2xl border border-green-200 bg-green-50 p-4">
          <h3 className="text-sm font-semibold text-green-900">Recommendation</h3>
          <p className="mt-1 text-sm text-green-900">{scan.recommendation}</p>
        </section>
      )}

      {sources.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-800">Evidence sources</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
            {sources.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </section>
      )}

      {warnings.length > 0 && (
        <section
          role="alert"
          className="rounded-2xl border border-amber-300 bg-amber-50 p-4"
        >
          <h3 className="text-sm font-semibold text-amber-900">Warnings</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-amber-900">
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
