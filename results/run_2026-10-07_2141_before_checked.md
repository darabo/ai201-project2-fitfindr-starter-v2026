# Criteria check — before run (2026-10-07T21:41)

Produced by `check_criteria.py`, applying `criteria.md` to the run's
sessions. Every FAIL has its reason underneath.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item each tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has price, platform, ≤70 words, not selling (revised) | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 5. The empty wardrobe doesn't invent a closet (revised) | 4 of 5 | FAIL | FAIL | PASS | PASS | FAIL | MISSED (2/5) |

The revised rows are scored with the checks under **Revised in unit 4**
in `criteria.md`. The same tries, scored with the original checks:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 4. Fit card has price, platform, ≤70 words, not selling (as originally written) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The empty wardrobe doesn't invent a closet (as originally written) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Every fit card in the run, revised check 4:** 7 of 40 read as the poster selling the item (not scored, for the diagnosis).

- matching query completes, try 3: "Grab it before I change my mind and keep it for myself!"
- state: vintage graphic tee, try 3: "Grab it over on my depop before I change my mind and keep it!"
- state: vintage graphic tee, try 4: "Still obsessing over this faded grey vintage band tee I just dropped on Depop for $19." / "Go snag it before I change my mind and keep it for myself!"
- state: leather bag, try 4: "Still obsessed with this tan leather mini bag I just listed on Poshmark for $38."
- state: leather bag, try 5: "It’s listed over on my Poshmark and honestly goes with literally everything in my closet right now." / "Grab it before I change my mind and keep it!"
- fit card: price, platform, length, not selling, try 2: "Still obsessed with this faded grey vintage band tee I just dropped on depop for $19." / "Grab it before I change my mind and keep it for myself!"
- empty wardrobe doesn't invent a closet, try 4: "Still obsessed with this cropped Wrangler denim jacket I just listed on Poshmark." / "Grab it before I change my mind and keep it for myself!"

## Why each try passed or failed

### 1. A matching query completes all three tools

- try 1: PASS
- try 2: PASS
- try 3: PASS
- try 4: PASS
- try 5: PASS

### 2. An impossible query stops before the second tool

- try 1: PASS
- try 2: PASS
- try 3: PASS
- try 4: PASS
- try 5: PASS

### 3. The searched item is the item each tool receives

- vintage graphic tee under $30: PASS
- denim jacket: PASS
- y2k top size S: PASS
- chunky sneakers under $60: PASS
- leather bag: PASS
- Extra tries, not scored: 20/20 pass

### 4. Fit card has price, platform, ≤70 words, not selling (revised)

- try 1: PASS
- try 2: FAIL — reads as for sale: "Still obsessed with this faded grey vintage band tee I just dropped on depop for $19."; reads as for sale: "Grab it before I change my mind and keep it for myself!"
- try 3: PASS
- try 4: PASS
- try 5: PASS

### 5. The empty wardrobe doesn't invent a closet (revised)

- try 1: FAIL — outfit says "already own": "Since it’s cropped and vintage, here are two easy ways to style it with things you probably already own."
- try 2: FAIL — outfit says "already own": "Since it’s a cropped light wash, here are two easy, everyday outfits using basics you likely already own:"
- try 3: PASS
- try 4: PASS
- try 5: FAIL — outfit says "already own": "Both are super easy to pull off with basics you probably already own!"

