# Service desk gap finder

Demo page: https://pranavgudise.dev/service-desk-gap-finder/ (the topic board, the gap list, and every topic's last 50 drafts, no cloning needed)

A support desk's knowledge base and its resolved tickets often disagree. The step that actually closes a ticket can sit in the resolution notes, and often only in the outside support provider's notes, while the article is missing it, still lists a step nobody uses, or does not exist. An AI agent that drafts answers from those articles will be wrong in exactly those places.

This tool does the two things a first pilot on a desk like that needs:

1. **Find the gaps (week 1).** It reads 6,000 resolved tickets next to the knowledge base and, topic by topic, lists the steps the article is missing, the steps it should drop, and the one-off steps that should stay an escalation path rather than become the default answer. It also says whether each missing step is written down by both teams or mostly by the provider.
2. **Gate automation (weeks 2 to 4).** It drafts an answer for every pilot ticket from the articles, has a simulated analyst approve or edit each draft, and lets a topic answer on its own only once at least 48 of its last 50 drafts were approved with no edits. Point-of-sale outages, payments and security incidents always go to a person.

It runs the pilot twice, once with the articles as they are and once after the desk lead approves every suggested update, so you can see what the knowledge work alone changes.

## Results on the sample desk

| | Articles as they are | After approved updates |
|---|---|---|
| Drafted topics with an accurate article | 7 of 13 | 13 of 13 |
| Topics that clear the 48 of 50 gate | 3 | 6 |
| Share of all tickets on cleared topics | 11.9% | 31.5% |

The gap finder suggested 9 updates across 6 topics (8 steps to add, 1 to remove, one of them a whole new article). Three of the missing steps are written down mostly by the provider: in 100% of provider notes for their topic but in 18% to 32% of internal notes.

Seven topics still miss the gate after the updates. Six of them score 41 to 47 of 50, because some of their tickets need a one-off step (a hardware swap, a payroll correction, a circuit ticket with the network provider) that the default answer should not promise. The seventh, Laptop running slow at 32 of 50, has too many different causes for one article. All seven stay with an analyst, which is the gate doing its job.

These numbers come from made-up data and describe the mechanics, not a forecast for any real desk.

## Run it

```
python3 run.py                 # generate the sample desk, find gaps, run the pilot both ways
python3 -m unittest            # 9 tests
python3 scripts/build_demo.py  # rebuild docs/index.html from the results
```

Python 3.9 or later, standard library only. Results go to `reports/results.json` and `reports/report.md`.

## What is in it

| Path | What it is |
|---|---|
| `data/scenario.json` | The made-up desk: 16 topics with the steps that really close each one, what the current article says, how often a ticket needs a one-off step, and each topic's share of volume. About 30% of tickets are one-off issues outside the named topics. |
| `gapfinder/data.py` | Generates 6,000 resolved tickets (60% closed by the provider) and 50 pilot tickets per drafted topic, seeded so every run is the same. |
| `gapfinder/discover.py` | Week 1: compares each topic's notes with its article and proposes the updates. |
| `gapfinder/gate.py` | Weeks 2 to 4: drafts, simulated review, the 48 of 50 gate, and the share of tickets on cleared topics. |
| `run.py` | Runs everything and writes the reports. |
| `scripts/build_demo.py` | Builds the demo page in `docs/` from the results. |

## The rules

- **Add a step** when it is not in the article but appears in at least 40% of the topic's notes.
- **Remove a step** when it is in the article but appears in fewer than 5% of the notes.
- **Answer on its own** when at least 48 of the topic's last 50 drafts were approved with no edits, and the topic is not excluded.
- A missing step **lives in provider notes** when internal analysts write it down at less than half the provider's rate.

## Limits

- Notes carry tagged steps, so the tool counts steps instead of reading free text. On a real desk, week 1 has to extract those steps from what people wrote, and that is the hard part.
- The analyst is simulated: a draft is approved only when it has exactly the steps the ticket needed. Real reviewers accept small variations and catch tone, which this does not model.
- Reopen rates are not modeled, so the gate here is draft quality only. A real pilot would also send a topic back to drafting if its reopen rate rose above its own baseline.
- The scenario plants the gaps and the tool recovers them. History, pilot tickets and the simulated reviewer all share one ground truth, so approved updates make every article accurate by construction, and which topics clear the gate follows from each topic's one-off rate (48 of 50 needs about 4% or less). The build shows the mechanics, not that they work on a real desk.
- Every number comes from invented data and settings.
