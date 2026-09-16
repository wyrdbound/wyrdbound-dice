"""Security regression tests.

Each test here corresponds to a confirmed finding from the 2026-09-16 audit.
They are adversarial by construction: every input is something a hostile or
careless caller could supply through a bot command, a web form, or a config
file, and every assertion pins the boundary that stops it.
"""

import random
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from wyrdbound_dice import Dice, RollFormat
from wyrdbound_dice.dice import (
    MAX_DICE_COUNT,
    MAX_DIE_SIDES,
    MAX_EXPRESSION_LENGTH,
    MAX_TOTAL_DICE,
)
from wyrdbound_dice.errors import InfiniteConditionError, ParseError

REPO_ROOT = Path(__file__).resolve().parent.parent


def roll(expr, seed=42, **kw):
    return Dice.roll(expr, rng=random.Random(seed), **kw)


# --------------------------------------------------------------------------
# F1 - layout templates must not expose attribute traversal
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "layout",
    [
        "{total} {total.__class__}",
        "{total} {total.__class__.__mro__}",
        "{total} {expression.__class__.__base__.__subclasses__}",
        "{breakdown} {expression.__doc__}",
    ],
)
def test_layout_rejects_attribute_traversal(layout):
    """A layout may name a component, never reach through it."""
    with pytest.raises(ValueError):
        RollFormat(layout=layout)


@pytest.mark.parametrize(
    "layout",
    ["{total:>1000000}", "{total} {breakdown:^99999999}", "{total:{breakdown}}"],
)
def test_layout_rejects_format_specs(layout):
    """Format specs allow unbounded width, so no spec is accepted at all."""
    with pytest.raises(ValueError):
        RollFormat(layout=layout)


def test_layout_rejects_stray_braces():
    for layout in ["{total} {", "{total} }", "{total} {bogus}", "{}"]:
        with pytest.raises(ValueError):
            RollFormat(layout=layout)


def test_layout_escapes_still_work():
    fmt = RollFormat(layout="{{{total}}}")
    assert roll("1d20").format(fmt) == "{13}"


# --------------------------------------------------------------------------
# F2 - dropped_marker is a template too, and was unvalidated
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "marker",
    [
        "{value.__class__}",
        "{value.__class__.__mro__}",
        "{value:>100000000}",
        "{bogus}",
        "{}",
        "{value} {",
    ],
)
def test_dropped_marker_rejects_injection(marker):
    """Every rejection here was a render-time crash or a 100 MB allocation."""
    with pytest.raises(ValueError):
        RollFormat(dropped=RollFormat.VERBOSE.dropped, dropped_marker=marker)


def test_dropped_marker_valid_forms_still_work():
    fmt = RollFormat(dropped=RollFormat.VERBOSE.dropped, dropped_marker="[{value}]")
    assert "[1]" in roll("4d6kh3").format(fmt)


# --------------------------------------------------------------------------
# F3 - fudge_symbols indexing must not be able to IndexError at render time
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbols", [("-",), ("-", "B"), ("-", "B", "+", "?"), "-B+", ("-", "B", 3)]
)
def test_fudge_symbols_must_be_three_strings(symbols):
    with pytest.raises(ValueError):
        RollFormat(fudge_symbols=symbols)


# --------------------------------------------------------------------------
# F4 - formatting a successfully-evaluated roll never raises
# --------------------------------------------------------------------------


def test_every_preset_renders_every_corpus_shape():
    presets = [
        RollFormat.STANDARD,
        RollFormat.MINIMAL,
        RollFormat.COMPACT,
        RollFormat.VERBOSE,
    ]
    shapes = ["4d6kh3", "1d%", "4dF", "2d6 + 1d4 x 2 - 1", "0d6", "GOODFLUX"]
    for shape in shapes:
        for fmt in presets:
            assert isinstance(roll(shape).format(fmt), str)


# --------------------------------------------------------------------------
# D1/D2 - dice count and die size are bounded
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expr",
    [
        "1000000000d6",
        "1000000000000d6",
        "999999999d6kh1",
        "1" * 2000 + "d6",
        "1" * 20000 + "d6",
    ],
)
def test_oversized_dice_count_is_refused_promptly(expr):
    """Before this bound these hung the process; the cap must be cheap."""
    start = time.time()
    with pytest.raises(ParseError):
        Dice.roll(expr)
    assert time.time() - start < 1.0


@pytest.mark.parametrize("expr", ["1d6" + " + 1" * 5000, "1d6" + " " * 20000 + "kh1"])
def test_oversized_expression_is_refused_promptly(expr):
    """Long inputs cost more than linear to validate, and deep ones recursed."""
    start = time.time()
    with pytest.raises(ParseError):
        Dice.roll(expr)
    assert time.time() - start < 1.0


def test_expression_length_bound_admits_real_expressions():
    assert MAX_EXPRESSION_LENGTH >= 200
    assert Dice.roll("2d6 + 1d4 x 2 - 1").total != 0


@pytest.mark.parametrize(
    "expr",
    [
        "+".join(["9999d6"] * 143),
        "+".join(["1000d6"] * 143),
        "+".join(["9999d%"] * 143),
        "+".join(["9999d6e"] * 125),
    ],
)
def test_aggregate_dice_budget_is_enforced(expr):
    """Per-term caps leave the sum unbounded; the worst of these was 1.4M dice,
    ~10s of CPU and 650MB of peak memory for one 1000-byte input."""
    start = time.time()
    with pytest.raises(ParseError):
        Dice.roll(expr)
    assert time.time() - start < 0.5


def test_aggregate_budget_counts_expanded_shorthands():
    """The budget is counted after expansion, so FUDGE counts as the 4dF it is.

    A shorthand cannot actually breach the budget under the length cap (166
    FUDGE terms is 664 dice), so this asserts the counter's behaviour directly
    rather than through a roll that cannot exist.
    """
    from wyrdbound_dice.dice import DiceExpressionValidator

    DiceExpressionValidator.validate_total_dice("+".join(["4dF"] * 100))
    with pytest.raises(ParseError):
        DiceExpressionValidator.validate_total_dice("+".join(["9999dF"] * 3))
    assert Dice.roll("+".join(["FUDGE"] * 20)).total is not None


def test_aggregate_budget_admits_generous_real_rolls():
    assert MAX_TOTAL_DICE >= 2 * MAX_DICE_COUNT
    assert Dice.roll("+".join(["100d6"] * 100)).total >= 10000
    assert Dice.roll("8d6 + 2d6").total >= 10


# --------------------------------------------------------------------------
# D4 - a nearly-always-true explode condition bypasses the pre-flight count
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expr",
    [
        "1d1000000e>=2",
        "1d100000e>=2",
        "+".join(["1d1000000e>=2"] * 60),
        "1d1000000r>=2",
    ],
)
def test_runaway_explosion_is_stopped_by_the_runtime_budget(expr):
    """The validator only rejects conditions matching *every* face.

    ``1d1000000e>=2`` explodes on all but one face: it names one die, passes the
    pre-flight count, and rolled ~235,000 times before the runtime budget
    existed. Packed 60 deep it did not finish at all.
    """
    start = time.time()
    try:
        result = Dice.roll(expr)
    except (InfiniteConditionError, ParseError):
        pass
    else:
        # A geometric chain can terminate early by luck, so "always raises" is
        # not the invariant. "Never does unbounded work" is.
        rolled = sum(len(r.all_rolls) for r in result.results)
        assert rolled <= MAX_TOTAL_DICE + 1, rolled
    assert time.time() - start < 2.0


def test_always_true_explode_conditions_still_raise_immediately():
    for expr in ["1d6e>=1", "1d6e<=6", "1d6e>0", "9999d6e>=1"]:
        with pytest.raises(InfiniteConditionError):
            Dice.roll(expr)


def test_legitimate_exploding_dice_still_work():
    """Savage Worlds aces and ordinary rerolls must be untouched."""
    for expr in ["1d6e", "1d6e6", "1d10e>=8", "4d6r<=2kh3", "8d6r1<=1", "1d6e>=5"]:
        assert Dice.roll(expr, rng=random.Random(42)).total is not None


def test_oversized_die_size_is_refused():
    with pytest.raises(ParseError):
        Dice.roll("1d99999999999999999999")


def test_limits_admit_documented_usage():
    """The bounds must not break anything the README or tests already do."""
    assert MAX_DICE_COUNT >= 1000
    assert MAX_DIE_SIDES >= 1000000
    assert Dice.roll("1000d6").total >= 1000
    assert 1 <= Dice.roll("1d1000000").total <= 1000000


def test_error_message_names_the_limit():
    """A term over the per-term cap but under the total names the per-term cap."""
    with pytest.raises(ParseError) as excinfo:
        Dice.roll("15000d6")
    assert str(MAX_DICE_COUNT) in str(excinfo.value)

    with pytest.raises(ParseError) as excinfo:
        Dice.roll("+".join(["9999d6"] * 143))
    assert str(MAX_TOTAL_DICE) in str(excinfo.value)


# --------------------------------------------------------------------------
# G1 - the generated stats page must not execute an attacker's expression
# --------------------------------------------------------------------------


def test_graph_tool_escapes_the_expression(tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "stats.html"
    payload = "2d6<script>alert(1)</script>"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "graph.py"),
            payload,
            "-n",
            "20",
            "-o",
            str(out),
            "--no-browser",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    html = out.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_graph_tool_escapes_quotes_out_of_attributes(tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "stats.html"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "graph.py"),
            '2d6" onload="alert(1)',
            "-n",
            "20",
            "-o",
            str(out),
            "--no-browser",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    html = out.read_text(encoding="utf-8")
    assert not re.search(r'onload\s*=\s*"alert', html)
