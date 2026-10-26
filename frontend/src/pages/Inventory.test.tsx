import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { InventoryItem } from "../api/hooks";
import { ToastProvider } from "../components/Toast";
import { WorkspaceModeProvider } from "../context/WorkspaceModeContext";
import Inventory from "./Inventory";

const sampleItems: InventoryItem[] = [
  {
    id: "milk-batch",
    product_name: "Whole milk",
    category: "Dairy",
    quantity: 2,
    expiry_date: "2027-01-10",
    expiry_source: "user_entered",
    reminder_days_before: null,
    storage_location: "refrigerator",
    stock_location: null,
    opened_date: null,
    storage_notes: null,
    days_remaining: 76,
    status: "stored",
    source_scan_id: null,
    created_at: "2026-10-26T12:00:00Z",
    updated_at: "2026-10-26T12:00:00Z"
  },
  {
    id: "beans-batch",
    product_name: "Canned chickpeas",
    category: "Canned goods",
    quantity: 4,
    expiry_date: "2027-05-14",
    expiry_source: "ocr_confirmed",
    reminder_days_before: null,
    storage_location: "pantry",
    stock_location: null,
    opened_date: null,
    storage_notes: null,
    days_remaining: 200,
    status: "stored",
    source_scan_id: null,
    created_at: "2026-10-26T12:00:00Z",
    updated_at: "2026-10-26T12:00:00Z"
  }
];

vi.mock("../api/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/hooks")>();
  return {
    ...actual,
    useBusinessWorkspaces: () => ({ data: [], isPending: false, isError: false }),
    useInventory: () => ({ data: sampleItems, isPending: false, isError: false }),
    useCreateInventoryItem: () => ({ mutate: vi.fn(), isPending: false }),
    useUpdateInventoryItem: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
    useDeleteInventoryItem: () => ({ mutate: vi.fn(), isError: false })
  };
});

function renderInventory() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/inventory"]}>
        <ToastProvider>
          <WorkspaceModeProvider>
            <Inventory />
          </WorkspaceModeProvider>
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("inventory search", () => {
  beforeEach(() => localStorage.clear());

  it("filters immediately and clear restores results and search focus", () => {
    renderInventory();
    const search = screen.getByRole("textbox", { name: "Search pantry" });

    fireEvent.change(search, { target: { value: "milk" } });
    expect(screen.getByRole("heading", { name: "Whole milk" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Canned chickpeas" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export CSV (1)" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Clear inventory search" }));

    expect(screen.getByRole("heading", { name: "Whole milk" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Canned chickpeas" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export CSV (2)" })).toBeEnabled();
    expect(search).toHaveFocus();
    expect(screen.queryByRole("button", { name: "Clear inventory search" })).not.toBeInTheDocument();
  });
});
