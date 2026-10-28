import type { CapacitorConfig } from "@capacitor/cli";
import process from "node:process";

const config: CapacitorConfig = {
  appId: "app.freshsense.mobile",
  appName: "FreshSense AI",
  webDir: "dist",
  server: { androidScheme: "https", cleartext: process.env.MOBILE_ALLOW_HTTP === "1" },
  ios: { contentInset: "never" },
  plugins: { CapacitorHttp: { enabled: true } }
};

export default config;
