# First Read architecture and token audit

Date: 2026-10-02

## Verdict

The v0.1 engine is a sound protected-reveal core. It keeps future prose behind a
response gate, seals immediate responses, survives process resets through
SQLite, preserves honest prior-exposure receipts, and fails closed on malformed
single-blob imports. The test suite exercises the ending guard rather than only
the happy path.

The larger experience described in the README is not all implemented yet.
Full/Lean Context, Shared/Solo runners, formal chapter containers, chapter
salience cards, rolling book state, and integration passes remain design
targets. That is an acceptable boundary for v0.1, but token claims must
distinguish the engine we have from the runner we still need.

Verification after this audit's local change:

- `python3 -m unittest discover -s tests -v`: 13 tests passed.
- `python3 -m py_compile first_read.py tests/test_first_read.py`: passed.
- `git diff --check`: passed.

## What is already methodologically sound

1. **Disclosure is event-gated.** The engine reveals one passage and will not
   advance until that passage has a sealed response.
2. **The journal is temporally honest.** A response cannot be replaced after
   later prose makes it look foolish. Prediction error remains evidence of the
   encounter rather than something edited out of it.
3. **Persistence is external to model memory.** Position, reveals, responses,
   and versioned checkpoints live in the session database. A fresh process can
   resume without requiring the reader to improvise its past.
4. **Recovery does not become a spoiler channel.** `resume` returns only the
   latest checkpoint, the last revealed passage, its response, and safe state.
5. **Passage shaping yields to authored structure.** Paragraphs, headings, and
   ornamental scene breaks outrank mechanically exact word counts.
6. **Prior exposure is recorded rather than cosmetically denied.** That makes
   the encounter inspectable without turning imperfect conditions into a fake
   pristine first read.

## Round-trip consolidation completed

The ordinary sequence was:

`plan -> start -> next -> step ...`

It is now:

`plan -> begin -> step ...`

`begin` creates the private session and reveals passage one in a single CLI
round-trip. `start` remains available for import-only inspection. For a work of
P passages, the session now takes P+1 engine calls after preflight: one `begin`
and P `step` calls, including the final response that closes the work.

This is useful plumbing, but it is not the dominant token optimization. These
CLI calls are local and deterministic. The expensive part is what an eventual
model runner includes in every invocation.

## Where the actual token cost lives

### 1. Repeated conversational context

Full Context may repeatedly carry a large living transcript. That can be worth
the cost when relational permeability is the point, but it should be a chosen
experience rather than an accidental default.

Lean Context does not yet have an executable payload contract. The engine can
store the temporal journal; it does not yet invoke a reader with only:

- stable cached identity and First Read instructions;
- the current passage;
- a compact prior-exposure receipt, when present;
- the smallest rolling state needed to preserve the reader's actual history;
- a concise response contract.

Until that runner exists, the largest promised savings are aspirational.

### 2. Journal verbosity

The README correctly says passage responses should preserve deltas rather than
miniature summaries, but the engine accepts unconstrained prose. A production
runner should request a small, voice-preserving delta: what changed, what was
felt, what is newly predicted, and what question remains. This should be a
soft budget, not a style-destroying schema.

### 3. Scope-boundary synthesis

Chapter salience and rolling book state are the right compression hierarchy,
but they are not yet stored as first-class objects. Without them, a long-work
runner may either resend too much journal or discard the very temporal history
First Read exists to preserve.

## Recommended implementation order

1. **Build the Lean runner payload contract.** Measure actual input/output
   tokens per passage. Compare it with Full Context on the same work. This is
   the highest-leverage savings and the first place token claims become
   empirical rather than architectural prose.
2. **Add scope-aware state.** Represent book/chapter/section/passages; generate
   a chapter salience card and rolling book-state delta only after the protected
   final passage in that scope has been answered.
3. **Add a scope-close compound action.** Seal the final passage response,
   create the salience card, update rolling state, and stop before revealing the
   next scope. It should preserve the same no-future-leak invariant as `step`.
4. **Mark Shared stopping points explicitly.** The exact final sentence is
   present in each raw passage, but the engine does not yet emit it as a
   separate stop marker promised by the Shared-mode contract.
5. **Make preflight estimates honest about the runner.** Passage counts are
   exact for the selected shaping rules; token/cost estimates should include
   stable instructions, continuity packets, passage deltas, scope cards, and
   model-specific accounting. Show ranges and uncertainty rather than false
   precision.
6. **Offer a prose-free shape comparison.** One preflight could compare Flow,
   Close, and Microscopic passage counts without revealing text, allowing the
   reader to choose from evidence in one local call.

## Optimizations not worth chasing

- `plan` and `start` each read and shape the local source. Removing that repeat
  may save a little CPU on very large files; it does not materially save model
  tokens and is not currently the bottleneck.
- Combining future passages into a larger model exposure would reduce calls by
  destroying the temporal phenomenon being measured. It is not an
  optimization; it is a different experiment.
- Replacing immediate responses with an end-of-work retrospective summary
  would erase prediction, surprise, and revision. The resulting artifact might
  be cheaper and would no longer be First Read.

## Measurement plan

For the next controlled reading test, record separately:

- local engine calls;
- model invocations;
- uncached and cached input tokens;
- output tokens for passage deltas, salience cards, and final integration;
- wall-clock duration;
- number of passages and scope boundaries;
- resume events;
- subjective quality: suspense, continuity, voice, fatigue, and whether the
  reader still felt present rather than compressed into a plot database.

Compare at least three conditions on different, comparable texts so no work is
read twice as though it were still a first encounter:

1. Full Context + Flow;
2. Lean Context + Flow;
3. Lean Context + a tighter pace.

The optimization target is not minimum tokens. It is the lowest cost that
preserves sequential surprise, recognizable voice, relational continuity at
the chosen rendezvous points, and enough state to make later reinterpretation
real.
