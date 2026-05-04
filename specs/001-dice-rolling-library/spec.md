# Feature Specification: Dice Rolling Library for Tabletop RPGs

**Feature Branch**: `addRNGInjection`  
**Created**: 2026-05-03  
**Status**: Implemented (Documentation)  
**Input**: Document existing wyrdbound-dice repository codebase

## Clarifications

### Session 2026-05-03

- Q: How should RNG be injectable into `Dice.roll()`? → A: Add `rng=None` parameter — full signature `Dice.roll(expression, modifiers=None, rng=None)` — where `rng` is duck-typed to any object with a `random()` method, defaulting to stdlib random. Backward-compatible: existing callers unaffected.
- Q: Should GOODFLUX and BADFLUX be included in the system shorthands spec? → A: Yes — add to FR-011; they are fully implemented, tested, and documented.
- Q: Should the `rng` parameter propagate to nested modifier dice rolls? → A: Yes — the entire `Dice.roll()` call, including all modifier dice expressions, uses the same `rng` instance for end-to-end reproducibility.

## User Scenarios & Testing

### User Story 1 - Basic Dice Rolling (Priority: P1)

As a tabletop RPG player, I want to roll standard polyhedral dice (d4, d6, d8, d10, d12, d20, d100) so that I can resolve game actions quickly.

**Why this priority**: This is the core MVP functionality - without basic dice rolling, the library provides no value. This is the foundation all other features build upon.

**Independent Test**: Can be fully tested by rolling expressions like "1d20", "3d6", "2d8" and verifying results are within expected ranges.

**Acceptance Scenarios**:

1. **Given** a user enters "1d20", **When** the roll is executed, **Then** the result is between 1 and 20
2. **Given** a user enters "3d6", **When** the roll is executed, **Then** the result is between 3 and 18
3. **Given** a user enters "1d%", **When** the roll is executed, **Then** the result shows tens and ones digits separately

---

### User Story 2 - Mathematical Operations on Dice (Priority: P2)

As a player, I want to add, subtract, multiply, and divide dice results so that I can apply modifiers and calculate complex formulas.

**Why this priority**: Modifiers are essential to almost all RPG systems. Players need to add ability scores, proficiency bonuses, and other modifiers to their rolls.

**Independent Test**: Can be tested independently by rolling expressions like "1d20 + 5", "2d6 - 1", "1d6 × 2" and verifying correct arithmetic.

**Acceptance Scenarios**:

1. **Given** a user enters "1d20 + 5", **When** the roll is executed, **Then** the result equals the die roll plus 5
2. **Given** a user enters "2d6 + 1d4 × 2", **When** the roll is executed, **Then** the result follows proper order of operations (PEMDAS)
3. **Given** a user enters "1d6 - 1d6", **When** the roll is executed, **Then** the result can be negative, zero, or positive

---

### User Story 3 - Keep/Drop Mechanics (Priority: P3)

As a D&D 5e player, I want to keep the highest or lowest dice from a roll so that I can implement advantage/disadvantage and ability score generation.

**Why this priority**: Advantage/disadvantage is a core D&D 5e mechanic. Ability score generation (4d6 drop lowest) is universal across many systems.

**Independent Test**: Can be tested by rolling "2d20kh1" for advantage or "4d6kh3" for ability scores and verifying correct dice are kept.

**Acceptance Scenarios**:

1. **Given** a user enters "2d20kh1", **When** the roll is executed, **Then** the higher of the two dice is kept
2. **Given** a user enters "4d6kh3", **When** the roll is executed, **Then** the lowest die is dropped and the three highest are summed
3. **Given** a user enters "5d6kh3kl1", **When** the roll is executed, **Then** keep/drop operations chain correctly

---

### User Story 4 - Reroll Mechanics (Priority: P4)

As a player, I want to reroll dice that meet certain conditions so that I can implement mechanics like Great Weapon Fighting or Fey Touch.

**Why this priority**: Reroll mechanics are common in D&D 5e and other systems, allowing players to improve poor rolls under specific conditions.

**Independent Test**: Can be tested by rolling "1d6r<=2" and verifying dice showing 1 or 2 are rerolled.

**Acceptance Scenarios**:

1. **Given** a user enters "1d6r<=2", **When** the roll is executed, **Then** any die showing 1 or 2 is rerolled
2. **Given** a user enters "2d6r1<=2", **When** the roll is executed, **Then** each die can be rerolled once if it shows 1 or 2
3. **Given** a user enters "4d6r<=2kh3", **When** the roll is executed, **Then** rerolls happen before keep operations

---

### User Story 5 - Exploding Dice (Priority: P5)

As a Savage Worlds player, I want dice to explode on maximum values so that I can implement the Aces mechanic from Savage Worlds.

**Why this priority**: Exploding dice are core to Savage Worlds and add excitement by allowing exceptional results beyond normal maximums.

**Independent Test**: Can be tested by rolling "1d6e" and verifying that rolling a 6 triggers an additional die roll.

**Acceptance Scenarios**:

1. **Given** a user enters "1d6e", **When** a 6 is rolled, **Then** an additional d6 is rolled and added
2. **Given** a user enters "1d6e6", **When** a 6 is rolled, **Then** the die explodes
3. **Given** a user enters "1d6e>=5", **When** a 5 or 6 is rolled, **Then** the die explodes

---

### User Story 6 - Fudge/Fate Dice (Priority: P6)

As a Fate Core player, I want to roll Fudge dice (dF) so that I can play Fate Accelerated and other Fate-based games.

**Why this priority**: Fudge dice use a special distribution (-1, 0, +1) that standard dice cannot replicate, making this essential for Fate system players.

**Independent Test**: Can be tested by rolling "4dF" and verifying results show -, B, + symbols with appropriate values.

**Acceptance Scenarios**:

1. **Given** a user enters "4dF", **When** the roll is executed, **Then** each die shows -, B, or + with values -1, 0, or +1
2. **Given** a user enters "4dF + 2", **When** the roll is executed, **Then** the Fudge result has 2 added to it

---

### User Story 7 - System Shorthands (Priority: P7)

As a multi-system player, I want to use shorthand expressions like "FUDGE", "BOON", "BANE", "FLUX", "GOODFLUX", and "BADFLUX" so that I can quickly roll common patterns from different game systems.

**Why this priority**: Shorthands improve usability for players who frequently use specific mechanics from Traveller, Fate, and other systems.

**Independent Test**: Can be tested by rolling "FUDGE" and verifying it expands to "4dF".

**Acceptance Scenarios**:

1. **Given** a user enters "FUDGE", **When** the roll is executed, **Then** it rolls 4dF
2. **Given** a user enters "BOON", **When** the roll is executed, **Then** it rolls 3d6kh2 (Traveller advantage)
3. **Given** a user enters "FLUX", **When** the roll is executed, **Then** it rolls 1d6 - 1d6
4. **Given** a user enters "GOODFLUX", **When** the roll is executed, **Then** it rolls 2d6 and returns highest minus lowest (always ≥ 0)
5. **Given** a user enters "BADFLUX", **When** the roll is executed, **Then** it rolls 2d6 and returns lowest minus highest (always ≤ 0)

---

### User Story 8 - Named Modifiers (Priority: P8)

As a player, I want to apply named modifiers like "Strength", "Proficiency", or "Bless" so that I can track what bonuses are being applied to my rolls.

**Why this priority**: Named modifiers provide clarity and documentation for complex rolls with multiple bonuses, improving the user experience.

**Independent Test**: Can be tested by rolling "1d20" with modifiers={"Strength": 3, "Proficiency": 2} and verifying both are applied and labeled.

**Acceptance Scenarios**:

1. **Given** a user rolls "1d20" with modifiers {"Strength": 3}, **When** the roll is executed, **Then** the result shows "+ 3 (Strength)"
2. **Given** a user rolls "1d20" with modifiers {"Bless": "1d4"}, **When** the roll is executed, **Then** a d4 is rolled and labeled as "Bless"
3. **Given** a user rolls with a seeded `rng` and modifiers containing dice expressions, **When** the same `rng` seed is replayed, **Then** the total result and all modifier rolls are identical

---

### Edge Cases

- **Zero dice**: Rolling "0d6" returns 0
- **Negative dice**: Rolling "-1d6" returns a negative result
- **Division by zero**: Expression "1d6 / 0" raises DivisionByZeroError
- **Infinite reroll conditions**: Expression "1d6r<=6" raises InfiniteConditionError (would reroll forever)
- **Impossible explode conditions**: Expression "1d6e<=0" raises InfiniteConditionError (would explode forever)
- **Unicode operators**: Expressions with ×, ÷, − work correctly
- **Fullwidth characters**: Fullwidth digits and operators are normalized
- **Complex precedence**: "(2d6 + 3) × 2" evaluates correctly with parentheses

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse dice expressions in format NdM where N is number of dice and M is sides (or F for Fudge, % for percentile)
- **FR-002**: System MUST support standard polyhedral dice: d4, d6, d8, d10, d12, d20, d100
- **FR-003**: System MUST support mathematical operations: +, -, ×, ÷ with proper PEMDAS precedence
- **FR-004**: System MUST support keep highest (kh) and keep lowest (kl) operations
- **FR-005**: System MUST support drop highest (dh) and drop lowest (dl) operations
- **FR-006**: System MUST chain multiple keep/drop operations sequentially
- **FR-007**: System MUST support unlimited rerolls with comparison conditions (r<=, r>=, r<, r>, r=)
- **FR-008**: System MUST support limited rerolls (r1, r2, r3 for number of rerolls allowed)
- **FR-009**: System MUST support exploding dice on maximum (e) and custom thresholds (e>=, e<=, e=)
- **FR-010**: System MUST support Fudge dice (dF) with results -, B, + mapping to -1, 0, +1
- **FR-011**: System MUST support system shorthands: FUDGE, BOON, BANE, FLUX, GOODFLUX, BADFLUX, PERC, PERCENTILE
- **FR-012**: System MUST accept named modifiers as dictionary with string keys and int or dice expression values
- **FR-013**: System MUST return structured results including total, individual rolls, all rolls (including rerolls/explosions), and human-readable description
- **FR-014**: System MUST provide CLI tool for rolling dice expressions from command line
- **FR-015**: System MUST support JSON output format for CLI tool
- **FR-016**: System MUST support debug logging with customizable logger injection
- **FR-017**: System MUST be thread-safe for concurrent use
- **FR-018**: System MUST raise ParseError for invalid syntax
- **FR-019**: System MUST raise DivisionByZeroError for division by zero
- **FR-020**: System MUST raise InfiniteConditionError for impossible reroll/explode conditions
- **FR-021**: System MUST support Unicode operators (×, ÷, −) and fullwidth character normalization
- **FR-022**: System MUST support zero dice (0d6 returns 0) and negative dice (-1d6 returns negative result)
- **FR-023**: `Dice.roll()` MUST accept an optional `rng=None` parameter; when supplied, the provided object's `random()` method is used as the source of randomness for all dice in that call
- **FR-024**: The `rng` parameter MUST accept any object with a `random()` method returning a float in [0.0, 1.0) — no base class or formal interface required (duck-typed)
- **FR-025**: When `rng=None`, system MUST fall back to standard library random behavior — all existing callers with no `rng` argument MUST be unaffected
- **FR-026**: The top-level `roll()` convenience function MUST expose the same `rng=` parameter as `Dice.roll()`
- **FR-027**: When `rng` is supplied, it MUST be propagated to all dice rolls within that call, including dice expressions inside named modifiers, such that the entire `Dice.roll()` invocation is reproducible from a single seeded `rng` instance

### Key Entities

- **Dice**: Main entry point class providing static roll() method
- **RollResult**: Represents result of a single dice expression with rolls, kept dice, all_rolls, and total
- **RollResultSet**: Collection of RollResult objects with modifiers, providing subtotal and total
- **RollModifier**: Modifier that can be static integer or dice expression
- **ExpressionLexer**: Tokenizes dice expressions into tokens
- **ExpressionParser**: Parses tokens into evaluation tree with precedence rules
- **ExpressionToken**: Represents a single token (dice, number, operator, etc.)
- **DebugLogger**: Provides structured debug logging infrastructure
- **StringLogger**: In-memory logger for testing and API capture
- **RNG Protocol**: Any object implementing `random() -> float` in [0.0, 1.0); used to inject seeded, deterministic, or mock randomness per call

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can roll any standard dice expression and receive correct result within 1ms for simple rolls
- **SC-002**: System supports 100% of dice mechanics from D&D 5e, Savage Worlds, Fate Core, and Traveller as documented
- **SC-003**: All public APIs have comprehensive test coverage with passing tests
- **SC-004**: CLI tool starts and executes simple rolls in under 100ms
- **SC-005**: Debug logging provides step-by-step trace of parsing and evaluation when enabled
- **SC-006**: System handles 1000+ concurrent rolls without thread safety issues
- **SC-007**: Error messages clearly indicate the problem and how to fix invalid expressions
- **SC-008**: Library has zero external dependencies for core functionality
- **SC-009**: Given a seeded `rng`, repeated calls to `Dice.roll()` with identical expressions and modifiers produce identical results, including all modifier dice

## Assumptions

- Users have Python 3.8+ available
- Users are familiar with standard dice notation (NdM format)
- Core library remains dependency-free; visualization tools may have optional dependencies (matplotlib)
- Thread safety is achieved through avoiding global mutable state during rolling
- Debug logging follows Python's standard logging interface for compatibility
- CLI tools are optional utilities, not core library functionality
- Package is experimental and in active development (v0.0.2)
- Users understand that vibe coding approach means rapid iteration with strong test coverage
- RNG injection uses duck typing: any object with a `random()` method returning a float in [0.0, 1.0) is a valid `rng` argument; no formal interface, base class, or registration is required
