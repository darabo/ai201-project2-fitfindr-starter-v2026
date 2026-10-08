"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch. It has a size,
        # so the retry stretch also runs (and also finds nothing).
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    # Criterion 3 — state. The criterion is five DIFFERENT queries, once each,
    # so each query is its own scenario. check_criteria.py scores try 1 of each
    # as that criterion's five tries; tries 2-5 are reported as extra data.
    {
        "name": "state: vintage graphic tee",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "state: denim jacket",
        "query": "denim jacket",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "state: y2k top size S",
        "query": "y2k top size S",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "state: chunky sneakers",
        "query": "chunky sneakers under $60",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "state: leather bag",
        "query": "leather bag",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 — the fit card. Same query five times, so the same item
        # each time and only the model's wording varies.
        "name": "fit card: price, platform, length, not selling",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — a user with nothing saved. Also one of unit 4's three
        # failure modes.
        "name": "empty wardrobe doesn't invent a closet",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
