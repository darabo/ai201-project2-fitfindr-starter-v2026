# Criteria check — after2 run (2026-10-07T22:13)

Produced by `check_criteria.py`, applying `criteria.md` to the run's
sessions. Every FAIL has its reason underneath.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item each tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card has price, platform, ≤70 words, not selling (revised) | 4 of 5 | PASS | PASS | FAIL | PASS | PASS | MET (4/5) |
| 5. The empty wardrobe doesn't invent a closet (revised) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The revised rows are scored with the checks under **Revised in unit 4**
in `criteria.md`. The same tries, scored with the original checks:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 4. Fit card has price, platform, ≤70 words, not selling (as originally written) | 4 of 5 | PASS | PASS | FAIL | PASS | PASS | MET (4/5) |
| 5. The empty wardrobe doesn't invent a closet (as originally written) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Every fit card in the run, revised check 4:** 1 of 40 read as the poster selling the item (not scored, for the diagnosis).

- empty wardrobe doesn't invent a closet, try 1: "Score one for my Poshmark cart because this cropped Wrangler denim jacket is finally mine for just $42!"

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
- try 2: PASS
- try 3: FAIL — price $19.0 not written as $<price>
- try 4: PASS
- try 5: PASS

### 5. The empty wardrobe doesn't invent a closet (revised)

- try 1: PASS
- try 2: PASS
- try 3: PASS
- try 4: PASS
- try 5: PASS

