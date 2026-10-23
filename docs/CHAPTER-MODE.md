# Explicit Markdown chapter mode

This is the first bounded book-engine slice: a session/work owns ordered chapter
spans, which own passages. It is opt-in; existing databases and ordinary
short-form commands retain their previous behavior. It is not automatic book
structure detection or a general EPUB/PDF importer.

## Accepted structure

Pass `--chapter-level 2` to declare that every ATX `##` heading is a chapter.
Levels 1–6 and Markdown's zero-to-three-space heading indentation are supported.
The first non-whitespace source content must be a chapter heading. Higher-level
headings, preambles, empty chapters, and fenced code are rejected before session
creation, without printing their text. Lower-level headings shape passages but
are not first-class sections. Setext headings and inferred plain-text chapters
are not detected. Choose the level from known formatting, not by reading future
chapter titles. Sources with uncertain structure need correction before use;
there is no anonymous correction UI yet.

Chapter-mode `plan` omits the filename, titles, and prose and reports anonymous
chapter counts. The selected level is an explicit caller assertion, not a
statistical confidence score. Without this flag, headings remain passage hints
and **there is no hard chapter gate**. Existing sessions are not migrated.

## Disposable rehearsal

From the repository root (choose a new database path):

```bash
python3 first_read.py plan --source examples/kettle-chapters.md --chapter-level 2 --target-words 12
python3 first_read.py begin --source examples/kettle-chapters.md --db /tmp/kettle-reading.db --chapter-level 2 --target-words 12
python3 first_read.py step --db /tmp/kettle-reading.db --text "I trust the cupboard's fashion sense."
python3 first_read.py close-chapter --db /tmp/kettle-reading.db --text "The kettle disagrees." --card "The offered colander has been rejected; the kettle wants a second opinion." --state-delta "The hat question remains open."
python3 first_read.py resume --db /tmp/kettle-reading.db
python3 first_read.py open-chapter --db /tmp/kettle-reading.db
python3 first_read.py step --db /tmp/kettle-reading.db --text "The teaspoons have spoken."
python3 first_read.py close-chapter --db /tmp/kettle-reading.db --text "Tea is a gracious concession." --card "The colander won office; the kettle accepted it." --state-delta "The dispute ends with shared tea."
```

## Hard boundary contract

- Inside a chapter, `next`, `respond`, and `step` work as before.
- At its final passage, `step` refuses **before sealing anything**. `next`
  replays an unanswered passage or reports the boundary if already answered.
- `close-chapter` requires the final passage, a response, a chapter card, and a
  book-state delta. It seals all three in one SQLite transaction, does not
  advance the cursor, and returns no future prose. A failed write rolls all
  three back. Already-sealed passage responses are preserved by omitting
  `--text`; supplying replacement text is refused.
- Cards and deltas are caller-authored, nonempty free text, not model-generated
  or validated salience fields. Include the major reveal, emotional hit,
  reinterpretation, relationship/state changes, and live questions as useful.
- A closed chapter cannot be reclosed or edited. `next` cannot cross it.
  Only `open-chapter` reveals the first passage of the next chapter.
- Closing the last chapter marks the work complete without another reveal.
- `resume` contains the last revealed passage, its response, checkpoint, and
  ordered cards/deltas of completed chapters, never unrevealed chapter titles
  or prose. It retains those artifacts after the next chapter is opened.

This preserves passage journals and chapter artifacts, but does not yet merge
deltas into a compact rolling state or perform targeted artifact retrieval.
Full work → part → chapter → section hierarchy, uncertain-boundary correction,
and book-scale context management remain roadmap work. Use synthetic works
until those remaining requirements fit the intended real book.

Tests cover cold-process re-entry, deliberate opening, early/duplicate closure,
blank artifacts, a presealed final response, forced transaction rollback,
indented headings, anonymous preflight, malformed structure, and legacy mode.
