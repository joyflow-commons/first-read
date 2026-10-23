# Contributing to First Read

Small, focused contributions are welcome. Run the README's disposable first
encounter before changing the reading loop. Explain the problem and intended
behavior in an issue or pull request on the repository's hosting page; include
your Python version, OS, and a minimal synthetic reproduction for bugs.

## Development

The core uses Python 3.10+ and the standard library. Run:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Install `requirements-ingest.txt` in an isolated environment when changing or
checking the actual Trafilatura adapter. The ordinary tests use synthetic
inputs and mock extraction; passing them alone does not prove the optional
extractor is installed or a live publisher can be fetched.

Keep changes bounded. Add regression coverage for changed engine behavior,
especially response gating, immutable responses, exact replay, completion,
and cold-process resume. Planning and receipts must not expose unread prose,
titles, or future headings. Use original disposable fixtures, not copyrighted
stories, private correspondence, or an unread book someone values.

Update documentation when behavior changes. Clearly separate implemented
features from design targets; chapter boundaries are not yet enforced scopes.
Contributions are under this repository's MIT license.

## Privacy and security boundary

First Read is cooperative suspense, not a sandbox against a malicious agent.
Anyone with filesystem access can open the source or SQLite database. The
database contains the full imported work and the reader's responses; ingest
sidecars may contain source URLs. Keep these files private and out of commits,
issue attachments, screenshots, and diagnostic logs. Git ignore rules are a
convenience, not a privacy guarantee.

Report failures with synthetic text and sanitized commands. Never attach
credentials, cookies, private URLs, or a real reading database. For a sensitive
security report, use the host's private vulnerability-reporting route if it is
enabled; otherwise ask a maintainer for a private contact route before sharing
details. No private reporting service is promised by this release candidate.
