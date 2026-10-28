import { afterEach, describe, expect, it, vi } from "vitest";
import axios from "axios";

const storage = vi.hoisted(() => ({
  get: vi.fn(), set: vi.fn(), remove: vi.fn()
}));
vi.mock("@capacitor/core", () => ({ Capacitor: { isNativePlatform: () => true } }));
vi.mock("@aparajita/capacitor-secure-storage", () => ({
  SecureStorage: storage, KeychainAccess: { whenUnlockedThisDeviceOnly: 1 }
}));

afterEach(() => { vi.resetModules(); vi.clearAllMocks(); vi.unstubAllEnvs(); });

describe("native session transport", () => {
  it("stores the token in secure native storage and authenticates API requests without browser cookies", async () => {
    vi.stubEnv("VITE_API_URL", "https://api.freshsense.test/api/v1");
    storage.get.mockResolvedValue("native-token");
    const { saveNativeSession, clearNativeSession } = await import("../native/session");
    const { apiClient } = await import("./client");
    await saveNativeSession("native-token");
    expect(storage.set).toHaveBeenCalledWith(expect.any(String), "native-token", false, false, 1);
    const request = await apiClient.get("/auth/me", { adapter: async (config) => ({ data: null, status: 200, statusText: "OK", headers: {}, config }) });
    expect(request.config.withCredentials).toBe(false);
    expect(request.config.headers.Authorization).toBe("Bearer native-token");
    expect(request.config.headers["X-FreshSense-Client"]).toBe("native");
    expect(request.config.headers["X-CSRF-Token"]).toBeUndefined();
    await clearNativeSession();
    expect(storage.remove).toHaveBeenCalledWith(expect.any(String), false);
  });

  it("does not attach the stored token to a different host", async () => {
    vi.stubEnv("VITE_API_URL", "https://api.freshsense.test/api/v1");
    storage.get.mockResolvedValue("native-token");
    const { apiClient } = await import("./client");
    const response = await apiClient.get("https://other.test/image.jpg", { adapter: async (config) => ({ data: null, status: 200, statusText: "OK", headers: {}, config }) });
    expect(axios.isAxiosError(response)).toBe(false);
    expect(response.config.headers.Authorization).toBeUndefined();
  });
});
