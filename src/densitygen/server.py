"""A zero-dependency local server for the densitygen viz.

Serves the baked bundle as static files and exposes ``POST /api/screen`` so the
"suggest a precursor" input can re-rank live. The endpoint runs the *same*
``screen()`` the CLI does -- the browser never scores anything itself, it only
renders what this returns. Pure stdlib (``http.server``) so ``ald-screen serve``
works with no extra installs.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from densitygen.schemas import ScreeningRequest
from densitygen.screen import screen
from densitygen.viz import response_to_payload, write_bundle


def _make_handler(bundle_dir: Path, api_url: str):
    class Handler(BaseHTTPRequestHandler):
        # Quieter logging; one line per request is enough for a demo server.
        def log_message(self, fmt, *args):  # noqa: A003
            print("densitygen-serve:", fmt % args)

        def _cors(self):
            # REASON: the viz may be opened from file:// or a different port than
            # the API; allow any origin so the live re-rank fetch isn't blocked.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self):  # noqa: N802
            self.send_response(204)
            self._cors()
            self.end_headers()

        def _send_json(self, obj, status=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/api/screen":
                self._send_json({"error": "not found"}, 404)
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n) or b"{}")
                request = ScreeningRequest.model_validate(payload)
                resp = screen(request)
                out = response_to_payload(resp, request=request, mode="screen",
                                          api_url=api_url)
                self._send_json(out)
            except Exception as e:  # never 500 silently -- the UI shows this text
                self._send_json({"error": f"{type(e).__name__}: {e}"}, 400)

        def do_GET(self):  # noqa: N802
            # Static file serving rooted at the bundle dir. "/" -> the dc html.
            rel = self.path.split("?", 1)[0].lstrip("/")
            if rel in ("", "index.html"):
                rel = "densitygen.dc.html"
            target = (bundle_dir / rel).resolve()
            # Path-traversal guard: never serve outside the bundle dir.
            if bundle_dir.resolve() not in target.parents and target != bundle_dir.resolve():
                self._send_json({"error": "forbidden"}, 403)
                return
            if not target.is_file():
                self._send_json({"error": "not found"}, 404)
                return
            ctype = ("text/html" if target.suffix == ".html"
                     else "application/javascript" if target.suffix == ".js"
                     else "application/json" if target.suffix == ".json"
                     else "application/octet-stream")
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self._cors()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(request: ScreeningRequest, *, host: str = "127.0.0.1", port: int = 8765,
          bundle_dir: str | Path | None = None) -> None:
    """Bake a bundle for `request`, then serve it with a live /api/screen."""
    api_url = f"http://{host}:{port}"
    out = Path(bundle_dir or "densitygen_viz")
    resp = screen(request)
    payload = response_to_payload(resp, request=request, mode="screen", api_url=api_url)
    entry = write_bundle(payload, out)
    handler = _make_handler(out, api_url)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"densitygen viz live at  {api_url}/  (bundle: {entry})")
    print("suggest a precursor in the right rail -> live re-rank via POST /api/screen")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        httpd.shutdown()
