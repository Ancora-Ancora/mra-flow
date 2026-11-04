# mra-flow is installed by copy, with a checksum manifest and a strict ownership boundary

`install.sh` copies the package into the orchestrator and records a checksum per installed file in `.mra-flow/manifest`. The package owns only `.mra-flow/`, `.claude/skills/mra-*/` and `openspec/schemas/mra-flow/`; everything else (`mra-flow.toml`, `CLAUDE.md`, `GLOSSARY.md`, `docs/adr/`, `openspec/specs/`) belongs to the project and is never rewritten. The two shared files are touched minimally and idempotently: `CLAUDE.md` gets one `@.mra-flow/CLAUDE.md` import line if missing, and `.claude/settings.json` gets the SessionStart hook entry (keyed by its command path) and the required `enabledPlugins`. `--update` installs a chosen git tag, skips and reports any owned file whose checksum shows a local edit, and warns when a change is in flight.

## Considered Options

- **A marked block inside CLAUDE.md, rewritten on update.** Rejected: it means rewriting text inside a hand-edited file; an import keeps the package's text in a file the package fully owns.
- **An `--adopt` mode that takes over pre-existing unmanaged copies.** Rejected: the only orchestrator with pre-package files is the original one, and almost all of its files differ from the parametrized package or live at old paths. The installer stops on unmanaged files in owned paths instead, and that orchestrator is migrated by hand once.
- **Shipping everything as a Claude Code plugin.** Not chosen: the package also installs an OpenSpec schema and project scaffolding (beads, `.gitignore`, `mra-flow.toml`) that live in the repo, outside what a plugin provides.
