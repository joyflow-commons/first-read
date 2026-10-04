#!/usr/bin/env python3
"""Fetch a public web article into First Read without printing its prose."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from first_read import DEFAULT_FLOW_WORDS, split_passages


DEFAULT_MAX_BYTES = 12 * 1024 * 1024
DEFAULT_MIN_WORDS = 250
USER_AGENT = "FirstReadWebIngest/0.1 (+private cooperative reading tool)"
TRAILING_BOILERPLATE_PREFIXES = (
    "enjoyed this story? consider supporting us via one of the following methods",
)


class IngestError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_public_url(url: str) -> str:
    """Reject non-web and non-public targets before any request is made."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise IngestError("URL must use public http or https")
    if not parsed.hostname or parsed.username or parsed.password:
        raise IngestError("URL must have a hostname and no embedded credentials")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise IngestError("URL hostname did not resolve") from exc
    if not addresses:
        raise IngestError("URL hostname did not resolve")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise IngestError("URL resolved to an invalid address") from exc
        if not ip.is_global:
            raise IngestError("URL resolves to a private or non-public address")
    return url


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        target = urllib.parse.urljoin(request.full_url, new_url)
        validate_public_url(target)
        return super().redirect_request(
            request, file_pointer, code, message, headers, target
        )


def fetch_html(url: str, timeout: float, max_bytes: int) -> tuple[str, dict]:
    if timeout <= 0:
        raise IngestError("--timeout must be positive")
    if max_bytes < 1:
        raise IngestError("--max-bytes must be positive")
    validate_public_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Accept-Encoding": "identity",
        },
    )
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            validate_public_url(final_url)
            content_type = response.headers.get_content_type().lower()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise IngestError("URL did not return an HTML document")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise IngestError("HTML response exceeded --max-bytes")
            charset = response.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            metadata = {
                "source_url": url,
                "final_url": final_url,
                "redirected": final_url != url,
                "http_status": getattr(response, "status", 200),
                "content_type": content_type,
                "html_bytes": len(raw),
            }
            return html, metadata
    except IngestError:
        raise
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403, 407, 451}:
            raise IngestError(
                f"Publisher refused an unauthenticated fetch (HTTP {exc.code})"
            ) from exc
        raise IngestError(f"Web fetch failed with HTTP {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise IngestError("Web fetch failed before article extraction") from exc


def extract_markdown(
    html: str,
    url: str,
    extractor: Callable[..., str | None] | None = None,
) -> str:
    if extractor is None:
        try:
            from trafilatura import extract as extractor
        except ImportError as exc:
            raise IngestError(
                "Trafilatura is missing; install requirements-ingest.txt in an isolated environment"
            ) from exc
    xml = extractor(
        html,
        url=url,
        output_format="xml",
        include_comments=False,
        include_links=True,
        include_images=False,
        include_tables=True,
        favor_precision=True,
        deduplicate=True,
    )
    if not xml or not xml.strip():
        raise IngestError("Extractor found no article-shaped prose")
    return xml_to_markdown(xml)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def render_inline(element: ET.Element) -> str:
    parts = [element.text or ""]
    for child in element:
        child_text = render_inline(child)
        if local_name(child.tag) == "ref" and child.get("target"):
            child_text = f"[{child_text.strip()}]({child.get('target')})"
        elif local_name(child.tag) == "lb":
            child_text = "\n" + child_text
        parts.append(child_text)
        parts.append(child.tail or "")
    text = "".join(parts)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def xml_to_markdown(xml: str) -> str:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise IngestError("Extractor returned malformed structured output") from exc
    main = next((node for node in root.iter() if local_name(node.tag) == "main"), None)
    if main is None:
        raise IngestError("Extractor returned no article body")
    parent = {child: node for node in main.iter() for child in node}
    block_tags = {"head", "p", "quote", "item"}
    blocks = []
    for element in main.iter():
        tag = local_name(element.tag)
        if tag not in block_tags:
            continue
        ancestor = parent.get(element)
        nested = False
        while ancestor is not None and ancestor is not main:
            if local_name(ancestor.tag) in block_tags:
                nested = True
                break
            ancestor = parent.get(ancestor)
        if nested:
            continue
        text = render_inline(element)
        if not text:
            continue
        if tag == "head":
            text = f"## {text}"
        elif tag == "quote":
            text = f"> {text}"
        elif tag == "item":
            text = f"- {text}"
        blocks.append(text)
    while blocks:
        normalized = re.sub(r"\s+", " ", blocks[-1]).strip().casefold()
        if not any(
            normalized.startswith(prefix)
            for prefix in TRAILING_BOILERPLATE_PREFIXES
        ):
            break
        blocks.pop()
    if not blocks:
        raise IngestError("Extractor returned no article-shaped prose")
    markdown = "\n\n".join(blocks).strip() + "\n"
    passages = split_passages(markdown, DEFAULT_FLOW_WORDS)
    largest = max((len(passage.split()) for passage in passages), default=0)
    if not passages or largest > DEFAULT_FLOW_WORDS * 2:
        raise IngestError("Extracted article is not safely passage-shaped for First Read")
    return markdown


def quality_verdict(html: str, markdown: str, min_words: int) -> tuple[str, int]:
    if min_words < 1:
        raise IngestError("--min-words must be positive")
    words = len(markdown.split())
    lowered = html.lower()
    paywall_signals = (
        "subscribe to continue",
        "sign in to continue",
        "already a subscriber",
        "unlock this article",
        "meteredcontent",
        "paywall",
    )
    signaled = any(marker in lowered for marker in paywall_signals)
    if words < min_words or (signaled and words < min_words * 3):
        return "suspected paywall or stub", words
    if words < min_words * 2:
        return "short article-shaped extraction", words
    return "article-shaped extraction", words


def atomic_write(path: Path, body: str) -> None:
    temp_path = path.with_name(path.name + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(0o600)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def save_ingest(
    output_dir: Path,
    source_url: str,
    markdown: str,
    fetch_metadata: dict,
    quality: str,
    word_count: int,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_dir.chmod(0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    url_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12]
    stem = f"web-{timestamp}-{url_hash}"
    source_path = output_dir / f"{stem}.md"
    metadata_path = output_dir / f"{stem}.json"
    if source_path.exists() or metadata_path.exists():
        raise IngestError("Refusing to overwrite an existing ingest")
    metadata = {
        **fetch_metadata,
        "captured_at": now(),
        "extractor": "trafilatura-2.3.0",
        "markdown_bytes": len(markdown.encode("utf-8")),
        "word_count": word_count,
        "quality": quality,
    }
    atomic_write(source_path, markdown)
    try:
        atomic_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    except Exception:
        source_path.unlink(missing_ok=True)
        raise
    return source_path, metadata_path


def safe_receipt(
    source_path: Path,
    metadata_path: Path,
    word_count: int,
    quality: str,
    redirected: bool,
) -> str:
    return "\n".join(
        [
            "First Read web ingest (no article prose revealed)",
            f"Source file: {source_path.name}",
            f"Metadata file: {metadata_path.name}",
            f"Words: {word_count}",
            f"Quality: {quality}",
            f"Redirected: {'yes' if redirected else 'no'}",
        ]
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("url")
    root.add_argument("--output-dir", type=Path, required=True)
    root.add_argument("--timeout", type=float, default=25.0)
    root.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    root.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        html, fetch_metadata = fetch_html(args.url, args.timeout, args.max_bytes)
        markdown = extract_markdown(html, fetch_metadata["final_url"])
        quality, word_count = quality_verdict(html, markdown, args.min_words)
        source_path, metadata_path = save_ingest(
            args.output_dir,
            args.url,
            markdown,
            fetch_metadata,
            quality,
            word_count,
        )
        print(
            safe_receipt(
                source_path,
                metadata_path,
                word_count,
                quality,
                fetch_metadata["redirected"],
            )
        )
        return 0
    except (IngestError, OSError, ValueError) as exc:
        print(f"first-read-ingest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
