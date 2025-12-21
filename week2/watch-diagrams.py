#!/usr/bin/env python3
"""Watch PlantUML files and rebuild on changes."""

import subprocess
import sys
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Missing watchdog. Install with: pip3 install watchdog")
    sys.exit(1)


DIAGRAMS_DIR = Path(__file__).parent / "diagrams"


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
        print(f"  → {path.stem}.png")
    else:
        print(f"  ✗ Error: {result.stderr}")


def build_all():
    """Build all PlantUML files."""
    print("Building all diagrams...")
    for f in DIAGRAMS_DIR.glob("*.puml"):
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


def main():
    check_plantuml()
    build_all()

    print(f"Watching {DIAGRAMS_DIR} for changes...")
    print("Press Ctrl+C to stop\n")

    observer = Observer()
    observer.schedule(PumlHandler(), str(DIAGRAMS_DIR), recursive=False)
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
