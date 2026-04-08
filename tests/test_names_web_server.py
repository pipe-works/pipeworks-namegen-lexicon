"""Tests for the consumer-facing names-app HTTP server."""

import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from build_tools.names_web.server import (
    NamesAppHandler,
    find_available_port,
    run_server,
    select_auto_port,
)


def _make_handler() -> NamesAppHandler:
    """Create a ``NamesAppHandler`` instance with mocked socket I/O."""

    request = MagicMock()
    request.makefile.return_value = io.BytesIO()

    with patch.object(NamesAppHandler, "__init__", lambda self, *a, **kw: None):
        handler = NamesAppHandler.__new__(NamesAppHandler)
        handler.request = request
        handler.client_address = ("127.0.0.1", 9999)
        handler.server = MagicMock()
        handler.requestline = "GET / HTTP/1.1"
        handler.command = "GET"
        handler.headers = {}  # type: ignore[assignment]
        handler.wfile = io.BytesIO()
        handler.rfile = io.BytesIO()
        handler.send_response = MagicMock()  # type: ignore[method-assign]
        handler.send_header = MagicMock()  # type: ignore[method-assign]
        handler.end_headers = MagicMock()  # type: ignore[method-assign]
        handler.verbose = False
        handler.api_base_url = "http://127.0.0.1:8360"
        handler._response_body_enabled = True
    return handler


def test_root_serves_index_html() -> None:
    """The names app should serve its packaged index document at ``/``."""

    handler = _make_handler()
    handler._serve_static("index.html")
    body = handler.wfile.getvalue().decode("utf-8")
    assert "Pipe-Works Names" in body
    handler.send_response.assert_called_once_with(200)


def test_shared_base_styles_are_served_from_creator_assets() -> None:
    """Shared styling should come from the creator-workbench asset bundle."""

    handler = _make_handler()
    handler._serve_static("pipe-works-base.css")
    body = handler.wfile.getvalue().decode("utf-8")
    assert ":root" in body
    handler.send_response.assert_called_once_with(200)


def test_static_head_suppresses_body() -> None:
    """HEAD-style static responses should emit headers without a body."""

    handler = _make_handler()
    handler._response_body_enabled = False
    handler._serve_static("index.html")
    assert handler.wfile.getvalue() == b""


def test_directory_traversal_is_blocked() -> None:
    """Static path traversal should be rejected defensively."""

    handler = _make_handler()
    handler._serve_static("../secret.txt")
    handler.send_response.assert_called_once_with(403)


def test_app_config_route_returns_local_settings() -> None:
    """The names app should expose local app metadata for the frontend."""

    handler = _make_handler()
    handler.path = "/api/app-config"
    handler._handle_read_request()
    payload = json.loads(handler.wfile.getvalue())
    assert payload["app_name"] == "Pipe-Works Names"
    assert payload["api_base_url"] == "http://127.0.0.1:8360"


def test_proxy_request_forwards_success_payload() -> None:
    """Successful upstream proxy responses should be relayed transparently."""

    handler = _make_handler()

    class _Response:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    with patch("build_tools.names_web.server.urlopen", return_value=_Response()):
        handler._proxy_request("GET", "/api/version", None)

    assert json.loads(handler.wfile.getvalue()) == {"ok": True}
    handler.send_response.assert_called_once_with(200)


def test_proxy_request_relays_http_errors() -> None:
    """HTTP error payloads from the upstream API should be passed through."""

    handler = _make_handler()
    error = HTTPError(
        url="http://127.0.0.1:8360/api/generate",
        code=400,
        msg="Bad Request",
        hdrs={"Content-Type": "application/json"},
        fp=io.BytesIO(b'{"error":"bad"}'),
    )
    with patch("build_tools.names_web.server.urlopen", side_effect=error):
        handler._proxy_request("POST", "/api/generate", b"{}")

    assert json.loads(handler.wfile.getvalue()) == {"error": "bad"}
    handler.send_response.assert_called_once_with(400)


def test_proxy_request_returns_502_when_upstream_is_unreachable() -> None:
    """Network failures should become a local 502 JSON response."""

    handler = _make_handler()
    with patch("build_tools.names_web.server.urlopen", side_effect=URLError("offline")):
        handler._proxy_request("GET", "/api/version", None)

    payload = json.loads(handler.wfile.getvalue())
    assert payload["error"] == "Failed to reach upstream name-generation API."
    handler.send_response.assert_called_once_with(502)


def test_find_available_port_returns_port_when_bind_succeeds() -> None:
    """Port scanning should return the first mocked available port."""

    with patch(
        "build_tools.names_web.server.is_port_available",
        side_effect=[False, False, True, True],
    ):
        port = find_available_port("127.0.0.1", start=8890, tries=5)

    assert port == 8892


def test_select_auto_port_uses_primary_range_first() -> None:
    """Auto-port selection should prefer the primary names-app range."""

    with patch("build_tools.names_web.server.find_available_port", side_effect=[8381, None]):
        assert select_auto_port("127.0.0.1") == 8381


def test_run_server_uses_explicit_bind_host_and_port() -> None:
    """Server startup should honor the resolved host and port."""

    with patch("build_tools.names_web.server.ThreadingHTTPServer") as mock_server:
        mock_instance = MagicMock()
        mock_server.return_value = mock_instance
        run_server(
            bind_host="127.0.0.1",
            port=8380,
            api_base_url="http://127.0.0.1:8360",
            verbose=False,
        )

    mock_server.assert_called_once_with(("127.0.0.1", 8380), NamesAppHandler)
    assert NamesAppHandler.api_base_url == "http://127.0.0.1:8360"
    mock_instance.serve_forever.assert_called_once()
    mock_instance.server_close.assert_called_once()
