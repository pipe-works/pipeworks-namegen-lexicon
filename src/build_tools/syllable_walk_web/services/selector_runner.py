"""
Name selector service for the creator workbench web application.

This module acts as the bridge between the HTTP server and the underlying
name-selection logic in ``build_tools.name_selector``.  It owns two
responsibilities:

1. **Policy loading** — reads ``data/name_classes.yml`` from the project root
   once per server session and caches the result.  Parsing YAML on every
   request would be wasteful; policies are static for the lifetime of a
   running workbench.

2. **Selection execution** — accepts a list of in-memory candidate dicts
   (produced by the combiner) together with user-supplied parameters and
   delegates to ``name_selector.selector.select_names`` to apply the policy.

Path resolution
---------------
``name_classes.yml`` lives at the **project root** ``data/`` directory, i.e.
two levels above ``src/``.  The resolution chain from this file is:

    selector_runner.py          ← __file__
        └─ services/            ← parents[0]
            └─ syllable_walk_web/  ← parents[1]
                └─ build_tools/ ← parents[2]
                    └─ src/     ← parents[3]
                        └─ <project root>  ← parents[4]  ← correct anchor

Using ``parents[3]`` would land inside ``src/`` — which has no ``data/``
subdirectory — and cause ``load_name_classes`` to raise ``FileNotFoundError``,
silently failing the ``/api/walker/name-classes`` endpoint and leaving the
Name Class selector in the UI stuck on "Loading Classes...".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

# ---------------------------------------------------------------------------
# Policy cache
# ---------------------------------------------------------------------------

# Module-level sentinel so that YAML parsing (file I/O + object construction)
# only happens once per server session.  ``functools.lru_cache`` would also
# work here but adds unnecessary cache-key hashing overhead for a zero-arity
# loader that never changes its result.
_policies: dict | None = None

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

# Anchor on the project root (parents[4]) so that the path remains correct
# regardless of the current working directory when the server is launched.
#
# Ancestry chain (index → directory):
#   [0] services/
#   [1] syllable_walk_web/
#   [2] build_tools/
#   [3] src/              ← NOT the project root — no data/ here
#   [4] <project root>    ← data/name_classes.yml lives here
#
# Bug history: this was previously parents[3], which resolved to src/ and
# caused FileNotFoundError, leaving the Name Class dropdown permanently stuck
# on "Loading Classes..." in the Combine tab of the creator workbench.
NAME_CLASSES_PATH: Path = (
    Path(__file__).resolve().parents[4] / "data" / "name_classes.yml"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_policies() -> dict:
    """Load name-class policies from YAML, returning the cached result on
    subsequent calls.

    The policies dict maps each class name (e.g. ``"first_name"``) to a
    ``NameClassPolicy`` object as returned by
    ``build_tools.name_selector.name_class.load_name_classes``.

    Returns:
        dict: Mapping of class name → ``NameClassPolicy``.

    Raises:
        FileNotFoundError: If ``NAME_CLASSES_PATH`` does not exist.  This
            indicates a path resolution problem rather than a runtime error
            and should surface immediately rather than being swallowed.
        yaml.YAMLError: If the policy file is malformed.
    """
    global _policies
    if _policies is None:
        # Deferred import keeps server startup fast — name_selector pulls in
        # PyYAML which is only needed once the selector UI is first used.
        from build_tools.name_selector.name_class import load_name_classes

        _policies = load_name_classes(NAME_CLASSES_PATH)
    return _policies


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_name_classes() -> list[dict[str, Any]]:
    """Return metadata for all available name classes.

    Called by the ``/api/walker/name-classes`` endpoint to populate the Name
    Class dropdown in the Combine tab of the creator workbench.

    Each entry in the returned list contains:
        - ``name`` (str): Policy key used in subsequent selector calls
          (e.g. ``"first_name"``).
        - ``description`` (str): Human-readable label for the UI.
        - ``syllable_range`` (list[int]): ``[min, max]`` syllable count that
          this class targets.

    Returns:
        list[dict]: One dict per name class, sorted by insertion order from
        the YAML policy file.

    Raises:
        FileNotFoundError: Propagated from ``_get_policies`` if the policy
            file cannot be found.
    """
    policies = _get_policies()
    return [
        {
            "name": name,
            "description": policy.description,
            "syllable_range": list(policy.syllable_range),
        }
        for name, policy in policies.items()
    ]


def run_selector(
    candidates: Sequence[dict[str, Any]],
    *,
    name_class: str = "first_name",
    count: int = 100,
    mode: Literal["hard", "soft"] = "hard",
    order: Literal["alphabetical", "random"] = "alphabetical",
    seed: int | None = None,
) -> dict[str, Any]:
    """Select names from a candidate list using a name-class policy.

    Delegates to ``build_tools.name_selector.selector.select_names`` after
    resolving the requested ``name_class`` to its loaded policy object.

    Args:
        candidates: Sequence of candidate dicts produced by the combiner.
            Each dict must contain at least ``"name"`` (str) and
            ``"features"`` (dict of bool values keyed by feature name).
        name_class: Key identifying which policy to apply.  Must be one of
            the keys present in ``data/name_classes.yml``
            (e.g. ``"first_name"``, ``"last_name"``).  Defaults to
            ``"first_name"``.
        count: Maximum number of names to return.  The selector may return
            fewer if the candidate pool is small or heavily filtered.
            Defaults to ``100``.
        mode: Filtering strictness.
            ``"hard"`` — candidates that violate a *discouraged* feature rule
            are rejected outright.
            ``"soft"`` — violations apply a score penalty instead, allowing
            borderline candidates through at a lower rank.
            Defaults to ``"hard"``.
        order: Output ordering.
            ``"alphabetical"`` — sorted A→Z by name string.
            ``"random"`` — shuffled using ``seed`` as the RNG state.
            Defaults to ``"alphabetical"``.
        seed: Integer RNG seed used when ``order="random"``.  Ignored for
            alphabetical ordering.  Pass ``None`` for non-deterministic
            shuffling (not recommended for reproducible workbench sessions).

    Returns:
        dict: Result payload with the following keys:

        - ``"name_class"`` (str): The class key that was applied.
        - ``"mode"`` (str): The filtering mode that was used.
        - ``"count"`` (int): Number of names actually selected.
        - ``"requested"`` (int): The ``count`` argument that was passed in.
        - ``"selected"`` (list[dict]): Selected name dicts, each containing
          at minimum ``"name"`` and ``"score"`` fields.

        On failure (unknown class key):

        - ``"error"`` (str): Human-readable error message.  The HTTP layer
          treats any response containing ``"error"`` as a 400.

    Raises:
        FileNotFoundError: Propagated from ``_get_policies`` if the policy
            file cannot be found.
    """
    from build_tools.name_selector.selector import select_names

    policies = _get_policies()

    # Validate the requested class before delegating — selector internals
    # expect a policy object, not a raw string.
    if name_class not in policies:
        return {"error": f"Unknown name class: {name_class}"}

    policy = policies[name_class]

    selected = select_names(
        candidates=candidates,
        policy=policy,
        count=count,
        mode=mode,
        order=order,
        seed=seed,
    )

    return {
        "name_class": name_class,
        "mode": mode,
        "count": len(selected),
        "requested": count,
        "selected": selected,
    }
