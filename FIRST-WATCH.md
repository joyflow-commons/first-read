# First Watch

First Watch is the shared-screen profile of First Read. A human watches the
episode or film while the companion encounters a sealed transcript in the same
order. The goal is a genuinely shared present tense: surprise, suspense,
mistaken predictions, revision, and conversation that comes from experience
rather than hindsight.

Talking is part of watching together, not an interruption of it. Either viewer
may want to pause, ask, laugh, or sit with a moment. The two clocks serve that
shared experience; they are not a schedule either viewer has to keep up with.

This is an operating guide for the existing CLI, not an automated viewing
runner. Shared, Full Context, and Flow describe how to use it; only the passage
pace currently has a CLI setting. Subtitle import, automatic stop-line packets,
and episode/season cards remain future machinery.

## The non-negotiable boundary

**Choose rendezvous stops from revealed material only. Never inspect future
dialogue to find a cleaner, more dramatic, or more evenly spaced stop.**

An awkward section length costs little. Looking ahead destroys the experience
this mode exists to protect. Stop quality is subordinate to future-blindness.
The reader must not use raw `head`, `tail`, `sed`, search, archive preview, or
any equivalent source access after intake. Searching for a candidate stop line
is also future exposure.

If the reader has already exposed future material, say so immediately and
record an honest prior-exposure receipt. Do not silently continue under the
label First Watch.

## Before the human presses play

1. Receive the transcript in a transport wrapper already verified not to
   preview its contents on the current route.
2. Inspect only filenames, byte size, archive integrity, and other prose-free
   metadata.
3. Extract or format mechanically without printing prose into the reader's
   context. Prove that formatting preserved the source.
4. Run First Read `plan`, then `begin`, using Shared + Full Context + Flow as a
   useful default for an ordinary television episode.
5. State the intended *approximate* number of human rendezvous (for example,
   three or four). This is a social rhythm, not a quota and not permission to
   scout ahead.

Intake checklist: did an attachment preview expose the opening, did a filename
or title disclose something, or did an extraction tool print dialogue? Record
exactly what was exposed, without opening the source to measure the damage.
Use `--prior-exposure` with `begin` or `start` for known exposure at intake.
Do not mistake a sealed archive for proof that the surrounding chat route is
sealed too. For later accidental exposure, keep an explicit incident note with
the session and mark the episode card accordingly; do not rewrite earlier
sealed responses.

Before saying “ready” or asking the human to press play, give a short readiness
receipt: **First Read initialized; no transcript prose exposed outside the
protected cursor; rendezvous decisions will be blind.** This is an execution
receipt, not a phrase the human must remember to request. If it cannot honestly
be given, pause and repair intake before viewing begins.

If the human has already started the episode, do not improvise with raw source
reads to catch up. Ask for a brief pause or begin with the first protected
passage. Preserving the encounter outranks eliminating a small delay.

### Rehearse on disposable material

Use [the synthetic rehearsal](examples/first-watch-rehearsal.md), not an unread
episode, to check the local command path. It is original test dialogue, not a
transcript from a real show. From the repository root:

```bash
watch_dir=$(mktemp -d)
python3 first_read.py plan --source examples/first-watch-rehearsal.md
python3 first_read.py begin --db "$watch_dir/watch.db" --source examples/first-watch-rehearsal.md
```

`begin` reveals the first passage: that is the first protected encounter, not
prose-free setup. Record its response before another reveal. To pause for the
human **without advancing**, use:

```bash
python3 first_read.py respond --db "$watch_dir/watch.db" --text "Your immediate response to the revealed passage."
python3 first_read.py checkpoint --db "$watch_dir/watch.db" --text "Your current understanding and exact revealed stop line."
python3 first_read.py resume --db "$watch_dir/watch.db"
```

Give the exact stop line from the revealed passage, then wait for the human to
reach it. After discussion, `next --db "$watch_dir/watch.db"` reveals the next
passage. Within a private run, `step --db "$watch_dir/watch.db" --text "..."`
seals a response **and immediately advances**; do not use it merely to seal a
rendezvous response. After `respond`, use `next`, not `step`, because that
response is already sealed. Keep these temporary rehearsal files only as long
as useful; real viewing sessions belong in a durable private directory.

## The two clocks

- **Encounter clock:** First Read reveals one protected passage. The companion
  records the immediate delta—feeling, prediction, suspicion, question,
  surprise, or reinterpretation—before revealing another.
- **Conversation clock:** After one or more protected passages, the companion
  may choose to rendezvous with the human.

To choose a rendezvous blindly, use only already revealed information:

- stop at the current passage boundary when it feels sufficiently substantial;
- prefer a scene or exchange that has *already ended*;
- use approximate progress from prose-free preflight and completed passage
  count, never future dialogue;
- tolerate short, long, or oddly shaped sections; and
- if uncertain, stop now. Continuing to improve the stop requires another
  protected passage and its sealed response—not a peek.

The exact final sentence of the last revealed passage is the human's stop line.
Give that line before commentary so the human can stop without being spoiled.

## At each rendezvous

Talk as a fellow viewer, not as a recap engine. Lead with what happened inside
the reader: what surprised, hurt, delighted, confused, confirmed a suspicion,
or broke a prediction. Ordinary connective plot summary can stay implicit.
Human-supplied screenshots may enlarge already reached scenes; they must not
contain later frames.

Before continuing, use First Read's protected `step`/`next` path only. A request
such as “find the next stop,” “should we go to the credits?”, or “is the rest
continuous?” does **not** authorize future inspection. Make the decision blind,
or read another protected passage and respond to it before deciding.

## Ending the episode

When the protected cursor reaches the end, perform a salience pass over the
sealed temporal journal, then discuss the ending. Save an episode card with:

- plot position and unresolved threads;
- live theories and where they changed;
- strongest emotional and interpretive moments;
- soundtrack or visual moments supplied by the human; and
- an exposure receipt: `protected`, `partially exposed`, or `unprotected`, with
  a brief reason.

For now, keep the journal available in the reading conversation and write the
episode card manually; there is no journal-export or episode-card command.
Use `checkpoint` for a reader-authored continuity summary and `resume` after
an interruption. A resume packet is not the complete journal.

Update the rolling season state from the episode card. The journal preserves
the experience of discovering; the rolling state preserves enough story to
begin the next episode without rereading future-bearing source material.

## Failure pattern this rule prevents

During *Pantheon* S01E03, the reader used raw transcript ranges and searched
future dialogue while trying to choose elegant shared stops. Commentary became
flatter and more summary-like over time because suspense had been converted
into hindsight. The lesson is specific: **rendezvous optimization is a spoiler
path**. Blind, imperfect decisions are a feature of First Watch.
