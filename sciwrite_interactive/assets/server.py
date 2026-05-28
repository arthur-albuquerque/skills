#!/usr/bin/env python3
"""Light local server for the sciwrite_interactive interactive editor.

Serves the editor (editor.html + css/js/vendor) and the per-run document.json,
and accepts a POST /save of the final markdown which it writes next to the
original manuscript as <stem>_revised.md. Self-terminates on parent-process
death or idle timeout so it never leaks. Inspired by the make-pages-interactive
server, with free-port selection and browser auto-open added.

Usage:
  python3 server.py --docroot <assets dir> --workdir <session dir> \
      --source <abs manuscript> [--port 0] [--idle-timeout 1800] [--no-open]
"""

import argparse
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingTCPServer

# --- Globals configured from CLI args in main() ---------------------------
DOCROOT = None          # Path to assets/ (editor.html, editor.css, editor.js, vendor/)
WORKDIR = None          # Per-manuscript session dir (document.json, checkpoint.json, server.*)
SOURCE = None           # Path to the original manuscript
INITIAL_PPID = os.getppid()
IDLE_TIMEOUT_S = 1800
_last_activity = time.time()
_activity_lock = threading.Lock()

# Only these static files may be fetched from DOCROOT (plus /vendor/*).
STATIC_FILES = {
    "/editor.html": "text/html; charset=utf-8",
    "/editor.css": "text/css; charset=utf-8",
    "/editor.js": "application/javascript; charset=utf-8",
}
VENDOR_TYPE = "application/javascript; charset=utf-8"


def _touch_activity():
    global _last_activity
    with _activity_lock:
        _last_activity = time.time()


def _idle_seconds():
    with _activity_lock:
        return time.time() - _last_activity


def revised_path():
    """Output path = same dir as source, filename <source-stem>_revised.md."""
    src = Path(SOURCE)
    return src.with_name(src.stem + "_revised.md")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    def _send(self, code, body, content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        try:
            data = path.read_bytes()
        except OSError:
            self._send(404, "not found")
            return
        self._send(200, data, content_type)

    def do_GET(self):
        _touch_activity()
        path = self.path.split("?", 1)[0]

        if path == "/":
            path = "/editor.html"

        if path == "/document.json":
            self._send_file(WORKDIR / "document.json", "application/json; charset=utf-8")
            return

        if path == "/checkpoint":
            ckpt = WORKDIR / "checkpoint.json"
            if ckpt.exists():
                self._send_file(ckpt, "application/json; charset=utf-8")
            else:
                self._send(200, "{}", "application/json; charset=utf-8")
            return

        if path in STATIC_FILES:
            self._send_file(DOCROOT / path.lstrip("/"), STATIC_FILES[path])
            return

        if path.startswith("/vendor/"):
            target = (DOCROOT / path.lstrip("/")).resolve()
            vendor_root = (DOCROOT / "vendor").resolve()
            # Path-traversal guard.
            if not str(target).startswith(str(vendor_root) + os.sep):
                self._send(403, "forbidden")
                return
            self._send_file(target, VENDOR_TYPE)
            return

        self._send(404, "not found")

    def do_POST(self):
        _touch_activity()
        path = self.path.split("?", 1)[0]

        if path == "/checkpoint":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                json.loads(body)  # validate it parses as JSON
            except ValueError:
                self._send(400, "bad request")
                return
            # Atomic write: a partial/failed POST never corrupts the saved draft.
            ckpt = WORKDIR / "checkpoint.json"
            tmp = WORKDIR / "checkpoint.json.tmp"
            tmp.write_bytes(body)
            os.replace(tmp, ckpt)
            self._send(200, '{"ok":true}', "application/json; charset=utf-8")
            return

        if path != "/save":
            self._send(404, "not found")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            markdown = data["markdown"]
        except (ValueError, KeyError):
            self._send(400, "bad request")
            return

        out = revised_path()
        out.write_text(markdown, encoding="utf-8")
        # Sentinel so the agent can detect completion.
        out.with_name(".sciwrite-done").write_text(
            str(out), encoding="utf-8"
        )
        # Finish = done: clear the autosaved draft so the next open starts fresh.
        (WORKDIR / "checkpoint.json").unlink(missing_ok=True)
        self._send(
            200,
            json.dumps({"path": str(out)}),
            "application/json; charset=utf-8",
        )


class ReuseTCP(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _watchdog():
    """Exit on idle timeout only.

    We do NOT exit on parent death because the server may be launched via
    setsid/nohup so that it survives the launching shell (e.g. a bash tool
    with a short timeout).  The idle-timeout is the only leak-guard we need.
    """
    while True:
        time.sleep(5)
        if IDLE_TIMEOUT_S > 0 and _idle_seconds() > IDLE_TIMEOUT_S:
            sys.stderr.write(
                f"sciwrite_interactive server: idle >{IDLE_TIMEOUT_S}s, shutting down\n"
            )
            os._exit(0)


def main():
    global DOCROOT, WORKDIR, SOURCE, IDLE_TIMEOUT_S
    ap = argparse.ArgumentParser()
    ap.add_argument("--docroot", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--idle-timeout", type=int, default=1800)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    DOCROOT = Path(args.docroot).resolve()
    WORKDIR = Path(args.workdir).resolve()
    SOURCE = str(Path(args.source).resolve())
    IDLE_TIMEOUT_S = args.idle_timeout
    WORKDIR.mkdir(parents=True, exist_ok=True)

    # Free-port selection when --port 0.
    srv = ReuseTCP(("127.0.0.1", args.port), Handler)
    port = srv.socket.getsockname()[1]
    url = f"http://127.0.0.1:{port}/"

    print(f"SciWrite Interactive editor: {url}", flush=True)
    print(f"Revised file will be saved to: {revised_path()}", flush=True)

    # Discoverable handles so a later session can detect / reopen this server.
    (WORKDIR / "server.pid").write_text(str(os.getpid()), encoding="utf-8")
    (WORKDIR / "server.url").write_text(url, encoding="utf-8")

    threading.Thread(target=_watchdog, daemon=True).start()

    if not args.no_open:
        # Open after the server is ready to accept connections.
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
