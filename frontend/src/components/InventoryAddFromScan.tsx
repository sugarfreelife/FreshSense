import { useState } from "react";
import { Link } from "react-router-dom";
import type { Scan } from "../api/hooks";
import { useCreateInventoryItem } from "../api/hooks";

type ExpiryChoice = "confirm_ocr" | "enter_date" | "unknown";

export default function InventoryAddFromScan({ scan }: { scan: Scan }) {
  const hasOcrDate = Boolean(scan.expiry_date);
  const [name, setName] = useState(scan.product?.product_name || scan.product?.category || scan.food_type || "");
  const [category, setCategory] = useState(scan.product?.category || scan.food_type || "Other");
  const [quantity, setQuantity] = useState("1");
  const [expiryDate, setExpiryDate] = useState(scan.expiry_date ?? "");
  const [choice, setChoice] = useState<ExpiryChoice>(hasOcrDate ? "confirm_ocr" : "enter_date");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const createItem = useCreateInventoryItem();
  const [saved, setSaved] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("Add a product name so you can find it in your pantry.");
      return;
    }
    const count = Number(quantity);
    if (!Number.isInteger(count) || count < 1 || count > 9999) {
      setError("Enter a quantity from 1 to 9,999.");
      return;
    }
    if (choice !== "unknown" && !expiryDate) {
      setError("Enter the date from the package, or choose to track it without a date.");
      return;
    }
    if (choice === "confirm_ocr" && !confirmed) {
      setError("Check the printed date on the package, then confirm it here.");
      return;
    }

    createItem.mutate({
      product_name: name.trim(),
      category: category || undefined,
      quantity: count,
      expiry_date: choice === "unknown" ? undefined : expiryDate,
      expiry_source: choice === "unknown" ? "unknown" : choice === "confirm_ocr" ? "ocr_confirmed" : "user_entered",
      source_scan_id: String(scan.id)
    }, {
      onSuccess: () => setSaved(true),
      onError: () => setError("Could not save this purchase. Check your connection and try again.")
    });
  };

  if (saved) {
    return (
      <section id="pantry-entry" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4" aria-live="polite">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-800">Added to your inventory</p>
        <p className="mt-1 font-semibold text-emerald-950">{quantity} × {name}</p>
        <Link to="/inventory" className="mt-2 inline-block text-sm font-semibold text-emerald-800 underline">Open pantry inventory</Link>
      </section>
    );
  }

  return (
    <section id="pantry-entry" className="overflow-hidden rounded-2xl border border-emerald-200 bg-white shadow-sm">
      <div className="bg-slate-950 px-4 py-4 text-white">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-300">FreshSense / Stock intake</p>
        <h2 className="mt-1 text-lg font-semibold">Add this purchase to your pantry</h2>
        <p className="mt-1 text-sm text-slate-300">Track the quantity and the date printed on this batch.</p>
      </div>
      <form onSubmit={submit} className="space-y-3 p-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
          <label className="block text-sm">
            <span className="font-medium text-slate-700">Product</span>
            <input value={name} onChange={(e) => setName(e.target.value)} maxLength={160} required placeholder="e.g. Whole milk" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-slate-700">How many?</span>
            <input type="number" min={1} max={9999} step={1} inputMode="numeric" value={quantity} onChange={(e) => setQuantity(e.target.value)} required className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
        </div>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">Food category</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
            {[...new Set(["Dairy", "Meat", "Fish & seafood", "Canned food", "Bakery", "Produce", "Drinks", "Frozen", "Other", category].filter(Boolean))].map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
          <span className="mt-1 block text-xs text-slate-500">Pre-filled from the scan when a category was recognized; you can change it.</span>
        </label>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          {hasOcrDate ? (
            <>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">AI read from package: {scan.expiry_date}</p>
              <p className="mt-1 text-xs text-slate-600">Please check the printed label before saving. You can correct the date below.</p>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold text-slate-800">{scan.expiry_text ? `The label read only “${scan.expiry_text}”.` : "The expiry date was not read."}</p>
              <p className="mt-1 text-xs text-slate-600">Read the package and enter its date below. If there is no legible date, you can still track the item without one.</p>
            </>
          )}

          <label className="mt-3 block text-sm">
            <span className="font-medium text-slate-700">Package date</span>
            <input type="date" value={expiryDate} disabled={choice === "unknown"} onChange={(e) => { setExpiryDate(e.target.value); if (hasOcrDate && e.target.value !== scan.expiry_date) { setChoice("enter_date"); setConfirmed(false); } }} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 disabled:bg-slate-100" />
          </label>

          {hasOcrDate && expiryDate === scan.expiry_date && choice === "confirm_ocr" && (
            <label className="mt-3 flex items-start gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} className="mt-1 accent-emerald-700" />
              <span>I checked this date against the package.</span>
            </label>
          )}

          <label className="mt-3 flex items-start gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={choice === "unknown"} onChange={(e) => { setChoice(e.target.checked ? "unknown" : hasOcrDate ? "confirm_ocr" : "enter_date"); setConfirmed(false); }} className="mt-1 accent-emerald-700" />
            <span>No date is printed or I cannot verify it. Track without an expiry date.</span>
          </label>
        </div>

        {error && <p role="alert" className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">{error}</p>}
        <button type="submit" disabled={createItem.isPending} className="w-full rounded-xl bg-emerald-700 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-60">
          {createItem.isPending ? "Saving purchase…" : "Save to pantry inventory"}
        </button>
      </form>
    </section>
  );
}
