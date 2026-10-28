import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import net from "node:net";
import process from "node:process";

const root = dirname(fileURLToPath(import.meta.url));
const backend = join(root, "backend");
const frontend = join(root, "frontend");
const windows = process.platform === "win32";
const phoneMode = process.argv.includes("--phone");
const phoneHostIndex = process.argv.indexOf("--phone-host");
const phoneHostArg = phoneHostIndex >= 0 ? process.argv[phoneHostIndex + 1] : undefined;
const apiPortIndex = process.argv.indexOf("--api-port");
const requestedApiPort = apiPortIndex >= 0 ? Number(process.argv[apiPortIndex + 1]) : undefined;
const bindHost = phoneMode ? (phoneHostArg || await getPrivateIPv4()) : "127.0.0.1";
const frontendPort = await findAvailablePort(5173, bindHost);
const apiPort = requestedApiPort || await findAvailablePort(8000, bindHost);
const pythonVenv = join(
  backend,
  ".venv",
  windows ? "Scripts/python.exe" : "bin/python",
);
const python = existsSync(pythonVenv)
  ? pythonVenv
  : windows
    ? "python"
    : "python3";
const vite = join(frontend, "node_modules", "vite", "bin", "vite.js");

if (!existsSync(vite)) {
  console.error(`Frontend dependencies are missing. Run 'npm install' in ${frontend}.`);
  process.exit(1);
}

const children = [];
let stopping = false;

function stop(signal = "SIGTERM", exitCode = 0) {
  if (stopping) return;
  stopping = true;

  for (const child of children) {
    if (!child.pid || child.exitCode !== null) continue;
    if (windows) {
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], {
        stdio: "ignore",
        windowsHide: true,
      });
    } else {
      try {
        process.kill(-child.pid, signal);
      } catch {
        child.kill(signal);
      }
    }
  }
  process.exitCode = exitCode;
}

function launch(command, args, cwd, name, shell = false, env = process.env) {
  const child = spawn(command, args, {
    cwd,
    stdio: "inherit",
    shell,
    env,
    detached: !windows,
    windowsHide: false,
  });
  children.push(child);
  child.once("error", (error) => {
    console.error(`${name} failed to start: ${error.message}`);
    stop("SIGTERM", 1);
  });
  child.once("exit", (code, signal) => {
    if (!stopping) {
      const result = code ?? (signal ? 1 : 0);
      console.log(`${name} stopped${signal ? ` (${signal})` : ""}.`);
      stop("SIGTERM", result);
    }
  });
}

process.on("SIGINT", () => stop("SIGINT", 130));
process.on("SIGTERM", () => stop("SIGTERM", 143));

if (phoneMode) {
  console.log(`Backend:  http://${bindHost}:${apiPort}  (API docs: /docs)`);
  console.log(`Frontend: http://${bindHost}:${frontendPort}`);
  console.log(`Phone:    http://${bindHost}:${frontendPort} (connect phone and PC to the same Wi-Fi)`);
  console.log("Camera capture: open the app, sign in, then tap Take photo on the scan page.");
} else {
  console.log(`Backend:  http://${bindHost}:${apiPort}  (API docs: /docs)`);
  console.log(`Frontend: http://127.0.0.1:${frontendPort}`);
}
console.log("Press Ctrl+C to stop both services.");

const frontendEnv = {
  ...process.env,
  VITE_API_URL: "/api/v1",
  VITE_API_PROXY_TARGET: `http://${bindHost}:${apiPort}`,
};
const backendEnv = {
  ...process.env,
  CORS_ORIGINS: [
    `http://localhost:${frontendPort}`,
    `http://127.0.0.1:${frontendPort}`,
    ...(phoneMode ? [`http://${bindHost}:${frontendPort}`] : []),
  ].join(","),
};

const backendArgs = ["-m", "uvicorn", "app.main:app", "--host", bindHost, "--port", String(apiPort)];
// Uvicorn's Windows reload worker can fail to reattach its inherited socket
// when this launcher is started from the Codex terminal. Keep reload on Unix,
// but use one stable API process on Windows so the demo remains reachable.
if (!windows) backendArgs.push("--reload");
launch(python, backendArgs, backend, "Backend", false, backendEnv);
launch(process.execPath, [vite, "--host", bindHost, "--port", String(frontendPort), "--strictPort"], frontend, "Frontend", false, frontendEnv);

async function findAvailablePort(start, host) {
  for (let port = start; port < start + 20; port += 1) {
    const available = await new Promise((resolve) => {
      const server = net.createServer();
      server.once("error", () => resolve(false));
      server.listen({ host, port, exclusive: true }, () => server.close(() => resolve(true)));
    });
    if (available) return port;
  }
  throw new Error(`No free frontend port found near ${start}. Close another FreshSense/Vite server and retry.`);
}

async function getPrivateIPv4() {
  if (process.platform === "win32") {
    const { execFileSync } = await import("node:child_process");
    const output = execFileSync("ipconfig.exe", [], { encoding: "utf8" });
    const preferredAdapter = output.split(/\r?\n(?=[^\r\n].*adapter )/i);
    const addressFrom = (block) => {
      const ip = block.match(/IPv4[^:]*:\s*([0-9.]+)/i)?.[1];
      const gateway = block.match(/Default Gateway[^:]*:\s*([0-9.]+)/i)?.[1];
      return ip && gateway && gateway !== "0.0.0.0" && /^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/.test(ip) ? ip : null;
    };
    const address = preferredAdapter.map(addressFrom).find(Boolean);
    if (address) return address;
    throw new Error("Could not detect the private Wi-Fi address automatically. Run `ipconfig` in Command Prompt and use the IPv4 address with --phone-host, for example: node start-dev.mjs --phone --phone-host 192.168.1.23");
  }
  const { networkInterfaces } = await import("node:os");
  const entries = Object.values(networkInterfaces()).flat().filter(Boolean);
  const address = entries.find((item) => item.family === "IPv4" && !item.internal && /^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/.test(item.address));
  if (!address) throw new Error("No private Wi-Fi/LAN IPv4 address found. Connect this PC to Wi-Fi and retry.");
  return address.address;
}
