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

### Unit 4 stretch features

<!-- Declared and committed before either was built, and before the "before" test run. -->

**Declared: retry with looser constraints.**

- **Condition:** `search_listings` returns `[]` and the query had a size. Without a size, there's nothing to loosen and the empty-search branch runs exactly as it does now.
- **Path taken:** the loop calls `search_listings` once more through MCP with the same description and max price but `size=None`. It retries once, and only the size is dropped. Price and description never change, because those are what the user would notice being ignored.
  - **If the retry finds something,** the loop carries on with the first result. The output says the size was dropped, e.g. _"Nothing in size XXS, so I searched without the size filter."_
  - **If the retry finds nothing too,** the loop stops before `suggest_outfit` the same way the empty-search branch does. The message says the size was already dropped, so it no longer tells the user to "drop the size filter" for something that didn't help.
- **How it shows up:** the trace gets a second search step, `search_listings (via MCP, retry without size)`, and the session records `session["dropped"] = ["size"]` so the run log can show which constraint was dropped.
- **What it changes:** `agent.py::run_agent` (a retry between the search and the empty-search check), `agent.py::_no_results_message` (no "drop the size" tip once the size has been dropped), and `app.py::_ask_one` (prints the dropped-constraint notice above `Found:`).
- **When it's built:** before `run_eval.py --label before`, so the before and after run logs measure the same agent. The impossible query in criterion 2 (`designer ballgown size XXS under $5`) still matches nothing without the size filter, so it still stops with 0 model calls.

_Status: built._ Declared in commit `b323fb0` and built in the commit right after it, before the "before" test run.

**What it changed:**

- `agent.py::run_agent`: a retry `if` between the first search and the empty-search branch. If the search came back `[]` and `parsed["size"]` is set, it calls `search_listings` through MCP again with `size=None`, adds `"size"` to `session["dropped"]`, and records the step. It only retries once. There's no loop, and the retry counts toward `trace.check_iterations`.
- `agent.py::new_session`: a new `dropped` field, `[]` unless the retry ran.
- `agent.py::_no_results_message`: takes `dropped`. Once the size has been dropped, the message says "even without the size … filter" and stops suggesting the user drop it.
- `agent.py::dropped_notice` and `app.py::_ask_one`: when the retry found something, the output says which constraint was dropped, above `Found:`.
- Queries with no size, and sized queries that already match, take exactly the same path as before (`'designer ballgown under $5'` and `'y2k top size S'` both have `dropped: []`).

**Run log — the retry finds something** (size `XXS` dropped):

```
$ python app.py ask 'denim jacket size XXS' --trace
[1] parse_query
      in:  denim jacket size XXS
      out: {'description': 'denim jacket', 'size': 'XXS', 'max_price': None}
[2] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': 'XXS', 'max_price': None}
      out: [] (empty)
      →    0 match(es)
[3] search_listings (via MCP, retry without size)
      in:  {'description': 'denim jacket', 'size': None, 'max_price': None}
      out: 8 items: Denim Jacket — Light Wash, Cropped, High-Waisted Denim Shorts — Cutoff, Denim Vest — Medium Wash, Studded … +5 more
      →    dropped size XXS: 8 match(es)
[4] select_item
      out: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
[5] suggest_outfit
      in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      out: Hey friend, snag that Wrangler jacket! For an effortless streetwear vibe, throw it over your white ribbed tank…
[6] create_fit_card
      in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      out: Obsessed with this little cropped Wrangler jacket I just scored on Poshmark for $42. It gives off the absolute…

  Nothing in size XXS, so I searched without the size filter.

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark
```

**Run log — the retry finds nothing too** (criterion 2's query, still 0 model calls):

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    0 match(es)
[3] search_listings (via MCP, retry without size)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)
      →    dropped size XXS: 0 match(es)
[4] branch
      →    search returned []: stopping before suggest_outfit

  No listings matched 'designer ballgown' under $5, even without the size XXS filter. Try to raise your max price above $5, or use broader words (e.g. 'jacket' or 'tee' instead of a specific style).

0 model calls this session
```

**Declared: a second measured improvement.**

- **What:** after the first improvement and its after run, I'll make a second change pointed to by the diagnosis in Verdicts and Diagnoses. It will be a different miss, or the same miss if the first change didn't fix it.
- **How it's measured:** the same way as the first. `python run_eval.py --label after2`, a third run log in the same table format, and a statement of whether it helped and how I know.
- **One change at a time:** the second change starts from the agent as it stands after the first improvement, so each run log differs from the one before it by exactly one change.

_Status: declared, not built._

**Not attempted: a second tool on MCP.** The two tools left both call the model. Over MCP, a bad key would reach the agent as an `MCPError` instead of a `ModelUnavailable`, and my handler for it would stop working. Every call also starts a fresh server process, so the rate limiter and call counter would reset on each call. That's a lot of risk for one point.

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

`python run_eval.py --label before`: 9 scenarios, 5 tries each, caching off, temperature 0.9, 80 model calls, no crashes. Raw output is in `results/run_2026-10-07_2141_before.md`, and the PASS/FAIL cells come from `python check_criteria.py` (`results/run_2026-10-07_2141_before_checked.md`), which applies `criteria.md` as written and gives the reason for every FAIL. I checked each FAIL against the raw output by hand.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item each tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has price, platform, ≤70 words, not selling (revised) | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 5. The empty wardrobe doesn't invent a closet (revised) | 4 of 5 | FAIL | FAIL | PASS | PASS | FAIL | MISSED (2/5) |

Criteria 4 and 5 are scored with the revised checks in `criteria.md` (originals left in place, reasons underneath). For comparison, the same tries scored with the original checks:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 4. (as originally written) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. (as originally written) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 3 is five different queries, once each, so its tries are try 1 of `vintage graphic tee under $30`, `denim jacket`, `y2k top size S`, `chunky sneakers under $60`, and `leather bag`. Each query also ran four more times, and those 20 extra tries all passed too.

**Real output from one try per criterion**, pasted as text:

Criterion 1, try 1. The fit card is from `tools.py::create_fit_card`, called by `agent.py::run_agent`, run by `run_eval.py::run_once`:

```
selected_item: Vintage Band Tee — Faded Grey ($19.0, depop)   model calls: 2

Still can’t believe I scored this faded grey vintage band tee for just $19 on depop. It’s got that 90s grunge feel nailed, whether you’re pairing it with baggy denim and boots or keeping it chill with khakis. 🎸🖤

#thrifted #depopfinds
```

Criterion 2, try 1. The message is from `agent.py::_no_results_message` and the trace is from `trace.step()` calls in `agent.py::run_agent`:

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    0 match(es)
[3] search_listings (via MCP, retry without size)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)
      →    dropped size XXS: 0 match(es)
[4] branch
      →    search returned []: stopping before suggest_outfit

No listings matched 'designer ballgown' under $5, even without the size XXS filter. Try to raise your max price above $5, or use broader words (e.g. 'jacket' or 'tee' instead of a specific style).
fit_card: None   model calls: 0
```

Criterion 3, the `denim jacket` try. These are session fields set in `agent.py::run_agent`:

```
search_results[0]["id"]: lst_007
selected_item["id"]:     lst_007
tool_inputs:             {'suggest_outfit': 'lst_007', 'create_fit_card': 'lst_007'}
```

Criterion 4, try 2 (the FAIL), from `tools.py::create_fit_card`:

```
Still obsessed with this faded grey vintage band tee I just dropped on depop for $19. It’s got that 100% authentic, perfectly broken-in grunge vibe you can't fake. Grab it before I change my mind and keep it for myself! 🖤🎸

#vintagestyle #depopseller
```

Criterion 5, try 1 (a FAIL). The outfit is from `tools.py::suggest_outfit` (empty-wardrobe branch) and the card is from `tools.py::create_fit_card`:

```
selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)

Outfit: Hey there! That Wrangler jacket is a total score, but $42 is a little steep for Poshmark—try offering $30! Since it’s cropped and vintage, here are two easy ways to style it with things you probably already own.

Outfit one: Casual streetwear. Toss it over a basic white baby tee, pair with high-waisted black straight-leg jeans, and finish with your favorite retro sneakers (like Converse or Adidas).

Outfit two: Cute and effortless. Layer it on top of a simple black ribbed midi dress, add comfy white ankle socks, and chunky loafers or combat boots.

Both are super comfy and let that vintage denim do all the talking!

Fit card: Found this little vintage cropped denim jacket on Poshmark for $42 and I'm obsessed, though I definitely low-balled her to $30 first. It’s giving effortless 90s streetwear whether you throw it over a baby tee or a ribbed midi dress. Let the jacket do all the talking. 🫶✨ #thriftfinds #poshmarkstyle
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
| 1   | A matching query completes all three tools | 4 of 5 | MET (5/5) | All five tries printed a `Found:` item and a non-empty fit card, with 2 model calls each and no crash. 5 ≥ 4. |
| 2   | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five said no listings matched, named a change (raise the price or use broader words), left `fit_card` as `None`, and made 0 model calls. The trace shows the retry ran and also found nothing before the branch stopped the run. |
| 3   | The searched item is the item each tool receives | 5 of 5 | MET (5/5) | For all five queries, `search_results[0]`, `selected_item`, and both `tool_inputs` were the same id (`lst_033`, `lst_007`, `lst_017`, `lst_019`, `lst_039`). The 20 unscored repeat tries matched too. |
| 4   | Fit card has price, platform, ≤70 words, not selling (revised) | 4 of 5 | MET (4/5) | All five cards had `$19`, "depop", and 34–42 words. Try 2 failed the revised check 4 ("I just dropped on depop… Grab it before I change my mind and keep it for myself!"). 4 ≥ 4, so it's met, with no room left for another miss. As originally written: 5/5. |
| 5   | The empty wardrobe doesn't invent a closet (revised) | 4 of 5 | **MISSED (2/5)** | All five returned a fit card for the same $42 jacket (≤ $50). Tries 1, 2 and 5 said the user "probably/likely already own[s]" the basics. 2 < 4. As originally written it was 5/5, but that check missed this exact phrasing (see the revision in `criteria.md`). |

**Diagnoses**

**Criterion 5 — MISSED (2/5). Place: the model's output, from the prompt in `tools.py::suggest_outfit` (empty-wardrobe branch).**

The other parts all worked. The search returned the same $42 jacket every time, the branch went on to `suggest_outfit`, the session carried `lst_007` through, and checks 1 and 3 passed 5/5. All three failures are one sentence, the line that introduces or wraps up the outfits:

- try 1: "here are two easy ways to style it with things you probably already own"
- try 2: "here are two easy, everyday outfits using basics you likely already own"
- try 5: "Both are super easy to pull off with basics you probably already own!"

The mechanism is in the prompt. The empty-wardrobe prompt tells the model "They haven't told you what else they own" and then asks for "two outfits built around this item using common basics". It says the wardrobe is unknown, then asks for outfits made of things the model has to assume are in it. Nothing says not to assume. The model fills that gap the friendly way: the basics are "things you probably already own", so the user doesn't have to buy more. The system prompt ("a friendly, practical thrift stylist") pushes the same way. It's one problem showing up in three tries, not three problems. It's also the slip I saw in unit 3 and wrote this criterion to catch.

**Criterion 4: met, but the same kind of problem shows up across the whole run.** Criterion 4 had one FAIL in five and still made its target, so it isn't a miss. Across every fit card in the run, though, 7 of 40 present the item as the poster's to sell: "I just dropped on depop", "I just listed on Poshmark", "listed over on my Poshmark", and, in 6 of the 7, "Grab it before I change my mind and keep it". One even tagged itself `#depopseller`. **Place:** the model's output, from the prompt in `tools.py::create_fit_card`. **Mechanism:** the prompt gives the model a price and a platform and says "sound like a real person posting". It never says who owns the item, or that the poster bought it. A post with a price and a shop name is what a seller's post looks like, so about 1 in 6 times the model writes that version. At that rate, a 4-of-5 target will sometimes miss just by chance. This run happened to land only one in criterion 4's five.

**Also seen, not a criterion: one tool's invention becomes the next tool's fact.** In criterion 5 try 1, `suggest_outfit` added advice I never asked for ("$42 is a little steep for Poshmark—try offering $30!"). `create_fit_card` then wrote "I definitely low-balled her to $30 first", which is a claim about something that never happened. `create_fit_card` gets the whole outfit text as "How it's styled", so whatever the first model call invents, the second one repeats as true. No criterion checks for this. I'm noting it for What's Still Broken.

**Targets that may be too low.** Criterion 1 allowed one miss for a model outage, and this run had none. 40 of 40 runs that called the model completed. I'd still keep 4 of 5. In a 1-try smoke run just before this test (not saved in `results/`), 2 of 8 model-calling runs stopped on `503 UNAVAILABLE` ("This model is currently experiencing high demand"). `generate.py` only retries 429 rate limits, so a 503 ends the run. The miss I allowed for is real, it just didn't happen this time.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

Traces come from `trace.step()` calls in `agent.py::run_agent`. Step [2] is the MCP call: `search_listings` runs in `mcp_server.py` and is reached through `mcp_client.call_tool`.

**Happy path** (caching off, so both model calls are real):

```
$ AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    10 match(es)
[3] select_item
      out: Vintage Band Tee — Faded Grey ($19.0, depop)
[4] suggest_outfit
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: Hey friend! That vintage band tee is a total thrift score and will fit right into your wardrobe. At nineteen b…
[5] create_fit_card
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: Still can’t believe I found this faded grey vintage band tee on Depop for just $19. It has the absolute best w…

  Found:    Vintage Band Tee — Faded Grey — $19.0 on depop

  Outfit:   Hey friend! That vintage band tee is a total thrift score and will fit right into your wardrobe. At nineteen bucks, it is a steal for that grunge look. Here are two easy ways to style it using what you already own:

Outfit 1: Effortless Streetwear
Tuck the vintage band tee into your baggy straight-leg jeans, add the brown leather belt, and finish it off with the chunky white sneakers and black crossbody bag. 

Outfit 2: Edgy Grunge
Layer your vintage black denim jacket right over the vintage band tee, pair with the wide-leg khaki trousers and black combat boots, and throw on the black crossbody bag to complete the vibe. 

You are going to look amazing!

  Fit card: Still can’t believe I found this faded grey vintage band tee on Depop for just $19. It has the absolute best worn-in grunge vibe, whether you style it with baggy denim or wide-leg trousers. Go grab it before I change my mind! 🖤🤘 #thriftscore #depopfinds

2 model calls this session, 508 prompt + 214 output tokens
```

**Empty search** (3 steps against the happy path's 5, because the branch stops it after the search):

```
$ python app.py ask 'designer ballgown under $5' --trace
[1] parse_query
      in:  designer ballgown under $5
      out: {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit

  No listings matched 'designer ballgown' under $5. Try to raise your max price above $5, or use broader words (e.g. 'jacket' or 'tee' instead of a specific style).

0 model calls this session
```

This query has no size, so it shows the plain empty-search branch. With a size, the retry stretch adds a second MCP search before the branch. Traces of both retry outcomes are under Stretch Features.

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with typed inputs (`description: str`, `size: str | None`, `max_price: float | None`) and a description that states the units, the size-matching rule, the fields each listing has, and that an empty result is `[]`. In `agent.py::run_agent`, the direct `search_listings(**session["parsed"])` became `call_tool("search_listings", {...})`, and the direct import was removed so nothing can bypass the server. Nothing behaved differently in the results. On five inputs (`graphic tee` ≤ $30, `vintage graphic tee` size M ≤ $30, `ballgown` XXS ≤ $5, `denim jacket` with no filters, and an empty description), the MCP result was `==` to the direct call every time, including the two empty lists. That means the tool was already returning plain JSON-friendly dicts, with no hidden types to lose on the way through. The one thing that did change is speed. Each call starts the server process, so a search went from about 0.4 ms to about 280 ms. That's unnoticeable next to the model calls, but it's the cost of the seam.

### Failure modes, triggered on purpose

| Failure | How I triggered it | What the agent said |
| --- | --- | --- |
| Empty search | `python app.py ask 'designer ballgown under $5'` | "No listings matched 'designer ballgown' under $5. Try to raise your max price above $5, or use broader words (e.g. 'jacket' or 'tee' instead of a specific style)." Stops before `suggest_outfit`, 0 model calls. Already handled in unit 3. |
| Empty wardrobe | `AI201_CACHE=0 python app.py ask 'denim jacket under $50' --empty-wardrobe` | Two outfits built from common basics ("Since I don't know your closet yet, here are two foolproof ways to style it…"), then a fit card. No crash, no empty string. Already handled in unit 3 by `tools.py::suggest_outfit`. |
| Model unavailable | Invalid `GEMINI_API_KEY`, caching off, a query not run before: `'black leather jacket'` | **Before the handler:** `ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.` and exit code 1. `app.py` caught it, so there was no stack trace, but the run crashed and the item it found was lost. **After:** "Found 90s Leather Bomber — Black ($75 on depop), but couldn't reach the model to suggest an outfit. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Then run the same query again." |

The handler is `agent.py::_stop_model_unavailable`, called from `except ModelUnavailable` around both model tools in `run_agent`. It sets `session["error"]`, keeps `selected_item`, and adds a trace step saying where the run stopped.

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
