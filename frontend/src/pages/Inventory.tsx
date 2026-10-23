import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useCreateInventoryItem, useDeleteInventoryItem, useInventory, useUpdateInventoryItem, type InventoryItem } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";

type Filter = "all" | "attention" | "undated";

function dateLabel(value: string | null): string {
  if (!value) return "Date not recorded";
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function statusCopy(item: InventoryItem): string {
  if (item.status === "unknown") return "Date needed";
  if (item.status === "expired") return `${Math.abs(item.days_remaining ?? 0)} day(s) past label date`;
  if (item.days_remaining === 0) return "Label date is today";
  return `${item.days_remaining} day(s) to label date`;
}

function statusStyle(status: InventoryItem["status"]): string {
  if (status === "expired" || status === "urgent") return "border-rose-200 bg-rose-50 text-rose-800";
  if (status === "soon") return "border-amber-200 bg-amber-50 text-amber-900";
  if (status === "unknown") return "border-slate-200 bg-slate-100 text-slate-700";
  return "border-emerald-200 bg-emerald-50 text-emerald-800";
}

function sourceCopy(source: InventoryItem["expiry_source"]): string {
  if (source === "ocr_confirmed") return "AI read · confirmed by you";
  if (source === "user_entered") return "Entered by you";
  return "No date recorded";
}

function InventoryRow({ item }: { item: InventoryItem }) {
  const [quantity, setQuantity] = useState(String(item.quantity));
  const [expiryDate, setExpiryDate] = useState(item.expiry_date ?? "");
  const update = useUpdateInventoryItem();
  const remove = useDeleteInventoryItem();
  const [feedback, setFeedback] = useState("");

  const saveDate = () => update.mutate({ id: item.id, expiry_date: expiryDate || null, expiry_source: expiryDate ? "user_entered" : "unknown" }, {
    onSuccess: () => setFeedback("Package date saved."),
    onError: () => setFeedback("Date could not be saved. Try again.")
  });
  const saveQuantity = () => {
    const parsed = Number(quantity);
    if (Number.isInteger(parsed) && parsed >= 1 && parsed <= 9999 && parsed !== item.quantity) {
      update.mutate({ id: item.id, quantity: parsed }, {
        onSuccess: () => setFeedback("Quantity saved."),
        onError: () => setFeedback("Quantity could not be saved. Try again.")
      });
    } else if (!Number.isInteger(parsed) || parsed < 1 || parsed > 9999) {
      setQuantity(String(item.quantity));
    }
  };

  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-900">{item.product_name}</h3>
            {item.category && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{item.category}</span>}
          </div>
          <p className="mt-1 text-sm text-slate-600">{dateLabel(item.expiry_date)} <span className="text-slate-400">/</span> {sourceCopy(item.expiry_source)}</p>
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${statusStyle(item.status)}`}>{statusCopy(item)}</span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <label className="block text-xs font-medium text-slate-500">Quantity in this batch
          <input type="number" min={1} max={9999} value={quantity} onChange={(e) => setQuantity(e.target.value)} onBlur={saveQuantity} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); saveQuantity(); e.currentTarget.blur(); } }} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900" aria-label={`Quantity for ${item.product_name}`} />
        </label>
        <label className="block text-xs font-medium text-slate-500">Update package date
          <input type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} onBlur={() => { if (expiryDate !== (item.expiry_date ?? "")) saveDate(); }} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900" aria-label={`Expiry date for ${item.product_name}`} />
        </label>
        <div className="flex items-center justify-between gap-3 sm:justify-end">
          {update.isPending ? <span className="text-xs text-slate-500" role="status">Saving…</span> : <span className="text-xs text-slate-500">{item.quantity} unit{item.quantity === 1 ? "" : "s"}</span>}
          {item.source_scan_id && <Link to={`/result/${item.source_scan_id}`} className="text-xs font-medium text-emerald-800 underline">Scan</Link>}
          <button type="button" onClick={() => { if (window.confirm(`Remove ${item.product_name} from your inventory?`)) remove.mutate(item.id); }} className="rounded-lg px-2 py-2 text-xs font-medium text-slate-500 hover:bg-rose-50 hover:text-rose-700" aria-label={`Remove ${item.product_name}`}>Remove</button>
        </div>
      </div>
      {feedback && <p role="status" className={`mt-2 text-xs ${feedback.includes("could not") ? "text-rose-700" : "text-emerald-800"}`}>{feedback}</p>}
      {(update.isError || remove.isError) && <p role="alert" className="mt-2 text-xs text-rose-700">Could not save that change. Please retry.</p>}
    </li>
  );
}

export default function Inventory() {
  const inventory = useInventory();
  const create = useCreateInventoryItem();
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [expiryDate, setExpiryDate] = useState("");
  const [formError, setFormError] = useState("");

  const items = inventory.data ?? [];
  const summary = useMemo(() => ({
    batches: items.length,
    units: items.reduce((sum, item) => sum + item.quantity, 0),
    attention: items.filter((item) => ["expired", "urgent", "soon"].includes(item.status)).length,
    undated: items.filter((item) => item.status === "unknown").length
  }), [items]);
  const next = items.find((item) => ["expired", "urgent", "soon"].includes(item.status));
  const needsDate = items.find((item) => item.status === "unknown");
  const insight = next
    ? `${next.product_name}: ${statusCopy(next).toLowerCase()}. Check the package and plan this batch first.`
    : needsDate
      ? `${needsDate.product_name} has no date recorded. Check its package and add the date to sharpen your pantry timeline.`
      : items.length
        ? "Your tracked batches have no label dates due within the next 7 days. FreshSense will update this queue as dates approach."
        : "Add a scanned purchase to start your expiry watch. FreshSense will sort batches by their recorded package dates.";

  const visible = items.filter((item) => {
    const matchesQuery = `${item.product_name} ${item.category ?? ""}`.toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === "all" || (filter === "attention" && ["expired", "urgent", "soon"].includes(item.status)) || (filter === "undated" && item.status === "unknown");
    return matchesQuery && matchesFilter;
  });

  const addManual = (event: React.FormEvent) => {
    event.preventDefault();
    setFormError("");
    const count = Number(quantity);
    if (!name.trim()) { setFormError("Enter a product name."); return; }
    if (!Number.isInteger(count) || count < 1 || count > 9999) { setFormError("Quantity must be between 1 and 9,999."); return; }
    create.mutate({ product_name: name.trim(), category: category.trim() || undefined, quantity: count, expiry_date: expiryDate || undefined, expiry_source: expiryDate ? "user_entered" : "unknown" }, {
      onSuccess: () => { setName(""); setCategory(""); setQuantity("1"); setExpiryDate(""); },
      onError: () => setFormError("Could not save this batch. Check your connection and try again.")
    });
  };

  return (
    <Layout>
      <div className="mx-auto max-w-5xl">
        <section className="relative overflow-hidden rounded-[28px] bg-slate-950 px-5 py-6 text-white shadow-xl sm:px-8 sm:py-8">
          <div className="pointer-events-none absolute -right-10 -top-20 h-64 w-64 rounded-full border border-emerald-400/20" />
          <div className="pointer-events-none absolute -right-3 -top-12 h-48 w-48 rounded-full border border-emerald-400/20" />
          <div className="relative">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">FreshSense / Pantry intelligence</p>
            <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Food inventory</h1>
                <p className="mt-2 max-w-xl text-sm text-slate-300">Every purchase is a batch. Confirm the label date, track its quantity, and see what needs attention next.</p>
              </div>
              <Link to="/scan" className="rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-emerald-300">Scan a purchase</Link>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {[["Batches", summary.batches], ["Units tracked", summary.units], ["Date watch", summary.attention], ["Need a date", summary.undated]].map(([label, value]) => (
                <div key={String(label)} className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-3 backdrop-blur">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 sm:p-5" aria-label="FreshSense Copilot insight">
          <div className="flex items-start gap-3">
            <span aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-800 text-sm text-white">✦</span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-900">FreshSense Copilot / Use-next signal</p>
              <p className="mt-1 text-sm font-medium text-slate-900">{insight}</p>
              <p className="mt-1 text-xs text-slate-600">Prioritized from dates you confirmed or entered. This is an organizing cue, not a food-safety verdict.</p>
            </div>
          </div>
        </section>

        <details className="mt-4 rounded-2xl border border-slate-200 bg-white shadow-sm">
          <summary className="cursor-pointer list-none px-4 py-4 font-semibold text-slate-800 marker:content-none">+ Add a batch manually</summary>
          <form onSubmit={addManual} className="grid gap-3 border-t border-slate-100 p-4 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">Product name<input value={name} onChange={(e) => setName(e.target.value)} maxLength={160} placeholder="e.g. Canned tuna" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">Category<input value={category} onChange={(e) => setCategory(e.target.value)} maxLength={80} placeholder="e.g. Canned food" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">Quantity purchased<input type="number" min={1} max={9999} value={quantity} onChange={(e) => setQuantity(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">Expiry / best-before date<input type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /><span className="mt-1 block text-xs font-normal text-slate-500">Leave blank if there is no readable date.</span></label>
            {formError && <p role="alert" className="text-sm text-rose-700 sm:col-span-2">{formError}</p>}
            <button type="submit" disabled={create.isPending} className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60 sm:col-span-2">{create.isPending ? "Saving batch…" : "Add batch"}</button>
          </form>
        </details>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Tracked batches</h2>
            <p className="mt-1 text-sm text-slate-500">A different purchase can have a different expiry date.</p>
          </div>
          <label className="sr-only" htmlFor="inventory-search">Search pantry</label>
          <input id="inventory-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search products" className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm sm:w-56" />
        </div>

        <div className="mt-3 flex flex-wrap gap-2" aria-label="Inventory filters">
          {([["all", "All batches"], ["attention", "Date watch"], ["undated", "Need a date"]] as const).map(([value, label]) => (
            <button key={value} type="button" onClick={() => setFilter(value)} aria-pressed={filter === value} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${filter === value ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-600 hover:border-slate-500"}`}>{label}</button>
          ))}
        </div>

        {inventory.isPending ? <div className="mt-4"><LoadingSkeleton lines={5} /></div> : inventory.isError ? (
          <p role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">Could not load your inventory. Check that the FreshSense backend is running, then refresh.</p>
        ) : visible.length === 0 ? (
          <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-10 text-center">
            <p className="text-lg font-semibold text-slate-900">{items.length ? "No batches match this view" : "Your pantry is ready"}</p>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-600">{items.length ? "Try another filter or search term." : "Scan a purchase and FreshSense will ask how many you bought and confirm the package date."}</p>
            {!items.length && <Link to="/scan" className="mt-4 inline-flex rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white">Start with a scan</Link>}
          </div>
        ) : (
          <ul className="mt-4 space-y-3">{visible.map((item) => <InventoryRow key={item.id} item={item} />)}</ul>
        )}
      </div>
    </Layout>
  );
}
