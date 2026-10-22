# Privacy

The skills package does not run a hosted service, transmit project content, collect personal information, or include first-party telemetry. `dev-docs` and `dev-rules` contain static instructions. `doc-research` additionally includes an optional local CLI that reads only the selected normalized corpus and writes a local SQLite index; it performs no network requests or telemetry.

Document indexes and evidence artifacts may contain source text. Store and retain them under the same access rules as the original corpus. `doc-research` permits optional OCR, structural parsing, connectors, and external retrieval services only when they are separately available and authorized for the applicable data scope.

Installation tools, coding agents, hosting providers, and optional project tooling may process data under their own privacy policies. In particular, the open-source `skills` CLI documents anonymous installation telemetry and supports opt-out through `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

For security reports, follow [SECURITY.md](SECURITY.md).
