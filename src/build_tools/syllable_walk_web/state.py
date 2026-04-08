"""In-memory state models for the Pipe-Works creator workbench.

These dataclasses model the live, mutable state held by the browser-facing
creator workbench process. They intentionally describe ephemeral runtime state,
not durable package artifacts:

- :class:`PatchState` tracks one loaded comparison patch and its derived data.
- :class:`PipelineJobState` tracks the currently running pipeline job.
- :class:`CreatorWorkbenchState` groups those pieces into the shared server state used by
  the HTTP handler layer.

All of this state is process-local and is rebuilt on restart. That distinction
matters because the workbench is an authoring environment, while package ZIPs,
metadata, manifests, and API-imported SQLite data are the durable outputs.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PatchState:
    """Live state for one side of the dual-patch walker workspace.

    A patch is the loaded corpus/run context plus the derived data created
    while a creator explores it: annotated syllables, generated walks,
    candidate pools, reach-cache metadata, and selected names.

    The fields are intentionally verbose because the workbench can move a patch
    through several stages over time:

    1. discover a run
    2. load the corpus and annotations
    3. verify manifest and reach-cache provenance
    4. generate walks and candidates
    5. save selections or package the resulting material
    """

    run_id: str | None = None
    corpus_type: str | None = None
    corpus_dir: Path | None = None
    syllable_count: int = 0
    walker: Any | None = None  # SyllableWalker, lazy-loaded
    walker_ready: bool = False
    loading_stage: str | None = None  # Current loading stage (for progress display)
    # Monotonic counter for corpus load attempts on this patch.
    # Each new load request increments the generation so in-flight
    # background threads can detect if they became stale.
    load_generation: int = 0
    # Generation ID currently considered authoritative.
    # ``None`` means no load is currently in progress.
    active_load_generation: int | None = None
    # Terminal loader error for the current generation, if any.
    # Cleared at the start of each new load request.
    loading_error: str | None = None
    # Manifest IPC hashes for the currently loaded run (if available).
    manifest_ipc_input_hash: str | None = None
    manifest_ipc_output_hash: str | None = None
    # Manifest IPC verification outcome for the loaded run.
    # Values: verified|mismatch|missing|error (or None before first verification).
    manifest_ipc_verification_status: str | None = None
    manifest_ipc_verification_reason: str | None = None
    # Profile reach cache outcome for the currently loaded run.
    # Values: hit|miss|invalid|error|none (or None before first attempt).
    reach_cache_status: str | None = None
    # Reach-cache IPC hashes for the cache artifact loaded/written for this run.
    reach_cache_ipc_input_hash: str | None = None
    reach_cache_ipc_output_hash: str | None = None
    # Reach-cache IPC verification outcome.
    # Values: verified|mismatch|missing|error (or None before first verification).
    reach_cache_ipc_verification_status: str | None = None
    reach_cache_ipc_verification_reason: str | None = None
    profile_reaches: dict[str, Any] | None = None  # ReachResult per profile
    annotated_data: list[dict] | None = None
    frequencies: dict[str, int] | None = None
    walks: list[dict] = field(default_factory=list)
    candidates: list[dict] | None = None  # combiner output (in-memory)
    candidates_path: Path | None = None
    selections_path: Path | None = None
    selected_names: list[dict] = field(default_factory=list)


@dataclass
class PipelineJobState:
    """Live state for the currently active pipeline job.

    The creator workbench only runs one pipeline job at a time in-process.
    This structure is therefore a single mutable snapshot of the pipeline's
    current status, progress, logs, and failure state.
    """

    job_id: str | None = None
    status: str = "idle"
    config: dict | None = None
    current_stage: str | None = None
    progress_percent: int = 0
    log_lines: list[dict] = field(default_factory=list)
    output_path: Path | None = None
    error_message: str | None = None
    process: Any | None = None  # subprocess.Popen


@dataclass
class CreatorWorkbenchState:
    """Shared creator-workbench server state.

    This state object is attached to the handler class because the stdlib HTTP
    server constructs a new request handler instance for every request. It is
    therefore the shared bridge between:

    - Pipeline operations
    - Walker patch state
    - Session lock coordination
    - Filesystem roots selected by the operator
    """

    patch_a: PatchState = field(default_factory=PatchState)
    patch_b: PatchState = field(default_factory=PatchState)
    pipeline_job: PipelineJobState = field(default_factory=PipelineJobState)
    output_base: Path = field(default_factory=lambda: Path("_working/output"))
    # Optional explicit sessions directory override.
    # When ``None``, session storage should default to ``output_base/sessions``.
    sessions_base: Path | None = None
    corpus_dir_a: Path | None = None
    corpus_dir_b: Path | None = None
    # Cooperative single-user session locks keyed by session_id.
    # This is a UX consistency guard for multi-tab use, not a security boundary.
    walker_session_locks: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Thread-safety guard for lock map updates under ThreadingHTTPServer.
    walker_session_locks_guard: threading.Lock = field(default_factory=threading.Lock)
    # Active loaded session context (if current patch state came from load-session API).
    active_session_id: str | None = None
    # Current holder id for the active session lock.
    active_session_lock_holder_id: str | None = None


# ``ServerState`` remains available as a compatibility alias while the
# workbench package adopts the more descriptive canonical name.
ServerState = CreatorWorkbenchState
