import type { InventoryItem } from "../api/hooks";

type QueueEntry = {
  item: InventoryItem;
  score: number;
  reason: string;
  action: string;
};

function makeQueue(items: InventoryItem[]): QueueEntry[] {
  const totalUnits = Math.max(1, items.reduce((sum, item) => sum + item.quantity, 0));

  return items.map((item) => {
    const urgency = item.status === "expired" ? 1
      : item.status === "urgent" ? 0.9
      : item.status === "soon" ? 0.75
      : item.status === "unknown" ? 0.55
      : 0.15;
    const evidenceGap = item.expiry_source === "unknown" || !item.expiry_date ? 1
      : item.expiry_source === "user_entered" ? 0.3
      : 0.1;
    const quantityShare = Math.min(1, item.quantity / totalUnits);
    const score = Math.round(100 * (0.45 * urgency + 0.35 * evidenceGap + 0.2 * quantityShare));

    const unitPhrase = item.quantity === 1 ? "1 unit" : `${item.quantity} units`;
    const reason = !item.expiry_date
      ? `${unitPhrase} ${item.quantity === 1 ? "has" : "have"} no recorded package date`
      : item.status === "expired"
        ? `${unitPhrase} ${item.quantity === 1 ? "is" : "are"} past the recorded label date`
        : item.status === "urgent" || item.status === "soon"
          ? `${unitPhrase} ${item.quantity === 1 ? "is" : "are"} close to the recorded label date`
          : `${unitPhrase}; date source: ${item.expiry_source === "ocr_confirmed" ? "OCR, confirmed by user" : "entered by user"}`;
    const action = !item.expiry_date ? "Add the package date"
      : item.status === "expired" ? "Review the printed date and batch count"
      : item.status === "urgent" || item.status === "soon" ? "Check this batch first"
      : "Review batch evidence";

    return { item, score, reason, action };
  }).sort((a, b) => b.score - a.score || a.item.created_at.localeCompare(b.item.created_at));
}

export default function EvidencePriorityQueue({ items, business }: { items: InventoryItem[]; business: boolean }) {
  const queue = makeQueue(items).slice(0, 5);

  return (
    <section className="mt-4 rounded-2xl border border-cyan-200 bg-cyan-50/70 p-4 sm:p-5" aria-labelledby="evidence-queue-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-cyan-900">FreshSense / Adaptive review queue</p>
          <h2 id="evidence-queue-title" className="mt-1 text-lg font-bold text-slate-950">What should be checked next?</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-700">Ranks batches using recorded-date urgency, date evidence source, and quantity at stake. The priority number is a workflow cue, not a freshness or safety probability.</p>
        </div>
        <span className="rounded-full border border-cyan-200 bg-white px-3 py-1 text-xs font-semibold text-cyan-900">Explainable rule</span>
      </div>
      {queue.length ? (
        <ol className="mt-3 space-y-2">
          {queue.map(({ item, score, reason, action }, index) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-cyan-100 bg-white p-3">
              <div className="flex min-w-0 items-start gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-100 text-sm font-bold text-cyan-950">{index + 1}</span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-950">{item.product_name}</p>
                  <p className="mt-0.5 text-xs text-slate-600">{reason}</p>
                  <p className="mt-1 text-xs font-semibold text-cyan-900">{action}</p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="text-right text-xs text-slate-500"><strong className="block text-lg tabular-nums text-slate-900">{score}</strong>priority</span>
                <button type="button" onClick={() => document.getElementById(`batch-${item.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })} className="rounded-lg border border-cyan-300 px-3 py-2 text-xs font-semibold text-cyan-950 hover:bg-cyan-50">Review batch</button>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-3 rounded-xl border border-cyan-100 bg-white p-3 text-sm text-slate-600">{business ? "Record a stock batch to build the review queue." : "Record a pantry batch to build the review queue."}</p>
      )}
      <details className="mt-3 text-xs text-slate-600">
        <summary className="cursor-pointer font-medium text-cyan-950">How is priority calculated?</summary>
        <p className="mt-1">The prototype combines date urgency (45%), the date evidence gap (35%), and this batch’s share of tracked units (20%). Missing dates receive the largest evidence gap; manually entered dates receive a smaller gap than missing dates, and OCR dates confirmed by the user receive the smallest. These weights are transparent design choices and have not been scientifically validated.</p>
      </details>
    </section>
  );
}
