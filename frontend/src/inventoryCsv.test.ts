import { describe, expect, it } from "vitest";
import type { InventoryItem } from "./api/hooks";
import { buildInventoryCsv, inventoryCsvFilename } from "./inventoryCsv";

const sample: InventoryItem = {
  id: "batch-1",
  product_name: "Canned chickpeas",
  category: "Canned goods",
  quantity: 12,
  expiry_date: "2027-05-14",
  expiry_source: "ocr_confirmed",
  reminder_days_before: 7,
  storage_location: "pantry",
  stock_location: "North store",
  opened_date: null,
  storage_notes: 'Keep dry, shelf "A"',
  days_remaining: 200,
  status: "stored",
  source_scan_id: "scan-1",
  created_at: "2026-10-26T12:00:00Z",
  updated_at: "2026-10-26T12:00:00Z"
};

describe("inventory CSV export", () => {
  it("exports the selected batch fields with quoted commas and dates", () => {
    const csv = buildInventoryCsv([{ ...sample, storage_notes: 'Keep dry, shelf "A"' }]);
    expect(csv).toContain('"Product","Category","Quantity","Package date"');
    expect(csv).toContain('"Canned chickpeas","Canned goods","12","2027-05-14"');
    expect(csv).toContain('"OCR read, confirmed by user"');
    expect(csv).toContain('"Keep dry, shelf ""A"""');
    expect(csv).toContain('"2026-10-26"');
  });

  it("neutralizes spreadsheet formulas and preserves embedded line breaks", () => {
    const csv = buildInventoryCsv([{ ...sample, product_name: "  =HYPERLINK(\"https://example.test\")", storage_notes: "line one\nline two" }]);
    expect(csv).toContain("\"'  =HYPERLINK(\"\"https://example.test\"\")\"");
    expect(csv).toContain('"line one\nline two"');
  });

  it("creates a safe filename from a workspace name using the local date", () => {
    expect(inventoryCsvFilename("Épicerie / North", new Date(2026, 9, 26))).toBe("freshsense-epicerie-north-20261026.csv");
  });
});
