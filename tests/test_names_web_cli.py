"""Tests for the consumer-facing names-app CLI."""

from pathlib import Path
from unittest.mock import patch

import pytest

from build_tools.names_web.cli import (
    NamesAppSettings,
    create_argument_parser,
    load_names_app_settings,
    main,
    parse_arguments,
)


def test_parser_defaults() -> None:
    """The names-app parser should expose the expected defaults."""

    args = create_argument_parser().parse_args([])
    assert args.bind_host is None
    assert args.port is None
    assert args.api_base_url is None
    assert args.quiet is False
    assert args.config == "server.ini"


def test_parse_all_arguments() -> None:
    """All supported CLI flags should parse cleanly together."""

    args = parse_arguments(
        [
            "--bind-host",
            "0.0.0.0",
            "--port",
            "8390",
            "--api-base-url",
            "http://127.0.0.1:9999",
            "--quiet",
            "--config",
            "custom.ini",
        ]
    )
    assert args.bind_host == "0.0.0.0"
    assert args.port == 8390
    assert args.api_base_url == "http://127.0.0.1:9999"
    assert args.quiet is True
    assert args.config == "custom.ini"


def test_load_names_app_settings_defaults_for_missing_file(tmp_path: Path) -> None:
    """Missing config files should yield built-in defaults."""

    settings = load_names_app_settings(tmp_path / "missing.ini")
    assert settings == NamesAppSettings()


def test_load_names_app_settings_reads_values(tmp_path: Path) -> None:
    """The ``[names_app]`` section should populate the names-app settings."""

    config_path = tmp_path / "server.ini"
    config_path.write_text(
        "\n".join(
            [
                "[names_app]",
                "bind_host = 127.0.0.1",
                "port = 8380",
                "api_base_url = http://127.0.0.1:8360/",
                "verbose = false",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_names_app_settings(config_path)
    assert settings.bind_host == "127.0.0.1"
    assert settings.port == 8380
    assert settings.api_base_url == "http://127.0.0.1:8360"
    assert settings.verbose is False


def test_main_passes_resolved_values_to_server(tmp_path: Path) -> None:
    """CLI resolution order should be INI values overridden by explicit CLI flags."""

    config_path = tmp_path / "server.ini"
    config_path.write_text(
        "[names_app]\nport = 8380\napi_base_url = http://127.0.0.1:8360\n",
        encoding="utf-8",
    )

    with patch("build_tools.names_web.server.run_server") as mock_run_server:
        result = main(["--config", str(config_path), "--bind-host", "0.0.0.0", "--quiet"])

    assert result == 0
    mock_run_server.assert_called_once_with(
        bind_host="0.0.0.0",
        port=8380,
        api_base_url="http://127.0.0.1:8360",
        verbose=False,
    )


def test_main_returns_error_code_when_server_raises() -> None:
    """Unexpected startup failures should produce exit code ``1``."""

    with patch("build_tools.names_web.server.run_server", side_effect=RuntimeError("boom")):
        result = main([])

    assert result == 1


def test_parse_invalid_port_raises() -> None:
    """Argparse should reject invalid integer values for ``--port``."""

    with pytest.raises(SystemExit):
        parse_arguments(["--port", "not-a-number"])
