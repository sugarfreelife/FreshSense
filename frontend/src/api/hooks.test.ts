import { afterEach, describe, expect, it } from "vitest";
import { apiClient } from "./client";
import { resolveScanImageUrl } from "./hooks";

const originalBaseURL = apiClient.defaults.baseURL;

afterEach(() => {
  apiClient.defaults.baseURL = originalBaseURL;
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
