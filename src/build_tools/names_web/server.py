"""HTTP server for the Pipe-Works consumer-facing names app.

This server has one job: present a lightweight browser UI while delegating
runtime truth to ``pipeworks-namegen-api``. To keep that boundary explicit, the
names app serves static assets locally and proxies only the narrow API routes
needed by the first consumer workflow cut.
"""

from __future__ import annotations

import json
import mimetypes
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pipeworks_namegen_lexicon import __version__

mimetypes.add_type("font/woff2", ".woff2")

STATIC_DIR = Path(__file__).resolve().parent / "static"
CREATOR_STATIC_DIR = Path(__file__).resolve().parent.parent / "syllable_walk_web" / "static"
AUTO_PORT_PRIMARY_START = 8380
AUTO_PORT_PRIMARY_TRIES = 50
AUTO_PORT_FALLBACK_START = 8400
AUTO_PORT_FALLBACK_TRIES = 200
NAMES_LOG_LABEL = "pipeworks-names-web"

SHARED_STATIC_MAP: dict[str, Path] = {
    "pipe-works-fonts.css": CREATOR_STATIC_DIR / "css" / "pipe-works-fonts.css",
    "pipe-works-base.css": CREATOR_STATIC_DIR / "css" / "pipe-works-base.css",
}

PROXIED_GET_PATHS: set[str] = {
    "/api/version",
    "/api/generation/package-options",
    "/api/generation/package-syllables",
    "/api/favorites",
    "/api/favorites/tags",
}

PROXIED_POST_PATHS: set[str] = {
    "/api/generate",
    "/api/favorites",
    "/api/favorites/delete",
    "/api/favorites/update",
}


def is_port_available(bind_host: str, port: int) -> bool:
    """Return whether ``bind_host:port`` can be bound locally."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_host, port))
        except OSError:
            return False
    return True


def find_available_port(
    bind_host: str,
    *,
    start: int,
    tries: int,
) -> int | None:
    """Scan a local port range and return the first available port."""

    for port in range(start, start + tries):
        if is_port_available(bind_host, port):
            return port
    return None


def select_auto_port(bind_host: str) -> int:
    """Pick the first preferred local port for the names app."""

    primary = find_available_port(
        bind_host,
        start=AUTO_PORT_PRIMARY_START,
        tries=AUTO_PORT_PRIMARY_TRIES,
    )
    if primary is not None:
        return primary

    fallback = find_available_port(
        bind_host,
        start=AUTO_PORT_FALLBACK_START,
        tries=AUTO_PORT_FALLBACK_TRIES,
    )
    if fallback is not None:
        return fallback

    raise RuntimeError("No available port found for the names app.")


class NamesAppHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the consumer-facing names app."""

    server_version = "PipeWorksNamesApp/0.1"
    verbose: bool = True
    api_base_url: str = "http://127.0.0.1:8360"
    service_log_label: str = NAMES_LOG_LABEL
    _response_body_enabled: bool = True

    def do_GET(self) -> None:  # noqa: N802
        """Handle ``GET`` requests."""

        self._response_body_enabled = True
        self._handle_read_request()

    def do_HEAD(self) -> None:  # noqa: N802
        """Handle ``HEAD`` requests using the same routing as ``GET``."""

        self._response_body_enabled = False
        self._handle_read_request()

    def do_POST(self) -> None:  # noqa: N802
        """Handle ``POST`` requests."""

        parsed = urlparse(self.path)
        if parsed.path in PROXIED_POST_PATHS:
            body = self._read_request_body()
            self._proxy_request("POST", self.path, body)
            return

        self._send_error(404, f"Unknown API route: {parsed.path}")

    def _handle_read_request(self) -> None:
        """Route read-only requests for static assets or proxied API calls."""

        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self._serve_static("index.html")
            return

        if path == "/health":
            self._send_json({"status": "ok", "service": "names_app"})
            return

        if path == "/api/app-config":
            self._send_json(
                {
                    "app_name": "Pipe-Works Names",
                    "app_version": __version__,
                    "api_base_url": self.api_base_url,
                }
            )
            return

        if path.startswith("/static/"):
            self._serve_static(path.removeprefix("/static/"))
            return

        if path in PROXIED_GET_PATHS:
            self._proxy_request("GET", self.path, None)
            return

        self._send_error(404, f"Unknown route: {path}")

    def _resolve_static_path(self, rel_path: str) -> Path:
        """Resolve one static asset path for the names app.

        The names app intentionally reuses the shared Pipe-Works font and base
        styles from the creator workbench package so both human-facing apps
        retain one visual language without copying those assets into multiple
        places.
        """

        shared_match = SHARED_STATIC_MAP.get(rel_path)
        if shared_match is not None:
            return shared_match
        if rel_path.startswith("fonts/"):
            return CREATOR_STATIC_DIR / rel_path
        return STATIC_DIR / rel_path

    def _serve_static(self, rel_path: str) -> None:
        """Serve one packaged frontend asset."""

        try:
            file_path = self._resolve_static_path(rel_path).resolve()
        except (OSError, ValueError):
            self._send_error(400, "Invalid path")
            return

        allowed_roots = [STATIC_DIR.resolve(), CREATOR_STATIC_DIR.resolve()]
        if not any(str(file_path).startswith(str(root)) for root in allowed_roots):
            self._send_error(403, "Forbidden")
            return
        if not file_path.is_file():
            self._send_error(404, f"Not found: {rel_path}")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self._response_body_enabled:
            self.wfile.write(data)

    def _read_request_body(self) -> bytes:
        """Return the raw request body bytes for proxying."""

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _proxy_request(self, method: str, path_with_query: str, body: bytes | None) -> None:
        """Proxy one consumer-safe API request to ``pipeworks-namegen-api``."""

        upstream_url = f"{self.api_base_url.rstrip('/')}{path_with_query}"
        headers = {"Accept": "application/json"}
        content_type = self.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type

        request = Request(upstream_url, data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310 - fixed local upstream
                payload = response.read()
                status = response.status
                response_type = response.headers.get("Content-Type", "application/json")
        except HTTPError as exc:
            payload = exc.read()
            status = exc.code
            response_type = exc.headers.get("Content-Type", "application/json")
        except URLError as exc:
            self._send_json(
                {
                    "error": "Failed to reach upstream name-generation API.",
                    "details": str(exc.reason),
                },
                status=502,
            )
            return

        self.send_response(status)
        self.send_header("Content-Type", response_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self._response_body_enabled:
            self.wfile.write(payload)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """Send one JSON response."""

        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if self._response_body_enabled:
            self.wfile.write(encoded)

    def _send_error(self, status: int, message: str) -> None:
        """Send a JSON error response."""

        self._send_json({"error": message}, status=status)

    def log_message(self, fmt: str, *args: object) -> None:
        """Respect ``verbose`` while keeping a useful service label."""

        if not self.verbose:
            return
        message = fmt % args
        sys.stderr.write(f"[{self.service_log_label}] {message}\n")


def run_server(
    *,
    bind_host: str = "127.0.0.1",
    port: int | None = None,
    api_base_url: str = "http://127.0.0.1:8360",
    verbose: bool = True,
) -> int:
    """Run the names-app HTTP server until interrupted."""

    resolved_port = port if port is not None else select_auto_port(bind_host)
    NamesAppHandler.verbose = verbose
    NamesAppHandler.api_base_url = api_base_url.rstrip("/")

    server = ThreadingHTTPServer((bind_host, resolved_port), NamesAppHandler)
    if verbose:
        sys.stderr.write(
            f"[{NAMES_LOG_LABEL}] serving on http://{bind_host}:{resolved_port} "
            f"with upstream {NamesAppHandler.api_base_url}\n"
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - interactive lifecycle
        pass
    finally:
        server.server_close()
    return resolved_port
