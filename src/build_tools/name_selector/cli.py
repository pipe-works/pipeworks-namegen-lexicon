"""
Command-line interface for the name selector.

This module provides the CLI for filtering and ranking name candidates
against a name class policy. It follows the project's CLI documentation
standards with sphinx-argparse compatible argument parser.

Usage
-----
Select first names from 2-syllable candidates::

    python -m build_tools.name_selector \\
        --run-dir _working/output/20260110_115453_pyphen/ \\
        --candidates candidates/pyphen_candidates_2syl.json \\
        --name-class first_name \\
        --count 100

Use soft mode (penalties instead of hard rejection)::

    python -m build_tools.name_selector \\
        --run-dir _working/output/20260110_115453_pyphen/ \\
        --candidates candidates/pyphen_candidates_2syl.json \\
        --name-class first_name \\
        --mode soft
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and return the argument parser for the name selector.

    Returns
    -------
    argparse.ArgumentParser
        Configured ArgumentParser ready to parse command-line arguments.

    Notes
    -----
    This function follows the project's CLI documentation standards,
    enabling sphinx-argparse to auto-generate documentation.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Filter and rank name candidates against a name class policy. "
            "Evaluates candidates using the 12-feature policy matrix and produces "
            "ranked, admissible name lists. This is a build-time tool for the "
            "Selection Policy Layer."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples::

    # Select first names from 2-syllable candidates
    python -m build_tools.name_selector \\
        --run-dir _working/output/20260110_115453_pyphen/ \\
        --candidates candidates/pyphen_candidates_2syl.json \\
        --name-class first_name \\
        --count 100

    # Select place names with soft mode (penalties instead of rejection)
    python -m build_tools.name_selector \\
        --run-dir _working/output/20260110_115453_pyphen/ \\
        --candidates candidates/pyphen_candidates_3syl.json \\
        --name-class place_name \\
        --mode soft

    # Use a custom policy file
    python -m build_tools.name_selector \\
        --run-dir _working/output/20260110_115453_pyphen/ \\
        --candidates candidates/pyphen_candidates_2syl.json \\
        --name-class first_name \\
        --policy-file custom_policies.yml

Output:
    Creates ``selections/{prefix}_{name_class}_{N}syl.json`` in the run directory.
    The prefix and syllable count are extracted from the candidates filename.
        """,
    )

    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help=(
            "Path to extraction run directory. " "Example: _working/output/20260110_115453_pyphen/"
        ),
    )

    parser.add_argument(
        "--candidates",
        type=Path,
        required=True,
        help=(
            "Path to candidates JSON file, relative to run-dir. "
            "If the wrong prefix is specified (e.g., nltk_ for a pyphen run), "
            "the correct file will be auto-detected. "
            "Example: candidates/pyphen_candidates_2syl.json"
        ),
    )

    parser.add_argument(
        "--name-class",
        type=str,
        required=True,
        help=(
            "Name class identifier from name_classes.yml. "
            "Examples: first_name, last_name, place_name"
        ),
    )

    parser.add_argument(
        "--policy-file",
        type=Path,
        default=None,
        help=(
            "Path to name_classes.yml. If not specified, uses data/name_classes.yml "
            "from project root. Default: data/name_classes.yml"
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Maximum number of names to output. Default: 100.",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["hard", "soft"],
        default="hard",
        help=(
            "Evaluation mode. 'hard' rejects candidates with discouraged features. "
            "'soft' applies -10 penalty instead. Default: hard."
        ),
    )

    return parser


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters
    ----------
    args : list[str] | None, optional
        Arguments to parse. If None, uses sys.argv.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = create_argument_parser()
    return parser.parse_args(args)


def extract_extractor_type(run_dir: Path) -> str | None:
    """
    Extract extractor type from run directory name.

    Parameters
    ----------
    run_dir : Path
        Run directory like "_working/output/20260118_201318_pyphen"

    Returns
    -------
    str | None
        Extractor type (e.g., "pyphen", "nltk") or None if not found.
    """
    # Pattern: YYYYMMDD_HHMMSS_{extractor}
    parts = run_dir.name.split("_")
    if len(parts) >= 3:
        return "_".join(parts[2:])  # Handle multi-word extractors
    return None


def resolve_candidates_path(run_dir: Path, candidates: Path) -> Path:
    """
    Resolve candidates path, auto-detecting prefix if needed.

    If the specified path doesn't exist, tries to find a matching file
    using the extractor type from the run directory name.

    Parameters
    ----------
    run_dir : Path
        Run directory path
    candidates : Path
        Candidates path (relative to run_dir)

    Returns
    -------
    Path
        Resolved candidates path (may be different from input if auto-detected)
    """
    candidates_path = run_dir / candidates
    if candidates_path.exists():
        return candidates_path

    # Try to auto-detect the correct prefix
    extractor_type = extract_extractor_type(run_dir)
    if not extractor_type:
        return candidates_path  # Return original, will fail with proper error

    # Check if user specified wrong prefix - try the correct one
    stem = candidates.stem  # e.g., "nltk_candidates_2syl"
    parts = stem.split("_")

    if len(parts) >= 3 and parts[1] == "candidates":
        # User specified a prefix, try replacing it with the correct one
        wrong_prefix = parts[0]
        if wrong_prefix != extractor_type:
            correct_filename = f"{extractor_type}_{'_'.join(parts[1:])}.json"
            correct_path = run_dir / candidates.parent / correct_filename
            if correct_path.exists():
                print(f"Note: Auto-corrected prefix from '{wrong_prefix}' to '{extractor_type}'")
                return correct_path

    # Try to find any matching candidates file in the directory
    candidates_dir = run_dir / candidates.parent
    if candidates_dir.exists():
        # Look for files matching *_candidates_*syl.json
        for json_file in candidates_dir.glob(f"{extractor_type}_candidates_*.json"):
            if "_meta" not in json_file.name:
                # Check if syllable count matches (if specified in original)
                if "syl" in stem:
                    syl_part = stem.split("_")[-1]  # e.g., "2syl"
                    if syl_part in json_file.name:
                        print(f"Note: Found matching candidates file: {json_file.name}")
                        return json_file

    return candidates_path  # Return original, will fail with proper error


def extract_prefix_and_syllables(candidates_filename: str) -> tuple[str, int]:
    """
    Extract prefix and syllable count from candidates filename.

    Parameters
    ----------
    candidates_filename : str
        Filename like "pyphen_candidates_2syl.json"

    Returns
    -------
    tuple[str, int]
        (prefix, syllable_count) e.g., ("pyphen", 2)

    Raises
    ------
    ValueError
        If filename doesn't match expected pattern.
    """
    # Expected: {prefix}_candidates_{N}syl.json
    stem = Path(candidates_filename).stem  # pyphen_candidates_2syl
    parts = stem.split("_")

    if len(parts) < 3 or parts[1] != "candidates":
        raise ValueError(f"Unexpected candidates filename format: {candidates_filename}")

    prefix = parts[0]

    # Extract syllable count from last part (e.g., "2syl" -> 2)
    syl_part = parts[-1]
    if not syl_part.endswith("syl"):
        raise ValueError(f"Cannot extract syllable count from: {candidates_filename}")

    try:
        syllables = int(syl_part[:-3])  # Remove "syl" suffix
    except ValueError as err:
        raise ValueError(f"Cannot parse syllable count from: {syl_part}") from err

    return prefix, syllables


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the name selector CLI.

    Parameters
    ----------
    args : list[str] | None, optional
        Command-line arguments. If None, uses sys.argv.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    # Import here to avoid circular imports and speed up --help
    from build_tools.name_selector.name_class import get_default_policy_path, load_name_classes
    from build_tools.name_selector.selector import compute_selection_statistics, select_names

    parsed = parse_arguments(args)

    # Validate run directory
    run_dir = parsed.run_dir.resolve()
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}", file=sys.stderr)
        return 1

    # Resolve candidates path (with auto-detection)
    candidates_path = resolve_candidates_path(run_dir, parsed.candidates)
    if not candidates_path.exists():
        # Provide helpful error message
        extractor_type = extract_extractor_type(run_dir)
        if extractor_type:
            expected = f"candidates/{extractor_type}_candidates_Nsyl.json"
            print(
                f"Error: Candidates file not found: {run_dir / parsed.candidates}\n"
                f"  Hint: This is a '{extractor_type}' run. Expected format: {expected}",
                file=sys.stderr,
            )
        else:
            print(
                f"Error: Candidates file not found: {run_dir / parsed.candidates}", file=sys.stderr
            )
        return 1

    # Load candidates
    print(f"Loading candidates from: {candidates_path}")
    try:
        with open(candidates_path) as f:
            candidates_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {candidates_path}: {e}", file=sys.stderr)
        return 1

    candidates = candidates_data.get("candidates", [])
    print(f"Loaded {len(candidates):,} candidates")

    # Resolve policy file
    policy_path = parsed.policy_file or get_default_policy_path()
    if not policy_path.exists():
        print(f"Error: Policy file not found: {policy_path}", file=sys.stderr)
        return 1

    # Load policies
    print(f"Loading policies from: {policy_path}")
    try:
        policies = load_name_classes(policy_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error loading policies: {e}", file=sys.stderr)
        return 1

    # Get target policy
    if parsed.name_class not in policies:
        available = ", ".join(sorted(policies.keys()))
        print(
            f"Error: Unknown name class '{parsed.name_class}'. " f"Available: {available}",
            file=sys.stderr,
        )
        return 1

    policy = policies[parsed.name_class]
    print(f"Using policy: {parsed.name_class} - {policy.description}")

    # Compute statistics
    print(f"Evaluating candidates (mode={parsed.mode})...")
    stats = compute_selection_statistics(candidates, policy, mode=parsed.mode)  # type: ignore[arg-type]

    print(f"  Evaluated: {stats['total_evaluated']:,}")
    print(
        f"  Admitted: {stats['admitted']:,} ({stats['admitted']/stats['total_evaluated']*100:.1f}%)"
    )
    print(f"  Rejected: {stats['rejected']:,}")

    if stats["rejection_reasons"]:
        print("  Rejection reasons:")
        for reason, count in sorted(stats["rejection_reasons"].items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count:,}")

    # Select top names
    selected = select_names(candidates, policy, count=parsed.count, mode=parsed.mode)  # type: ignore[arg-type]
    print(f"Selected top {len(selected):,} names")

    # Prepare output - use resolved candidates_path (may have auto-corrected prefix)
    try:
        prefix, syllables = extract_prefix_and_syllables(candidates_path.name)
    except ValueError as e:
        print(f"Warning: {e}. Using defaults.", file=sys.stderr)
        prefix = "unknown"
        syllables = candidates_data.get("metadata", {}).get("syllable_count", 0)

    selections_dir = run_dir / "selections"
    selections_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"{prefix}_{parsed.name_class}_{syllables}syl.json"
    output_path = selections_dir / output_filename

    # Build output structure
    output = {
        "metadata": {
            "source_candidates": parsed.candidates.name,
            "name_class": parsed.name_class,
            "policy_description": policy.description,
            "policy_file": str(policy_path),
            "mode": parsed.mode,
            "total_evaluated": stats["total_evaluated"],
            "admitted": stats["admitted"],
            "rejected": stats["rejected"],
            "rejection_reasons": stats["rejection_reasons"],
            "score_distribution": stats["score_distribution"],
            "output_count": len(selected),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "selections": selected,
    }

    # Write output
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote selections to: {output_path}")

    # Show top 5 samples
    if selected:
        print("\nTop 5 selections:")
        for s in selected[:5]:
            features_summary = len([f for f, v in s["features"].items() if v])
            print(
                f"  {s['rank']:3d}. {s['name']:15s} score={s['score']:2d} "
                f"({features_summary} features)"
            )

    # Write meta file
    meta_output = {
        "tool": "name_selector",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "arguments": {
            "run_dir": str(run_dir),
            "candidates": str(parsed.candidates),
            "name_class": parsed.name_class,
            "policy_file": str(policy_path),
            "count": parsed.count,
            "mode": parsed.mode,
        },
        "input": {
            "candidates_file": str(candidates_path),
            "candidates_loaded": len(candidates),
            "policy_file": str(policy_path),
            "policy_name": parsed.name_class,
            "policy_description": policy.description,
        },
        "output": {
            "selections_file": str(output_path),
            "selections_count": len(selected),
        },
        "statistics": {
            "total_evaluated": stats["total_evaluated"],
            "admitted": stats["admitted"],
            "admitted_percentage": round(stats["admitted"] / stats["total_evaluated"] * 100, 2),
            "rejected": stats["rejected"],
            "rejection_reasons": stats["rejection_reasons"],
            "score_distribution": stats["score_distribution"],
            "mode": parsed.mode,
            "source_prefix": prefix,
            "syllable_count": syllables,
        },
    }

    meta_filename = f"{prefix}_selector_meta.json"
    meta_path = selections_dir / meta_filename
    with open(meta_path, "w") as f:
        json.dump(meta_output, f, indent=2)

    print(f"Wrote meta to: {meta_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
