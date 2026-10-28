import { spawnSync } from "node:child_process";

const api = process.env.MOBILE_API_URL;
if (!api) throw new Error("Set MOBILE_API_URL to your reachable backend URL, ending in /api/v1.");
const url = new URL(api);
if (!url.pathname.endsWith("/api/v1") || url.username || url.password || url.search || url.hash) {
  throw new Error("MOBILE_API_URL must be an API base URL ending in /api/v1, without credentials or query parameters.");
}
if (url.protocol !== "https:" && !(url.protocol === "http:" && process.env.MOBILE_ALLOW_HTTP === "1")) {
  throw new Error("Mobile release builds require HTTPS. For local device testing only, set MOBILE_ALLOW_HTTP=1.");
}
const env = { ...process.env, VITE_API_URL: api, VITE_NATIVE_BUILD: "1" };
for (const args of [["run", "build"], ["exec", "cap", "sync", ...process.argv.slice(2)]]) {
  const result = spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", args, { env, stdio: "inherit" });
  if (result.status !== 0) process.exit(result.status || 1);
}
