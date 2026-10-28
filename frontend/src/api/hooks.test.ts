import { afterEach, describe, expect, it, vi } from "vitest";
import { createElement, type ReactNode } from "react";
import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { apiClient } from "./client";
import { resolveScanImageUrl, useLogin, useRegister } from "./hooks";

const originalBaseURL = apiClient.defaults.baseURL;

afterEach(() => {
  vi.restoreAllMocks();
  apiClient.defaults.baseURL = originalBaseURL;
});

describe("confirmed browser sessions", () => {
  function provider(client: QueryClient) {
    return ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
  }

  it("confirms the cookie on login before caching the signed-in user", async () => {
    const user = { id: "session-user", email: "session@example.com", name: "Session" };
    vi.spyOn(apiClient, "post").mockResolvedValue({ data: { user } });
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({ data: user });
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    const { result } = renderHook(() => useLogin(), { wrapper: provider(client) });
    await act(async () => {
      await result.current.mutateAsync({ email: user.email, password: "pass1234" });
    });
    expect(get).toHaveBeenCalledWith("/auth/me");
    expect(client.getQueryData(["me"])).toEqual(user);
  });

  it("does not report signup success when the browser cannot use its session", async () => {
    vi.spyOn(apiClient, "post").mockResolvedValue({ data: { user: { id: "new-user", email: "new@example.com" } } });
    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("Unauthorized"));
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    const { result } = renderHook(() => useRegister(), { wrapper: provider(client) });
    await act(async () => {
      await expect(result.current.mutateAsync({ name: "New", email: "new@example.com", password: "pass1234" })).rejects.toThrow("session could not be confirmed");
    });
    expect(client.getQueryData(["me"])).toBeUndefined();
  });
});

describe("resolveScanImageUrl", () => {
  it("resolves same-origin scan images when the production API base is relative", () => {
    apiClient.defaults.baseURL = "/api/v1";

    expect(resolveScanImageUrl("/api/v1/scans/scan-123/image")).toBe(
      `${window.location.origin}/api/v1/scans/scan-123/image`
    );
  });

  it("keeps the configured backend origin during local development", () => {
    apiClient.defaults.baseURL = "http://127.0.0.1:8000/api/v1";

    expect(resolveScanImageUrl("/api/v1/scans/scan-123/image")).toBe(
      "http://127.0.0.1:8000/api/v1/scans/scan-123/image"
    );
  });
});
