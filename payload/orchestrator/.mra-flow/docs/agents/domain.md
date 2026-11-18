# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Which layout this orchestrator uses

The orchestrator is in one of two layouts, and the files on disk say which:

- **Multi-context** when `docs/GLOSSARY-MAP.md` exists: each code repo is its own domain, with its own glossary and ADRs under `docs/<repo-key>/`.
- **Single-context** otherwise: one glossary and one ADR sequence at the orchestrator root, shared by all code repos.

Switching to multi-context means creating `docs/GLOSSARY-MAP.md` (and moving any existing terms and ADRs to their context); no setting changes.

## Before exploring, read these

**Single-context:**

- **`GLOSSARY.md`** at the orchestrator root.
- **`docs/adr/`**: ADRs that touch the area you're about to work in.

**Multi-context:**

- **`docs/GLOSSARY-MAP.md`**: points at one `docs/<repo-key>/GLOSSARY.md` per code repo, plus a root `docs/GLOSSARY.md` for terms spanning repos. Read each one relevant to the topic.
- **`docs/adr/`**: system-wide decisions and decisions spanning repos (e.g. a contract between two code repos).
- **`docs/<repo-key>/adr/`**: the context-scoped decisions of each repo you're touching.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `mattpocock-skills:domain-modeling` skill (reached via `/mra-grill`, `/mra-propose` and `/mra-update`) creates them lazily when terms or decisions actually get resolved. Wherever another `mra-*` skill says `GLOSSARY.md` or `docs/adr/`, read it as the glossaries and ADR folders of the layout in use.

## File structure

Single-context:

```
/                                   ← orchestrator (this repo)
├── GLOSSARY.md
├── docs/adr/
│   ├── 0001-example-decision.md
│   └── 0002-another-decision.md
├── docs/research/                  ← cited research notes (/mra-research)
├── openspec/
├── mra-flow.toml                   ← the code repos and their dependencies
├── <repo path>/                    ← separate git repo, one per [repos.<key>]
└── <repo path>/
```

Multi-context:

```
/                                   ← orchestrator (this repo)
├── docs/
│   ├── GLOSSARY-MAP.md             ← its presence selects this layout
│   ├── GLOSSARY.md                 ← created lazily: terms spanning repos
│   ├── adr/                        ← system-wide / cross-repo decisions
│   │   └── 0001-example-decision.md
│   ├── <repo-key>/
│   │   ├── GLOSSARY.md
│   │   └── adr/
│   │       └── 0001-repo-only-decision.md
│   └── <repo-key>/
│       ├── GLOSSARY.md
│       └── adr/
├── docs/research/                  ← cited research notes (/mra-research)
├── openspec/
│   └── specs/                      ← capability names may be prefixed by context: <repo-key>/<capability>, unprefixed when spanning repos
├── mra-flow.toml                   ← the code repos and their dependencies
├── <repo path>/                    ← separate git repo, one per [repos.<key>]
└── <repo path>/
```

In multi-context, a term or decision belongs to the narrowest context it binds: one repo → `docs/<repo-key>/`; several repos → the root. Each context's ADRs are numbered independently, starting at `0001`. `docs/GLOSSARY-MAP.md` lists each context with a one-line description and the relationships between contexts.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in the relevant glossary. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/mra-grill`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
