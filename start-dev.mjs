import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const root = dirname(fileURLToPath(import.meta.url));
const backend = join(root, "backend");
const frontend = join(root, "frontend");
const windows = process.platform === "win32";
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
const vite = join(
  frontend,
  "node_modules",
  ".bin",
  windows ? "vite.cmd" : "vite",
);

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

function launch(command, args, cwd, name, shell = false) {
  const child = spawn(command, args, {
    cwd,
    stdio: "inherit",
    shell,
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

console.log("Backend:  http://127.0.0.1:8000  (API docs: /docs)");
console.log("Frontend: http://127.0.0.1:5173");
console.log("Press Ctrl+C to stop both services.");

launch(python, ["-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"], backend, "Backend");
launch("npm", ["run", "dev", "--", "--host", "127.0.0.1"], frontend, "Frontend", windows);
