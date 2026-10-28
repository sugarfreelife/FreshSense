"""Export only application source for a Vercel API deployment, never local secrets/data."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = set()
for folder, suffixes in [("backend/app", {".py"}), ("backend/alembic", {".py"}), ("frontend/src", {".ts", ".tsx", ".css"}), ("frontend/public", {".svg", ".html", ".js", ".webmanifest"})]:
    paths.update(p for p in (root / folder).rglob("*") if p.is_file() and p.suffix in suffixes)
for name in ["api/index.py", "requirements.txt", ".python-version", "vercel.json", "backend/requirements-vercel.txt", "backend/requirements-production.lock", "backend/scripts/setup_product_recognition.py", "frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json", "frontend/vite.config.ts", "frontend/tailwind.config.js", "frontend/index.html"]:
    paths.add(root / name)
files = [{"file": str(p.relative_to(root)), "data": p.read_text(), "encoding": "utf-8"} for p in sorted(paths)]
payload = json.dumps(files, ensure_ascii=True)
chunk_size = 48000
if len(sys.argv) == 1:
    print(json.dumps({"files": len(files), "bytes": len(payload), "chunks": (len(payload) + chunk_size - 1) // chunk_size}))
else:
    index = int(sys.argv[1])
    print(json.dumps(payload[index * chunk_size:(index + 1) * chunk_size]))
