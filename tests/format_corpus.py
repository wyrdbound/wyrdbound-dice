"""Characterization corpus for roll rendering.

This is the characterization corpus for roll rendering. Entries are
append-only -- never edited, never reordered, because their snapshots are the
regression contract.
"""

SEED = 42

EXPRESSIONS = [
    # basic polyhedral
    "1d20",
    "3d6",
    "1d4",
    "1d8",
    "1d12",
    "1d100",
    "0d6",
    "-1d6",
    # percentile
    "1d%",
    "PERC",
    "PERCENTILE",
    # arithmetic and precedence
    "2d6 + 3",
    "1d20 - 2",
    "1d6 x 4",
    "1d10 / 2",
    "2d6 + 1d4 x 2 - 1",
    "(2d6 + 3) x 2 + 1d4 - 1",
    "1d6 - 1d6",
    "2d6 × 2",
    "1d10 ÷ 2",
    "5 + 3",
    "10 - 2 x 3",
    # keep / drop
    "4d6kh3",
    "2d20kh1",
    "2d20kl1",
    "4d6kl3",
    "4d6dh1",
    "4d6dl1",
    "5d6kh3kl1",
    "4d6kh0",
    "4d6dl0",
    # rerolls
    "1d6r<=2",
    "1d6r1<=2",
    "1d6r3<=3",
    "1d6ro<=2",
    "4d6r<=2kh3",
    "1d20r=1",
    "1d6r<2",
    "1d8r>=7",
    # exploding
    "1d6e",
    "1d6e6",
    "1d10e>=8",
    "1d6e>=5",
    "2d6e",
    # fudge
    "1dF",
    "4dF",
    "4dF + 2",
    "FUDGE",
    # system shorthands
    "BOON",
    "BANE",
    "FLUX",
    "GOODFLUX",
    "BADFLUX",
    # combinations
    "8d6r1<=1",
    "1d8 + 3d6",
    "2d20kh1 + 8",
    "1d6e + 2",
    "4dF + 3",
    "2d6r1<=2",
    # error paths -- the snapshot stores "!ExceptionName"
    "1d6 / 0",
    "1d6r<=6",
    "1d6e<=0",
]

MODIFIER_CASES = [
    ("1d20", {"Strength": 3}),
    ("1d20", {"Strength": 3, "Proficiency": 2}),
    ("1d20", {"Bless": "1d4"}),
    ("1d20", {"Bane": "-1d4"}),
    ("1d20", {"Strength": 3, "Proficiency": 2, "Bless": "1d4"}),
    ("2d6", {"DM": 1}),
    ("4dF + 3", {"Aspect": 2}),
]
