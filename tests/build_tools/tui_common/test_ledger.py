"""
Tests for the ExtractionLedgerContext in tui_common.ledger.

This module tests all branches of the ledger context manager including:
- Early return when CORPUS_DB_AVAILABLE is False
- Exception handling during initialization
- Exit scenarios (exception, explicit failure, explicit success, default success)
- Recording methods when context is not available
"""

from pathlib import Path
from unittest.mock import Mock, patch

from build_tools.tui_common.ledger import ExtractionLedgerContext

# Common patch targets
LEDGER_PATCH_TARGET = "build_tools.corpus_db.CorpusLedger"
CORPUS_DB_AVAILABLE_PATCH = "build_tools.tui_common.ledger.CORPUS_DB_AVAILABLE"


class TestExtractionLedgerContextInitialization:
    """Tests for context manager initialization."""

    def test_default_initialization(self) -> None:
        """Test default values are set correctly."""
        ctx = ExtractionLedgerContext(
            extractor_tool="test_tool",
            extractor_version="1.0.0",
        )

        assert ctx.extractor_tool == "test_tool"
        assert ctx.extractor_version == "1.0.0"
        assert ctx.pyphen_lang is None
        assert ctx.min_len is None
        assert ctx.max_len is None
        assert ctx.recursive is False
        assert ctx.pattern is None
        assert ctx.quiet is False
        assert ctx._ledger is None
        assert ctx._run_id is None
        assert ctx._success is None

    def test_all_parameters(self) -> None:
        """Test all parameters are set correctly."""
        ctx = ExtractionLedgerContext(
            extractor_tool="test_tool",
            extractor_version="1.0.0",
            pyphen_lang="en_US",
            min_len=2,
            max_len=8,
            recursive=True,
            pattern="*.txt",
            command_line="test command",
            quiet=True,
        )

        assert ctx.pyphen_lang == "en_US"
        assert ctx.min_len == 2
        assert ctx.max_len == 8
        assert ctx.recursive is True
        assert ctx.pattern == "*.txt"
        assert ctx.command_line == "test command"
        assert ctx.quiet is True


class TestExtractionLedgerContextCorpusDBUnavailable:
    """Tests for when CORPUS_DB_AVAILABLE is False."""

    def test_enter_returns_self_when_corpus_db_unavailable(self) -> None:
        """Test __enter__ returns self without initializing ledger when unavailable."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            ctx = ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            )
            result = ctx.__enter__()

            assert result is ctx
            assert ctx._ledger is None
            assert ctx._run_id is None
            assert ctx.is_available is False

    def test_exit_returns_early_when_not_available(self) -> None:
        """Test __exit__ returns early when ledger not available."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            ctx = ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            )
            ctx.__enter__()
            # Should not raise any errors
            ctx.__exit__(None, None, None)

    def test_record_input_returns_early_when_not_available(self) -> None:
        """Test record_input returns early when not available."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                # Should not raise any errors
                ctx.record_input(Path("/test/file.txt"))

    def test_record_inputs_returns_early_when_not_available(self) -> None:
        """Test record_inputs returns early when not available."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                # Should not raise any errors
                ctx.record_inputs([Path("/test/file1.txt"), Path("/test/file2.txt")])

    def test_record_output_returns_early_when_not_available(self) -> None:
        """Test record_output returns early when not available."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                # Should not raise any errors
                ctx.record_output(
                    output_path=Path("/test/output.txt"),
                    unique_syllable_count=100,
                )


class TestExtractionLedgerContextExceptionHandling:
    """Tests for exception handling during initialization."""

    def test_enter_handles_ledger_init_exception(self) -> None:
        """Test __enter__ handles exception when CorpusLedger init fails."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger_class.side_effect = Exception("Init failed")

            ctx = ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
                quiet=True,  # Suppress warning output
            )
            result = ctx.__enter__()

            assert result is ctx
            assert ctx._ledger is None
            assert ctx._run_id is None
            assert ctx.is_available is False

    def test_enter_prints_warning_on_exception_when_not_quiet(self) -> None:
        """Test __enter__ prints warning when init fails and not quiet."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger_class.side_effect = Exception("Database connection failed")

            with patch("sys.stderr") as mock_stderr:
                ctx = ExtractionLedgerContext(
                    extractor_tool="test_tool",
                    extractor_version="1.0.0",
                    quiet=False,
                )
                ctx.__enter__()

                # Should have printed warning
                mock_stderr.write.assert_called()


class TestExtractionLedgerContextExitScenarios:
    """Tests for __exit__ with different scenarios."""

    def test_exit_with_exception_marks_failed(self) -> None:
        """Test __exit__ marks run as failed when exception occurred."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            ctx = ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            )
            ctx.__enter__()

            # Simulate exception during exit
            ctx.__exit__(ValueError, ValueError("test error"), None)

            mock_ledger.complete_run.assert_called_once()
            call_kwargs = mock_ledger.complete_run.call_args[1]
            assert call_kwargs["exit_code"] == 1
            assert call_kwargs["status"] == "failed"
            mock_ledger.close.assert_called_once()

    def test_exit_with_explicit_failure_marks_failed(self) -> None:
        """Test __exit__ marks run as failed when set_result(False) called."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.set_result(success=False)

            mock_ledger.complete_run.assert_called_once()
            call_kwargs = mock_ledger.complete_run.call_args[1]
            assert call_kwargs["exit_code"] == 1
            assert call_kwargs["status"] == "failed"

    def test_exit_with_explicit_success_marks_completed(self) -> None:
        """Test __exit__ marks run as completed when set_result(True) called."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.set_result(success=True)

            mock_ledger.complete_run.assert_called_once()
            call_kwargs = mock_ledger.complete_run.call_args[1]
            assert call_kwargs["exit_code"] == 0
            assert call_kwargs["status"] == "completed"

    def test_exit_without_explicit_result_defaults_to_success(self) -> None:
        """Test __exit__ defaults to success when no set_result called."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ):
                pass  # No set_result called

            mock_ledger.complete_run.assert_called_once()
            call_kwargs = mock_ledger.complete_run.call_args[1]
            assert call_kwargs["exit_code"] == 0
            assert call_kwargs["status"] == "completed"


class TestExtractionLedgerContextProperties:
    """Tests for property accessors."""

    def test_is_available_false_when_ledger_none(self) -> None:
        """Test is_available returns False when ledger is None."""
        with patch(CORPUS_DB_AVAILABLE_PATCH, False):
            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                assert ctx.is_available is False

    def test_is_available_false_when_run_id_none(self) -> None:
        """Test is_available returns False when run_id is None."""
        ctx = ExtractionLedgerContext(
            extractor_tool="test_tool",
            extractor_version="1.0.0",
        )
        ctx._ledger = Mock()
        ctx._run_id = None
        assert ctx.is_available is False

    def test_is_available_true_when_both_set(self) -> None:
        """Test is_available returns True when both ledger and run_id set."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 42

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                assert ctx.is_available is True
                assert ctx.run_id == 42


class TestExtractionLedgerContextRecordMethods:
    """Tests for recording methods."""

    def test_record_input_with_file_count(self) -> None:
        """Test record_input passes file_count correctly."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.record_input(Path("/test/dir"), file_count=10)

            mock_ledger.record_input.assert_called_once()
            call_args = mock_ledger.record_input.call_args[0]
            assert call_args[0] == 1  # run_id
            assert call_args[1] == Path("/test/dir")
            assert call_args[2] == 10  # file_count

    def test_record_inputs_with_source_dir(self) -> None:
        """Test record_inputs records directory with file count."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            files = [Path(f"/test/file{i}.txt") for i in range(5)]
            source_dir = Path("/test")

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.record_inputs(files, source_dir=source_dir)

            # Should record directory once with file_count
            mock_ledger.record_input.assert_called_once()
            call_kwargs = mock_ledger.record_input.call_args[1]
            assert call_kwargs["file_count"] == 5

    def test_record_inputs_without_source_dir(self) -> None:
        """Test record_inputs records each file individually without source_dir."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            files = [Path(f"/test/file{i}.txt") for i in range(3)]

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.record_inputs(files)  # No source_dir

            # Should record each file individually
            assert mock_ledger.record_input.call_count == 3

    def test_record_output_all_parameters(self) -> None:
        """Test record_output passes all parameters correctly."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            output_path = Path("/test/output.txt")
            meta_path = Path("/test/output_meta.txt")

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                ctx.record_output(
                    output_path=output_path,
                    unique_syllable_count=500,
                    meta_path=meta_path,
                )

            mock_ledger.record_output.assert_called_once()
            call_kwargs = mock_ledger.record_output.call_args[1]
            assert call_kwargs["output_path"] == output_path
            assert call_kwargs["unique_syllable_count"] == 500
            assert call_kwargs["meta_path"] == meta_path


class TestExtractionLedgerContextSafeCall:
    """Tests for _safe_call method."""

    def test_safe_call_returns_result_on_success(self) -> None:
        """Test _safe_call returns function result on success."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            with ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
            ) as ctx:
                result = ctx._safe_call("test op", lambda: "success")

            assert result == "success"

    def test_safe_call_uses_quiet_override(self) -> None:
        """Test _safe_call respects quiet parameter override."""
        with patch(LEDGER_PATCH_TARGET) as mock_ledger_class:
            mock_ledger = Mock()
            mock_ledger_class.return_value = mock_ledger
            mock_ledger.start_run.return_value = 1

            ctx = ExtractionLedgerContext(
                extractor_tool="test_tool",
                extractor_version="1.0.0",
                quiet=False,  # Instance is not quiet
            )
            ctx.__enter__()

            # Call with explicit quiet=True
            with patch("build_tools.tui_common.ledger.record_corpus_db_safe") as mock_safe:
                ctx._safe_call("test op", lambda: None, quiet=True)
                mock_safe.assert_called_once()
                assert mock_safe.call_args[1]["quiet"] is True

            ctx.__exit__(None, None, None)
