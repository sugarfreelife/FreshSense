import { Capacitor } from "@capacitor/core";

export const isNativeApp = Capacitor.isNativePlatform();
const sessionKey = `freshsense.session:${import.meta.env.VITE_API_URL || "/api/v1"}`;

export async function nativeToken(): Promise<string | null> {
  if (!isNativeApp) return null;
  const { SecureStorage } = await import("@aparajita/capacitor-secure-storage");
  const value = await SecureStorage.get(sessionKey, false, false);
  return typeof value === "string" ? value : null;
}

export async function saveNativeSession(token?: string | null): Promise<void> {
  if (!isNativeApp) return;
  if (!token) throw new Error("The server did not create a mobile session. Please update the backend and try again.");
  const { SecureStorage, KeychainAccess } = await import("@aparajita/capacitor-secure-storage");
  await SecureStorage.set(sessionKey, token, false, false, KeychainAccess.whenUnlockedThisDeviceOnly);
}

export async function clearNativeSession(): Promise<void> {
  if (!isNativeApp) return;
  const { SecureStorage } = await import("@aparajita/capacitor-secure-storage");
  await SecureStorage.remove(sessionKey, false);
}
