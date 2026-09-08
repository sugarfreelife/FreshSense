import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import ResultCard from "./components/ResultCard";
import { ToastProvider } from "./components/Toast";

function renderApp(initialEntries: string[]) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } }
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={initialEntries}>
        <ToastProvider>
          <App />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("routing", () => {
  it("renders landing page with Start Scan CTA", () => {
    renderApp(["/"]);
    expect(screen.getByRole("heading", { name: /freshsense ai/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /start scan/i })).toBeInTheDocument();
  });

  it("renders login page", () => {
    renderApp(["/login"]);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });
});

describe("ResultCard", () => {
  it("renders freshness, confidence, expiry, VOC/temp/humidity, recommendation, sources and warnings", () => {
    render(
      <ResultCard
        scan={{
          id: "scan-1",
          food_type: "milk",
          freshness: "Spoiled",
          freshness_label: "Spoiled",
          confidence: 0.92,
          expiry_date: "2026-09-01",
          shelf_life_days: 0,
          voc_index: 780,
          temperature_c: 8,
          humidity_pct: 70,
          recommendation: "Do not consume. Discard safely.",
          sources: ["vision", "ocr", "voc"],
          warnings: ["High VOC level detected"],
          created_at: "2026-09-08T00:00:00Z"
        }}
      />
    );

    expect(screen.getByText("Spoiled")).toBeInTheDocument();
    expect(screen.getByText(/92%/)).toBeInTheDocument();
    expect(screen.getByText("2026-09-01")).toBeInTheDocument();
    expect(screen.getByText(/8 °C/)).toBeInTheDocument();
    expect(screen.getByText(/70% RH/)).toBeInTheDocument();
    expect(screen.getByText(/780/)).toBeInTheDocument();
    expect(screen.getByText(/Do not consume/)).toBeInTheDocument();
    expect(screen.getByText("vision")).toBeInTheDocument();
    expect(screen.getByText(/High VOC level detected/)).toBeInTheDocument();
  });

  it("handles missing optional fields without crashing", () => {
    render(<ResultCard scan={{ id: "scan-2" }} />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
    expect(screen.getByText("Not detected")).toBeInTheDocument();
  });
});
