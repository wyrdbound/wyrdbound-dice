# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `rng=` parameter on `Dice.roll()` and the `roll()` convenience function: any object with a `random() -> float` method is accepted (duck-typed), making rolls reproducible from a single seeded instance across all dice, including modifier expressions
- `--seed N` flag on `tools/roll.py` for reproducible command-line rolls; seed value included in `--json` output

## v0.0.2 (2025-10-14)

### Fixed

- Fixed [bug](https://github.com/wyrdbound/wyrdbound-dice/issues/6) where keep/drop operations after reroll or explode operations were ignored (e.g., `4d6r<=2kh3` now correctly keeps the highest 3 dice after rerolling)
- Corrected incorrect GH user in links in pyproject.toml

## v0.0.1 (2025-07-28)

### Added

- Initial release
- Complete dice expression parser with mathematical precedence
- Support for major RPG dice mechanics
- Comprehensive test suite with decent coverage
- CLI tools for rolling and analyzing dice expressions
- Thread-safe operation
- Unicode support
- Debug logging for trouble-shooting and logger configuration
- Extensive documentation and examples
