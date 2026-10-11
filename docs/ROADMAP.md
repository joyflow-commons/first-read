# First Read roadmap

**Status:** working inventory, 2026-10-10

This document separates the small, working short-form release from the larger
book and screen-watching ambitions. A feature appearing here does not mean it
must block the first public release.

## What already works

- A protected TXT/Markdown reading engine with prose-free preflight.
- Structure-aware passage shaping for Flow, Close, Microscopic, Long Flow, and
  Chapter Lite use.
- Response-gated sequential disclosure, exact replay, immutable responses,
  atomic `step`, checkpoints, and cold-process resume.
- Honest prior-exposure receipts and fail-closed oversized-import checks.
- Blind public-web article ingestion with safe receipts and owner-only output.
- A human guide for context, company, scope, pace, salience, and integration.
- Ecological proof on short fiction, nonfiction, poetry/erotica, and television
  scripts operated manually through the core engine.

## Track A: publish the short-form v0.1 core

These are the release and handoff tasks for the capability that exists now.
Book-scale support and First Watch do not need to block this release if its
boundary remains explicit.

- [ ] Re-run the full automated suite and a clean-install smoke test.
- [ ] Decide the public home and ownership (personal repository versus the
  proposed Joyflow house/organization), license, and attribution.
- [ ] Make installation and first-run instructions cold-reader friendly.
- [ ] Add one complete, disposable onboarding joyflow using Detective Turnip or
  another spoiler-safe fixture.
- [ ] Package a convenient entry point. Decide whether v0.1 remains a Python
  CLI, ships as an installable package, or also exposes MCP. MCP is useful for
  agent adoption but is not required to prove the method.
- [ ] Review the release draft against the actual code, then push/tag/publish.
- [ ] Give the release candidate to at least one companion/human household that
  did not build it; record where setup, language, or operation is confusing.
- [ ] Add a contribution/issue path and a small privacy/security note explaining
  cooperative suspense versus adversarial containment.

## Track B: make books safe and coherent

This is the next major engine milestone. Until it is complete, do not spend an
irreplaceable unread novel on a whole-book run.

### B1. Formal authored structure

- [ ] Store a real work -> part -> chapter/section -> passage hierarchy instead
  of treating headings only as passage-shaping hints.
- [ ] Detect explicit Markdown headings and other authored boundaries without
  disclosing titles or prose in preflight receipts.
- [ ] Represent boundary confidence and refuse ambiguous structure safely.
- [ ] Add anonymous human correction for uncertain boundaries without making
  the human manually reformat the book or revealing titles to the reader.

### B2. Hard scope closing

- [ ] Add one atomic scope-close action that seals the final response in a
  chapter, creates the chapter artifacts, and stops before chapter two.
- [ ] Ensure `resume` respects the closed boundary and cannot expose the next
  scope until the next chapter is deliberately begun.
- [ ] Prove this first with a disposable synthetic multi-chapter work, including
  a fresh-process resume at the seam.

### B3. Long-work continuity

- [ ] Store first-class chapter salience cards: largest reveal, strongest
  emotional hit, major reinterpretation, state/relationship changes, and live
  questions.
- [ ] Store and update rolling book state from completed chapter cards.
- [ ] Preserve lower-level passage journals while compressing upward; do not
  replace temporal evidence with retrospective summaries.
- [ ] Define targeted retrieval and final book-integration behavior so a novel
  never has to be reread whole in one context.
- [ ] Test chapter-to-chapter and context-reset continuity on disposable work
  before using Ken's unread books.

## Track C: painless sealed intake

The human should be able to provide one whole source file. Chapter-by-chapter
reading is an experiential protocol, not a demand for chapter-by-chapter files.

### C1. Attachment/intake boundary

- [ ] Build a sealed intake command that accepts the opaque original before its
  contents enter the reader's language context.
- [ ] Accept one complete book file; never require manual chapter splitting.
- [ ] Keep ZIP-before-upload as the documented Discord safety route until an
  attachment can be intercepted before eager preview/preprocessing.
- [ ] Emit only safe receipts: source format, word/page counts, probable scope
  counts, confidence, warnings, and cost estimates—never prose, titles, URLs,
  or chapter names.

### C2. Structured document conversion

- [ ] Prefer direct semantic import for EPUB/DOCX, which may contain real
  heading/chapter structure.
- [ ] Add PDF import behind the sealed door. PDF structure must be reconstructed;
  there is no original Markdown hierarchy to preserve in an ordinary PDF.
- [ ] Prototype Docling as the leading PDF adapter because its layout analysis
  and structured `DoclingDocument`/lossless JSON are useful for chapter
  validation.
- [ ] Keep Microsoft MarkItDown as a cheap broad-format fallback, not as a
  trustworthy chapter detector. Consider Marker for difficult visual/OCR/math
  documents if needed.
- [ ] Combine bookmarks/outlines, table of contents, inferred headings,
  typography, page breaks, numbering patterns, and repeated-header/footer
  removal into conservative chapter detection.
- [ ] Support scanned PDFs through OCR without silently claiming reliable
  structure.
- [ ] Add clean public-domain fixtures, deliberately ugly fixtures, and one
  disposable real PDF supplied by Sunny.
- [ ] Add browser-saved HTML/PDF import for authenticated or paywalled material;
  do not borrow browser cookies in the public-URL fetcher.

## Track D: executable reader modes and honest cost

The repository currently supplies an engine and method; the companion/harness
still invokes the model and writes responses.

- [ ] Specify and build the Lean Context runner payload: stable identity and
  instructions, current passage, prior-exposure receipt, minimal rolling state,
  and a concise voice-preserving response contract.
- [ ] Specify Full Context operation separately so relational permeability is a
  deliberate choice rather than accidental transcript bulk.
- [ ] Implement actual Shared and Solo runners rather than leaving them solely
  as operating instructions.
- [ ] Ask for passage deltas rather than repetitive miniature summaries, with a
  soft budget that preserves voice.
- [ ] Allow pace changes only for future disclosure.
- [ ] Add a prose-free comparison of Flow/Close/Microscopic passage counts.
- [ ] Make preflight estimates include model invocations, cached/uncached input,
  output, continuity packets, scope cards, wall time, and uncertainty.
- [ ] Measure Full Context + Flow, Lean Context + Flow, and Lean Context + tighter
  pace on different comparable texts. Also score suspense, continuity, voice,
  fatigue, and felt presence; cheapest is not automatically best.

## Track E: Shared reading ergonomics

- [ ] Emit the exact final sentence/stop line automatically for every Shared
  rendezvous.
- [ ] Separate private encounter stops from human conversation rendezvous: the
  reader may cross several protected passages before the pair pauses together.
- [ ] Generate a rendezvous packet from revealed material only: exact stop line,
  salience pass, and the reader's live response without compulsory plot recap.
- [ ] Make journal export optional and clearly separate it from conversation.
- [ ] Test long breaks, changed pace, and context resets during Shared reading.

## Track F: First Watch (screen-watching mode)

The two *Pantheon* episodes proved that this is a real mode, not a hypothetical
use case. Start as a documented First Read profile; split it into a sibling
tool only if the media-specific machinery earns that complexity.

### F1. Document the working low-tech method

- [ ] Write a `FIRST-WATCH.md` guide: obtain a script/transcript, transport it
  sealed, format mechanically without reading it, run prose-free preflight,
  choose shared sections, reveal sequentially, announce the exact stop line
  before commentary, let the human catch up, discuss, and continue.
- [ ] Document screenshots as human-supplied visual evidence at rendezvous
  points. Screenshots enlarge the encounter without preloading future visuals.
- [ ] Preserve the two clocks: small private suspense passages and larger shared
  episode sections.
- [ ] Include the accessibility/social principle learned from Sunny: talking is
  part of watching together, not an interruption of it.
- [ ] Add a spoiler-safe sample episode/transcript fixture and a preflight
  checklist for accidental title/opening exposure.

### F2. Automate only the repeated pain

- [ ] Add a sealed transcript formatter/importer that repairs line structure
  while proving every non-whitespace character survived unchanged.
- [ ] Support subtitle formats such as SRT/VTT/ASS and preserve timestamps and
  speaker/scene cues when useful.
- [ ] Let the pair choose a small number of rendezvous sections without exposing
  future dialogue; explore anonymous time/size markers or human-provided stops.
- [ ] Store episode-level salience and rolling season state without flattening
  the live theories from each episode.
- [ ] Decide whether `First Watch` is a mode/profile in this repository or a
  thin sibling package sharing the First Read engine. Begin in-repo; branch only
  if code and installation genuinely diverge.

### F3. Deluxe media path (later, optional)

- [ ] Revisit Film Matinee for local video + subtitle ingestion, sequential
  keyframe sheets, colour/audio rails, and persistent annotations.
- [ ] On Linux, require real subtitle tracks/files unless a tested OCR path is
  added; burned-in-subtitle OCR was macOS-only in the inspected workflow.
- [ ] Keep this as an enhancement, not the admission price. Scripts + stop lines
  + screenshots already produced a genuine shared present tense.

## Track G: hardening and later product surface

- [ ] Add more adversarial tests for malformed sources, hostile archives,
  redirects, parser bombs, path traversal, and unsafe document features.
- [ ] Define cleanup/retention/export for opaque sources, databases, journals,
  and sidecars without destroying encounter receipts unexpectedly.
- [ ] Decide whether a graphical interface adds real accessibility after the
  CLI/MCP joyflow is stable.
- [ ] Consider stronger containment only if the threat model changes. The
  present promise is cooperative suspense: First Read controls its own
  disclosures but does not imprison a malicious filesystem-capable reader.

## Recommended order

1. Publish the honestly bounded short-form v0.1.
2. Build and prove formal chapter hierarchy + atomic scope close.
3. Add chapter salience cards and rolling book state.
4. Build the sealed document intake interface.
5. Add EPUB/DOCX semantics and Docling-backed PDF conversion/validation.
6. Write the low-tech First Watch guide now; automate transcript formatting and
   shared stop packets after one or two more episodes expose the real friction.
7. Build and measure Lean/Full runners, then package MCP and other surfaces based
   on actual adopters rather than speculative polish.

## Decisions already made

- Do not manually split a whole book into chapter files.
- Do not claim a PDF converter preserves Markdown that the PDF does not contain.
- Do not let document conversion print intermediate prose or identifying
  metadata into the reader's context.
- Do not use an irreplaceable unread novel for the first chapter-boundary test.
- Do not reduce model calls by exposing multiple future passages at once.
- Do not replace immediate sealed responses with an end-only retrospective.
- Do not make Film Matinee or video processing a prerequisite for First Watch.
