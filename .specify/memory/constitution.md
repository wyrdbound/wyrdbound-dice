# Wyrdbound Dice Constitution

## Core Principles

### I. Library-First Design

Every feature starts as a standalone, self-contained library component:
- **Self-contained modules**: Each module must be independently testable and documented
- **Clear purpose**: No organizational-only libraries; each component solves a specific dice-rolling problem
- **Zero external dependencies**: Core library must remain dependency-free (optional deps for visualization/tools only)
- **Python 3.8+ compatibility**: All code must work across Python 3.8-3.12+

### II. CLI Interface Protocol

Every library feature exposes functionality via CLI tools:
- **Text in/out protocol**: stdin/args → stdout, errors → stderr
- **Dual output formats**: Support both human-readable and JSON output (`--json` flag)
- **Verbosity options**: `-v, --verbose` for detailed breakdowns
- **Batch operations**: Support `--count N` for multiple rolls
- **Debug mode**: `--debug` flag for troubleshooting with structured output

### III. Test-First Development (NON-NEGOTIABLE)

TDD is mandatory for all changes:
1. **Tests written first**: User must approve test cases before implementation
2. **Red-Green-Refactor**: Tests must fail → Implementation → Tests pass → Refactor
3. **Comprehensive coverage**: All edge cases, error conditions, and RPG system mechanics
4. **Integration tests**: Required for parser changes, keep/drop chains, reroll+explode combinations
5. **Chaos engineering**: Stress tests for thread safety and concurrent usage

### IV. Mathematical Precision

Dice rolling must be mathematically correct and deterministic:
- **Proper precedence**: PEMDAS/BODMAS order of operations in expressions
- **Accurate probability**: All mechanics must produce statistically correct distributions
- **Edge case handling**: Zero dice, negative dice, division by zero, infinite conditions
- **Thread safety**: All operations must be safe for concurrent use
- **Reproducibility**: Same expression + same random seed = same result

### V. RPG System Fidelity

Support must accurately reflect tabletop RPG mechanics:
- **System shorthands**: FUDGE, BOON, BANE, FLUX, PERC must match official rules
- **Keep/drop mechanics**: `kh`, `kl`, `dh`, `dl` must work in chains
- **Reroll mechanics**: Limited and unlimited rerolls with comparison operators
- **Exploding dice**: Simple explosion and threshold-based explosion
- **Fudge dice**: Proper `-, B, +` symbol display and arithmetic
- **Unicode support**: Full support for `×`, `÷`, `−`, and fullwidth characters

### VI. Observability & Debugging

All code must be debuggable and observable:
- **Debug logging**: Structured debug output with `[TAG]` format
- **Custom logger injection**: Support Python logging + custom logger interfaces
- **Step-by-step tracing**: Tokenization, parsing, evaluation, result calculation
- **CLI debug output**: `--debug` flag captures logs in JSON output
- **Error clarity**: ParseError, DivisionByZeroError, InfiniteConditionError with clear messages

## Code Quality Standards

### Formatting & Linting
- **Black**: Code formatted with `black --line-length=88`
- **isort**: Imports sorted with `isort --profile=black`
- **Ruff**: Linting with `ruff check --line-length=100`
- **Type hints**: All public APIs must have type annotations

### Documentation
- **Docstrings**: All public classes, methods, and functions documented
- **Examples**: Usage examples in docstrings and README
- **Module-level docs**: Each module explains its purpose
- **README updates**: New features documented with examples

### Error Handling
- **Specific exceptions**: Use ParseError, DivisionByZeroError, InfiniteConditionError
- **Clear messages**: Error messages must help users fix their expressions
- **No silent failures**: All errors must be reported clearly

## Development Workflow

### Git Branching & Commits
- **Feature branches**: `feature/description` or `fix/description`
- **Sequential numbering**: Use Spec Kit's sequential branch numbering
- **Conventional commits REQUIRED**: Format `<type>[optional scope]: <description>`
  - Examples: `feat: add success counting for World of Darkness`, `fix(parser): resolve reroll chain edge case`, `chore: update dependencies`
  - **Description MUST be lowercase**: the word immediately after `type: ` must begin with a lowercase letter
  - **NO itemized lists**: Commit messages must be single high-level descriptions, not bullet lists of changes
  - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`
  - Breaking changes: Append `!` before colon or add `BREAKING CHANGE:` footer
- **PR templates**: Follow `.github/pull_request_template.md`

### Code Review Checklist
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Code formatted with black/isort
- [ ] No ruff violations
- [ ] Docstrings added/updated
- [ ] README updated if user-facing change
- [ ] CHANGELOG.md updated
- [ ] Manual testing with CLI tools

### Version Management
- **Semantic versioning**: MAJOR.MINOR.PATCH
- **pyproject.toml**: Update version before release
- **__init__.py**: Keep `__version__` in sync
- **CHANGELOG.md**: Document all changes under "Unreleased"

## Technical Architecture

### Module Structure
```
src/wyrdbound_dice/
├── __init__.py          # Public API exports
├── dice.py              # Main Dice class and rolling logic
├── expression_lexer.py  # Tokenization
├── expression_parser.py # Parsing with precedence
├── expression_token.py  # Token types
├── roll_result.py       # RollResult data structure
├── debug_logger.py      # Debug logging infrastructure
└── errors.py            # Custom exceptions
```

### Testing Structure
```
tests/
├── test_base.py                          # Foundation tests
├── test_dice.py                          # Core dice tests
├── test_dice_*.py                        # Feature-specific tests
├── test_expression_parsing.py            # Parser tests
├── test_infinite_conditions.py           # Error handling tests
└── test_debug_logging.py                 # Debug infrastructure tests
```

### Tool Structure
```
tools/
├── roll.py                               # CLI rolling tool
└── graph.py                              # Visualization tool
```

## Performance Standards

- **Thread safety**: No global mutable state during rolling
- **Memory efficiency**: Avoid unnecessary allocations in hot paths
- **Startup time**: CLI tools must start quickly (<100ms for simple rolls)
- **Roll throughput**: Simple rolls should complete in <1ms

## Security Considerations

- **No eval()**: Expression parsing must not use eval or exec
- **Input validation**: All user input sanitized and validated
- **Resource limits**: Prevent infinite loops in reroll/explode conditions
- **Dependency minimization**: Core library has zero dependencies

## Governance

This constitution supersedes all other development practices for wyrdbound-dice.

**Amendments require:**
1. Discussion in GitHub issue or PR
2. Rationale documented in CHANGELOG
3. Migration plan for existing code (if breaking)
4. Update to this constitution

**Compliance verification:**
- All PRs must be reviewed against this constitution
- Complexity must be justified against Core Principles
- Use `.specify/templates/` for runtime development guidance

---

**Version**: 1.0.0  
**Ratified**: 2026-05-03  
**Last Amended**: 2026-05-03  
**Project**: wyrdbound-dice v0.0.2
