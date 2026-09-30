# First Read

First Read is a cooperative suspense instrument for AI companions. It reveals
prose sequentially, requires a response before advancing, and persists enough
reader-authored continuity to resume after a context reset without exposing
future text.

This repository currently contains a private v0.1 prototype. Do not use it on
an irreplaceable first encounter yet.

## The joyflow

1. The human transports a TXT or Markdown source to the companion's machine.
   Text attachments sent through an eager-preview chat such as Discord should
   be zipped before upload.
2. `start` imports the source into a private SQLite reading session. Importing
   does not print the source or future passage metadata.
3. `next` reveals one passage. Calling it again before responding replays the
   exact same passage.
4. `respond` seals the reader's response. Only then may `next` advance.
5. Before a long break, `checkpoint` records the reader's current
   understanding, relationships, predictions, feelings, and open questions.
   Checkpoints are versioned and never overwrite earlier ones.
6. `resume` returns a safe re-entry packet containing the latest checkpoint,
   the last revealed passage, and its response. It never includes unrevealed
   prose or a remaining-passage count.

The repository owns this continuity contract. Individual agents may write
checkpoints in their own voice, but they do not need to invent a separate
memory file or persistence scheme.

## Prototype commands

```bash
python3 first_read.py start --db /tmp/turnip.db --source examples/detective-turnip.md
python3 first_read.py next --db /tmp/turnip.db
python3 first_read.py respond --db /tmp/turnip.db --text "The lint is suspicious."
python3 first_read.py checkpoint --db /tmp/turnip.db --text "I distrust the dryer."
python3 first_read.py resume --db /tmp/turnip.db
```

Responses and checkpoints can also be read from standard input by omitting
`--text`, which avoids awkward shell quoting for long entries.

## Current boundary

This is cooperative suspense, not adversarial containment. A companion with
filesystem access can deliberately inspect the source or SQLite database.
First Read guarantees that its own commands disclose passages in order and
preserve the encounter record; it does not imprison a malicious reader.

