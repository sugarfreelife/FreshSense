import type { Scan } from "../api/hooks";

function freshnessTone(freshness?: string | null): string {
  const v = (freshness ?? "").toLowerCase();
  if (v.includes("stale") || v.includes("use caution") || v.includes("moderate"))
    return "bg-amber-100 text-amber-900";
  if (v.includes("spoil") || v.includes("unsafe") || v.includes("expired"))
    return "bg-red-100 text-red-800";
  if (v.includes("fresh")) return "bg-green-100 text-green-800";
  return "bg-slate-100 text-slate-700";
}

function friendlyLabel(value?: string | null): string {
  if (!value) return "Unknown";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function recommendationTone(recommendation?: string | null): string {
  if (recommendation?.includes("DO_NOT_CONSUME")) return "border-red-200 bg-red-50 text-red-900";
  if (recommendation === "CONSUME_SOON" || recommendation === "CHECK_EXPIRY")
    return "border-amber-200 bg-amber-50 text-amber-900";
  return "border-green-200 bg-green-50 text-green-900";
}

function recommendationLabel(recommendation?: string | null): string {
  switch (recommendation) {
    case "CONSUME_NOW": return "Consume now";
    case "CONSUME_SOON": return "Consume soon";
    case "CHECK_EXPIRY": return "Check the expiry label";
    case "CAUTION_DO_NOT_CONSUME": return "Do not consume";
    default: return friendlyLabel(recommendation);
  }
}

function formatPct(conf?: number | null): string {
  if (conf === undefined || conf === null || Number.isNaN(conf)) return "—";
  const pct = conf <= 1 ? conf * 100 : conf;
  return `${pct.toFixed(0)}%`;
}

function evidenceTone(state: string): string {
  if (state === "warning") return "border-amber-300 bg-amber-50";
  if (state === "missing") return "border-slate-200 bg-slate-50";
  if (state === "context") return "border-blue-200 bg-blue-50";
  return "border-green-200 bg-green-50";
}

export default function ResultCard({ scan }: { scan: { id: Scan["id"] } & Partial<Omit<Scan, "id">> }) {
  const label = scan.freshness_label ?? scan.freshness ?? "Unknown";
  const sources = scan.sources ?? [];
  const warnings = scan.warnings ?? [];
  const scoreLabel = scan.model_score == null
    ? "Assessment score"
    : scan.confidence_kind === "heuristic_score"
      ? "Prototype score"
      : "Uncalibrated model score";

  return (
    <article aria-label="Scan result" className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <span
            className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${freshnessTone(label)}`}
          >
            {friendlyLabel(label)}
          </span>
          <span className="text-sm text-slate-600">
            {scoreLabel}{" "}
            <strong>{formatPct(scan.model_score ?? scan.confidence)}</strong>
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
        <section className={`rounded-2xl border p-4 ${recommendationTone(scan.recommendation)}`}>
          <h3 className="text-sm font-semibold">Recommendation</h3>
          <p className="mt-1 text-sm">{recommendationLabel(scan.recommendation)}</p>
        </section>
      )}

      {scan.notes && (
        <section className="rounded-xl border border-blue-200 bg-blue-50 p-3">
          <h3 className="text-sm font-semibold text-blue-900">Your note</h3>
          <p className="mt-1 whitespace-pre-wrap text-sm text-blue-900">{scan.notes}</p>
        </section>
      )}

      {scan.passport && (
        <section aria-label="Freshness Passport" className="rounded-2xl border border-emerald-200 bg-white p-4">
          <h3 className="text-base font-semibold text-slate-900">Freshness Passport</h3>
          <p className="mt-1 text-sm font-medium text-emerald-800">{scan.passport.summary}</p>
          <p className="mt-2 text-sm text-slate-600">{scan.passport.explanation}</p>

          <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence used</h4>
          <div className="mt-2 grid gap-2">
            {scan.passport.evidence.map((item) => (
              <div key={item.key} className={`rounded-xl border p-3 ${evidenceTone(item.state)}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                  <span className="text-xs capitalize text-slate-600">{item.state}</span>
                </div>
                <p className="mt-1 text-sm text-slate-700">{item.observation}</p>
                <p className="mt-1 text-xs text-slate-600">{item.explanation}</p>
              </div>
            ))}
          </div>

          <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Assessment timeline</h4>
          <ol className="mt-2 space-y-3 border-l border-slate-200 pl-4">
            {scan.passport.timeline.map((event) => (
              <li key={event.key}>
                <p className="text-sm font-medium text-slate-800">{event.title}</p>
                <p className="text-xs text-slate-600">{event.detail}</p>
                {event.occurred_at && (
                  <time className="text-xs text-slate-500" dateTime={event.occurred_at}>
                    {new Date(event.occurred_at).toLocaleString()}
                  </time>
                )}
              </li>
            ))}
          </ol>

          {scan.passport.limitations.length > 0 && (
            <div className="mt-4 rounded-lg bg-slate-50 p-3">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-600">Limits of this assessment</h4>
              <ul className="mt-1 list-disc pl-5 text-xs text-slate-600">
                {scan.passport.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
              </ul>
            </div>
          )}
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
