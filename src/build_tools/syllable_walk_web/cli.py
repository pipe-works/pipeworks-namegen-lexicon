"""Command-line interface for the Pipe-Works creator workbench.

This module keeps the external entrypoint intentionally small and explicit:
load settings, apply command-line overrides, and start the packaged web
server. The workbench is now the canonical product name, so the configuration
surface prefers ``[creator_workbench]`` while still understanding the older
``[build_tools]`` section name during transition.
"""

from __future__ import annotations

import argparse
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

WORKBENCH_SETTINGS_SECTION = "creator_workbench"
LEGACY_SETTINGS_SECTION = "build_tools"


@dataclass(frozen=True)
class CreatorWorkbenchSettings:
    """Resolved configuration for the creator workbench server.

    Attributes:
        output_base: Base directory for pipeline run discovery.
        sessions_dir: Optional explicit session storage directory.
        corpus_dir_a: Directory containing runs to auto-load into Patch A.
        corpus_dir_b: Directory containing runs to auto-load into Patch B.
        bind_host: Interface address to bind the local server to.
        port: Optional explicit port. ``None`` means auto-select.
        verbose: Print startup/runtime messages when True.
    """

    output_base: Path | None = None
    sessions_dir: Path | None = None
    corpus_dir_a: str | None = None
    corpus_dir_b: str | None = None
    bind_host: str = "127.0.0.1"
    port: int | None = None
    verbose: bool = True


def _read_optional_str(
    parser: ConfigParser,
    section_name: str,
    option_name: str,
) -> str | None:
    """Read a string option and normalise blank values to ``None``.

    The INI files used by the workbench often leave keys present but blank to
    indicate "intentionally unset". Normalising that once keeps the main
    loader readable and makes the blank-value behaviour consistent.
    """

    raw_value = parser.get(section_name, option_name, fallback=None)
    if raw_value is None:
        return None

    stripped = raw_value.strip()
    return stripped or None


def _resolve_settings_section(parser: ConfigParser) -> str | None:
    """Choose the INI section that should drive workbench settings.

    ``[creator_workbench]`` is the canonical section because it matches the
    maintained product name. ``[build_tools]`` remains a fallback so existing
    local configs continue to work until they are intentionally rewritten.
    """

    if parser.has_section(WORKBENCH_SETTINGS_SECTION):
        return WORKBENCH_SETTINGS_SECTION
    if parser.has_section(LEGACY_SETTINGS_SECTION):
        return LEGACY_SETTINGS_SECTION
    return None


def load_creator_workbench_settings(
    config_path: Path | None,
) -> CreatorWorkbenchSettings:
    """Load creator-workbench settings from an INI file.

    Args:
        config_path: Path to INI file. If missing/None, defaults are used.

    Returns:
        Parsed :class:`CreatorWorkbenchSettings` instance.
    """
    settings = CreatorWorkbenchSettings()

    if config_path is None or not config_path.exists():
        return settings

    parser = ConfigParser()
    parser.read(config_path, encoding="utf-8")

    section_name = _resolve_settings_section(parser)
    if section_name is None:
        return settings

    raw_output = _read_optional_str(parser, section_name, "output_base")
    output_base: Path | None = None
    if raw_output is not None:
        output_base = Path(raw_output).expanduser()

    raw_sessions = _read_optional_str(parser, section_name, "sessions_dir")
    sessions_dir: Path | None = None
    if raw_sessions is not None:
        sessions_dir = Path(raw_sessions).expanduser()

    corpus_dir_a = _read_optional_str(parser, section_name, "corpus_dir_a")

    corpus_dir_b = _read_optional_str(parser, section_name, "corpus_dir_b")

    bind_host = _read_optional_str(parser, section_name, "bind_host") or settings.bind_host

    raw_port = _read_optional_str(parser, section_name, "port")
    port: int | None = None
    if raw_port is not None:
        port = int(raw_port)

    verbose = parser.getboolean(section_name, "verbose", fallback=settings.verbose)

    return CreatorWorkbenchSettings(
        output_base=output_base,
        sessions_dir=sessions_dir,
        corpus_dir_a=corpus_dir_a,
        corpus_dir_b=corpus_dir_b,
        bind_host=bind_host,
        port=port,
        verbose=verbose,
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the creator workbench.

    Returns:
        Configured ArgumentParser ready to parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Launch the Pipe-Works creator workbench web application. "
            "Combines Pipeline (extraction/normalization/annotation) and "
            "Walker (dual-patch syllable walking, name generation) tools "
            "in a browser-based interface."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples::

  # Launch on auto-detected port (default)
  python -m build_tools.syllable_walk_web

  # Launch on a specific port
  python -m build_tools.syllable_walk_web --port 9000

  # Launch in quiet mode (suppress HTTP request logs)
  python -m build_tools.syllable_walk_web --quiet

  # Use a custom config file
  python -m build_tools.syllable_walk_web --config server.ini
        """,
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
        help=(
            "Port to serve on. If not specified, automatically finds an "
            "available port (checks 8000-8099 first, then 8100-8999). "
            "Default: auto-detect"
        ),
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress HTTP request logging. Default: False",
    )

    parser.add_argument(
        "--output-base",
        type=str,
        default=None,
        help=("Base directory for pipeline run discovery. " "Default: _working/output"),
    )

    parser.add_argument(
        "--sessions-dir",
        type=str,
        default=None,
        help=("Optional directory for saved walker sessions. " "Default: <output_base>/sessions"),
    )

    parser.add_argument(
        "--config",
        type=str,
        default="server.ini",
        help=(
            "Path to INI config file. Prefers [creator_workbench] and falls "
            "back to [build_tools] for existing local configs. Reads "
            "output_base, sessions_dir, corpus_dir_a, corpus_dir_b, bind_host, "
            "port, and verbose. CLI arguments override INI values. "
            "Default: server.ini"
        ),
    )

    return parser


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = create_argument_parser()
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the creator workbench CLI entrypoint.

    Resolution order is:

    1. Read the requested INI file when present.
    2. Prefer ``[creator_workbench]`` settings over ``[build_tools]``.
    3. Apply any explicit CLI overrides on top.

    Returns:
        Exit code: 0 for success, 1 for error, 130 for keyboard interrupt.
    """
    parsed = parse_arguments(args)

    try:
        from build_tools.syllable_walk_web.server import run_server

        # Load INI settings, then let CLI args override.
        ini_settings = load_creator_workbench_settings(Path(parsed.config))

        # Resolve output_base: CLI > INI > None
        if parsed.output_base is not None:
            output_base = Path(parsed.output_base)
        elif ini_settings.output_base is not None:
            output_base = ini_settings.output_base
        else:
            output_base = None

        # Resolve sessions_dir: CLI > INI > None
        if parsed.sessions_dir is not None:
            sessions_dir = Path(parsed.sessions_dir)
        elif ini_settings.sessions_dir is not None:
            sessions_dir = ini_settings.sessions_dir
        else:
            sessions_dir = None

        # Resolve bind_host: CLI > INI > default
        bind_host = parsed.bind_host if parsed.bind_host is not None else ini_settings.bind_host

        # Resolve port: CLI > INI > None
        port = parsed.port if parsed.port is not None else ini_settings.port

        # Resolve verbose: --quiet CLI flag overrides INI
        verbose = not parsed.quiet if parsed.quiet else ini_settings.verbose

        return run_server(
            bind_host=bind_host,
            port=port,
            verbose=verbose,
            output_base=output_base,
            sessions_dir=sessions_dir,
            corpus_dir_a=ini_settings.corpus_dir_a,
            corpus_dir_b=ini_settings.corpus_dir_b,
        )
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


# Transitional aliases preserve older imports while the repo adopts creator-
# workbench terminology internally and in operator-facing documentation.
BuildToolsSettings = CreatorWorkbenchSettings
load_build_tools_settings = load_creator_workbench_settings
