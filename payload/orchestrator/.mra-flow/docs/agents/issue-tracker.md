# Issue tracker: beads (`bd`)

Issues for this project live in beads, in this orchestrator repo's Dolt database (`.beads/`).
A single tracker covers both code repos (`low-and-slow-cooking-lab-fe`, `low-and-slow-cooking-lab-be`).
Do not use GitHub Issues or files under `.scratch/`.

## Conventions

- **Target repo**: every implementation issue carries the label `repo:fe` or `repo:be` (both only if it genuinely touches both).
- **OpenSpec change**: issues born from a change carry the label `openspec:<change-id>` and `--spec-id openspec/changes/<change-id>`.
- **Hierarchy**: one change = one epic (`-t epic`); tasks are children (`--parent <epic-id>`). Labels are inherited from the parent.
- **Types**: `task` for planned work, `bug` for defects, `epic` for changes.
- **Discussion**: comments via `bd comments add <id> "..."`; progress notes via `bd update <id> --append-notes "..."`.

## When a skill says "publish to the issue tracker"

```bash
bd create "<title>" -t task -d "<description>" -l repo:be,openspec:<change-id> --parent <epic-id>
```

For a spec (`to-spec`) without an OpenSpec change: create an epic with the spec as its description (`--body-file`).

## When a skill says "fetch the relevant ticket"

`bd show <id>` (add `--json` for structured output). The user will normally pass the id directly.

## Wayfinding operations

Used by `/wayfinder`.

- **Map**: an epic (`-t epic -l wayfinder`); the epic description holds Notes / Decisions-so-far / Fog. Update it with `bd update <epic> --body-file -`.
- **Child ticket**: `bd create "<question>" --parent <epic> -l type:<research|prototype|grilling|task>`.
- **Blocking**: `bd dep add <blocked> <blocker>`.
- **Frontier**: `bd ready --parent <epic>` (open, unblocked); highest priority first.
- **Claim**: `bd update <id> --claim` before any work.
- **Resolve**: `bd close <id> --reason "<answer>"`, then append a context pointer (gist + id) to the epic's Decisions-so-far.
