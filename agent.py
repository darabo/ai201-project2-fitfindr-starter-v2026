"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card, _keywords
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "tool_inputs": {},           # item id each model tool actually received
        "steps": [],                 # which steps ran, in order — the run log
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_RE = re.compile(r"(?:under|below|less than|max|up to)?\s*\$\s*(\d+(?:\.\d+)?)", re.I)
_SIZE_RE = re.compile(r"\bsize\s+([A-Za-z0-9./]+)", re.I)
_FILLER_RE = re.compile(
    r"\b(i'?m|i am|looking for|looking|want|need|find me|show me|please"
    r"|something|anything|stuff|things?|items?|cheap|nice|some|any)\b",
    re.I,
)


def parse_query(query: str) -> dict:
    """
    Pull description / size / max_price out of a plain-language query with
    regex. "vintage graphic tee under $30, size M" →
    {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    text = query or ""

    max_price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        max_price = float(price_match.group(1))
        text = text[:price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[:size_match.start()] + " " + text[size_match.end():]

    text = _FILLER_RE.sub(" ", text)
    description = " ".join(re.sub(r"[,;]", " ", text).split())
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what the user could change, not just "no results"."""
    tips = []
    if parsed["max_price"] is not None:
        tips.append(f"raise your max price above ${parsed['max_price']:g}")
    if parsed["size"]:
        tips.append(f"drop the size {parsed['size']} filter")
    tips.append("use broader words (e.g. 'jacket' or 'tee' instead of a specific style)")
    return (
        f"No listings matched '{parsed['description']}'"
        + (f" in size {parsed['size']}" if parsed["size"] else "")
        + (f" under ${parsed['max_price']:g}" if parsed["max_price"] is not None else "")
        + ". Try to " + ", or ".join(tips) + "."
    )


def _too_vague_message(parsed: dict) -> str:
    """Second branch: say what was understood and ask for the missing piece."""
    understood = []
    if parsed["size"]:
        understood.append(f"size {parsed['size']}")
    if parsed["max_price"] is not None:
        understood.append(f"under ${parsed['max_price']:g}")
    got = f"I got {' and '.join(understood)}, but" if understood else "I"
    return (
        f"{got} couldn't tell what kind of item you want. Add a word or two "
        "about the item itself — e.g. 'graphic tee', 'denim jacket', or "
        "'leather bag' — and I'll search again."
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    # Step 1 — parse the query.
    count += 1
    trace.check_iterations(count)
    session["parsed"] = parse_query(session["query"])
    session["steps"].append("parse_query")

    # BRANCH 2 (stretch): nothing left to search for → ask, don't search.
    if not _keywords(session["parsed"]["description"]):
        session["error"] = _too_vague_message(session["parsed"])
        session["steps"].append("stop: query too vague")
        return session

    # Step 2 — search.
    count += 1
    trace.check_iterations(count)
    session["search_results"] = search_listings(**session["parsed"])
    session["steps"].append("search_listings")

    # THE BRANCH: nothing found → explain what to change and stop here.
    # suggest_outfit is never called with nothing.
    if not session["search_results"]:
        session["error"] = _no_results_message(session["parsed"])
        session["steps"].append("stop: no listings matched")
        return session

    # Otherwise take the best match.
    session["selected_item"] = session["search_results"][0]

    # Step 3 — outfit, read back out of the session.
    count += 1
    trace.check_iterations(count)
    session["tool_inputs"]["suggest_outfit"] = session["selected_item"]["id"]
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"]
    )
    session["steps"].append("suggest_outfit")

    # Step 4 — fit card, read back out of the session.
    count += 1
    trace.check_iterations(count)
    session["tool_inputs"]["create_fit_card"] = session["selected_item"]["id"]
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )
    session["steps"].append("create_fit_card")

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
