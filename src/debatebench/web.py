"""A small local web UI for running and watching a debate.

Deliberately built on the standard library alone: this project's dependency
set is four packages and a web framework is not worth adding to it for a
local tool. Progress is streamed to the browser over Server-Sent Events,
which is a plain long-lived GET and needs nothing on either side.

    debatebench web                    # defaults, opens a browser
    debatebench web --port 8000        # pick a port
    debatebench web configs/example.yaml   # prefill from a config

Human mode works here too. The orchestrator blocks on a queue that the page
fills when you click a response, so picking a winner in the browser takes
the place of typing a code at a prompt.
"""

from __future__ import annotations

import json
import queue
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config import DebateConfig, load_config
from .debate import run_debate
from .orchestrator.base import Orchestrator

STATIC = Path(__file__).parent / "static"
# Sentinel pushed onto the event queue so the streaming request knows to stop.
_END = object()


class WebOrchestrator(Orchestrator):
    """Picks the winner from whatever the browser sends back."""

    def __init__(self, session: "Session"):
        self.session = session

    def pick_winner(self, topic: str, round_num: int, responses: dict[str, str]) -> str:
        self.session.emit("awaiting", {"round": round_num, "codes": list(responses)})
        while True:
            code = self.session.picks.get()
            if code in responses:
                return code
            # A stale click from an earlier round; keep waiting.


class Session:
    """One debate run: events flowing out, winner picks flowing in."""

    def __init__(self) -> None:
        self.events: queue.Queue = queue.Queue()
        self.picks: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def emit(self, kind: str, payload: dict) -> None:
        self.events.put({"type": kind, **payload})

    def start(self, config: DebateConfig) -> None:
        orchestrator = WebOrchestrator(self) if config.orchestrator.mode == "human" else None

        def work() -> None:
            try:
                run_debate(config, on_event=self.emit, orchestrator=orchestrator)
            except Exception as exc:  # surfaced in the page rather than the console
                self.emit("error", {"message": f"{type(exc).__name__}: {exc}"})
            finally:
                self.events.put(_END)

        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()


session = Session()

# Optional starting values for the form, from a config passed on the command
# line. Kept in memory rather than written next to the code.
preset: dict | None = None


class Handler(BaseHTTPRequestHandler):
    # Quieter than the default one-line-per-request logging.
    def log_message(self, fmt: str, *args) -> None:
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            page = STATIC / "index.html"
            if not page.exists():
                self._send(500, b"static/index.html is missing", "text/plain")
                return
            self._send(200, page.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/api/preset":
            self._json(200, preset or {})
            return

        if path == "/api/events":
            self._stream()
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
            return

        if path == "/api/run":
            if session.running:
                self._json(409, {"error": "a debate is already running"})
                return
            try:
                config = DebateConfig(**body)
            except Exception as exc:
                self._json(400, {"error": str(exc)})
                return
            session.start(config)
            self._json(200, {"ok": True})
            return

        if path == "/api/pick":
            code = body.get("code")
            if not code:
                self._json(400, {"error": "code is required"})
                return
            session.picks.put(code)
            self._json(200, {"ok": True})
            return

        self._send(404, b"not found", "text/plain")

    def _stream(self) -> None:
        """Server-Sent Events for the life of one debate."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            while True:
                try:
                    item = session.events.get(timeout=15)
                except queue.Empty:
                    # A comment line keeps the connection from being reaped
                    # by an idle proxy or the browser.
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue
                if item is _END:
                    self.wfile.write(b"event: end\ndata: {}\n\n")
                    self.wfile.flush()
                    return
                self.wfile.write(f"data: {json.dumps(item)}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # the page went away


def serve(port: int = 7777, config_path: str | None = None, open_browser: bool = True) -> None:
    global preset
    if config_path:
        # Load it here so a bad path fails before the server starts rather
        # than on the first request.
        preset = load_config(config_path).model_dump()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"DebateBench UI on {url}  (ctrl-c to stop)")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
