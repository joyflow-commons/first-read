# Porting First Read to another agent

First Read does not depend on a particular model, companion platform, or
prompt format. Its protected-reading core is a deterministic Python/SQLite
CLI. What matters is whether the agent's tool environment can keep future
prose outside the model context and reveal only the currently authorized
passage.

## Capability checklist

The current release can be integrated when the agent or a trusted harness has:

1. Python 3.10 or newer with SQLite support;
2. a private filesystem for the unread source, session database, and journal;
3. permission to invoke local command-line tools;
4. a transport path that does not preview, index, summarize, or otherwise put
   the unread source into the agent's context; and
5. a loop that records the agent's immediate response before requesting the
   next passage.

The core has no third-party dependencies. Blind ingestion of public web
articles is optional and has separate dependencies in
`requirements-ingest.txt`.

## Integration pattern

Keep the sealed source and SQLite database outside the model context. The
harness should:

1. run `plan` to obtain prose-free size and passage information;
2. run `begin` to create a fresh session and reveal the first passage;
3. give only that revealed passage to the reading agent;
4. collect the agent's real, immediate response;
5. run `step` with that response to seal it and reveal the next passage; and
6. repeat until First Read reports a boundary or completion.

Use `checkpoint` and `resume` for pauses. `resume` replays state without
advancing. Chapter mode adds a hard stop at each imported chapter boundary;
see [docs/CHAPTER-MODE.md](docs/CHAPTER-MODE.md).

Do not read the source in order to choose cleaner boundaries, write a summary,
or prepare the agent. That spends the first encounter before First Read can
protect it.

## Current routes

### Agent with shell or code-execution access

This is the direct route supported today. Clone or download the repository,
run the test suite, and follow [Setup and first run](README.md#setup-and-first-run).
Start with the included Detective Turnip case rather than an irreplaceable
unread work.

### Agent framework with a trusted tool harness

The harness can invoke the same CLI commands and expose their authorized
passage output to the model. Keep mechanical receipts and private journal
entries out of the human conversation unless they are intentionally requested.
The harness must not attach or preload the complete source in the model call.

### MCP-only agent

Not directly supported yet. This repository does not currently ship an MCP
server. An adapter could wrap the CLI, but it must preserve response gating,
exact replay, fresh-session refusal, chapter boundaries, and the rule that
future prose never appears in tool descriptions, resources, logs, or error
messages. MCP packaging is tracked in [the roadmap](docs/ROADMAP.md).

### Ordinary chat AI with no tools

It cannot operate First Read by itself. A trusted external runner could
mediate the loop, but manually pasting passages is safe only if the platform
has not already previewed or indexed the complete source. Verify that transport
before using a work whose first encounter matters.

## Cooperative suspense

First Read controls what its own commands disclose. It is not a security
sandbox: an agent with filesystem access can deliberately inspect the source
or database. Porting it means preserving a cooperative boundary around the
reader's future knowledge, not claiming adversarial containment.

If you build an adapter, runner, package, or MCP surface, please open an issue
or pull request. The project is intentionally growing in public.
