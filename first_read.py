#!/usr/bin/env python3
"""Minimal persistent, response-gated prose reader."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
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


def split_passages(text: str, target_words: int) -> list[str]:
    blocks = [block.strip() for block in text.replace("\r\n", "\n").split("\n\n") if block.strip()]
    passages: list[str] = []
    current: list[str] = []
    words = 0
    for block in blocks:
        block_words = len(block.split())
        is_heading = block.startswith("#")
        if is_heading:
            if current:
                passages.append("\n\n".join(current))
            current, words = [block], 0
            continue
        if current and words and words + block_words > target_words:
            passages.append("\n\n".join(current))
            current, words = [], 0
        current.append(block)
        words += block_words
    if current:
        passages.append("\n\n".join(current))
    return passages


def start(
    db_path: Path,
    source_path: Path,
    target_words: int,
    prior_exposure: str | None = None,
) -> str:
    if db_path.exists():
        raise FirstReadError(f"Refusing to overwrite existing session: {db_path}")
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
        connection.commit()
    finally:
        connection.close()
    db_path.chmod(0o600)
    return "Reading session created. No passage has been revealed."


def next_passage(db_path: Path) -> str:
    with connect(db_path) as connection:
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
        elif response_row:
            parts.append("## State\nReady for the next passage.")
        else:
            parts.append("## State\nRespond to the current passage before advancing.")
        return "\n\n".join(parts)


def input_text(value: str | None) -> str:
    return value if value is not None else sys.stdin.read()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    create = sub.add_parser("start")
    create.add_argument("--db", type=Path, required=True)
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--target-words", type=int, default=180)
    create.add_argument("--prior-exposure")
    for name in ("next", "resume"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
    for name in ("respond", "checkpoint"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--text")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "start":
            result = start(
                args.db, args.source, args.target_words, args.prior_exposure
            )
        elif args.command == "next":
            result = next_passage(args.db)
        elif args.command == "respond":
            result = respond(args.db, input_text(args.text))
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
