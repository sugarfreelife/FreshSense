import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";
import process from "node:process";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      disable: process.env.VITE_NATIVE_BUILD === "1",
      registerType: "autoUpdate",
      includeAssets: ["icons/icon-192.svg", "icons/icon-512.svg", "offline.html"],
      manifest: {
        name: "FreshSense AI",
        short_name: "FreshSense",
        description:
          "A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction",
        theme_color: "#16a34a",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [
          {
            src: "icons/icon-192.svg",
            sizes: "192x192",
            type: "image/svg+xml",
            purpose: "any"
          },
          {
            src: "icons/icon-512.svg",
            sizes: "512x512",
            type: "image/svg+xml",
            purpose: "any"
          },
          {
            src: "icons/icon-512.svg",
            sizes: "512x512",
            type: "image/svg+xml",
            purpose: "maskable"
          }
        ]
      },
      workbox: {
        importScripts: ["notification-click.js"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//, /^\/downloads\//],
        globPatterns: ["**/*.{js,css,html,svg,png,ico}"],
        runtimeCaching: [
          {
            urlPattern: ({ url, request }) =>
              !url.pathname.startsWith("/api/") && !url.pathname.startsWith("/downloads/") && (
                request.destination === "document" ||
                request.destination === "script" ||
                request.destination === "style" ||
                request.destination === "image"
              ),
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "freshsense-app-shell",
              expiration: { maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 }
            }
          },
          {
            // Never cache authenticated API results; network-only with offline fallback.
            urlPattern: ({ url }) => url.pathname.startsWith("/api/"),
            handler: "NetworkOnly"
          }
        ]
      }
    })
  ],
  server: {
    port: 5173,
    // Keep browser sessions on the page's origin, including localhost and LAN access.
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
        timeout: 180_000,
        proxyTimeout: 180_000
      }
    }
  },
  test: {
    environment: "jsdom",
    // Newer Node versions expose storage globals that shadow jsdom's storage.
    execArgv: process.allowedNodeEnvironmentFlags.has("--no-experimental-webstorage")
      ? ["--no-experimental-webstorage"]
      : [],
    globals: true,
    setupFiles: ["./src/test-setup.ts"]
  }
});
