# pipeworks-namegen-lexicon

Lexicon creation pipeline and web tooling for Pipeworks name generation.

## Scope

- Corpus extraction, normalization, annotation, and selection workflows under `build_tools/`.
- Syllable walk web app (`build_tools.syllable_walk_web`) for lexicon pipeline operations.
- Versioned lexicon artifact generation for downstream runtime/API import flows.

## Out of Scope

- Runtime name-generation API service (`pipeworks-namegen-api`).
- Deterministic generation engine library (`pipeworks-namegen-core`).
- TUI applications (`pipeline_tui`, `syllable_walk_tui`) are retired in this
  repo.

## Development

```bash
pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
pytest -q
```

## Web App Entry Point

```bash
pipeworks-namegen-lexicon-web --help
```
