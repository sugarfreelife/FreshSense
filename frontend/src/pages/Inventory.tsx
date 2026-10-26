import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useBusinessWorkspaces, useCreateInventoryItem, useDeleteInventoryItem, useInventory, useUpdateInventoryItem, type InventoryItem } from "../api/hooks";
import Layout from "../components/Layout";
import LoadingSkeleton from "../components/LoadingSkeleton";
import { useWorkspaceMode } from "../context/WorkspaceModeContext";
import EvidencePriorityQueue from "../components/EvidencePriorityQueue";
import BusinessWorkspacePanel from "../components/BusinessWorkspacePanel";

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

function daysUntil(dateValue: string, now = new Date()): number {
  const [year, month, day] = dateValue.split("-").map(Number);
  return Math.round((Date.UTC(year, month - 1, day) - Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())) / 86_400_000);
}

function InventoryReminders({ items }: { items: InventoryItem[] }) {
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">("default");
  const [today, setToday] = useState(() => new Date());
  const notified = useRef(new Set<string>());
  const due = items.filter((item) => item.expiry_date && item.reminder_days_before !== null && item.reminder_days_before !== undefined && daysUntil(item.expiry_date, today) >= 0 && daysUntil(item.expiry_date, today) <= item.reminder_days_before);

  useEffect(() => {
    setPermission("Notification" in window ? Notification.permission : "unsupported");
  }, []);

  useEffect(() => {
    const check = () => {
      const now = new Date();
      setToday(now);
      if (!("Notification" in window) || Notification.permission !== "granted") return;
      for (const item of items) {
        if (!item.expiry_date || item.reminder_days_before == null) continue;
        const remaining = daysUntil(item.expiry_date, now);
        if (remaining < 0 || remaining > item.reminder_days_before) continue;
        const marker = `freshsense-reminder:${item.id}:${item.expiry_date}:${item.reminder_days_before}`;
        try { if (localStorage.getItem(marker)) continue; } catch { /* Keep this session usable when browser storage is blocked. */ }
        if (notified.current.has(marker)) continue;
        notified.current.add(marker);
        const body = remaining === 0 ? "Its package date is today. Check the label and your storage conditions." : `Its package date is in ${remaining} day${remaining === 1 ? "" : "s"}.`;
        const sendNotification = async () => {
          try {
            if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
              const registration = await navigator.serviceWorker.ready;
              await registration.showNotification("FreshSense pantry reminder", { body: `${item.product_name}: ${body}`, icon: "/icons/icon-192.svg", data: { url: "/inventory" } });
            } else {
              const notification = new Notification("FreshSense pantry reminder", { body: `${item.product_name}: ${body}` });
              notification.onclick = () => { window.focus(); window.location.assign("/inventory"); };
            }
            try { localStorage.setItem(marker, "sent"); } catch { /* In-memory de-duplication prevents repeat alerts this session. */ }
          } catch { /* The in-app reminder list remains visible if OS alerts are blocked. */ }
        };
        void sendNotification();
      }
    };
    check();
    const timer = window.setInterval(check, 60_000);
    window.addEventListener("focus", check);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", check); };
  }, [items]);

  const enable = async () => {
    if (!("Notification" in window)) { setPermission("unsupported"); return; }
    try { setPermission(await Notification.requestPermission()); }
    catch { setPermission("denied"); }
  };

  return (
    <section className="mt-4 rounded-2xl border border-indigo-200 bg-indigo-50 p-4" aria-label="Expiry reminders">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-indigo-950">Expiry reminders</h2>
          <p className="mt-1 text-sm text-indigo-900">{due.length ? `${due.length} tracked batch${due.length === 1 ? "" : "es"} is inside its reminder window.` : "Choose a reminder window on any batch to add it here."}</p>
          <p className="mt-1 text-xs text-indigo-800">Browser alerts are checked while FreshSense is open. The in-app date watch remains available any time.</p>
        </div>
        {permission === "granted" ? <span className="rounded-full bg-indigo-100 px-3 py-1.5 text-xs font-semibold text-indigo-900">Browser alerts enabled</span>
          : permission === "unsupported" || permission === "denied" ? <span className="text-xs text-indigo-900">Browser alerts unavailable or blocked</span>
            : <button type="button" onClick={enable} className="rounded-lg bg-indigo-900 px-3 py-2 text-sm font-semibold text-white">Enable browser alerts</button>}
      </div>
      {due.length > 0 && <ul className="mt-3 grid gap-2 sm:grid-cols-2">{due.map((item) => <li key={item.id} className="rounded-xl border border-indigo-100 bg-white p-3 text-sm"><span className="font-semibold text-slate-900">{item.product_name}</span><span className="ml-2 text-slate-600">{daysUntil(item.expiry_date!, today) === 0 ? "label date today" : `${daysUntil(item.expiry_date!, today)} days to label date`}</span></li>)}</ul>}
    </section>
  );
}

function InventoryRow({ item }: { item: InventoryItem }) {
  const { mode } = useWorkspaceMode();
  const business = mode === "business";
  const [quantity, setQuantity] = useState(String(item.quantity));
  const [expiryDate, setExpiryDate] = useState(item.expiry_date ?? "");
  const [category, setCategory] = useState(item.category ?? "");
  const [stockLocation, setStockLocation] = useState(item.stock_location ?? "");
  const [storageNotes, setStorageNotes] = useState(item.storage_notes ?? "");
  const [openedDate, setOpenedDate] = useState(item.opened_date ?? "");
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
    <li id={`batch-${item.id}`} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-900">{item.product_name}</h3>
            {item.category && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{item.category}</span>}
          </div>
          <p className="mt-1 text-sm text-slate-600">{dateLabel(item.expiry_date)} <span className="text-slate-400">/</span> {sourceCopy(item.expiry_source)}</p>
          <p className="mt-1 text-xs text-slate-500">{business ? "Received" : "Added"} {item.created_at ? new Date(item.created_at).toLocaleDateString() : "date not available"}{item.storage_location && item.storage_location !== "unknown" ? ` · ${item.storage_location.replaceAll("_", " ")}` : ""}{business && item.stock_location ? ` · ${item.stock_location}` : ""}</p>
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${statusStyle(item.status)}`}>{statusCopy(item)}</span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <label className="block text-xs font-medium text-slate-500">{business ? "Stock on hand in this batch" : "Quantity in this batch"}
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
      <details className="mt-3 rounded-xl border border-slate-200 bg-slate-50">
        <summary className="cursor-pointer px-3 py-2.5 text-sm font-semibold text-slate-700">Storage context & reminders</summary>
        <div className="grid gap-3 border-t border-slate-200 p-3 sm:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">Product category
            <input value={category} onChange={(e) => setCategory(e.target.value)} onBlur={() => { if (category !== (item.category ?? "")) update.mutate({ id: item.id, category: category.trim() || null }, { onSuccess: () => setFeedback("Product category saved."), onError: () => setFeedback("Category could not be saved.") }); }} maxLength={80} placeholder="e.g. Dairy, canned food" className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="block text-xs font-medium text-slate-600">Stored in
            <select value={item.storage_location} onChange={(e) => update.mutate({ id: item.id, storage_location: e.target.value as NonNullable<InventoryItem["storage_location"]> }, { onSuccess: () => setFeedback("Storage location saved."), onError: () => setFeedback("Storage details could not be saved.") })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
              <option value="unknown">Not recorded</option><option value="pantry">Pantry</option><option value="refrigerator">Refrigerator</option><option value="freezer">Freezer</option><option value="room_temperature">Room temperature</option><option value="other">Other</option>
            </select>
          </label>
          {business && <label className="block text-xs font-medium text-slate-600">Branch / stock location
            <input value={stockLocation} onChange={(event) => setStockLocation(event.target.value)} onBlur={() => { if (stockLocation !== (item.stock_location ?? "")) update.mutate({ id: item.id, stock_location: stockLocation.trim() || null }, { onSuccess: () => setFeedback("Stock location saved."), onError: () => setFeedback("Stock location could not be saved.") }); }} maxLength={120} placeholder="e.g. Store 2 · Cold room" className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>}
          <label className="block text-xs font-medium text-slate-600">Opened on
            <input type="date" value={openedDate} onChange={(e) => setOpenedDate(e.target.value)} onBlur={() => { if (openedDate !== (item.opened_date ?? "")) update.mutate({ id: item.id, opened_date: openedDate || null }, { onSuccess: () => setFeedback("Opened date saved."), onError: () => setFeedback("Opened date could not be saved.") }); }} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="block text-xs font-medium text-slate-600">Remind me
            <select disabled={!item.expiry_date} value={item.reminder_days_before ?? "none"} onChange={(e) => update.mutate({ id: item.id, reminder_days_before: e.target.value === "none" ? null : Number(e.target.value) as 1 | 3 | 7 }, { onSuccess: () => setFeedback("Reminder preference saved."), onError: () => setFeedback("Reminder could not be saved.") })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100">
              <option value="none">No reminder</option><option value={7}>7 days before</option><option value={3}>3 days before</option><option value={1}>1 day before</option>
            </select>
            {!item.expiry_date && <span className="mt-1 block font-normal text-slate-500">Add a package date to enable reminders.</span>}
          </label>
          <label className="block text-xs font-medium text-slate-600 sm:col-span-2">Storage or opening notes
            <textarea value={storageNotes} onChange={(e) => setStorageNotes(e.target.value)} onBlur={() => { if (storageNotes !== (item.storage_notes ?? "")) update.mutate({ id: item.id, storage_notes: storageNotes || null }, { onSuccess: () => setFeedback("Storage notes saved."), onError: () => setFeedback("Storage notes could not be saved.") }); }} maxLength={500} rows={2} placeholder="e.g. Opened Monday; kept on the middle fridge shelf" className="mt-1 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
        </div>
      </details>
      {feedback && <p role="status" className={`mt-2 text-xs ${feedback.includes("could not") ? "text-rose-700" : "text-emerald-800"}`}>{feedback}</p>}
      {(update.isError || remove.isError) && <p role="alert" className="mt-2 text-xs text-rose-700">Could not save that change. Please retry.</p>}
    </li>
  );
}

export default function Inventory() {
  const { mode, workspaceId, setWorkspaceId } = useWorkspaceMode();
  const business = mode === "business";
  const workspacesQuery = useBusinessWorkspaces();
  const workspaces = workspacesQuery.data ?? [];
  const activeWorkspace = workspaces.find((workspace) => workspace.id === workspaceId);
  const inventory = useInventory(mode, workspaceId);
  const create = useCreateInventoryItem();
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [expiryDate, setExpiryDate] = useState("");
  const [stockLocation, setStockLocation] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (!business || !workspacesQuery.data) return;
    if (!workspaceId || !workspaces.some((workspace) => workspace.id === workspaceId)) {
      setWorkspaceId(workspaces[0]?.id ?? null);
    }
  }, [business, workspaces, workspacesQuery.data, workspaceId, setWorkspaceId]);

  const items = inventory.data ?? [];
  const summary = useMemo(() => ({
    batches: items.length,
    units: items.reduce((sum, item) => sum + item.quantity, 0),
    attention: items.filter((item) => ["expired", "urgent", "soon"].includes(item.status)).length,
    expiringUnits: items.filter((item) => item.status === "urgent" || item.status === "soon").reduce((sum, item) => sum + item.quantity, 0),
    expiredUnits: items.filter((item) => item.status === "expired").reduce((sum, item) => sum + item.quantity, 0),
    undated: items.filter((item) => item.status === "unknown").length
  }), [items]);
  const next = items.find((item) => ["expired", "urgent", "soon"].includes(item.status));
  const needsDate = items.find((item) => item.status === "unknown");
  const insight = next
    ? `${next.product_name}: ${statusCopy(next).toLowerCase()}. Check the package and ${business ? "review this stock batch" : "plan this batch"} first.`
    : needsDate
      ? `${needsDate.product_name} has no date recorded. Check its package and add the date to sharpen your ${business ? "stock timeline" : "pantry timeline"}.`
      : items.length
        ? "Your tracked batches have no label dates due within the next 7 days. FreshSense will update this queue as dates approach."
        : `Add a ${business ? "received stock batch" : "scanned purchase"} to start your expiry watch. FreshSense will sort batches by their recorded package dates.`;

  const visible = items.filter((item) => {
    const matchesQuery = `${item.product_name} ${item.category ?? ""}`.toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === "all" || (filter === "attention" && ["expired", "urgent", "soon"].includes(item.status)) || (filter === "undated" && item.status === "unknown");
    return matchesQuery && matchesFilter;
  });

  const addManual = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    setFormError("");
    const count = Number(quantity);
    if (!name.trim()) { setFormError("Enter a product name."); return; }
    if (!Number.isInteger(count) || count < 1 || count > 9999) { setFormError("Quantity must be between 1 and 9,999."); return; }
    create.mutate({ product_name: name.trim(), category: category.trim() || undefined, quantity: count, expiry_date: expiryDate || undefined, expiry_source: expiryDate ? "user_entered" : "unknown", ...(business && stockLocation.trim() ? { stock_location: stockLocation.trim() } : {}) }, {
      onSuccess: () => { setName(""); setCategory(""); setQuantity("1"); setExpiryDate(""); setStockLocation(""); },
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
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">FreshSense / {business ? "Seller stock intelligence" : "Pantry intelligence"}</p>
            <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{business ? "Stock & expiry manager" : "Food inventory"}</h1>
                <p className="mt-2 max-w-xl text-sm text-slate-300">{business ? "Record received stock by batch, see units on hand, and review quantities with package dates due soon." : "Every purchase is a batch. Confirm the label date, track its quantity, and see what needs attention next."}</p>
              </div>
              <Link to="/scan" className="rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-emerald-300">{business ? "Scan incoming stock" : "Scan a purchase"}</Link>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {(business ? [["Batches", summary.batches], ["Units on hand", summary.units], ["Units due ≤7 days", summary.expiringUnits], ["Units past date", summary.expiredUnits]] : [["Batches", summary.batches], ["Units tracked", summary.units], ["Date watch", summary.attention], ["Need a date", summary.undated]]).map(([label, value]) => (
                <div key={String(label)} className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-3 backdrop-blur">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {business && <BusinessWorkspacePanel
          workspaces={workspaces}
          selectedId={workspaceId}
          onSelect={setWorkspaceId}
          onCreated={setWorkspaceId}
        />}

        {business && workspacesQuery.isPending ? <div className="mt-4"><LoadingSkeleton lines={4} /></div>
          : business && workspacesQuery.isError ? <p role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">Could not load your business workspaces. Check the connection and retry.</p>
            : business && !activeWorkspace ? null : <>

        <section className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 sm:p-5" aria-label="FreshSense Copilot insight">
          <div className="flex items-start gap-3">
            <span aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-800 text-sm text-white">✦</span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-900">FreshSense Copilot / {business ? "Stock review signal" : "Use-next signal"}</p>
              <p className="mt-1 text-sm font-medium text-slate-900">{insight}</p>
              <p className="mt-1 text-xs text-slate-600">Prioritized from dates you confirmed or entered. This is an organizing cue, not a food-safety verdict.</p>
            </div>
          </div>
        </section>

        <InventoryReminders items={items} />

        <EvidencePriorityQueue items={items} business={business} />

        <details className="mt-4 rounded-2xl border border-slate-200 bg-white shadow-sm">
          <summary className="cursor-pointer list-none px-4 py-4 font-semibold text-slate-800 marker:content-none">+ {business ? "Receive a stock batch manually" : "Add a batch manually"}</summary>
          <form noValidate onSubmit={addManual} className="grid gap-3 border-t border-slate-100 p-4 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">Product name<input value={name} onChange={(e) => setName(e.target.value)} maxLength={160} placeholder="e.g. Canned tuna" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">Category<input value={category} onChange={(e) => setCategory(e.target.value)} maxLength={80} placeholder="e.g. Canned food" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">{business ? "Units received" : "Quantity purchased"}<input type="number" min={1} max={9999} value={quantity} onChange={(e) => setQuantity(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            <label className="text-sm font-medium text-slate-700">Expiry / best-before date<input type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /><span className="mt-1 block text-xs font-normal text-slate-500">Leave blank if there is no readable date.</span></label>
            {business && <label className="text-sm font-medium text-slate-700">Branch / stock location<input value={stockLocation} onChange={(e) => setStockLocation(e.target.value)} maxLength={120} placeholder="e.g. Store 2 · Cold room" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>}
            {formError && <p role="alert" className="text-sm text-rose-700 sm:col-span-2">{formError}</p>}
            <button type="submit" disabled={create.isPending} className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60 sm:col-span-2">{create.isPending ? "Saving batch…" : business ? "Receive stock" : "Add batch"}</button>
          </form>
        </details>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-900">{business ? "Stock batches" : "Tracked batches"}</h2>
            <p className="mt-1 text-sm text-slate-500">{business ? "Each delivery lot keeps its own count and package date." : "A different purchase can have a different expiry date."}</p>
          </div>
          <label className="sr-only" htmlFor="inventory-search">{business ? "Search stock" : "Search pantry"}</label>
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
            </>}
      </div>
    </Layout>
  );
}
