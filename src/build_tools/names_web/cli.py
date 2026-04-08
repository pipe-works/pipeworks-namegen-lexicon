"""Command-line interface for the Pipe-Works names app.

The names app is the intentionally simpler consumer-facing counterpart to the
creator workbench. Its configuration surface stays deliberately small:

- where the local HTTP server should bind
- which upstream API base URL should be proxied
- whether startup/runtime messages should be printed
"""

from __future__ import annotations

import argparse
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

NAMES_APP_SETTINGS_SECTION = "names_app"


@dataclass(frozen=True)
class NamesAppSettings:
    """Resolved configuration for the consumer-facing names app.

    Attributes:
        bind_host: Interface address for the local HTTP server.
        port: Optional explicit port. ``None`` means auto-select.
        api_base_url: Base URL of the upstream ``pipeworks-namegen-api`` service.
        verbose: Print startup/runtime information when True.
    """

    bind_host: str = "127.0.0.1"
    port: int | None = None
    api_base_url: str = "http://127.0.0.1:8360"
    verbose: bool = True


def _read_optional_str(
    parser: ConfigParser,
    section_name: str,
    option_name: str,
) -> str | None:
    """Read a string option and normalize blank values to ``None``."""

    raw_value = parser.get(section_name, option_name, fallback=None)
    if raw_value is None:
        return None

    stripped = raw_value.strip()
    return stripped or None


def load_names_app_settings(config_path: Path | None) -> NamesAppSettings:
    """Load names-app settings from an INI file.

    Args:
        config_path: Optional INI path. Missing or absent files fall back to
            built-in defaults.

    Returns:
        Parsed :class:`NamesAppSettings`.
    """

    settings = NamesAppSettings()
    if config_path is None or not config_path.exists():
        return settings

    parser = ConfigParser()
    parser.read(config_path, encoding="utf-8")
    if not parser.has_section(NAMES_APP_SETTINGS_SECTION):
        return settings

    bind_host = (
        _read_optional_str(parser, NAMES_APP_SETTINGS_SECTION, "bind_host") or settings.bind_host
    )
    raw_port = _read_optional_str(parser, NAMES_APP_SETTINGS_SECTION, "port")
    port = int(raw_port) if raw_port is not None else settings.port
    api_base_url = (
        _read_optional_str(parser, NAMES_APP_SETTINGS_SECTION, "api_base_url")
        or settings.api_base_url
    )
    verbose = parser.getboolean(NAMES_APP_SETTINGS_SECTION, "verbose", fallback=settings.verbose)
    return NamesAppSettings(
        bind_host=bind_host,
        port=port,
        api_base_url=api_base_url.rstrip("/"),
        verbose=verbose,
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the names-app argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Launch the Pipe-Works names web application. "
            "This is the consumer-facing surface for generating names from "
            "prepared package data while the upstream API remains the runtime "
            "contract owner."
        ),
    )
    parser.add_argument(
        "--bind-host",
        type=str,
        default=None,
        help="Interface address to bind the local HTTP server to. Default: 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to serve on. If not specified, an available local port is selected.",
    )
    parser.add_argument(
        "--api-base-url",
        type=str,
        default=None,
        help="Base URL of the upstream name-generation API. Default: http://127.0.0.1:8360",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress HTTP request logging.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="server.ini",
        help="Path to INI config file. Reads [names_app] values. Default: server.ini",
    )
    return parser


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the names app."""

    parser = create_argument_parser()
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the names-app CLI entrypoint."""

    parsed = parse_arguments(args)

    try:
        from build_tools.names_web.server import run_server

        ini_settings = load_names_app_settings(Path(parsed.config))
        bind_host = parsed.bind_host or ini_settings.bind_host
        port = parsed.port if parsed.port is not None else ini_settings.port
        api_base_url = (parsed.api_base_url or ini_settings.api_base_url).rstrip("/")
        verbose = False if parsed.quiet else ini_settings.verbose

        run_server(
            bind_host=bind_host,
            port=port,
            api_base_url=api_base_url,
            verbose=verbose,
        )
        return 0
    except KeyboardInterrupt:
        print("\nShutting down names app...", file=sys.stderr)
        return 130
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1
