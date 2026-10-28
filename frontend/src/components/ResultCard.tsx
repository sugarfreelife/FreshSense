import type { Scan } from "../api/hooks";
import { Link } from "react-router-dom";
import AuthenticatedImage from "./AuthenticatedImage";

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
  const normalized = recommendation?.toLowerCase() ?? "";
  if (normalized.includes("do_not_consume") || normalized.includes("do not consume")) return "Do not consume";
  if (normalized.includes("consume soon")) return "Consume soon";
  if (normalized.includes("consume now")) return "Consume now";
  if (normalized.includes("check expiry")) return "Check the expiry label";
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

function ocrLabel(provider?: string): string {
  switch (provider) {
    case "tesseract": return "Read with Tesseract";
    case "easyocr": return "Read with EasyOCR";
    case "rapidocr": return "Read with RapidOCR";
    case "manual": return "Text entered manually";
    case "legacy": return "Older scan · needs OCR refresh";
    case "unavailable": return "OCR engine unavailable";
    case "tesseract_error":
    case "easyocr_error": return "Could not read this image";
    default: return "Waiting for package text reading";
  }
}

export default function ResultCard({
  scan,
  onReanalyze,
  isReanalyzing = false,
  reanalyzeError
}: {
  scan: { id: Scan["id"] } & Partial<Omit<Scan, "id">>;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
  reanalyzeError?: string | null;
}) {
  const label = scan.freshness_label ?? scan.freshness ?? "Unknown";
  const sources = scan.sources ?? [];
  const warnings = scan.warnings ?? [];
  const isHeuristicScore = scan.confidence_kind === "heuristic_score";
  const scoreLabel = scan.model_score == null
    ? "Assessment score"
    : isHeuristicScore
      ? "Prototype rule score"
      : "Uncalibrated model score";
  const scoreValue = scan.model_score == null
    ? formatPct(scan.confidence)
    : isHeuristicScore
      ? scan.model_score.toFixed(2)
      : formatPct(scan.model_score);
  const product = scan.product;
  const productCategory = product?.category ?? null;
  const productFromText = product?.source === "package_text" || product?.source === "image_and_text";
  const visualProduct = product?.source === "image_model" || product?.source === "image_and_text";
  const labelDetails = product?.label_details;
  const nextAction = scan.passport?.next_action;
  const nextActionTo = nextAction?.target === "pantry"
    ? "#pantry-entry"
    : `/scan${scan.tracked_item_id ? `?item=${encodeURIComponent(scan.tracked_item_id)}` : ""}`;

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
            <strong>{scoreValue}</strong>
          </span>
        </div>
        {isHeuristicScore && (
          <p className="mt-1 text-right text-xs text-slate-500">Fixed rule output · not accuracy or a probability</p>
        )}
        {scan.tracked_item_id && scan.tracked_item_label && (
          <Link to={`/items/${scan.tracked_item_id}`} className="mt-2 inline-block text-sm font-semibold text-green-700 underline">
            View {scan.tracked_item_label} over time
          </Link>
        )}
        {scan.image_url && (
          <AuthenticatedImage
            src={scan.image_url}
            alt={scan.food_type ? `Photo of ${scan.food_type}` : "Scanned food photo"}
          />
        )}
      </section>

      <section aria-label="Product recognition" className="overflow-hidden rounded-2xl border border-emerald-200 bg-white">
        <div className="border-b border-emerald-100 bg-emerald-50/70 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-800">Food & product identification</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">{product?.product_name ?? productCategory ?? "A clearer view is needed"}</h2>
            {visualProduct && (
              <span className="rounded-full border border-emerald-200 bg-white px-2.5 py-1 text-xs font-medium text-emerald-800">
                {product?.status === "uncertain" ? "Possible visual match" : product?.source === "image_and_text" ? "Photo + label text" : "Identified from photo"}
              </span>
            )}
            {product?.source === "package_text" && (
              <span className="rounded-full border border-emerald-200 bg-white px-2.5 py-1 text-xs font-medium text-emerald-800">
                matched from package text
              </span>
            )}
            {product?.source === "user_label" && (
              <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600">
                label supplied by you
              </span>
            )}
          </div>
          {productCategory && product?.product_name !== productCategory && (
            <p className="mt-1 text-sm text-slate-700">{productCategory}</p>
          )}
        </div>
        <div className="space-y-3 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="text-slate-600">{visualProduct ? product?.model : ocrLabel(scan.ocr_provider)}</span>
            {visualProduct && product?.confidence_kind === "cosine_similarity" && product.confidence != null && (
              <span className="font-medium text-slate-700">Visual similarity {product.confidence.toFixed(3)} · not a probability</span>
            )}
            {productFromText && product?.confidence != null && (
              <span className="font-medium text-slate-700">Text match strength {formatPct(product.confidence)}</span>
            )}
            {!productFromText && scan.ocr_confidence != null && (
              <span className="font-medium text-slate-700">Text-read score {formatPct(scan.ocr_confidence)}</span>
            )}
          </div>
          {product?.evidence && product.evidence.length > 0 && (
            <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-900">Recognition evidence</p>
              <div className="mt-2 flex flex-wrap gap-2" aria-label="Recognition evidence">
                {product.evidence.map((term) => (
                  <span key={term} className="rounded-md border border-emerald-200 bg-white px-2 py-1 font-mono text-xs text-emerald-950">{term}</span>
                ))}
              </div>
            </div>
          )}
          {product?.packaging && (
            <p className="text-sm text-slate-700"><strong>Likely presentation:</strong> {product.packaging}</p>
          )}
          {product?.alternatives && product.alternatives.length > 0 && (
            <details className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <summary className="cursor-pointer text-sm font-medium text-slate-700">Compare visual matches</summary>
              <ul className="mt-2 space-y-1 text-sm text-slate-600">
                {product.alternatives.map((candidate, index) => (
                  <li key={`${candidate.name}-${index}`}>{candidate.name} · similarity {candidate.similarity.toFixed(3)}</li>
                ))}
              </ul>
            </details>
          )}
          {labelDetails && (
            <div className="rounded-xl border border-slate-200 p-3">
              <p className="text-sm font-semibold text-slate-800">Visible label details</p>
              <p className="mt-1 text-xs text-slate-500">Read from package text. Check the label before relying on ingredients or allergens.</p>
              <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                {([
                  ["Package size", labelDetails.package_size],
                  ["Ingredients", labelDetails.ingredients],
                  ["Allergen statement", labelDetails.allergens],
                  ["Storage instructions", labelDetails.storage_instructions],
                  ["Nutrition", labelDetails.nutrition_text]
                ] as const).map(([title, value]) => (
                  <div key={title}><dt className="font-medium text-slate-700">{title}</dt><dd className="mt-1 text-slate-600">{value || "Not readable in this photo"}</dd></div>
                ))}
              </dl>
            </div>
          )}
          {product?.limitations?.map((limitation) => <p key={limitation} className="text-xs text-slate-500">{limitation}</p>)}
          {!productCategory && (
            <p className="text-sm text-slate-600">
              A clear view of the product name can identify categories such as dairy, bread, canned fish, and drinks.
            </p>
          )}
          {["unavailable", "legacy", "unknown"].includes(scan.ocr_provider ?? "unknown") && (
            <p role="status" className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              This scan has no package text yet. Automatic reading needs an OCR engine such as Tesseract installed on the backend computer; then choose “Read this label again.”
            </p>
          )}
          {onReanalyze && (
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={onReanalyze}
                disabled={isReanalyzing}
                className="rounded-lg border border-emerald-300 bg-white px-3 py-2 text-sm font-semibold text-emerald-800 transition-colors hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2 disabled:cursor-wait disabled:opacity-60"
              >
                {isReanalyzing ? "Analyzing photo…" : "Analyze photo again"}
              </button>
              {reanalyzeError && <span role="alert" className="text-sm text-red-700">{reanalyzeError}</span>}
            </div>
          )}
          {scan.ocr_text && (
            <details className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <summary className="cursor-pointer text-sm font-medium text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600">
                Inspect AI label readout
              </summary>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <div className="rounded-lg bg-white p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Expiry cue</p>
                  <p className="mt-1 font-mono text-sm font-semibold text-slate-900">
                    {scan.expiry_label || scan.expiry_text
                      ? [scan.expiry_label, scan.expiry_text].filter(Boolean).join(" · ")
                      : "No expiry cue isolated"}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">
                    {scan.expiry_date
                      ? "A complete date was read from the package text."
                      : scan.expiry_text
                        ? "Partial stamp only. Check the printed package before relying on a date."
                        : "The recognized text did not contain a usable expiry date."}
                  </p>
                </div>
                <div className="rounded-lg bg-white p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Text reader</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">{ocrLabel(scan.ocr_provider)}</p>
                  <p className="mt-1 text-xs text-slate-600">
                    {scan.ocr_confidence != null
                      ? `Reader score ${formatPct(scan.ocr_confidence)} · a text-recognition score, not date certainty.`
                      : "This prototype does not yet report a calibrated OCR confidence."}
                  </p>
                </div>
              </div>
              <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Recognized package text</p>
              <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-white p-3 font-mono text-xs leading-relaxed text-slate-700">{scan.ocr_text}</pre>
            </details>
          )}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">{scan.expiry_label === "unlabeled date" ? "Printed date · label not visible" : "Printed expiry date"}</p>
          <p className="mt-1 text-sm font-semibold text-slate-800">
              {scan.expiry_date ?? (scan.expiry_text ? `${scan.expiry_text} · year not read` : "Not detected")}
          </p>
          {!scan.expiry_date && !scan.expiry_text && ["unavailable", "legacy", "unknown"].includes(scan.ocr_provider ?? "unknown") && (
            <p className="text-xs text-amber-800">OCR setup or refresh needed</p>
          )}
            {scan.expiry_text && !scan.expiry_date && (
              <p className="text-xs text-slate-500">Partial stamp read{scan.expiry_label ? ` after “${scan.expiry_label}”` : ""}; no year was detected, so this was not used to calculate expiry.</p>
            )}
          {scan.expiry_date && scan.expiry_label && (
            <p className="text-xs text-slate-500">{scan.expiry_label === "unlabeled date"
              ? "Confirm that this stamp is the expiry or best-before date before saving it to your pantry."
              : `Read after “${scan.expiry_label}”`}</p>
          )}
          {scan.shelf_life_days !== undefined && scan.shelf_life_days !== null && (
            <p className="text-xs text-slate-500">
            {scan.shelf_life_days >= 0
              ? `${scan.shelf_life_days} day(s) remaining`
              : `${Math.abs(scan.shelf_life_days)} day(s) past the printed date`}
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
          {scan.sensor_source && scan.sensor_source !== "user_entered" && (
            <p className="mt-1 text-xs font-medium text-amber-800">
              {scan.sensor_source === "demo_estimate" ? "Illustrative demo values · not measured" : scan.sensor_source === "mixed" ? "Mixed entered and demo values" : "Older scan · value source not recorded"}
            </p>
          )}
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

          {nextAction && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-800">Evidence recovery loop · rule-based</p>
              <h4 className="mt-1 text-sm font-bold text-slate-900">{nextAction.title}</h4>
              <p className="mt-1 text-sm text-slate-700">{nextAction.detail}</p>
              <Link
                to={nextActionTo}
                className="mt-3 inline-flex rounded-lg border border-emerald-300 bg-white px-3 py-2 text-sm font-semibold text-emerald-800 transition-colors hover:bg-emerald-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:ring-offset-2"
              >
                {nextAction.action_label}
              </Link>
              <p className="mt-2 text-xs text-slate-600">This follow-up rule helps complete the record; it is not a trained freshness prediction.</p>
            </div>
          )}

          {scan.passport.conflicts.length > 0 && (
            <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3" role="status">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-900">Signals that disagree</h4>
              <ul className="mt-2 space-y-2">
                {scan.passport.conflicts.map((conflict) => (
                  <li key={conflict.key}>
                    <p className="text-sm font-semibold text-amber-900">{conflict.title}</p>
                    <p className="text-sm text-amber-900">{conflict.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

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
