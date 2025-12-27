#!/usr/bin/env python3
"""Watch PlantUML files and serve with live reload."""

import http.server
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import unquote

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Missing watchdog. Install with: pip3 install watchdog")
    sys.exit(1)


DIAGRAMS_DIR = Path(__file__).parent / "diagrams"
PORT = 8080

# Track last change for live reload
last_change = {"time": time.time(), "file": ""}


def check_plantuml():
    """Check if plantuml is available."""
    try:
        subprocess.run(["plantuml", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PlantUML not found. Install with: brew install plantuml")
        sys.exit(1)


def build_file(path: Path):
    """Build a single PlantUML file."""
    print(f"[{time.strftime('%H:%M:%S')}] Building: {path.name}")
    result = subprocess.run(
        ["plantuml", "-tpng", str(path)],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        png_path = path.with_suffix('.png')
        print(f"  -> {png_path.name}")
        last_change["time"] = time.time()
        last_change["file"] = str(png_path.relative_to(DIAGRAMS_DIR))
    else:
        print(f"  x Error: {result.stderr}")


def build_all():
    """Build all PlantUML files."""
    print("Building all diagrams...")
    for f in DIAGRAMS_DIR.glob("**/*.puml"):
        build_file(f)
    print()


class PumlHandler(FileSystemEventHandler):
    """Handle PlantUML file changes."""

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".puml"):
            build_file(Path(event.src_path))

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".puml"):
            build_file(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.endswith(".puml"):
            build_file(Path(event.dest_path))


def get_diagrams_list():
    """Get list of PNG diagrams."""
    diagrams = []
    for f in sorted(DIAGRAMS_DIR.glob("**/*.png")):
        rel_path = f.relative_to(DIAGRAMS_DIR)
        diagrams.append({
            "path": str(rel_path),
            "name": f.stem,
            "folder": str(rel_path.parent) if rel_path.parent != Path(".") else ""
        })
    return diagrams


INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Diagrams</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex; height: 100vh; background: #1a1a1a; color: #eee;
        }
        .sidebar {
            width: 220px; background: #252525; padding: 16px;
            border-right: 1px solid #333; overflow-y: auto;
        }
        .sidebar h3 { font-size: 12px; color: #888; margin: 16px 0 8px; text-transform: uppercase; }
        .sidebar h3:first-child { margin-top: 0; }
        .sidebar a {
            display: block; padding: 8px 12px; color: #ccc; text-decoration: none;
            border-radius: 6px; margin: 2px 0; font-size: 14px;
        }
        .sidebar a:hover { background: #333; }
        .sidebar a.active { background: #0066cc; color: white; }
        .main { flex: 1; display: flex; flex-direction: column; }
        .toolbar {
            padding: 12px 20px; background: #252525; border-bottom: 1px solid #333;
            display: flex; align-items: center; gap: 16px;
        }
        .toolbar .title { font-weight: 600; }
        .toolbar .status { font-size: 12px; color: #888; margin-left: auto; }
        .toolbar .status.connected { color: #4a4; }
        .viewer { flex: 1; overflow: auto; padding: 20px; background: #2a2a2a; }
        .viewer img {
            max-width: 100%; background: white; border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .zoom-controls { display: flex; gap: 8px; }
        .zoom-controls button {
            padding: 6px 12px; background: #333; border: none; color: #ccc;
            border-radius: 4px; cursor: pointer;
        }
        .zoom-controls button:hover { background: #444; }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar"></div>
    <div class="main">
        <div class="toolbar">
            <span class="title" id="title">Select a diagram</span>
            <div class="zoom-controls">
                <button onclick="zoom(-0.1)">-</button>
                <button onclick="zoom(0.1)">+</button>
                <button onclick="resetZoom()">Reset</button>
            </div>
            <span class="status" id="status">Connecting...</span>
        </div>
        <div class="viewer" id="viewer">
            <p style="color:#666">Select a diagram from sidebar</p>
        </div>
    </div>
    <script>
        let currentPath = '';
        let scale = 1;
        let lastChange = 0;

        function loadList() {
            fetch('/api/list').then(r => r.json()).then(diagrams => {
                const sidebar = document.getElementById('sidebar');
                let html = '';
                let currentFolder = null;
                diagrams.forEach(d => {
                    if (d.folder !== currentFolder) {
                        currentFolder = d.folder;
                        html += `<h3>${currentFolder || 'Root'}</h3>`;
                    }
                    html += `<a href="#" data-path="${d.path}" onclick="selectDiagram('${d.path}')">${d.name}</a>`;
                });
                sidebar.innerHTML = html;

                // Auto-select first or from hash
                const hash = location.hash.slice(1);
                if (hash) selectDiagram(decodeURIComponent(hash));
                else if (diagrams.length) selectDiagram(diagrams[0].path);
            });
        }

        function selectDiagram(path) {
            currentPath = path;
            location.hash = path;
            document.querySelectorAll('.sidebar a').forEach(a => {
                a.classList.toggle('active', a.dataset.path === path);
            });
            document.getElementById('title').textContent = path;
            loadImage();
        }

        function loadImage() {
            if (!currentPath) return;
            const img = new Image();
            img.onload = () => {
                const viewer = document.getElementById('viewer');
                img.style.transform = `scale(${scale})`;
                img.style.transformOrigin = 'top left';
                viewer.innerHTML = '';
                viewer.appendChild(img);
            };
            img.src = '/diagrams/' + currentPath + '?t=' + Date.now();
        }

        function zoom(delta) {
            scale = Math.max(0.25, Math.min(3, scale + delta));
            const img = document.querySelector('.viewer img');
            if (img) img.style.transform = `scale(${scale})`;
        }

        function resetZoom() {
            scale = 1;
            const img = document.querySelector('.viewer img');
            if (img) img.style.transform = 'scale(1)';
        }

        function poll() {
            fetch('/api/changes').then(r => r.json()).then(data => {
                document.getElementById('status').textContent = 'Live';
                document.getElementById('status').className = 'status connected';
                if (data.time > lastChange) {
                    lastChange = data.time;
                    if (currentPath === data.file || !currentPath) {
                        loadImage();
                    }
                }
            }).catch(() => {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status';
            }).finally(() => {
                setTimeout(poll, 500);
            });
        }

        loadList();
        poll();
    </script>
</body>
</html>
"""


class DiagramHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for diagram server."""

    def log_message(self, format, *args):
        pass  # Suppress logs

    def do_GET(self):
        path = unquote(self.path)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode())

        elif path == "/api/list":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_diagrams_list()).encode())

        elif path == "/api/changes":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(last_change).encode())

        elif path.startswith("/diagrams/"):
            file_path = path.split("?")[0]  # Remove query string
            file_path = DIAGRAMS_DIR / file_path[10:]  # Remove "/diagrams/"
            if file_path.exists() and file_path.suffix in (".png", ".svg"):
                self.send_response(200)
                content_type = "image/png" if file_path.suffix == ".png" else "image/svg+xml"
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_error(404)
        else:
            self.send_error(404)


def run_server():
    """Run HTTP server in background."""
    server = http.server.HTTPServer(("", PORT), DiagramHandler)
    server.serve_forever()


def main():
    check_plantuml()
    build_all()

    # Start HTTP server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"Server running at http://localhost:{PORT}")
    print(f"Watching {DIAGRAMS_DIR} for changes...")
    print("Press Ctrl+C to stop\n")

    observer = Observer()
    observer.schedule(PumlHandler(), str(DIAGRAMS_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped.")

    observer.join()


if __name__ == "__main__":
    main()
