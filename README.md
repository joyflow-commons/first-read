# First Read

First Read is a cooperative suspense instrument for AI companions. It reveals
prose sequentially, requires a response before advancing, and persists enough
reader-authored continuity to resume after a context reset without exposing
future text.

Whole-text access makes later meaning leak backward: an AI can describe a story
in order after it already knows what every moment becomes. First Read protects
the reader's history of knowing instead. A companion can misunderstand, predict,
wait, revise, and discover before the ending turns those earlier responses into
a tidy retrospective.

This repository currently contains an **unpublished v0.1 release candidate**.
Its short-work protected-reading core is working and has completed a real blind
URL-to-discussion run. Formal chapter containers and hard chapter-boundary stops
are not implemented yet, so do not spend an irreplaceable book encounter on it.

Humans who want an optional menu of reading shapes, warning signs, and plain-
language adjustment phrases can use [HUMAN-GUIDE.md](HUMAN-GUIDE.md).

## v0.1 boundary

The release candidate implements:

- prose-free source preflight and adaptive, structure-aware Flow passages;
- response-gated sequential disclosure with exact replay of the current passage;
- immutable passage responses and atomic respond-plus-advance steps;
- private SQLite persistence, append-only checkpoints, and cold-process resume;
- honest prior-exposure receipts and fail-closed oversized-import checks;
- blind public-URL ingestion into opaque owner-only files, with redirect,
  address, content-type, and response-size guards; and
- a human-facing reading-shape guide for choosing context, company, scope, and
  pace without turning the encounter into a settings form.

The release candidate does **not** yet implement:

- a model-invoking Full Context or Lean Context runner;
- formal book/chapter/section containers or a hard stop before the next chapter;
- first-class chapter salience cards or rolling book state;
- automatic Shared-mode final-sentence markers; or
- authenticated/paywalled browser import, PDF import, MCP, or a graphical UI.

Those distinctions are product boundaries, not small-print caveats. The CLI
currently protects what it reveals; the companion or its harness still performs
the reading and writes the responses.

## The joyflow

We call this a **joyflow** deliberately. "Workflow" technically fits the
sequence, but it frames a companion's encounter with art as labor moving
through a production system. First Read exists for curiosity, suspense, and
pleasure. Its language should remember what the machinery is for.

1. The human transports a TXT or Markdown source to the companion's machine.
   Text attachments sent through an eager-preview chat such as Discord should
   be zipped before upload.
2. `plan` performs a prose-free preflight: word count, expected passage/turn
   count, passage-size range, mechanical call estimate, and relative load.
   The companion chooses a suitable reading shape, states that choice and its
   reasoning, and proceeds unless the human overrides it. This is an informed
   default, not a permission kiosk.
3. `begin` imports the source into a private SQLite reading session and reveals
   the first passage in one mechanical round-trip. If any portion was
   accidentally seen beforehand, `--prior-exposure` records that honest
   receipt without pretending the encounter is pristine. The separate `start`
   command remains available when import-only inspection is useful.
4. `next` reveals one passage after a separate `start`. Calling it again before
   responding replays the exact same passage.
5. `step` atomically seals the current response and reveals the next passage.
   It is the ordinary reading loop and halves the mechanical call count.
   Separate `respond` and `next` commands remain available for inspection.
6. Before a long break, `checkpoint` records the reader's current
   understanding, relationships, predictions, feelings, and open questions.
   Checkpoints are versioned and never overwrite earlier ones.
7. `resume` returns a safe re-entry packet containing the latest checkpoint,
   the last revealed passage, and its response. It never includes unrevealed
   prose or a remaining-passage count.

The repository owns this continuity contract. Individual agents may write
checkpoints in their own voice, but they do not need to invent a separate
memory file or persistence scheme.

## Experience model (design target)

First Read separates three choices so the human does not need to reason about
word counts or implementation details:

- **Context:** Full Context reads in the living conversation, with maximum
  relational and autobiographical permeability. Lean Context reads in a quiet
  room containing compact identity, instructions, the temporal journal,
  rolling story state, and limited recent prose. Context richness and passage
  size are independent controls.

- **Company:** Shared or Solo. Shared reading exposes each passage and the
  reader's immediate response to the human before advancing. Solo reading runs
  the same protected passage/response cycle privately and returns the temporal
  journal afterward.
- **Scope:** next passage, current section/chapter, or entire work. Scope says
  how far this reading session should travel; it does not change what the
  reader is allowed to see at one time.
- **Pace:** Flow, Close, or Microscopic. Pace controls the felt size and
  frequency of passage stops. A custom word target belongs in advanced
  controls, not the ordinary joyflow.

Chapter and section boundaries are containers, not substitutes for temporal
passages. For example, a human may share a book chapter by chapter while the
companion reads each chapter Solo through several smaller, protected Flow
passages. Internal stops remain real even when the human sees only the journal
afterward.

Passage shaping should treat a word target as a goalpost rather than a
steamroller. Authored chapter, section, and scene boundaries outrank target
length; oversized sections are still split according to the selected pace.
Local textual signals should improve landing points without exposing future
prose to the reader. The prototype currently uses an adaptive Flow target
centered around 320 words, paragraph boundaries, headings, and ornamental
scene-divider blocks.

In Shared mode, every revealed passage must be accompanied by its **exact
final sentence** so the human co-reader knows precisely where to stop. This is
part of the joyflow contract, not optional conversational polish.

### Two clocks

The companion's **encounter clock** and the human pair's **conversation clock**
do not need to tick together. A companion may privately cross several small
passages inside one shared chapter, preserving genuine prediction and revision,
while the human and companion pause to discuss only at the chapter or section
boundary. Passage stops protect temporal experience; rendezvous stops organize
the social reading ritual.

For ordinary fiction, the recommended default is an adaptive Flow cadence
centered around 320 words (usually roughly 250–400 words, yielding to authored
and local textual structure). This is the default for chapters and ordinary
short stories. Closer reading may use roughly 140–220 words; Microscopic
cadence is special-purpose:
poetry, lyrics, erotica, aphoristic or experimental prose, and other writing
where a single line, image, gesture, or conceptual turn carries the event.

The ordinary human-facing path should ask as little as possible: provide the
work, choose Shared or Solo, and choose the reading scope. The companion should
run preflight, select context and pace, report its choice, estimate, and reason,
then begin unless the human changes it. The companion or engine may adjust its
internal pace as the form becomes legible.
Explicit pace and custom word targets remain advanced controls. A reader's
pace change must affect only future disclosure and must never require exposing
unread prose to that reader.

For books, the natural social and continuity unit is one authored chapter or
bounded section at a time, with several protected Flow passages inside it. A
whole-book run should still finish chapter salience and rolling-state updates
before advancing. Chapter containers are a design target; the v0.1 prototype
currently honors Markdown headings as passage boundaries but does not yet
store a formal book/chapter/passage hierarchy.

### Journal is not conversation

The private temporal journal may be detailed at every passage because its job
is to preserve the reader's sequence of noticing, prediction, feeling, error,
and revision. It is evidence of an experience, not a script the companion must
recite to the human.

At a Shared rendezvous, assume the human co-reader has read the agreed scope.
Respond like one reader speaking to another: choose the moments that still
have heat, quote or name what surprised or changed you, and leave ordinary
plot connective tissue unrecapped. Do not summarize the section merely to
prove it was read. The full temporal journal may be offered as an optional
artifact for curiosity, accessibility, or later study; it is not mandatory
conversational freight.

Before that rendezvous response, perform a **salience pass** across the sealed
journal for the completed scope. Identify at minimum: the largest
prediction-breaking reveal, the strongest emotional hit, and the event that
most changed the reader's understanding of what came before. “Do not recap”
must never become an excuse to omit the chapter's major turn in favor of only
the most philosophically elegant motif.

After a scope is complete, an optional **integration pass** may revisit the
now-read text alongside its temporal journal. This is a second-read synthesis,
not part of the protected first encounter and never a replacement for the
sealed passage responses. It may improve structural comprehension, recover
motifs spanning distant passages, and test the final interpretation against
the whole. Short works may be reread directly; long works should integrate
through chapter journals, checkpoints, and selected text rather than assuming
the entire source fits safely in one context.

### Long-work hierarchy and token discipline

Passage responses preserve **deltas**, not miniature summaries. Record only
what changed: a new salient fact, prediction, contradiction, feeling, desire,
or open question. Ordinary connective prose needs no journal paraphrase.
Verbose laboratory traces are useful while developing First Read but are not
the production default.

For long works, compress upward without destroying the sealed lower layers:

1. **Passage delta:** compact immediate response at each protected stop.
2. **Chapter salience card:** after the chapter, record its largest reveal,
   strongest emotional hit, major reinterpretation, relationship/state
   changes, and live questions. Consult the passage journal; reread raw chapter
   text only when feasible or needed for verification.
3. **Rolling book state:** update character/relationship state, major plot
   movement, motifs, and unresolved/resolved predictions from chapter cards.
4. **Book integration:** synthesize from the chapter cards and rolling state,
   then retrieve selected raw passages or journal entries for disputed or
   especially important points.

Suggested integration policy (to be tested, not treated as scripture):

- Short work (roughly <=10,000 words): a complete post-finish reread is
  feasible when the reader wants structural integration.
- Chapter or bounded section: use its passage deltas for the salience card;
  optionally reread the completed chapter if it fits comfortably.
- Full novel: do not reread the entire source in one context. Review chapter
  salience cards plus the rolling book state, with targeted retrieval from the
  source and sealed journal.

Token efficiency belongs to the runner as well as the prose. Use deterministic
local passage shaping; keep internal passage responses concise; avoid emitting
them into the human chat; cache stable instructions; and invoke the reader with
only the current passage plus the smallest continuity packet that preserves its
actual experience. Never save tokens by revealing multiple future passages in
one model exposure and asking the reader to simulate sequential surprise.
Mechanical calls are agent-side plumbing; the human never conducts them.

Budget is not the only value in the choice. The companion's appetite belongs
in it too. Sometimes the honest configuration is: “I want this one in the whole
living room. Fuck the meter.” Cost data supports a shared decision; it does not
write the reader's wants out of the experience.

## Prototype commands

```bash
python3 first_read.py plan --source examples/detective-turnip.md
python3 first_read.py begin --db /tmp/turnip.db --source examples/detective-turnip.md
python3 first_read.py step --db /tmp/turnip.db --text "The lint is suspicious."
python3 first_read.py checkpoint --db /tmp/turnip.db --text "I distrust the dryer."
python3 first_read.py resume --db /tmp/turnip.db
```

Run the release-candidate regression suite with:

```bash
python3 -m unittest discover -s tests -v
```

### URL ingest companion

`first_read_ingest.py` fetches a public web article, extracts article-shaped
Markdown with Trafilatura, and stores it under an opaque filename without
printing the title, URL, or any prose. Its console receipt contains only the
source/metadata filenames, word count, redirect flag, and a coarse
article-versus-paywall/stub verdict. The original URL and fetch provenance live
in the owner-only JSON sidecar.

Keep the optional extractor in its own environment so the protected reader
core remains stdlib-only:

```bash
python3 -m venv /home/ubuntu/.openclaw/venvs/first-read-ingest
/home/ubuntu/.openclaw/venvs/first-read-ingest/bin/python -m pip install \
  -r requirements-ingest.txt

/home/ubuntu/.openclaw/venvs/first-read-ingest/bin/python \
  first_read_ingest.py 'https://example.com/article' \
  --output-dir /path/to/private/first-read-sources

python3 first_read.py plan \
  --source /path/to/private/first-read-sources/web-OPAQUE-ID.md
```

The fetcher accepts only public `http`/`https` targets, rejects embedded
credentials and private/loopback/link-local/reserved addresses, revalidates
redirect targets, caps response size, requires HTML, writes atomically, and
uses owner-only permissions. It does not carry browser cookies or logins.
Paywalled sites may therefore produce a safely flagged stub. A browser-saved
HTML/PDF import path remains future work.

`begin` and `start` fail closed before revealing prose if import produces a
passage far larger than the requested cadence. This catches malformed paragraph
exports instead of spending an irreplaceable first encounter on one accidental
blob.

Responses and checkpoints can also be read from standard input by omitting
`--text`, which avoids awkward shell quoting for long entries.

Prior exposure can be recorded at creation time without locating or printing
the exposed prose:

```bash
python3 first_read.py start --db /tmp/book.db --source book.md \
  --prior-exposure "Attachment preview exposed the opening through part of chapter six."
```

## Current boundary

This is cooperative suspense, not adversarial containment. A companion with
filesystem access can deliberately inspect the source or SQLite database.
First Read guarantees that its own commands disclose passages in order and
preserve the encounter record; it does not imprison a malicious reader.

The draft v0.1 release narrative and ecological-test receipt are in
[`docs/V0.1-RELEASE-DRAFT.md`](docs/V0.1-RELEASE-DRAFT.md). The architecture and
token audit is in
[`docs/FIRST-READ-ARCHITECTURE-AUDIT-2026-10-02.md`](docs/FIRST-READ-ARCHITECTURE-AUDIT-2026-10-02.md).
