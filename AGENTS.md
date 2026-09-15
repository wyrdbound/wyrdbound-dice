# wyrdbound-dice Development Guidelines

Last updated: 2026-09-15

**Spec Kit is no longer used in this project.** Do not run or reference
`/speckit.*` commands. The constitution and the feature plans are the governing
documents; author and edit them directly.

## Governing Documents

| Document | Purpose |
|---|---|
| [`planning/constitution.md`](planning/constitution.md) | **Project constitution** — non-negotiable principles. Read first. |
| [`planning/features/`](planning/features) | **Active build plan** — ordered features, specs, plans, and task lists. |
| [`README.md`](README.md) | User-facing documentation and API reference |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history; document all changes under "Unreleased" |

## Verification Contract

Every task ends with the gate green. No exceptions.

1. **Tests pass.** `pytest` is green from the repo root.
2. **Lint and format are clean.** `ruff check src/ tests/ tools/` passes; new code
   is formatted with `black --line-length=88` and `isort --profile=black`.
3. **Docs kept in sync.** README updated for user-facing changes; CHANGELOG
   updated under "Unreleased"; docstrings on all public APIs.
4. **A failing test blocks merge.** Never delete or weaken a test to make the
   gate green.

Work one task per run, in order, and stop rather than guessing. A task that
cannot finish without breaking the gate is a badly split task: split it
differently rather than landing a broken state.

## Project Constitution (Summary — full text in `planning/constitution.md`)

These articles are **non-negotiable**. When in doubt, the constitution wins.

1. **Article I — Library-First Design.** Every feature starts as a standalone,
   self-contained, independently testable module with a clear dice-rolling
   purpose. The core library has **zero external dependencies** (optional deps
   only for visualization/tools) and must run on **Python 3.8–3.12+**.
2. **Article II — CLI Interface Protocol.** Every library feature is reachable
   from the CLI: stdin/args → stdout, errors → stderr. Support both human-readable
   and `--json` output, `-v/--verbose`, `--count N`, and `--debug`.
3. **Article III — Test-First Development (NON-NEGOTIABLE).** Tests are written
   before implementation (Red → Green → Refactor). Cover all edge cases, error
   conditions, and RPG mechanics. Integration tests are required for parser
   changes, keep/drop chains, and reroll+explode combinations. Stress tests cover
   thread safety and concurrent use.
4. **Article IV — Mathematical Precision.** Correct PEMDAS/BODMAS precedence,
   statistically accurate probability, and sane handling of edge cases (zero dice,
   negative dice, division by zero, infinite conditions). All operations are
   thread-safe. Same expression + same seed = same result.
5. **Article V — RPG System Fidelity.** Shorthands (FUDGE, BOON, BANE, FLUX,
   PERC), keep/drop chains (`kh`, `kl`, `dh`, `dl`), limited/unlimited rerolls,
   exploding dice, and Fudge symbol display must match the official rules. Full
   Unicode support (`×`, `÷`, `−`, fullwidth characters).
6. **Article VI — Observability & Debugging.** Structured `[TAG]` debug output,
   injectable Python/custom loggers, step-by-step tracing (tokenize, parse,
   evaluate, result), `--debug` capture in JSON output, and clear
   `ParseError` / `DivisionByZeroError` / `InfiniteConditionError` messages.

### Code Quality

- **Formatting**: `black --line-length=88`, `isort --profile=black`
- **Linting**: `ruff check --line-length=100`
- **Typing**: every public API carries type annotations
- **Docs**: docstrings on all public classes, methods, and functions; module-level
  docs explaining purpose
- **Errors**: specific exception types, messages that help users fix their
  expression, no silent failures

### Performance Standards

- No global mutable state during rolling (thread safety)
- Avoid unnecessary allocations in hot paths
- CLI tools start in <100 ms for simple rolls
- Simple rolls complete in <1 ms

### Security

- **No `eval()` / `exec()`** in expression parsing
- Validate and sanitize all user input
- Resource limits prevent infinite reroll/explode loops
- Core library keeps zero dependencies

### Development Workflow

- **Branches**: `feature/description` or `fix/description`
- **Conventional commits REQUIRED**: `<type>[optional scope]: <description>`
  - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`,
    `build`, `style`
  - Description after `type: ` MUST start lowercase
  - Single high-level description — no itemized bullet lists
  - Breaking changes: `!` before the colon or a `BREAKING CHANGE:` footer
- **PRs**: follow `.github/pull_request_template.md`
- **Review checklist**: tests pass · new tests added · black/isort clean · no ruff
  violations · docstrings updated · README updated if user-facing · CHANGELOG
  updated · manual CLI testing done
- **Versioning**: semver MAJOR.MINOR.PATCH; keep `pyproject.toml` and
  `__init__.py:__version__` in sync

### Governance

This constitution supersedes all other development practices for
wyrdbound-dice. Amendments require:

1. Discussion in a GitHub issue or PR
2. Rationale documented in CHANGELOG
3. A migration plan for existing code (if breaking)
4. An update to `planning/constitution.md`

All PRs are reviewed against the constitution, and complexity must be justified
against the Core Principles.

## General Working Principles

These apply to every task regardless of feature.

1. **Tests first, always.** Write the failing test before the implementation.
   Tests are the specification; they are never edited to match buggy behavior.
2. **The gate is green.** Do not end a task with a failing test, a lint
   violation, or unformatted code.
3. **Determinism and reproducibility.** Any randomness a feature introduces must
   be injectable and seedable (see `rng=` on `Dice.roll()`). Same input + same
   seed = same output. Never reach for `secrets`, `os.urandom`, or system time in
   library code.
4. **Minimal dependencies.** Prefer the standard library. The core package stays
   dependency-free.
5. **No scope creep.** Do what the task asks. New features require a plan entry
   under `planning/features/` first.
6. **Explain through docs, not comments.** Code should be self-explanatory;
   public behavior belongs in docstrings and the README.
7. **Stop rather than guess.** If the task is ambiguous, ask. Do not invent
   requirements or silently drop requirements you don't understand.

## Commands

```bash
# Environment
pip install -e ".[dev]"              # dev install
pip install -e ".[dev,visualization]"  # + graph tool deps

# Gate
pytest                               # run full suite
pytest --cov=wyrdbound_dice          # with coverage
ruff check src/ tests/ tools/        # lint

# Format
black src/ tests/ tools/             # format
isort src/ tests/ tools/             # sort imports

# CLI tools
python tools/roll.py "1d20 + 5"      # roll
python tools/roll.py "2d6" --count 10
python tools/roll.py "1d20" --json
python tools/roll.py "2d6 + 3" --debug
python tools/graph.py "2d6"          # probability distribution
```

The gate runs from the repo root: `pytest && ruff check src/ tests/ tools/`.

## Architecture

```text
src/wyrdbound_dice/
├── __init__.py          # public API exports
├── dice.py              # Dice class and rolling logic
├── expression_lexer.py  # tokenization
├── expression_parser.py # parsing with precedence
├── expression_token.py  # token types
├── roll_result.py       # RollResult data structure
├── debug_logger.py      # debug logging infrastructure
└── errors.py            # custom exceptions
```

Layering: `dice.py` orchestrates; lexer → parser → evaluation is one-directional;
`tools/` and `tests/` may import anything. The core package imports only the
standard library.

## Project Structure

```text
src/                 # library code (wyrdbound_dice/)
tests/               # test suite
tools/               # CLI tools (roll.py, graph.py)
planning/            # constitution + feature specs, plans, and tasks
```

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
