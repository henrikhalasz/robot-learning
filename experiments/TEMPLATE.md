# NN: <the question, as a short statement>

Copy this to `experiments/NN-short-name/README.md`. Everything above the gate is written,
approved, committed and pushed before the first run, and never edited afterwards.

## Probe card

For a probe, this section is the whole of the top half.

- **Question:** what are we trying to decide?
- **Prediction:** what we expect, with a probability, and why.
- **What each outcome changes:** if this, we do A; if not, B.
- **Go:** <date>

Probe numbers steer the work but are never quoted. To quote a number, fill in the protocol below
instead.

## Question

What does this decide, and which decision or open question is waiting on it? If no outcome would
change what we do next, don't run it.

## Prior art

Who has measured this already and what they got, with how we know it. If nobody has, give the
queries, sources and depth searched: "not found at this depth", never "unclaimed".

## Prediction

Dated, with a probability. The mechanism, not only the number.

## Method

- The one command that runs it, and the commit it runs at.
- What varies and over what range; what is held fixed.
- n per condition, and how the interval is computed. n = 1 is not a measurement.
- Controls, and the run order.

## What would falsify the prediction

The result that would change our mind. If no result could, this is not an experiment.

## Known confounds

What could produce the predicted result for the wrong reason.

---

## APPROVED BY HENRIK: <date>

---

## What was run

Exact commands, commit, machine and date. Any deviation from the method, stated as a deviation.

## Results

Numbers with intervals, generated from result files; name the script and the files.

## Was the prediction right?

Answered directly. If it was wrong, say what in the reasoning was wrong.

## What this establishes

## What this does NOT establish

Scope limits, unresolved confounds, and anything a reviewer would attack.

## Consequence

Which decision this supports, creates or overturns, and what we do next.
