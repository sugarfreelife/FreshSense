import type { InventoryItem } from "./api/hooks";

const CSV_COLUMNS = [
  "Product",
  "Category",
  "Quantity",
  "Package date",
  "Date source",
  "Status",
  "Days to package date",
  "Storage location",
  "Branch / stock location",
  "Opened on",
  "Reminder days before",
  "Storage notes",
  "Batch added"
] as const;

function csvCell(value: string | number | null): string {
  const text = value === null ? "" : String(value);
  // Neutralize spreadsheet formulas even when whitespace/control characters come first.
  const safe = /^[\u0000-\u0020]*[=+\-@]/.test(text) ? `'${text}` : text;
  return `"${safe.replaceAll('"', '""')}"`;
}

function dateOnly(value: string | null): string {
  return value ? value.slice(0, 10) : "";
}

export function buildInventoryCsv(items: InventoryItem[]): string {
  const rows = items.map((item) => [
    item.product_name,
    item.category,
    item.quantity,
    dateOnly(item.expiry_date),
    item.expiry_source === "ocr_confirmed"
      ? "OCR read, confirmed by user"
      : item.expiry_source === "user_entered"
        ? "Entered by user"
        : "Not recorded",
    item.status,
    item.days_remaining,
    item.storage_location.replaceAll("_", " "),
    item.stock_location ?? null,
    dateOnly(item.opened_date),
    item.reminder_days_before,
    item.storage_notes,
    dateOnly(item.created_at)
  ]);

  return [CSV_COLUMNS, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n");
}

export function inventoryCsvFilename(scope: string, date = new Date()): string {
  const safeScope = scope
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "inventory";
  const localDate = [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("");
  return `freshsense-${safeScope}-${localDate}.csv`;
}

export function downloadInventoryCsv(items: InventoryItem[], scope: string): void {
  if (!items.length) return;
  const file = new Blob(["\uFEFF", buildInventoryCsv(items)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = inventoryCsvFilename(scope);
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  // Give the browser time to begin reading the Blob before releasing its URL.
  window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
}
