"""
Tests for pyphen_syllable_extractor interactive mode.

This module tests the interactive workflow for the pyphen syllable extractor.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from build_tools.pyphen_syllable_extractor.interactive import (
    run_interactive,
    select_language,
)


class TestSelectLanguage:
    """Tests for select_language function."""

    def test_select_language_by_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test selecting language by number."""
        # Select English (US) which should be in the list
        with patch("builtins.input", return_value="13"):
            code = select_language()
            # Verify it returns a valid language code
            assert "_" in code or code.isalpha()

    def test_select_language_by_code(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test selecting language by code."""
        with patch("builtins.input", return_value="en_US"):
            code = select_language()
            assert code == "en_US"
            captured = capsys.readouterr()
            assert "en_US" in captured.out

    def test_select_language_by_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test selecting language by name."""
        with patch("builtins.input", return_value="English (US)"):
            code = select_language()
            assert code == "en_US"

    def test_select_language_auto_detection(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test selecting auto detection."""
        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.is_detection_available",
            return_value=True,
        ):
            with patch("builtins.input", return_value="auto"):
                code = select_language()
                assert code == "auto"
                captured = capsys.readouterr()
                assert "Automatic language detection" in captured.out

    def test_select_language_auto_not_available(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test selecting auto when not available."""
        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.is_detection_available",
            return_value=False,
        ):
            with patch("builtins.input", side_effect=["auto", "en_US"]):
                code = select_language()
                assert code == "en_US"
                captured = capsys.readouterr()
                assert "not available" in captured.out

    def test_select_language_quit(self) -> None:
        """Test quit exits the program."""
        with patch("builtins.input", return_value="quit"):
            with pytest.raises(SystemExit) as excinfo:
                select_language()
            assert excinfo.value.code == 0

    def test_select_language_invalid_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test invalid number selection."""
        with patch("builtins.input", side_effect=["999", "en_US"]):
            code = select_language()
            assert code == "en_US"
            captured = capsys.readouterr()
            assert "number between" in captured.out

    def test_select_language_invalid_selection(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test invalid selection shows error."""
        with patch("builtins.input", side_effect=["invalid_selection", "en_US"]):
            code = select_language()
            assert code == "en_US"
            captured = capsys.readouterr()
            assert "Invalid selection" in captured.out


class TestRunInteractive:
    """Tests for run_interactive function."""

    def test_run_interactive_with_manual_language(self, tmp_path: Path) -> None:
        """Test run_interactive with manual language selection."""
        # Create test input file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world this is a test file")

        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.select_language",
            return_value="en_US",
        ):
            with patch(
                "build_tools.pyphen_syllable_extractor.interactive.prompt_extraction_settings",
                return_value=(2, 8),
            ):
                with patch(
                    "build_tools.pyphen_syllable_extractor.interactive.prompt_input_file",
                    return_value=test_file,
                ):
                    with patch(
                        "build_tools.pyphen_syllable_extractor.interactive.generate_output_filename"
                    ) as mock_output:
                        syllables_path = tmp_path / "run" / "syllables" / "test.txt"
                        metadata_path = tmp_path / "run" / "meta" / "test.txt"
                        syllables_path.parent.mkdir(parents=True, exist_ok=True)
                        metadata_path.parent.mkdir(parents=True, exist_ok=True)
                        mock_output.return_value = (syllables_path, metadata_path)

                        with patch(
                            "build_tools.pyphen_syllable_extractor.interactive.ExtractionLedgerContext"
                        ) as mock_ctx:
                            mock_ctx_instance = MagicMock()
                            mock_ctx.return_value.__enter__ = MagicMock(
                                return_value=mock_ctx_instance
                            )
                            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

                            run_interactive()

                            # Verify ledger methods were called
                            mock_ctx_instance.record_input.assert_called_once()
                            mock_ctx_instance.record_output.assert_called_once()
                            mock_ctx_instance.set_result.assert_called()

    def test_run_interactive_with_auto_detection(self, tmp_path: Path) -> None:
        """Test run_interactive with auto language detection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world this is a test file")

        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.select_language",
            return_value="auto",
        ):
            with patch(
                "build_tools.pyphen_syllable_extractor.interactive.prompt_extraction_settings",
                return_value=(2, 8),
            ):
                with patch(
                    "build_tools.pyphen_syllable_extractor.interactive.prompt_input_file",
                    return_value=test_file,
                ):
                    with patch(
                        "build_tools.pyphen_syllable_extractor.interactive.SyllableExtractor"
                    ) as mock_extractor_class:
                        # Mock the class method for auto-detection
                        mock_extractor_class.extract_file_with_auto_language.return_value = (
                            {"hel", "lo", "world"},
                            {
                                "total_words": 3,
                                "skipped_unhyphenated": 0,
                                "rejected_syllables": 0,
                                "processed_words": 3,
                            },
                            "en_US",
                        )
                        # Mock the instance for saving
                        mock_instance = MagicMock()
                        mock_extractor_class.return_value = mock_instance

                        with patch(
                            "build_tools.pyphen_syllable_extractor.interactive.generate_output_filename"
                        ) as mock_output:
                            syllables_path = tmp_path / "run" / "syllables" / "test.txt"
                            metadata_path = tmp_path / "run" / "meta" / "test.txt"
                            syllables_path.parent.mkdir(parents=True, exist_ok=True)
                            metadata_path.parent.mkdir(parents=True, exist_ok=True)
                            mock_output.return_value = (syllables_path, metadata_path)

                            with patch(
                                "build_tools.pyphen_syllable_extractor.interactive.ExtractionLedgerContext"
                            ) as mock_ctx:
                                mock_ctx_instance = MagicMock()
                                mock_ctx.return_value.__enter__ = MagicMock(
                                    return_value=mock_ctx_instance
                                )
                                mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

                                with patch(
                                    "build_tools.pyphen_syllable_extractor.interactive.save_metadata"
                                ):
                                    run_interactive()

                                    # Verify auto-detection was used
                                    mock_extractor_class.extract_file_with_auto_language.assert_called_once()

    def test_run_interactive_extraction_error(self, tmp_path: Path) -> None:
        """Test run_interactive handles extraction errors."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.select_language",
            return_value="en_US",
        ):
            with patch(
                "build_tools.pyphen_syllable_extractor.interactive.prompt_extraction_settings",
                return_value=(2, 8),
            ):
                with patch(
                    "build_tools.pyphen_syllable_extractor.interactive.prompt_input_file",
                    return_value=test_file,
                ):
                    with patch(
                        "build_tools.pyphen_syllable_extractor.interactive.SyllableExtractor"
                    ) as mock_extractor_class:
                        mock_instance = MagicMock()
                        mock_instance.extract_syllables_from_file.side_effect = Exception(
                            "Extraction failed"
                        )
                        mock_extractor_class.return_value = mock_instance

                        with patch(
                            "build_tools.pyphen_syllable_extractor.interactive.ExtractionLedgerContext"
                        ) as mock_ctx:
                            mock_ctx_instance = MagicMock()
                            mock_ctx.return_value.__enter__ = MagicMock(
                                return_value=mock_ctx_instance
                            )
                            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

                            with pytest.raises(SystemExit) as excinfo:
                                run_interactive()
                            assert excinfo.value.code == 1
                            mock_ctx_instance.set_result.assert_called_with(success=False)

    def test_run_interactive_invalid_language(self) -> None:
        """Test run_interactive handles invalid language initialization."""
        with patch(
            "build_tools.pyphen_syllable_extractor.interactive.select_language",
            return_value="invalid_lang",
        ):
            with patch(
                "build_tools.pyphen_syllable_extractor.interactive.prompt_extraction_settings",
                return_value=(2, 8),
            ):
                with patch(
                    "build_tools.pyphen_syllable_extractor.interactive.SyllableExtractor"
                ) as mock_extractor_class:
                    mock_extractor_class.side_effect = ValueError("Invalid language")

                    with pytest.raises(SystemExit) as excinfo:
                        run_interactive()
                    assert excinfo.value.code == 1
