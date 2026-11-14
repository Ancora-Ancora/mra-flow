---
name: mra-prototype
description: Use when a design question in an mra-flow orchestrator stays open after discussion - a state model or logic to sanity-check, or a UI whose shape is undecided - usually from /mra-grill, sometimes from /mra-update.
disable-model-invocation: true
argument-hint: <design question> [--repo <key>]
---

# mra-prototype — answer a design question with throwaway code

Build a throwaway prototype that settles the design question in `$ARGUMENTS`, record the **verdict** as a decision, and keep the prototype on its own branch as a primary source. The verdict is what moves forward; the prototype code never does.

## Steps

1. **Frame the question.** Restate it as one question ending in `?`, plus what a verdict looks like (e.g. "variant B", "the state model needs a paused state"). Pick the branch: logic / state model, or UI. Read the `GLOSSARY.md` terms and the ADRs it touches. Done when the user confirms the question and the branch.
2. **Pick the repo.** The code repo that owns the module or page (`--repo`, else `.mra-flow/bin/mra-repo list` and each repo's `description` in `mra-flow.toml`; ask if two fit). Choose a kebab-case `<slug>` for the question.
3. **Isolate.** Create the worktree `.worktrees/proto-<slug>/<key>` on a new branch `prototype/<slug>`, started from the repo's up-to-date default branch: `git -C <path> fetch`, then `git -C <path> worktree add <orchestrator>/.worktrees/proto-<slug>/<key> -b prototype/<slug> origin/<default-branch>`.
4. **Build.** Call the Skill tool with `mattpocock-skills:prototype` and follow it inside that worktree, with two overrides:
   - "close to where it will be used" means inside the worktree, next to the module or page in question;
   - its "capture" rule is replaced by steps 6-7 below: no implementation issue exists yet.
5. **Run it with the user** until they state the verdict and the reason behind it. Done when the question from step 1 has an answer the user owns; "looks fine" without a choice is not a verdict.
6. **Capture the prototype.** Commit it on `prototype/<slug>` with a message that carries the question and the verdict, e.g. `Prototype <slug>: <question> -> <verdict>`. Remove the worktree (`git -C <path> worktree remove <orchestrator>/.worktrees/proto-<slug>/<key>`) and keep the branch.
7. **Record the verdict** with a pointer to the branch: `<key>` branch `prototype/<slug>` at `<sha>`.
   - Hard-to-reverse → an ADR, through the Skill tool `mattpocock-skills:domain-modeling`, with the pointer in its body; new terms go to `GLOSSARY.md`.
   - Otherwise → a **carried decision** for `/mra-propose` (or for `openspec-update-change` when called from `/mra-update`).
   - A change already tracked in beads (`bd list -t epic -l openspec:<change-id>`) → also `bd update <epic> --append-notes "prototype <slug>: <verdict>; <key> prototype/<slug> <sha>"`.
8. End with a summary: question, verdict, where it is recorded, branch and sha, and the command to resume — back to `/mra-grill` (the grilling continues from here), `/mra-propose <change-id>`, or `/mra-update <change-id>`.

## Rules

- The `prototype/<slug>` branch is never merged, pushed or rebased onto a change branch; `/mra-build` rebuilds the validated behaviour test-first from the specs.
- Create no beads issues; the only beads write is the epic note in step 7.
- Do not commit in the orchestrator; list the changed files (ADR, glossary) and let the user decide.
