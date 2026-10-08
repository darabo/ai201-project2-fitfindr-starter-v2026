# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**How to check:** run `python app.py ask 'vintage graphic tee under $30'`
five times with caching off (`AI201_CACHE=0`). A try passes if it prints a
`Found:` line and a non-empty `Fit card:` line, with no stack trace.

**Why this target:**
The search half is deterministic. `search_listings` is a plain keyword match
over the listings file, and this query returns ten listings under $30. The
rest of the run makes two model calls, though, and `run_agent` doesn't handle
`ModelUnavailable` yet (that comes in unit 4). One rate-limit or network error
means no fit card. I'm allowing one miss in five for that, not for the search.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**How to check:** run `python app.py ask 'designer ballgown size XXS under $5'`
five times. A try passes if the output says it found no listings and names at
least one concrete change (raise the max price, drop the size, or use broader
words), `session["fit_card"]` is `None`, and the run reports
`0 model calls this session`.

**Why this target:**
Nothing on this path is random. Parsing is regex, the search is a filter, and
the branch in `agent.py::run_agent` returns before any model call. The message
comes from a template in `_no_results_message`. If it fails even once, the
branch is broken, so anything below 5 of 5 would excuse a real bug.

---

## 3. Something about state

For five different matching queries (`vintage graphic tee under $30`,
`denim jacket`, `y2k top size S`, `chunky sneakers under $60`,
`leather bag`), call `run_agent(query, get_example_wardrobe())` once each.
A try passes when the three values below are the same listing `id`:

- `session["search_results"][0]["id"]`
- `session["selected_item"]["id"]`
- `session["tool_inputs"]["suggest_outfit"]` and `session["tool_inputs"]["create_fit_card"]`

The target is 5 of 5 queries.

**Why this target:**
`run_agent` puts every result into the session and passes the next tool's
inputs back out of it, and `tool_inputs` records which item id each model tool
actually got. None of that involves the model, so the ids either line up every
time or the state handling is wrong. I used five different queries rather than
one query five times. The same query would land on the same item every time,
so it couldn't catch the wrong item being carried forward.
---

## 4. Something about the fit card

Run `python app.py ask 'vintage graphic tee under $30'` five times with
caching off. A fit card passes if it meets all four of these:

1. It contains the selected item's price as `$<price>` (for example `$19` or
   `$19.00`).
2. It contains the platform name, ignoring case (for example `depop`).
3. It is 70 words or fewer, counting hashtags.
4. It doesn't present the item as being for sale by the poster. The words
   "selling" and "listing these" don't appear.

The target is at least 4 of 5 fit cards.

**Why this target:**
`create_fit_card` runs at `TEMPERATURE = 0.9`. The prompt asks for the price
and platform once each, but the model decides how to write them. I've already
seen `$38` in one card and `$38.00` in another. One card for the Levi's said
"catch me listing these over on depop soon", which reads like the poster is
selling the jeans, and that's what check 4 is for. Because the wording is
random, 5 of 5 would be a target I can't control. Letting more than one card
in five miss would mean the caption tool can't be trusted.

> **Revised in unit 4:** Check 4 becomes: it doesn't present the item as being
> for sale by the poster. None of these appear, ignoring case: "selling",
> "listing", "listed", "dropped on", "my depop", "my poshmark", "my thredup",
> "before I change my mind". Checks 1–3 and the target (at least 4 of 5) are
> unchanged.
>
> **Why revised:** check 4 measured two phrasings, not the thing it was for.
> In the before run, 7 of 40 fit cards presented the item as the poster's to
> sell and still passed: "I just dropped on depop for $19", "I just listed on
> Poshmark", "It's listed over on my Poshmark", "Grab it before I change my
> mind and keep it for myself". Each of those is what check 4 was written to
> catch ("reads like the poster is selling"), and none of them uses the words
> "selling" or "listing these". The new list is made of the phrasings that
> actually showed up. The revision makes the check stricter, not looser.
---

## 5. The empty wardrobe doesn't invent a closet

Run `python app.py ask --empty-wardrobe 'denim jacket under $50'` five
times with caching off. A try passes when all three of these hold:

1. A fit card comes back.
2. The `Outfit:` text doesn't claim the user already owns anything. None of
   these phrases appear, ignoring case: "you own", "you already", "your
   wardrobe", "your closet", "from your".
3. The item in `Found:` costs $50 or less.

The target is at least 4 of 5 tries.

**Why this target:**
With an empty wardrobe, `suggest_outfit` switches to a prompt that says the
user "haven't told you what else they own". When I tested it on the Levi's
501s, the model still ended with "Both looks use pieces you probably already
own." So this slip really happens, and it's a model wording problem, not a
code bug. That's why I'm allowing one miss and not targeting 5 of 5. The price
part is deterministic. If an item over $50 shows up even once, the parser or
the filter is broken.

> **Revised in unit 4:** Check 2 becomes: the `Outfit:` text doesn't claim or
> assume the user already owns anything. None of these phrases appear,
> ignoring case: "already own", "already have", "you own", "in your closet",
> "in your wardrobe", "from your closet", "from your wardrobe". Checks 1 and 3
> and the target (at least 4 of 5) are unchanged.
>
> **Why revised:** the phrase list missed the exact slip this criterion was
> written for. The reason above quotes it: "pieces you probably already own".
> The banned phrase was "you already", and the model puts a word in between
> ("you probably already own", "you likely already own"), so 3 of the 5
> before-run outfits made that claim and still passed. The list also failed
> the other way. In a smoke run, "Since I don't know your closet yet" matched
> "your closet" and failed a try that claimed nothing. The new list catches
> "already own/have" whatever comes before it, and only flags "closet" and
> "wardrobe" when they're used to mean the user's existing clothes ("in your…",
> "from your…").
---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
