# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools and the planning loop are built. That last command runs the
> whole agent.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a plain-language thrifting request like `vintage graphic tee under $30, size M` and turns it into a search over 40 secondhand listings, filtering by keywords, size, and a price ceiling. It takes the best match and asks the model to style it with pieces from the user's wardrobe (or with common basics if the wardrobe is empty). Then it writes a short, postable caption — a "fit card" — that names the item, its price, and its platform. If nothing matches, it stops before any model call and tells the user which part of the request to loosen.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters `data/listings.json` by price and size, then ranks what's left by keyword overlap with the description (title hits count double) and returns the best matches.
- **Inputs:** `description` (str), `size` (str | None — None skips size filtering), `max_price` (float | None — inclusive; None skips price filtering)
- **Returns:** A `list[dict]` of at most 10 listing dicts (`config.SEARCH_RESULT_LIMIT`), best match first, ties broken by lower price. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. **Size rule:** listing sizes are split on `/`, anything in parentheses is ignored, and comparison is case-insensitive on whole tokens — so `M` matches `S/M` and `M/L`, `S` does **not** match `US 9`, `L` does **not** match `XL`, and any `One Size` listing matches every size. `W30` does not match `W30 L30` (whole token only).
- **When it has nothing:** An empty list `[]` — never `None`, never an exception. Also `[]` if the description has no usable keywords.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that pair the new item with pieces the user already owns, naming those pieces exactly as they appear in the wardrobe.
- **Inputs:** `new_item` (dict — a listing dict from `search_listings`), `wardrobe` (dict — `{"items": [...]}` where each item has `id`, `name`, `category`, `colors`, `style_tags`, `notes`)
- **Returns:** A non-empty `str` of plain-text outfit suggestions, roughly under 120 words.
- **When it has nothing:** If `wardrobe["items"]` is empty, it does not fail — it asks the model for two outfits built from common basics and returns that `str`. If the model returns blank text, it returns a one-line fallback (`"Pair the <title> with simple basics in neutral colors."`).

### `create_fit_card`

- **What it does:** Asks the model for a casual 2–4 sentence social caption about the find that mentions the item, price, and platform once each, with at most two emoji and two hashtags.
- **Inputs:** `outfit` (str — the output of `suggest_outfit`), `new_item` (dict — the same listing dict)
- **Returns:** A `str` caption of 2–4 sentences.
- **When it has nothing:** If `outfit` is empty or whitespace, it returns the string `"Can't write a fit card without an outfit suggestion — suggest_outfit returned nothing."` without calling the model.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names what to change (raise the max price, drop the size filter, or use broader words) and stop — `suggest_outfit` and `create_fit_card` are never called. Otherwise, take the first result as `session["selected_item"]`, go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**Second branch (stretch, see Stretch Features):** If the parsed description has no searchable keywords left (e.g. `size M under $30`), put a message in `session["error"]` asking what kind of item the user wants, and stop _before_ `search_listings`. Otherwise, go on to search. This is also in `agent.py::run_agent`.

**How the query is parsed:** Regex, in `agent.py::parse_query`. `$<number>` (optionally after "under"/"below"/"max") becomes `max_price`; `size <token>` becomes `size` (uppercased); filler words like "looking for" are removed and whatever is left is the `description`.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → second branch check → `search_results` → empty-search branch check → `selected_item` → `outfit_suggestion` → `fit_card`. Before each model tool runs, the id of the item it receives is written to `session["tool_inputs"]`, for example `{"suggest_outfit": "lst_033", "create_fit_card": "lst_033"}`, so criterion 3 can check that the searched item is the item each tool got. `session["steps"]` lists every step that ran, in order. On either early stop, `error` is set and `selected_item`, `outfit_suggestion`, and `fit_card` stay `None`. Each tool reads its inputs back out of the session, not from local variables.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Hey there! Grab that butterfly baby tee—at $18, it's a total steal and fits right into your Y2K collection.

Outfit one: Balance the tiny tee's pink and purple tones with your baggy straight-leg jeans and chunky white sneakers. Throw on your vintage black denim jacket for that classic contrast, and you are ready for a casual coffee run.

Outfit two: Lean into the cottagecore side of the top by pairing it with your wide-leg khaki trousers and brown leather belt. Slip into your black combat boots for a cool grunge-meets-sweet balance, and carry your black crossbody bag to finish the look. So cute and easy!

  Fit card: Found the ultimate Y2K butterfly baby tee on Depop for just $18. Obsessed with this pink and purple print for casual coffee runs or grunge-meets-sweet fits. Grab it before I change my mind and keep it! 🦋✨

#depop #y2kstyle

2 model calls this session, 506 prompt + 202 output tokens
```

**The branch — a query that matches nothing**

```
$ python app.py ask 'designer ballgown size XXS under $5'
  No listings matched 'designer ballgown' in size XXS under $5. Try to raise your max price above $5, or drop the size XXS filter, or use broader words (e.g. 'jacket' or 'tee' instead of a specific style).

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r=search_listings('graphic tee', max_price=30); print(len(r)); [print(x['id'], x['title'], x['size'], x['price'], x['platform']) for x in r]"
6
lst_006 Graphic Tee — 2003 Tour Bootleg Style L 24.0 depop
lst_002 Y2K Baby Tee — Butterfly Print S/M 18.0 depop
lst_033 Vintage Band Tee — Faded Grey L 19.0 depop
lst_017 Mesh Long-Sleeve Top — Black S/M 15.0 depop
lst_015 Vintage Graphic Hoodie — Faded Black L 26.0 depop
lst_011 Low-Rise Cargo Pants — Khaki W29 27.0 poshmark

$ python -c "from tools import search_listings; print(search_listings('ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Hey there! At thirty-eight bucks, those vintage Levi's are a total steal and will fit right into your closet. Since you already own baggy dark jeans, these medium-wash straight legs will give you a great lighter denim option. Here are two easy ways to style them:

Outfit 1 (Casual Streetwear): Pair your new vintage Levi's 501 Jeans — Medium Wash with the white ribbed tank top, black cropped zip hoodie layered on top, and chunky white sneakers. Add the black crossbody bag to finish the look.

Outfit 2 (Cozy Vintage): Wear the vintage Levi's 501 Jeans — Medium Wash with the oversized grey crewneck sweatshirt, brown leather belt, and black combat boots. Throw on the vintage black denim jacket if you need an extra layer!
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats a worn-in pair of vintage Levi's 501 jeans styled with clean white sneakers for that effortless 90s off-duty look. Snagged this medium wash pair for just $38.00 and they fit like an absolute dream. Catch me listing these over on depop soon because my closet is out of room. 👖✨ #VintageDenim #DepopFinds

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't write a fit card without an outfit suggestion — suggest_outfit returned nothing.
```

---

## How I Used AI

**Moment 1**

- _What I asked for:_ I'd written helper functions for `search_listings` (`_keywords`, `_size_tokens`, `_size_matches`) and asked Claude to help fix the bugs in `tools.py`, which wouldn't import.
- _What came back:_ It found three bugs: I'd pasted the helpers between the `def search_listings(...)` line and its docstring (an `IndentationError`), `re` was never imported, and `p.strip().upper` was missing its `()` — so every size token was a method object and no size could ever match.
- _What I changed:_ Moved the helpers above the function, added `import re`, added the `()`, and checked that `S` no longer matches `US 9` and `L` no longer matches `XL`.

**Moment 2**

- _What I asked for:_ I asked Claude for guidance for the three tools and the planning loop from my Tool Inventory spec, and then to draft criteria 3–5.
- _What came back:_ Working tools and a regex-based `parse_query`. When it got to the state criterion, it pointed out that the session only held `selected_item`, so nothing recorded what actually reached `suggest_outfit`. That made the criterion untestable. It added `session["tool_inputs"]` to record the item id each model tool receives. Its first draft of criterion 1 also said the query matched six listings; when we ran it, it matched ten.
- _What I changed:_ Reworded tools wording and criteria to be more specific and checkable, and ensured the tests would actually catch what they claimed to. Testing caught "something in size M" taking the wrong branch.

## Stretch Features

<!-- Declared here, and committed, before any of it was built. -->

**Declared: a second branch — a query too vague to search.**

- **Condition:** after parsing, the description has no searchable keywords left. For example, `under $30` or `something in size M` only gives a price or a size.
- **Path taken:** the loop stops _before_ `search_listings` is called. It puts a message in `session["error"]` asking what kind of item the user wants, and keeps whatever price or size it did understand. No tool runs and no model call is made.
- **Why it's a separate branch from the empty search:** the empty-search branch runs the search and then stops because nothing matched. This one never searches, because there's nothing to search for. Without it, `search_listings('')` returns `[]`, and the user gets told to "use broader words" for a query that had no words in it.
- **What it changes:** `agent.py::run_agent` gets a second `if`, between parsing and searching. The session gets a `steps` list so a run log shows which steps ran.

_Status: built._ It was declared in commit `8f91e6a` and built in `2564f3a`.

**What it changed:**

- `agent.py::run_agent` has a second `if`, right after `parse_query`. If `_keywords(session["parsed"]["description"])` is empty, it sets `session["error"]` from `_too_vague_message` and returns, so `search_listings` never runs.
- `agent.py::parse_query` now also strips vague filler ("something", "anything", "cheap", "stuff", "items"…). Before, "something in size M" searched for the word "something", matched nothing, and took the wrong branch.
- The session has a `steps` list recording each step that ran. The run log below is read from it.

**Run log — the second branch taken:**

```
$ python app.py ask 'something in size M under $30'

  I got size M and under $30, but couldn't tell what kind of item you want. Add a word or two about the item itself — e.g. 'graphic tee', 'denim jacket', or 'leather bag' — and I'll search again.

0 model calls this session
```

**Run log — all three paths side by side**, read from `session["steps"]`:

```
$ python -c "
from agent import run_agent
from utils.data_loader import get_example_wardrobe
for q in ['something in size M under \$30', 'designer ballgown size XXS under \$5', 'vintage graphic tee under \$30']:
    s = run_agent(q, get_example_wardrobe())
    print(repr(q)); print('  steps:      ', s['steps']); print('  tool_inputs:', s['tool_inputs']); print('  fit_card is None:', s['fit_card'] is None)"

'something in size M under $30'
  steps:       ['parse_query', 'stop: query too vague']
  tool_inputs: {}
  fit_card is None: True
'designer ballgown size XXS under $5'
  steps:       ['parse_query', 'search_listings', 'stop: no listings matched']
  tool_inputs: {}
  fit_card is None: True
'vintage graphic tee under $30'
  steps:       ['parse_query', 'search_listings', 'suggest_outfit', 'create_fit_card']
  tool_inputs: {'suggest_outfit': 'lst_033', 'create_fit_card': 'lst_033'}
  fit_card is None: False
```

The second branch stops before `search_listings`. The empty-search branch stops after it. The happy path runs all three tools.

---

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   |           |        |         |               |
| 2   |           |        |         |               |
| 3   |           |        |         |               |
| 4   |           |        |         |               |
| 5   |           |        |         |               |

**Diagnoses**

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
