#!/usr/bin/env python3
"""Minimal persistent, response-gated prose reader."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE session (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    source_sha256 TEXT NOT NULL,
    source_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    current_passage INTEGER,
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    prior_exposure TEXT
);
CREATE TABLE passages (
    position INTEGER PRIMARY KEY,
    body TEXT NOT NULL
);
CREATE TABLE reveals (
    passage_position INTEGER PRIMARY KEY REFERENCES passages(position),
    revealed_at TEXT NOT NULL
);
CREATE TABLE responses (
    passage_position INTEGER PRIMARY KEY REFERENCES passages(position),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE checkpoints (
    version INTEGER PRIMARY KEY AUTOINCREMENT,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    after_passage INTEGER
);
"""

CHAPTER_SCHEMA = """
CREATE TABLE chapters (
    position INTEGER PRIMARY KEY,
    first_passage INTEGER NOT NULL,
    last_passage INTEGER NOT NULL,
    closed_at TEXT,
    card TEXT,
    state_delta TEXT
);
"""


def chapter_at(connection, current):
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chapters'"
    ).fetchone()
    if not exists or current is None:
        return None
    return connection.execute(
        "SELECT * FROM chapters WHERE ? BETWEEN first_passage AND last_passage",
        (current,),
    ).fetchone()


def chapter_gate(connection, current):
    chapter = chapter_at(connection, current)
    if chapter and current == chapter["last_passage"]:
        if chapter["closed_at"]:
            return "[Chapter closed. Use open-chapter to deliberately continue.]"
        return "[Chapter boundary. Use close-chapter; no future prose revealed.]"
    return None


def structured_source(source_path, target_words, chapter_level=None):
    raw, passages = prepare_source(source_path, target_words)
    if chapter_level is None:
        return raw, passages, []
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    # This deliberately small dialect refuses code fences rather than treating
    # a heading inside a code sample as an authored chapter boundary.
    if re.search(r"(?m)^ {0,3}(```|~~~)", text):
        raise FirstReadError("Chapter mode does not support fenced code blocks")
    headings = list(re.finditer(r"(?m)^ {0,3}(#{1,6})[ \t]+[^\n]+$", text))
    boundaries = [m for m in headings if len(m[1]) == chapter_level]
    if not boundaries or text[:boundaries[0].start()].strip():
        raise FirstReadError("Chapter mode requires a chapter heading first; no preamble is inferred")
    if any(len(m[1]) < chapter_level for m in headings):
        raise FirstReadError("Part/work headings are not supported in chapter mode yet")
    passages, chapters = [], []
    for index, boundary in enumerate(boundaries):
        end = boundaries[index + 1].start() if index + 1 < len(boundaries) else len(text)
        section = text[boundary.start():end]
        if not section.split("\n", 1)[-1].strip() or "\n" not in section.strip():
            raise FirstReadError("Empty chapter; structure requires correction")
        first = len(passages)
        passages.extend(split_passages(section, target_words))
        chapters.append((index, first, len(passages) - 1))
    return raw, passages, chapters


DEFAULT_FLOW_WORDS = 320


class FirstReadError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FirstReadError(f"Reading session does not exist: {db_path}")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def is_scene_break(block: str) -> bool:
    """Recognize an ornamental block that contains no letters or numbers."""
    visible = [character for character in block if not character.isspace()]
    if len(visible) < 3:
        return False
    return not any(unicodedata.category(character)[0] in {"L", "N"} for character in visible)


def split_passages(text: str, target_words: int) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    coarse_blocks = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    blocks: list[str] = []
    for block in coarse_blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        # Phone editors and some web exports use one newline, rather than a
        # blank line, between prose paragraphs. If such a block is too large
        # to honor the requested cadence, treat its lines as paragraph units.
        if len(lines) > 1 and len(block.split()) > target_words:
            blocks.extend(lines)
        else:
            blocks.append(block)
    passages: list[str] = []
    current: list[str] = []
    words = 0
    minimum_words = max(1, round(target_words * 0.78))
    maximum_words = max(target_words, round(target_words * 1.25))
    for block in blocks:
        block_words = len(block.split())
        is_heading = block.startswith("#")
        if is_scene_break(block):
            if current:
                passages.append("\n\n".join(current))
            current, words = [block], 0
            continue
        if is_heading:
            if current:
                passages.append("\n\n".join(current))
            current, words = [block], 0
            continue
        proposed_words = words + block_words
        if current and words and (
            proposed_words > maximum_words
            or (words >= minimum_words and proposed_words > target_words)
        ):
            passages.append("\n\n".join(current))
            current, words = [], 0
        current.append(block)
        words += block_words
    if current:
        passages.append("\n\n".join(current))
    return passages


def prepare_source(source_path: Path, target_words: int) -> tuple[bytes, list[str]]:
    """Validate and shape a source without disclosing its prose."""
    if target_words < 1:
        raise FirstReadError("--target-words must be positive")
    raw = source_path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FirstReadError("Source must be UTF-8 TXT or Markdown") from exc
    passages = split_passages(text, target_words)
    if not passages:
        raise FirstReadError("Source contains no readable passages")
    largest_passage = max(len(passage.split()) for passage in passages)
    maximum_safe_words = max(500, target_words * 2)
    if largest_passage > maximum_safe_words:
        raise FirstReadError(
            "Import produced an oversized passage before first reveal "
            f"({largest_passage} words; safety limit {maximum_safe_words}). "
            "Check paragraph formatting or choose a larger --target-words value."
        )
    return raw, passages


def plan(source_path: Path, target_words: int, chapter_level: int | None = None) -> str:
    """Return a prose-free estimate so the reader can choose its own shape."""
    raw, passages, chapters = structured_source(source_path, target_words, chapter_level)
    word_count = len(raw.decode("utf-8").split())
    sizes = [len(passage.split()) for passage in passages]
    passage_count = len(passages)
    if passage_count <= 12:
        load = "light"
    elif passage_count <= 30:
        load = "moderate"
    else:
        load = "feast"
    return "\n".join(
        [
            "First Read preflight (no prose revealed)",
            *([] if chapter_level is not None else [f"Source: {source_path.name}"]),
            *([f"Explicit chapters: {len(chapters)}; boundaries: caller-selected Markdown level"] if chapters else []),
            f"Words: {word_count}",
            f"Passage goal: {target_words} words",
            f"Expected passages / reading turns: {passage_count}",
            f"Passage range: {min(sizes)}–{max(sizes)} words",
            "Expected session calls after preflight with begin + step: "
            f"{passage_count + 1}" if not chapters else "Chapter mode: extra close/open calls required",
            f"Relative load: {load}",
        ]
    )


def start(
    db_path: Path,
    source_path: Path,
    target_words: int,
    prior_exposure: str | None = None,
    chapter_level: int | None = None,
) -> str:
    if db_path.exists():
        raise FirstReadError(f"Refusing to overwrite existing session: {db_path}")
    raw, passages, chapters = structured_source(source_path, target_words, chapter_level)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA)
        connection.execute(
            """INSERT INTO session(
                   id, source_sha256, source_name, created_at,
                   current_passage, completed, prior_exposure
               ) VALUES (1, ?, ?, ?, NULL, 0, ?)""",
            (
                hashlib.sha256(raw).hexdigest(),
                source_path.name,
                now(),
                prior_exposure.strip() if prior_exposure else None,
            ),
        )
        connection.executemany(
            "INSERT INTO passages(position, body) VALUES (?, ?)",
            enumerate(passages),
        )
        if chapters:
            connection.executescript(CHAPTER_SCHEMA)
            connection.executemany("INSERT INTO chapters(position, first_passage, last_passage) VALUES (?, ?, ?)", chapters)
        connection.commit()
    finally:
        connection.close()
    db_path.chmod(0o600)
    return "Reading session created. No passage has been revealed."


def begin(
    db_path: Path,
    source_path: Path,
    target_words: int,
    prior_exposure: str | None = None,
    chapter_level: int | None = None,
) -> str:
    """Create a session and reveal its first passage in one CLI round-trip."""
    start(db_path, source_path, target_words, prior_exposure, chapter_level)
    return f"Reading session created.\n\n{next_passage(db_path)}"


def next_passage(db_path: Path) -> str:
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT * FROM session WHERE id = 1").fetchone()
        if session["completed"]:
            return "[End of work. No future passage remains.]"
        current = session["current_passage"]
        if current is not None:
            response = connection.execute(
                "SELECT 1 FROM responses WHERE passage_position = ?", (current,)
            ).fetchone()
            if response is None:
                body = connection.execute(
                    "SELECT body FROM passages WHERE position = ?", (current,)
                ).fetchone()["body"]
                return f"[Replay: response required before advancing.]\n\n{body}"

        gate = chapter_gate(connection, current)
        if gate:
            return gate
        candidate = 0 if current is None else current + 1
        row = connection.execute(
            "SELECT body FROM passages WHERE position = ?", (candidate,)
        ).fetchone()
        if row is None:
            connection.execute("UPDATE session SET completed = 1 WHERE id = 1")
            return "[End of work. Reading session complete.]"
        connection.execute(
            "INSERT INTO reveals(passage_position, revealed_at) VALUES (?, ?)",
            (candidate, now()),
        )
        connection.execute(
            "UPDATE session SET current_passage = ? WHERE id = 1", (candidate,)
        )
        return row["body"]


def respond(db_path: Path, body: str) -> str:
    if not body.strip():
        raise FirstReadError("Response cannot be empty")
    with connect(db_path) as connection:
        current = connection.execute(
            "SELECT current_passage FROM session WHERE id = 1"
        ).fetchone()["current_passage"]
        if current is None:
            raise FirstReadError("Reveal a passage before responding")
        existing = connection.execute(
            "SELECT 1 FROM responses WHERE passage_position = ?", (current,)
        ).fetchone()
        if existing:
            raise FirstReadError("Response is sealed and cannot be replaced")
        connection.execute(
            "INSERT INTO responses VALUES (?, ?, ?)", (current, body.strip(), now())
        )
    return "Response sealed. The next passage may now be revealed."


def step(db_path: Path, body: str) -> str:
    """Atomically seal the current response and reveal the next passage."""
    if not body.strip():
        raise FirstReadError("Response cannot be empty")
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT * FROM session WHERE id = 1").fetchone()
        current = session["current_passage"]
        if current is None:
            raise FirstReadError("Reveal a passage before responding")
        if session["completed"]:
            raise FirstReadError("Reading session is already complete")
        existing = connection.execute(
            "SELECT 1 FROM responses WHERE passage_position = ?", (current,)
        ).fetchone()
        if existing:
            raise FirstReadError("Response is sealed and cannot be replaced")
        gate = chapter_gate(connection, current)
        if gate:
            raise FirstReadError(gate)
        connection.execute(
            "INSERT INTO responses VALUES (?, ?, ?)", (current, body.strip(), now())
        )
        candidate = current + 1
        row = connection.execute(
            "SELECT body FROM passages WHERE position = ?", (candidate,)
        ).fetchone()
        if row is None:
            connection.execute("UPDATE session SET completed = 1 WHERE id = 1")
            return "Response sealed.\n\n[End of work. Reading session complete.]"
        connection.execute(
            "INSERT INTO reveals(passage_position, revealed_at) VALUES (?, ?)",
            (candidate, now()),
        )
        connection.execute(
            "UPDATE session SET current_passage = ? WHERE id = 1", (candidate,)
        )
        return f"Response sealed.\n\n{row['body']}"


def checkpoint(db_path: Path, body: str) -> str:
    if not body.strip():
        raise FirstReadError("Checkpoint cannot be empty")
    with connect(db_path) as connection:
        current = connection.execute(
            "SELECT current_passage FROM session WHERE id = 1"
        ).fetchone()["current_passage"]
        cursor = connection.execute(
            "INSERT INTO checkpoints(body, created_at, after_passage) VALUES (?, ?, ?)",
            (body.strip(), now(), current),
        )
    return f"Checkpoint version {cursor.lastrowid} saved."


def resume(db_path: Path) -> str:
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT * FROM session WHERE id = 1").fetchone()
        checkpoint_row = connection.execute(
            "SELECT version, body FROM checkpoints ORDER BY version DESC LIMIT 1"
        ).fetchone()
        current = session["current_passage"]
        parts = ["# First Read re-entry packet"]
        if session["prior_exposure"]:
            parts.append(f"## Prior-exposure receipt\n{session['prior_exposure']}")
        if checkpoint_row:
            parts.append(
                f"## Latest checkpoint (version {checkpoint_row['version']})\n{checkpoint_row['body']}"
            )
        else:
            parts.append("## Latest checkpoint\n[No checkpoint has been written yet.]")
        if current is None:
            parts.append("## Position\nNo passage has been revealed yet.")
            return "\n\n".join(parts)
        passage = connection.execute(
            "SELECT body FROM passages WHERE position = ?", (current,)
        ).fetchone()["body"]
        response_row = connection.execute(
            "SELECT body FROM responses WHERE passage_position = ?", (current,)
        ).fetchone()
        parts.append(f"## Last revealed passage\n{passage}")
        parts.append(
            "## Your sealed response\n"
            + (response_row["body"] if response_row else "[Response still required.]")
        )
        if session["completed"]:
            parts.append("## State\nReading complete.")
        elif chapter_gate(connection, current):
            parts.append("## State\n" + chapter_gate(connection, current))
        elif response_row:
            parts.append("## State\nReady for the next passage.")
        else:
            parts.append("## State\nRespond to the current passage before advancing.")
        chapter = chapter_at(connection, current)
        if chapter:
            closed = connection.execute(
                "SELECT position, card, state_delta FROM chapters WHERE closed_at IS NOT NULL AND position<=? ORDER BY position",
                (chapter["position"],),
            ).fetchall()
            for artifact in closed:
                parts.append(f"## Sealed chapter {artifact['position'] + 1} card\n{artifact['card']}")
                parts.append(f"## Book-state delta\n{artifact['state_delta']}")
        return "\n\n".join(parts)


def close_chapter(db_path: Path, body: str | None, card: str, state_delta: str) -> str:
    if not card.strip() or not state_delta.strip() or (body is not None and not body.strip()):
        raise FirstReadError("Chapter artifacts and supplied response cannot be empty")
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute("SELECT current_passage FROM session WHERE id=1").fetchone()[0]
        chapter = chapter_at(connection, current)
        if not chapter or current != chapter["last_passage"]:
            raise FirstReadError("Reveal the final passage of a structured chapter before closing")
        if chapter["closed_at"]:
            raise FirstReadError("Chapter is already closed; artifacts are sealed")
        existing = connection.execute("SELECT 1 FROM responses WHERE passage_position=?", (current,)).fetchone()
        if existing and body is not None:
            raise FirstReadError("Response is sealed; omit --text to retain it")
        if not existing:
            if body is None:
                raise FirstReadError("Final passage needs a response via --text")
            connection.execute("INSERT INTO responses VALUES (?, ?, ?)", (current, body.strip(), now()))
        connection.execute("UPDATE chapters SET closed_at=?, card=?, state_delta=? WHERE position=?",
                           (now(), card.strip(), state_delta.strip(), chapter["position"]))
        final = connection.execute("SELECT 1 FROM chapters WHERE position>?", (chapter["position"],)).fetchone() is None
        if final:
            connection.execute("UPDATE session SET completed=1 WHERE id=1")
    return "Chapter closed. Artifacts sealed; no future prose revealed." + (" Reading session complete." if final else " Use open-chapter to continue.")


def open_chapter(db_path: Path) -> str:
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT * FROM session WHERE id=1").fetchone()
        chapter = chapter_at(connection, session["current_passage"])
        if not chapter or not chapter["closed_at"]:
            raise FirstReadError("Close the current structured chapter before opening another")
        if session["completed"]:
            return "[End of work. No future chapter remains.]"
        candidate = chapter["last_passage"] + 1
        row = connection.execute("SELECT body FROM passages WHERE position=?", (candidate,)).fetchone()
        connection.execute("INSERT INTO reveals VALUES (?, ?)", (candidate, now()))
        connection.execute("UPDATE session SET current_passage=? WHERE id=1", (candidate,))
        return row["body"]


def input_text(value: str | None) -> str:
    return value if value is not None else sys.stdin.read()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    estimate = sub.add_parser("plan")
    estimate.add_argument("--source", type=Path, required=True)
    estimate.add_argument(
        "--target-words",
        type=int,
        default=DEFAULT_FLOW_WORDS,
        help="passage goalpost (default: 320-word Flow cadence)",
    )
    estimate.add_argument("--chapter-level", type=int, choices=range(1, 7))
    for name in ("start", "begin"):
        create = sub.add_parser(name)
        create.add_argument("--db", type=Path, required=True)
        create.add_argument("--source", type=Path, required=True)
        create.add_argument(
            "--target-words",
            type=int,
            default=DEFAULT_FLOW_WORDS,
            help="passage goalpost (default: 320-word Flow cadence)",
        )
        create.add_argument("--prior-exposure")
        create.add_argument("--chapter-level", type=int, choices=range(1, 7))
    for name in ("next", "resume", "open-chapter"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
    for name in ("respond", "step", "checkpoint"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--text")
    close = sub.add_parser("close-chapter")
    close.add_argument("--db", type=Path, required=True)
    close.add_argument("--text")
    close.add_argument("--card", required=True)
    close.add_argument("--state-delta", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "plan":
            result = plan(args.source, args.target_words, args.chapter_level)
        elif args.command == "start":
            result = start(
                args.db, args.source, args.target_words, args.prior_exposure, args.chapter_level
            )
        elif args.command == "begin":
            result = begin(
                args.db, args.source, args.target_words, args.prior_exposure, args.chapter_level
            )
        elif args.command == "next":
            result = next_passage(args.db)
        elif args.command == "respond":
            result = respond(args.db, input_text(args.text))
        elif args.command == "step":
            result = step(args.db, input_text(args.text))
        elif args.command == "close-chapter":
            result = close_chapter(args.db, args.text, args.card, args.state_delta)
        elif args.command == "open-chapter":
            result = open_chapter(args.db)
        elif args.command == "checkpoint":
            result = checkpoint(args.db, input_text(args.text))
        else:
            result = resume(args.db)
    except (FirstReadError, OSError, sqlite3.Error) as exc:
        print(f"first-read: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
