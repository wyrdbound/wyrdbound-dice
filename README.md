# Wyrdbound Dice

A comprehensive dice rolling library for tabletop RPGs, designed to handle complex dice expressions with mathematical precision and extensive system support.

This library is designed for use in [wyrdbound](https://github.com/wyrdbound), a text-based RPG system that emphasizes narrative and player choice.

[![CI](https://github.com/wyrdbound/wyrdbound-dice/actions/workflows/ci.yml/badge.svg)](https://github.com/wyrdbound/wyrdbound-dice/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 📣 This library is experimental and was built with much :heart: and [vibe coding](https://en.wikipedia.org/wiki/Vibe_coding). Please do not launch :rocket: or perform :brain: surgery using it. (Should be :a:-:ok: for your Table-Top application though!)

## Features

Wyrdbound Dice supports an extensive range of dice rolling mechanics used across many tabletop RPG systems:

### Basic Dice Rolling

- **Standard polyhedral dice**: `1d4`, `1d6`, `1d8`, `1d10`, `1d12`, `1d20`, `1d100`
- **Multiple dice**: `3d6`, `4d8`, etc.
- **Percentile dice**: `1d%` (displays as [tens, ones])

### Mathematical Operations

- **Arithmetic operations**: `2d6 + 3`, `1d20 - 2`, `1d6 × 4`, `1d10 ÷ 2`
- **Complex expressions**: `2d6 + 1d4 × 2 - 1`
- **Proper precedence**: Mathematical order of operations (PEMDAS/BODMAS)
- **Unicode operators**: Support for `×`, `÷`, `−`, and fullwidth characters

### Keep/Drop Mechanics

- **Keep highest**: `4d6kh3` (ability score generation), `2d20kh1` (advantage)
- **Keep lowest**: `4d6kl3`, `2d20kl1` (disadvantage)
- **Drop operations**: `4d6dh1` (drop highest), `4d6dl1` (drop lowest)
- **Multiple operations**: `5d6kh3kl1` (chain keep/drop operations)

### Reroll Mechanics

- **Unlimited rerolls**: `1d6r<=2` (reroll while ≤ 2)
- **Limited rerolls**: `1d6r1<=2` (reroll once), `1d6r3<=3` (reroll up to 3 times)
- **Comparison operators**: `<=`, `<`, `>=`, `>`, `=`
- **Alternate notation**: `1d6ro<=2` (reroll once)

### Exploding Dice

- **Simple explosion**: `1d6e` (explode on max value)
- **Explicit threshold**: `1d6e6`, `1d10e>=8`
- **Custom conditions**: `1d6e>=5` (explode on 5 or 6)
- **Multiple explosions**: Dice can explode repeatedly

### Fudge Dice (Fate Core/Accelerated)

- **Single Fudge die**: `1dF` (results: -1, 0, +1)
- **Standard Fate roll**: `4dF`
- **Symbol display**: Shows as `-, B, +`
- **Math operations**: Can be combined with other dice and modifiers

### System Shorthands

- **FUDGE**: `4dF` (Fate Core)
- **BOON**: `3d6kh2` (Traveller advantage)
- **BANE**: `3d6kl2` (Traveller disadvantage)
- **FLUX**: `1d6 - 1d6` (Traveller flux)
- **GOODFLUX**: Always positive flux (highest 1d6 - lowest 1d6)
- **BADFLUX**: Always negative flux (lowest 1d6 - highest 1d6)
- **PERC / PERCENTILE**: `1d%`

### Named Modifiers

- **Static modifiers**: `{"Strength": 3, "Proficiency": 2}`
- **Dice modifiers**: `{"Guidance": "1d4", "Bane": "-1d4"}`
- **Mixed modifiers**: Combine static numbers and dice expressions

### Advanced Features

- **Zero dice handling**: `0d6` returns 0
- **Negative dice**: `-1d6` returns negative result
- **Thread safety**: Safe for concurrent use
- **Error handling**: Clear exceptions for invalid conditions
- **Infinite condition detection**: Prevents impossible reroll/explode scenarios

## Installation

### For End Users

```bash
pip install wyrdbound-dice
```

> **Note**: This package is currently in development and not yet published to PyPI. For now, please use the development installation method below.

### For Development

If you want to contribute to the project or use the latest development version:

```bash
# Clone the repository
git clone https://github.com/wyrdbound/wyrdbound-dice.git
cd wyrdbound-dice

# Install in development mode
pip install -e .
```

### Optional Dependencies

For visualization features (graph tool):

```bash
pip install "wyrdbound-dice[visualization]"
```

For development:

```bash
pip install -e ".[dev]"
```

For both visualization and development:

```bash
pip install -e ".[dev,visualization]"
```

## Quick Start

```python
from wyrdbound_dice import Dice

# Basic roll
result = Dice.roll("1d20")
print(result.total) # 20
print(result)       # 20 = 20 (1d20: 20)

# Complex expression
result = Dice.roll("2d6 + 1d4 × 2 + 3")
print(result) # 17 = 8 (2d6: 6, 2) + 3 (1d4: 3) x 2 + 3

# Advantage roll (D&D 5e)
result = Dice.roll("2d20kh1")
print(result) # 19 = 19 (2d20kh1: 19, 12)

# Reroll (D&D 5e - Great Weapon Fighting)
result = Dice.roll("2d6r1<=2")
print(result) # 12 = 12 (2d6r1<=2: 1, 2, 6, 6)

# Exploding dice (Savage Worlds)
result = Dice.roll("1d6e")
print(result) # 11 = 11 (1d6e6: 6, 5)

# Fate Core
result = Dice.roll("4dF + 2")
print(result) # 2 = 0 (4dF: +, B, -, B) + 2

# With named modifiers
modifiers = {"Strength": 3, "Proficiency": 2, "Bless": "1d4"}
result = Dice.roll("1d20", modifiers)
print(result) # 20 = 12 (1d20: 12) + 3 (Strength) + 2 (Proficiency) + 3 (Bless: 3 = 3 (1d4: 3))
```

## API Reference

### Main Classes

#### `Dice`

The main entry point for dice rolling.

**`Dice.roll(expression, modifiers=None)`**

- `expression` (str): Dice expression to evaluate
- `modifiers` (dict, optional): Named modifiers as `{name: value}` where value can be int or dice expression string
- Returns: `RollResultSet` object

#### `RollResultSet`

Contains the results of a dice roll.

**Properties:**

- `total` (int): Final calculated result
- `results` (list): List of individual `RollResult` objects
- `modifiers` (list): List of applied modifiers
- `__str__()`: Human-readable description of the complete roll

#### `RollResult`

Represents a single dice expression result.

**Properties:**

- `num` (int): Number of dice rolled
- `sides` (int/str): Number of sides (or "F" for Fudge, "%" for percentile)
- `rolls` (list): Final kept dice values
- `all_rolls` (list): All dice rolled (including rerolls, explosions)
- `total` (int): Sum of kept dice

### Exceptions

- **`ParseError`**: Invalid dice expression syntax
- **`DivisionByZeroError`**: Division by zero in expression
- **`InfiniteConditionError`**: Impossible reroll/explode condition

## Command Line Tools

### Roll Tool

Roll dice expressions from the command line:

```bash
# Basic usage
python tools/roll.py "1d20 + 5"

# Multiple rolls
python tools/roll.py "2d6" --count 10

# JSON output (single roll)
python tools/roll.py "1d20" --json

# JSON output (multiple rolls)
python tools/roll.py "1d6" --count 3 --json
```

**Options:**

- `-v, --verbose`: Show detailed breakdown
- `-n, --count N`: Roll N times
- `--json`: Output results as JSON

**JSON Output Format:**

Single roll returns an object:

```json
{
  "result": 14,
  "description": "14 = 14 (1d20: 14)"
}
```

Multiple rolls return an array:

```json
[
  {
    "result": 4,
    "description": "4 = 4 (1d6: 4)"
  },
  {
    "result": 6,
    "description": "6 = 6 (1d6: 6)"
  }
]
```

### Visualization Tool

Generate probability distributions and statistics:

```bash
# Basic distribution graph
python tools/graph.py "2d6"

# Complex expression with more samples
python tools/graph.py "1d20 + 5" --num-rolls 50000

# Specify output file
python tools/graph.py "4d6kh3" --output ability_scores.html
```

**Features:**

- Probability distribution histograms
- Statistical analysis (mean, mode, range)
- Comparison charts for multiple expressions
- Export to various image formats

## Supported Systems

WyrdBound Dice has been designed to support mechanics from many popular RPG systems:

- **D&D 5e / Pathfinder**: Advantage/disadvantage (`2d20kh1`/`2d20kl1`), ability scores (`4d6kh3`)
- **Savage Worlds**: Exploding dice (`1d6e`), wild dice, aces
- **Fate Core/Accelerated**: Fudge dice (`4dF`, `FUDGE`)
- **Traveller**: Boon/Bane (`BOON`/`BANE`), Flux dice (`FLUX`)
- **World of Darkness**: Dice pools with success counting (upcoming)
- **Shadowrun**: Exploding dice, glitch detection (upcoming)

## Examples

### Character Creation

```python
# D&D 5e ability scores
stats = []
for _ in range(6):
    result = Dice.roll("4d6kh3")
    stats.append(result.total)

# Traveller characteristics with modifiers
characteristics = Dice.roll("2d6", {"DM": 1})
```

### Combat Rolls

```python
# D&D 5e attack with advantage
attack = Dice.roll("2d20kh1 + 8")  # +8 attack bonus

# Savage Worlds damage with ace
damage = Dice.roll("1d6e + 2")

# Fate Core with aspects
fate_roll = Dice.roll("4dF + 3", {"Aspect": 2})
```

### Complex Expressions

```python
# Fireball damage (8d6) with Metamagic (reroll 1s)
fireball = Dice.roll("8d6r1<=1")

# Sneak attack with multiple damage types
sneak = Dice.roll("1d8 + 3d6")  # Rapier + sneak attack

# Mathematical complexity
complex_formula = Dice.roll("(2d6 + 3) × 2 + 1d4 - 1")
```

## Debug Logging

WyrdBound Dice includes comprehensive debug logging to help troubleshoot dice rolling issues and understand how expressions are parsed and evaluated.

### Enabling Debug Mode

```python
from wyrdbound_dice import Dice

# Enable debug logging for a roll
result = Dice.roll("2d6 + 3", debug=True)
```

### Debug Output Example

When debug mode is enabled, you'll see detailed step-by-step information:

```
DEBUG: [START] Rolling expression: '2d6 + 3'
DEBUG: [PROCESSING] Starting expression processing
DEBUG: NORMALIZED: '2d6 + 3'
DEBUG: [PARSER_SELECTION] Using precedence parser
DEBUG: [TOKENIZING] Tokenizing expression: '2d6 + 3'
DEBUG: Tokens: ['DICE(2d6)@0', 'PLUS(+)@3', 'NUMBER(3)@4']
DEBUG: [PARSING] Parsing tokens with precedence rules
DEBUG: [EVALUATING] Evaluating parsed expression
DEBUG: Rolling 1d6: 5
DEBUG: Rolling 1d6: 4
DEBUG: [RESULT] Expression evaluated to: 12
DEBUG: TOTAL 12 modifiers(0) = 12
DEBUG: [COMPLETE] Final result: 12
```

### What Debug Mode Shows

Debug logging provides insights into:

- **Expression normalization**: How input expressions are cleaned and processed
- **Shorthand expansion**: When shortcuts like "FUDGE" are expanded to "4dF"
- **Parser selection**: Whether the precedence parser or original parser is used
- **Tokenization**: How complex expressions are broken into tokens
- **Individual dice rolls**: Each die roll with specific results
- **Keep/drop operations**: Parsed keep/drop operations like "kh2"
- **Mathematical evaluation**: Step-by-step calculation of complex expressions
- **Modifier processing**: How modifiers are applied to results
- **Error handling**: Debug information even when errors occur

### Debug Examples

```python
# Simple dice with debug
result = Dice.roll("1d20", debug=True)

# Complex expression with debug
result = Dice.roll("2d6 * 2 + 1d4", debug=True)

# Keep operations with debug
result = Dice.roll("4d6kh3", debug=True)

# Shorthand expansion with debug
result = Dice.roll("FUDGE", debug=True)

# With modifiers and debug
modifiers = {"strength": 3, "magic_bonus": 2}
result = Dice.roll("1d20", modifiers=modifiers, debug=True)
```

### Custom Debug Loggers

You can inject your own logger to capture debug output using Python's standard logging interface:

```python
import logging
from wyrdbound_dice import Dice
from wyrdbound_dice.debug_logger import StringLogger

# Method 1: Use the built-in StringLogger for testing/API purposes
string_logger = StringLogger()
result = Dice.roll("2d6 + 3", debug=True, logger=string_logger)

# Get all the debug output as a string
debug_output = string_logger.get_logs()
print(debug_output)

# Clear the logger for reuse
string_logger.clear()

# Method 2: Use Python's standard logging module
# Create a custom logger with your preferred configuration
logger = logging.getLogger('my_dice_app')
logger.setLevel(logging.DEBUG)

# Add your own handler (file, web service, etc.)
handler = logging.FileHandler('dice_debug.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(handler)

# Use with dice rolling
result = Dice.roll("1d20", debug=True, logger=logger)

# Method 3: Create a custom logger class
class WebAppLogger:
    def debug(self, message):
        # Send to your web app's logging system
        app.logger.debug(message)

    def info(self, message):
        app.logger.info(message)

    def warning(self, message):
        app.logger.warning(message)

    def error(self, message):
        app.logger.error(message)

web_logger = WebAppLogger()
result = Dice.roll("1d20", debug=True, logger=web_logger)
```

### Logger Interface

Custom loggers should implement Python's standard logging interface methods:

```python
class MyCustomLogger:
    def debug(self, message: str) -> None:
        """Log a debug message."""
        ...

    def info(self, message: str) -> None:
        """Log an info message."""
        ...

    def warning(self, message: str) -> None:
        """Log a warning message."""
        ...

    def error(self, message: str) -> None:
        """Log an error message."""
        ...
class MyLogger:
    def log(self, message: str) -> None:
        # Your custom logging implementation
        pass
```

### Command Line Debug

The `tools/roll.py` script also supports debug mode:

```bash
# Basic roll with debug
python tools/roll.py "2d6 + 3" --debug

# Complex expression with debug
python tools/roll.py "4d6kh3" --debug

# Multiple rolls with debug
python tools/roll.py "1d6" -n 3 --debug

# JSON output with debug information included
python tools/roll.py "2d6 + 3" --json --debug

# Help shows all options including debug
python tools/roll.py --help
```

When using `--json --debug`, the debug output is captured and included in the JSON response under a "debug" key:

```json
{
  "result": 11,
  "description": "11 = 8 (2d6: 4, 4) + 3",
  "debug": "DEBUG: [START] Rolling expression: '2d6 + 3'\nDEBUG: [PROCESSING] Starting expression processing\n..."
}
```

### Debug Output Format

Debug messages are prefixed with `DEBUG:` and use structured labels like `[START]`, `[TOKENIZING]`, `[PARSING]`, etc. This makes it easy to follow the progression through the dice rolling engine and identify where issues might occur.

## Development

### Setting Up Development Environment

```bash
# Install the package with development dependencies
pip install -e ".[dev]"

# Install with both development and visualization dependencies
pip install -e ".[dev,visualization]"

# Or install development dependencies separately
pip install pytest pytest-cov black isort ruff
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=wyrdbound_dice

# Run with coverage and generate HTML report
python -m pytest tests/ --cov=wyrdbound_dice --cov-report=html

# Run specific test class
python -m pytest tests/test_dice.py::TestDiceKeepHighestLowest
```

### Code Quality

```bash
# Format code
black src/ tests/ tools/

# Sort imports
isort src/ tests/ tools/

# Lint code
ruff check src/ tests/ tools/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Areas for Contribution

- New features for existing RPG systems
- Performance optimizations
- Additional CLI tools
- Documentation improvements
- Bug fixes and testing

### Continuous Integration

This project uses GitHub Actions for CI/CD:

- **Testing**: Automated tests across Python 3.8-3.12 on Ubuntu, Windows, and macOS
- **Code Quality**: Black formatting, isort import sorting, and Ruff linting
- **Package Validation**: Installation testing and CLI tool verification

All pull requests are automatically tested and must pass all checks before merging.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the diverse mechanics of tabletop RPG systems
- Thanks to the RPG community for feedback and feature requests
- Built with mathematical precision and gaming passion
