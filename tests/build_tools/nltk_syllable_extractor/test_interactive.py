"""
Tests for nltk_syllable_extractor interactive mode.

This module tests the interactive workflow for the NLTK syllable extractor.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from build_tools.nltk_syllable_extractor.interactive import run_interactive


class TestRunInteractive:
    """Tests for run_interactive function."""

    def test_run_interactive_successful(self, tmp_path: Path) -> None:
        """Test successful run_interactive workflow."""
        # Create test input file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world this is a test file")

        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.prompt_input_file",
                return_value=test_file,
            ):
                with patch(
                    "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
                ) as mock_extractor_class:
                    mock_instance = MagicMock()
                    mock_instance.extract_syllables_from_file.return_value = (
                        {"hel", "lo", "world"},
                        {
                            "total_words": 3,
                            "fallback_count": 0,
                            "rejected_syllables": 0,
                            "processed_words": 3,
                        },
                    )
                    mock_extractor_class.return_value = mock_instance

                    with patch(
                        "build_tools.nltk_syllable_extractor.interactive.generate_output_filename"
                    ) as mock_output:
                        syllables_path = tmp_path / "run" / "syllables" / "test.txt"
                        metadata_path = tmp_path / "run" / "meta" / "test.txt"
                        syllables_path.parent.mkdir(parents=True, exist_ok=True)
                        metadata_path.parent.mkdir(parents=True, exist_ok=True)
                        mock_output.return_value = (syllables_path, metadata_path)

                        with patch(
                            "build_tools.nltk_syllable_extractor.interactive.ExtractionLedgerContext"
                        ) as mock_ctx:
                            mock_ctx_instance = MagicMock()
                            mock_ctx.return_value.__enter__ = MagicMock(
                                return_value=mock_ctx_instance
                            )
                            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

                            with patch(
                                "build_tools.nltk_syllable_extractor.interactive.save_metadata"
                            ):
                                run_interactive()

                                # Verify ledger methods were called
                                mock_ctx_instance.record_input.assert_called_once()
                                mock_ctx_instance.record_output.assert_called_once()
                                mock_ctx_instance.set_result.assert_called_with(success=True)

    def test_run_interactive_extractor_init_error(self) -> None:
        """Test run_interactive handles extractor initialization errors."""
        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
            ) as mock_extractor_class:
                mock_extractor_class.side_effect = ImportError("NLTK not found")

                with pytest.raises(SystemExit) as excinfo:
                    run_interactive()
                assert excinfo.value.code == 1

    def test_run_interactive_extraction_error(self, tmp_path: Path) -> None:
        """Test run_interactive handles extraction errors."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.prompt_input_file",
                return_value=test_file,
            ):
                with patch(
                    "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
                ) as mock_extractor_class:
                    mock_instance = MagicMock()
                    mock_instance.extract_syllables_from_file.side_effect = Exception(
                        "Extraction failed"
                    )
                    mock_extractor_class.return_value = mock_instance

                    with patch(
                        "build_tools.nltk_syllable_extractor.interactive.ExtractionLedgerContext"
                    ) as mock_ctx:
                        mock_ctx_instance = MagicMock()
                        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_ctx_instance)
                        mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

                        with pytest.raises(SystemExit) as excinfo:
                            run_interactive()
                        assert excinfo.value.code == 1
                        mock_ctx_instance.set_result.assert_called_with(success=False)

    def test_run_interactive_save_syllables_error(self, tmp_path: Path) -> None:
        """Test run_interactive handles syllable save errors."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.prompt_input_file",
                return_value=test_file,
            ):
                with patch(
                    "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
                ) as mock_extractor_class:
                    mock_instance = MagicMock()
                    mock_instance.extract_syllables_from_file.return_value = (
                        {"test"},
                        {
                            "total_words": 1,
                            "fallback_count": 0,
                            "rejected_syllables": 0,
                            "processed_words": 1,
                        },
                    )
                    mock_instance.save_syllables.side_effect = Exception("Save failed")
                    mock_extractor_class.return_value = mock_instance

                    with patch(
                        "build_tools.nltk_syllable_extractor.interactive.generate_output_filename"
                    ) as mock_output:
                        syllables_path = tmp_path / "run" / "syllables" / "test.txt"
                        metadata_path = tmp_path / "run" / "meta" / "test.txt"
                        mock_output.return_value = (syllables_path, metadata_path)

                        with patch(
                            "build_tools.nltk_syllable_extractor.interactive.ExtractionLedgerContext"
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

    def test_run_interactive_save_metadata_error(self, tmp_path: Path) -> None:
        """Test run_interactive handles metadata save errors."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.prompt_input_file",
                return_value=test_file,
            ):
                with patch(
                    "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
                ) as mock_extractor_class:
                    mock_instance = MagicMock()
                    mock_instance.extract_syllables_from_file.return_value = (
                        {"test"},
                        {
                            "total_words": 1,
                            "fallback_count": 0,
                            "rejected_syllables": 0,
                            "processed_words": 1,
                        },
                    )
                    mock_extractor_class.return_value = mock_instance

                    with patch(
                        "build_tools.nltk_syllable_extractor.interactive.generate_output_filename"
                    ) as mock_output:
                        syllables_path = tmp_path / "run" / "syllables" / "test.txt"
                        metadata_path = tmp_path / "run" / "meta" / "test.txt"
                        syllables_path.parent.mkdir(parents=True, exist_ok=True)
                        mock_output.return_value = (syllables_path, metadata_path)

                        with patch(
                            "build_tools.nltk_syllable_extractor.interactive.save_metadata"
                        ) as mock_save_meta:
                            mock_save_meta.side_effect = Exception("Metadata save failed")

                            with patch(
                                "build_tools.nltk_syllable_extractor.interactive.ExtractionLedgerContext"
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

    def test_run_interactive_lookup_error(self) -> None:
        """Test run_interactive handles LookupError (NLTK data not found)."""
        with patch(
            "build_tools.nltk_syllable_extractor.interactive.prompt_extraction_settings",
            return_value=(1, 999),
        ):
            with patch(
                "build_tools.nltk_syllable_extractor.interactive.NltkSyllableExtractor"
            ) as mock_extractor_class:
                mock_extractor_class.side_effect = LookupError("CMU Dict not downloaded")

                with pytest.raises(SystemExit) as excinfo:
                    run_interactive()
                assert excinfo.value.code == 1
