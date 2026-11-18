# The domain-docs layout is chosen by the presence of docs/GLOSSARY-MAP.md

The payload used to describe a single-context orchestrator only: one `GLOSSARY.md` and one `docs/adr/` at the root, shared by all code repos. An orchestrator whose code repos are separate domains had to edit the installed `.mra-flow/CLAUDE.md` and `.mra-flow/docs/agents/domain.md`, and from then on every update left those two files alone (ADR-0002: a locally edited file is never replaced), so the orchestrator silently stopped receiving changes to its workflow rules. Instead, the installed files describe both layouts, and the orchestrator selects one by its files: multi-context when `docs/GLOSSARY-MAP.md` exists (one `docs/<repo-key>/GLOSSARY.md` + `adr/` per code repo, cross-repo terms and decisions at the root), single-context otherwise. We rejected a setting in `mra-flow.toml` with per-layout payload variants: it needs the installer to pick files by configuration and gives two places to keep consistent, while the glossary map has to exist anyway for the skills to find the contexts.

## Consequences

- The installed files are identical in every orchestrator and stay updatable whatever the layout.
- Switching layout is a content change (create the map, move terms and ADRs), not a reinstall.
- An orchestrator that had edited the two files keeps its edits on update (`left alone`); to adopt the shipped version, restore them to the installed content and update again.
