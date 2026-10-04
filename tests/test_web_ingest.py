import json
import socket
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from first_read_ingest import (
    IngestError,
    extract_markdown,
    fetch_html,
    quality_verdict,
    safe_receipt,
    save_ingest,
    validate_public_url,
    xml_to_markdown,
)


class FirstReadWebIngestTest(unittest.TestCase):
    def test_private_and_loopback_targets_are_rejected(self):
        for url in ("http://127.0.0.1/secret", "http://169.254.169.254/latest"):
            with self.subTest(url=url), self.assertRaises(IngestError):
                validate_public_url(url)

    @mock.patch("first_read_ingest.socket.getaddrinfo")
    def test_public_target_is_accepted(self, getaddrinfo):
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        self.assertEqual(
            validate_public_url("https://public.example/article"),
            "https://public.example/article",
        )

    def test_extractor_adapter_returns_markdown_without_printing(self):
        calls = {}

        def fake_extract(html, **kwargs):
            calls.update(kwargs)
            return (
                "<doc><main><head>Secret title</head>"
                "<p>Secret opening sentence.</p></main></doc>"
            )

        result = extract_markdown(
            "<article>hidden</article>",
            "https://public.example/article",
            extractor=fake_extract,
        )
        self.assertIn("Secret opening sentence", result)
        self.assertEqual(calls["output_format"], "xml")
        self.assertFalse(calls["include_comments"])
        self.assertTrue(calls["include_links"])

    def test_structured_paragraphs_remain_first_read_passage_units(self):
        paragraphs = "".join(
            f"<p>Paragraph {index} " + ("word " * 80) + "</p>"
            for index in range(6)
        )
        markdown = xml_to_markdown(f"<doc><main>{paragraphs}</main></doc>")
        self.assertEqual(markdown.count("\n\n"), 5)
        self.assertNotIn("<p>", markdown)

    def test_explicit_line_breaks_survive_structured_extraction(self):
        markdown = xml_to_markdown(
            "<doc><main><p>first line<lb/>second line</p></main></doc>"
        )
        self.assertEqual(markdown, "first line\nsecond line\n")

    def test_trailing_lightspeed_support_prompt_is_removed(self):
        markdown = xml_to_markdown(
            "<doc><main>"
            "<p>The literary ending stays.</p>"
            "<p>Enjoyed this story? Consider supporting us via one of the "
            "following methods:</p>"
            "</main></doc>"
        )
        self.assertEqual(markdown, "The literary ending stays.\n")

    @mock.patch("first_read_ingest.validate_public_url")
    @mock.patch("first_read_ingest.urllib.request.build_opener")
    def test_publisher_block_is_classified_without_echoing_url(
        self, build_opener, validate_public_url
    ):
        build_opener.return_value.open.side_effect = urllib.error.HTTPError(
            "https://private-title.example/spoiler", 403, "Forbidden", {}, None
        )
        with self.assertRaisesRegex(
            IngestError, r"Publisher refused an unauthenticated fetch \(HTTP 403\)"
        ) as caught:
            fetch_html("https://private-title.example/spoiler", 2, 1024)
        self.assertNotIn("private-title", str(caught.exception))

    def test_short_or_paywalled_extraction_is_flagged(self):
        verdict, words = quality_verdict(
            "<p>Subscribe to continue</p>",
            "small extracted teaser",
            min_words=250,
        )
        self.assertEqual(verdict, "suspected paywall or stub")
        self.assertEqual(words, 3)

    def test_saved_receipt_never_contains_title_url_or_prose(self):
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp) / "sealed"
            markdown = "# Death Crab Returns\n\nThe secret opening sentence stays sealed.\n"
            source, metadata = save_ingest(
                output_dir,
                "https://public.example/death-crab-returns",
                markdown,
                {
                    "source_url": "https://public.example/death-crab-returns",
                    "final_url": "https://public.example/death-crab-returns",
                    "redirected": False,
                    "http_status": 200,
                    "content_type": "text/html",
                    "html_bytes": 5000,
                },
                "short article-shaped extraction",
                9,
            )
            receipt = safe_receipt(
                source,
                metadata,
                9,
                "short article-shaped extraction",
                False,
            )
            self.assertNotIn("Death Crab", receipt)
            self.assertNotIn("secret opening", receipt.lower())
            self.assertNotIn("public.example", receipt)
            self.assertEqual(source.read_text(encoding="utf-8"), markdown)
            sidecar = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["word_count"], 9)
            self.assertEqual(output_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(source.stat().st_mode & 0o777, 0o600)
            self.assertEqual(metadata.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
