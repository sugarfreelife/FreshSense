import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import InventoryAddFromScan from "./InventoryAddFromScan";
import { WorkspaceModeProvider } from "../context/WorkspaceModeContext";
import type { Scan } from "../api/hooks";

function renderInventoryForm(expiryDate: string | null) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const scan = {
    id: "synthetic-scan",
    product: { product_name: "Canned tuna", category: "Canned fish" },
    food_type: "Canned fish",
    expiry_date: expiryDate,
    expiry_text: expiryDate ? "11/2027" : null
  } as Scan;

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <WorkspaceModeProvider>
          <InventoryAddFromScan scan={scan} />
        </WorkspaceModeProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("inventory intake date confirmation", () => {
  it("keeps an OCR date unsavable until the user confirms the package", () => {
    renderInventoryForm("2027-11-30");

    const confirmButton = screen.getByRole("button", { name: "Confirm the package date to continue" });
    expect(confirmButton).toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "I checked this date against the package." }));

    expect(screen.getByRole("button", { name: "Save to pantry inventory" })).toBeEnabled();
  });

  it("requires a manual date unless the user chooses to track without one", () => {
    renderInventoryForm(null);

    expect(screen.getByRole("button", { name: "Enter a package date or choose no date" })).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: "No date is printed or I cannot verify it. Track without an expiry date." }));

    expect(screen.getByRole("button", { name: "Save to pantry inventory" })).toBeEnabled();
  });
});
