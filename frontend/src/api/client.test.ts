import type { InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it } from "vitest";
import { apiClient } from "./client";

describe("browser session requests", () => {
  afterEach(() => {
    document.cookie = "freshsense_csrf=; Max-Age=0; Path=/";
  });

  it("sends cookies and attaches the CSRF token without a bearer header", async () => {
    document.cookie = "freshsense_csrf=csrf-demo-token; Path=/; SameSite=Strict";
    let captured: InternalAxiosRequestConfig | undefined;

    await apiClient.post("/auth/logout", {}, {
      adapter: async (config) => {
        captured = config;
        return {
          data: null,
          status: 204,
          statusText: "No Content",
          headers: {},
          config
        };
      }
    });

    expect(apiClient.defaults.withCredentials).toBe(true);
    expect(captured?.headers.get("X-CSRF-Token")).toBe("csrf-demo-token");
    expect(captured?.headers.get("Authorization")).toBeUndefined();
  });
});
