---
name: mra-archive
description: Use when an OpenSpec change in the low-and-slow orchestrator has passed /mra-verify with no open bugs and must be integrated and archived - phase 7 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-archive — phase 7: integrate and archive

Integrate each repo's branch, then archive the OpenSpec change and close the beads epic.

## Steps

1. **Preconditions** (stop and report if any fails):
   - every child of the epic is closed: `bd list --parent <epic> --status open,in_progress,blocked` is empty;
   - the epic's last `verify` note says PASS and is newer than the last fix.
2. **Integrate each repo.** For each worktree in `.worktrees/<change-id>/`, call the Skill tool with `superpowers:finishing-a-development-branch` and let the user choose (merge locally, push + PR, keep). Integrate `be` before `fe`. Record each outcome (merge sha or PR url).
3. **Tick tasks.** In `openspec/changes/<change-id>/tasks.md`, tick each checkbox whose beads issue is closed (map in the epic notes). All must be ticked; stop if one is not.
4. **Archive.** Call the Skill tool with `openspec-archive-change` for `<change-id>` (syncs delta specs into `openspec/specs/`).
5. **ADRs.** For each ADR the change cited or created, set the `status:` field in its frontmatter (add the frontmatter if missing): `accepted` for an ADR this change created or confirmed, `superseded by ADR-NNNN` for one it replaced. Leave other ADRs untouched.
6. **Close the epic:** `bd close <epic> --reason "archived; be: <sha/PR>, fe: <sha/PR>"`.
7. **Orchestrator commit.** Show `git status` and the proposed message, e.g. `Archive <change-id> (be <sha/PR>, fe <sha/PR>)`, and commit after the user confirms.

## Rules

- Never archive with open bugs or a stale verify.
- If the user chose "keep" for a repo, stop after step 2: the change is not integrated yet.
