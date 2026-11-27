---
name: mra-archive
description: Use when an OpenSpec change in an mra-flow orchestrator has passed /mra-verify with no open bugs and must be integrated and archived - phase 7 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-archive — phase 7: integrate and archive

Integrate each repo's branch, then archive the OpenSpec change and close the beads epic.

## Steps

1. **Preconditions** (stop and report if any fails):
   - every child of the epic is closed: `bd list --parent <epic> --status open,in_progress,blocked` is empty;
   - the epic's last `verify` note says PASS and is newer than the last fix;
   - that note's `qa-ui:` is PASS or `SKIPPED (no UI paths touched)`; any other SKIPPED reason needs the user's explicit acceptance, recorded with `bd update <epic> --append-notes "qa-ui skip accepted: <reason>"`;
   - the *Plan check* of `/mra-track` reports no mismatch (ticked checkboxes aside, there are none yet);
   - the *Drift gate* below passes.

   **Actual effort** (only when the change id is a slice of a roadmap, `.mra-flow/docs/agents/roadmap.md`): run `.mra-flow/bin/mra-effort measure <change-id>` (add `--alias <grill topic>` or a hotfix's bd id when they did not name the change), as *Actuals* in that file says. Show the hours per phase and the unattributed stretches, propose which stretches belong to which phase, and ask the user to confirm or correct the per-phase figures in one question, with the start and end of the work (`measure`'s `start`/`end`, widened to any stretch assigned by hand). They are written in step 6.

   **Drift gate** (before integrating anything, so a finding can still be absorbed into this change). For each capability under `openspec/changes/<change-id>/specs/` and each repo owning it (the `[<key>]` tags in `tasks.md`):
   - `git -C <path> fetch`; `base=$(git -C .worktrees/<change-id>/<key> merge-base HEAD origin/<default-branch>)`.
   - `git -C <path> log $base..origin/<default-branch> --format='%h %an %s' --name-only`, keeping commits by authors other than `git -C <path> config user.name`. None in any repo → the gate passes silently.
   - A capability not yet in `openspec/specs/` (only ADDED by this change) has no spec to drift from: only the same-files check below applies.
   - Otherwise run the steps of `.claude/skills/mra-drift/SKILL.md` (it cannot be called through the Skill tool) with arguments `<capability> --since <base> --exclude-change <change-id>`, read-only as that skill requires, then decide:
     - **block** — a DRIFT-SPEC on a requirement this change's delta MODIFIES, REMOVES or RENAMES → `/mra-update <change-id>` (fold the colleague's behaviour into the delta), then `/mra-verify`;
     - **block** — a DRIFT-CODE → `bd create -t bug --parent <epic>` and `/mra-fix <change-id>` if this change caused it, else outside the epic with label `needs-triage`; ask the user which;
     - **block** — a colleague's commit touches a file this change also touches (compare with `git -C .worktrees/<change-id>/<key> diff --name-only $base`) → rebase or merge `origin/<default-branch>` into `change/<change-id>`, then `/mra-verify`;
     - **pass, with a note** — a DRIFT-SPEC only on requirements this change does not touch → record it in the epic notes and, after step 8, recommend a spec-only sync change as `/mra-drift` step 10 describes.

2. **Integrate each repo.** For each worktree in `.worktrees/<change-id>/`, in integration order (`.mra-flow/bin/mra-repo list`: dependencies first):
   - If `.mra-flow/bin/mra-repo integration` prints a command, the project integrates its own way: ask the user per repo to integrate or keep. Integrate → `.mra-flow/bin/mra-repo integrate <key> change/<change-id>`; its last output line is the outcome. A non-zero exit → stop and report its output; never retry or work around it.
   - Otherwise call the Skill tool with `superpowers:finishing-a-development-branch` and let the user choose (merge locally, push + PR, keep).

   Record each outcome (merge sha or PR url).
3. **Tick tasks.** In `openspec/changes/<change-id>/tasks.md`, tick each checkbox `X.Y` whose beads issue (`bd list --parent <epic> --metadata-field task=X.Y --all`) is closed. All must be ticked; stop if one is not. This is the only time beads status is written into `tasks.md`.
4. **Archive.** Call the Skill tool with `openspec-archive-change` for `<change-id>` (syncs delta specs into `openspec/specs/`).
5. **ADRs.** For each ADR the change cited or created, record its status: `accepted` for an ADR this change created or confirmed, `superseded by ADR-NNNN` for one it replaced. Use the status field the ADR already has, in its own format (e.g. a `**Status:**` header line, plus a `**Superseded by:**` line if the project uses one), and follow the project's ADR conventions in `CLAUDE.md` when it has them; add a frontmatter `status:` field only when the ADR has no status field at all. Leave other ADRs untouched.
6. **Close the epic:** `bd close <epic> --reason "archived; <key>: <sha/PR>, ..."` (one entry per integrated repo).
   **Roadmap**, for a slice: set its row's Status to `done`, then run `.mra-flow/bin/mra-effort record <initiative> <change-id> --phase <phase>=<hours> ... --start "<start>" --end "<end>"` with the confirmed figures and `.mra-flow/bin/mra-effort report <initiative>` (totals and `docs/roadmap/<initiative>-effort.md`); add a Log line (`<change-id> done: actual <n> h vs. estimate <range> h (<variance %>)`). Show the slice's row of the variance table. If every slice is now `done` or `dropped`, offer to close the initiative epic and set the front matter `status: done`.
   **No roadmap**: if the change is a slice of no roadmap and its epic has no `roadmap: declined` note, check the late signals of *A roadmap found missing late* in `.mra-flow/docs/agents/roadmap.md`; when one holds, recommend `/mra-roadmap --retro` once, after this archive completes, naming the related archived changes (when the project's roadmap exists, recommend `/mra-roadmap <project>` to add the change as a done slice instead). A decline is recorded in the closed epic's notes.
7. **Effort and model breakdown** (every change, not only roadmap slices): run `.mra-flow/bin/mra-effort breakdown <change-id>` (same `--alias` as for `measure`) and show its Markdown table as the closing summary: the change (epic) first with its total hours and tokens per model, then every task with its hours and the models and tokens it used, then `other` and `session`. See *Record* in `.mra-flow/docs/agents/model-display.md`.
8. **Orchestrator commit.** Show `git status` (the roadmap file included, when updated) and the proposed message, e.g. `Archive <change-id> (<key> <sha/PR>, ...)`, and commit after the user confirms.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Never archive with open bugs or a stale verify.
- Never skip the drift gate: colleagues' commits on the default branch never update `openspec/specs/`, and the delta specs merge on top of it.
- If the user chose "keep" for a repo, stop after step 2: the change is not integrated yet.
