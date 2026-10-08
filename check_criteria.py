#!/usr/bin/env python3
"""
Apply criteria.md to a run_eval.py run, try by try. ← UNIT 4, MILESTONE 3

    python check_criteria.py                                   newest run in results/
    python check_criteria.py results/run_2026-10-08_1400_before.json

run_eval.py leaves PASS/FAIL blank on purpose. This fills the cells in by
applying each criterion's checks exactly as criteria.md words them, and gives
the reason for every FAIL, so each cell can be checked by hand against the
output in the matching .md file. It's a counting aid. The verdicts in the
README are still mine to make.

Writes <run>_checked.md next to the run, and prints the same thing.
"""

import json
import re
import sys
from pathlib import Path

import config

# Straight from criteria.md: short name and the target out of five.
CRITERIA = {
    1: ("A matching query completes all three tools", 4),
    2: ("An impossible query stops before the second tool", 5),
    3: ("The searched item is the item each tool receives", 5),
    4: ("Fit card has price, platform, ≤70 words, not selling", 4),
    5: ("The empty wardrobe doesn't invent a closet", 4),
}
# Criteria with a unit 4 revision in criteria.md. The revised check is the one
# scored; the original is still reported underneath so both can be compared.
REVISED = {4, 5}

# Criterion 4, check 4: original, then "Revised in unit 4".
SALE_PATTERNS = [r"\bselling\b", r"listing these"]
SALE_PATTERNS_REVISED = [
    r"\bselling\b", r"\blisting\b", r"\blisted\b", r"dropped on",
    r"my depop", r"my poshmark", r"my thredup", r"before i change my mind",
]

# Criterion 5, check 2: original, then "Revised in unit 4".
OWNERSHIP_PHRASES = ["you own", "you already", "your wardrobe", "your closet", "from your"]
OWNERSHIP_PHRASES_REVISED = [
    "already own", "already have", "you own", "in your closet",
    "in your wardrobe", "from your closet", "from your wardrobe",
]
# Criterion 5, check 3.
CRITERION_5_MAX_PRICE = 50.0


# ── one check per criterion: (session, try record) → list of failure reasons ──

def _common(record):
    if record["crashed"]:
        return [f"crashed: {record['crashed']}"]
    if record["session"] is None:
        return ["no session came back"]
    return []


def check_1(record):
    """Found: line and a non-empty Fit card: line, no stack trace."""
    problems = _common(record)
    if problems:
        return problems
    s = record["session"]
    if s.get("error"):
        problems.append(f"stopped early: {s['error']}")
    if not s.get("selected_item"):
        problems.append("no selected item, so no Found: line")
    if not (s.get("fit_card") or "").strip():
        problems.append("fit card is empty")
    return problems


def check_2(record):
    """Says no listings, names a concrete change, fit_card None, 0 model calls."""
    problems = _common(record)
    if problems:
        return problems
    s = record["session"]
    message = (s.get("error") or "").lower()
    if "no listings" not in message:
        problems.append(f"message doesn't say it found no listings: {s.get('error')!r}")
    if not any(tip in message for tip in ("raise your max price", "drop the size", "broader words")):
        problems.append("message names no concrete change")
    if s.get("fit_card") is not None:
        problems.append("fit_card is not None")
    if record["model_calls"] != 0:
        problems.append(f"{record['model_calls']} model call(s), expected 0")
    return problems


def check_3(record):
    """search_results[0], selected_item, and both tool_inputs are the same id."""
    problems = _common(record)
    if problems:
        return problems
    s = record["session"]
    results = s.get("search_results") or []
    ids = {
        "search_results[0]": results[0]["id"] if results else None,
        "selected_item": (s.get("selected_item") or {}).get("id"),
        "tool_inputs.suggest_outfit": (s.get("tool_inputs") or {}).get("suggest_outfit"),
        "tool_inputs.create_fit_card": (s.get("tool_inputs") or {}).get("create_fit_card"),
    }
    missing = [name for name, value in ids.items() if value is None]
    if missing:
        problems.append("missing: " + ", ".join(missing))
    if len({v for v in ids.values() if v is not None}) > 1:
        problems.append("ids differ: " + ", ".join(f"{k}={v}" for k, v in ids.items()))
    return problems


def _has_price(text, price):
    """`$<price>`, e.g. $19 or $19.00 for 19.0. No space after the $."""
    for match in re.finditer(r"\$(\d+(?:\.\d{1,2})?)(?!\d)", text):
        if abs(float(match.group(1)) - float(price)) < 0.005:
            return True
    return False


def _word_count(text):
    """Whitespace-separated tokens with a letter or digit in them. Hashtags
    count; an emoji standing on its own does not."""
    return sum(1 for token in text.split() if re.search(r"\w", token))


def check_4(record, revised=True):
    """Fit card: $price, platform, ≤70 words, not presented as for sale."""
    problems = _common(record)
    if problems:
        return problems
    s = record["session"]
    card = (s.get("fit_card") or "").strip()
    item = s.get("selected_item") or {}
    if not card:
        return ["no fit card"] + ([f"stopped early: {s['error']}"] if s.get("error") else [])
    if not _has_price(card, item.get("price", -1)):
        problems.append(f"price ${item.get('price')} not written as $<price>")
    if str(item.get("platform", "")).lower() not in card.lower():
        problems.append(f"platform {item.get('platform')!r} not mentioned")
    words = _word_count(card)
    if words > 70:
        problems.append(f"{words} words, over 70")
    for pattern in (SALE_PATTERNS_REVISED if revised else SALE_PATTERNS):
        match = re.search(pattern, card, re.I)
        if match:
            problems.append(f'reads as for sale: "{_sentence_around(card, match.start())}"')
    return problems


def _sentence_around(text, at):
    """The sentence containing position `at`, for quoting in a FAIL reason."""
    start = max(text.rfind(c, 0, at) for c in ".!?\n") + 1
    ends = [i for i in (text.find(c, at) for c in ".!?\n") if i != -1]
    end = min(ends) + 1 if ends else len(text)
    return " ".join(text[start:end].split())


def check_5(record, revised=True):
    """Fit card back, outfit claims nothing owned, item ≤ $50."""
    problems = _common(record)
    if problems:
        return problems
    s = record["session"]
    if not (s.get("fit_card") or "").strip():
        problems.append("no fit card" + (f" (stopped early: {s['error']})" if s.get("error") else ""))
    outfit = s.get("outfit_suggestion") or ""
    for phrase in (OWNERSHIP_PHRASES_REVISED if revised else OWNERSHIP_PHRASES):
        at = outfit.lower().find(phrase)
        if at != -1:
            problems.append(f'outfit says "{phrase}": "{_sentence_around(outfit, at)}"')
    price = (s.get("selected_item") or {}).get("price")
    if price is None:
        problems.append("no selected item")
    elif float(price) > CRITERION_5_MAX_PRICE:
        problems.append(f"item costs ${price}, over ${CRITERION_5_MAX_PRICE:g}")
    return problems


CHECKS = {1: check_1, 2: check_2, 3: check_3, 4: check_4, 5: check_5}


# ── putting the five tries together ───────────────────────────────────────────

def five_tries(run, number):
    """
    The five scored tries for one criterion, as (label, record) pairs, plus any
    extra tries that were run but aren't scored.

    Criterion 3 is five different queries, once each: try N is try 1 of the
    Nth criterion-3 scenario. Every other criterion is one scenario run five
    times.
    """
    scenarios = [sc for sc in run["scenarios"] if sc.get("criterion") == number]
    if number == 3:
        scored = [(sc["query"], sc["tries"][0]) for sc in scenarios if sc["tries"]]
        extra = [(f"{sc['query']} (try {i})", t)
                 for sc in scenarios for i, t in enumerate(sc["tries"][1:], 2)]
        return scored, extra
    if not scenarios:
        return [], []
    sc = scenarios[0]
    scored = [(f"try {i}", t) for i, t in enumerate(sc["tries"], 1)]
    extra = [(f"{other['name']} try {i}", t)
             for other in scenarios[1:] for i, t in enumerate(other["tries"], 1)]
    return scored, extra


def report(run):
    out = [
        f"# Criteria check — {run.get('label') or 'unlabelled'} run ({run.get('when')})",
        "",
        "Produced by `check_criteria.py`, applying `criteria.md` to the run's",
        "sessions. Every FAIL has its reason underneath.",
        "",
        "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
        "| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |",
    ]
    details = []
    original_rows = []
    for number, (name, target) in CRITERIA.items():
        scored, extra = five_tries(run, number)
        results = [(label, CHECKS[number](record)) for label, record in scored]
        row_name = f"{name} (revised)" if number in REVISED else name
        out.append(_table_row(number, row_name, target, results))
        if number in REVISED:
            as_written = [(label, CHECKS[number](record, revised=False))
                          for label, record in scored]
            original_rows.append(_table_row(number, f"{name} (as originally written)",
                                            target, as_written))

        details.append(f"### {number}. {row_name}")
        details.append("")
        for label, problems in results:
            status = "PASS" if not problems else "FAIL — " + "; ".join(problems)
            details.append(f"- {label}: {status}")
        if extra:
            extra_results = [(label, CHECKS[number](record)) for label, record in extra]
            extra_fails = [(label, p) for label, p in extra_results if p]
            details.append(
                f"- Extra tries, not scored: {len(extra_results) - len(extra_fails)}"
                f"/{len(extra_results)} pass"
            )
            for label, problems in extra_fails:
                details.append(f"  - {label}: FAIL — " + "; ".join(problems))
        details.append("")

    if original_rows:
        out += [
            "",
            "The revised rows are scored with the checks under **Revised in unit 4**",
            "in `criteria.md`. The same tries, scored with the original checks:",
            "",
            "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
            "| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |",
            *original_rows,
        ]

    return "\n".join(out + _whole_run_sale_check(run)
                     + ["", "## Why each try passed or failed", ""] + details)


def _table_row(number, name, target, results):
    cells = ["PASS" if not problems else "FAIL" for _, problems in results]
    passes = cells.count("PASS")
    if len(cells) < 5:
        verdict = f"INCOMPLETE ({len(cells)} tries)"
    else:
        verdict = f"{'MET' if passes >= target else 'MISSED'} ({passes}/5)"
    cells += ["—"] * (5 - len(cells))
    return f"| {number}. {name} | {target} of 5 | {' | '.join(cells[:5])} | {verdict} |"


def _whole_run_sale_check(run):
    """
    The revised criterion 4 check 4 ("not presented as for sale") applied to
    every fit card in the run, not just criterion 4's five. Not scored. It's
    the pattern the diagnosis looks at.
    """
    cards, flagged = 0, []
    for sc in run["scenarios"]:
        for i, t in enumerate(sc["tries"], 1):
            card = ((t.get("session") or {}).get("fit_card") or "").strip()
            if not card:
                continue
            cards += 1
            hits = [_sentence_around(card, m.start())
                    for p in SALE_PATTERNS_REVISED for m in [re.search(p, card, re.I)] if m]
            if hits:
                flagged.append(f"- {sc['name']}, try {i}: " + " / ".join(f'"{h}"' for h in dict.fromkeys(hits)))
    return [
        "",
        f"**Every fit card in the run, revised check 4:** {len(flagged)} of {cards} "
        "read as the poster selling the item (not scored, for the diagnosis).",
        "",
        *flagged,
    ]


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        runs = sorted(config.RESULTS_DIR.glob("run_*.json"))
        if not runs:
            print("No run_*.json in results/. Run `python run_eval.py --label before` first.",
                  file=sys.stderr)
            sys.exit(1)
        path = runs[-1]

    run = json.loads(path.read_text(encoding="utf-8"))
    text = report(run)
    out_path = path.with_name(path.stem + "_checked.md")
    out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
