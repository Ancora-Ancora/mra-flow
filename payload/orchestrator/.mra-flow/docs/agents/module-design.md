# Module design: design a shared module's interface before it is specified

Rule shared by `/mra-roadmap`, `/mra-propose` and `/mra-update`. Goal: a module that later changes build on gets its interface chosen on purpose, among real alternatives, before specs and tasks fix it. Its vocabulary (module, interface, seam, adapter, depth) and its procedure come from the `mattpocock-skills:codebase-design` skill.

## Which change gets it

| The change brings | Module design |
|---|---|
| a module that other changes or roadmap slices will reuse: a shared UI pattern (list, table, filters, paging, form layout), an API client or error layer, a shared state owner (e.g. the current user) | **yes**, on that module |
| a seam: an interface placed so the code behind it can be swapped or split out later (e.g. an API meant to become its own service, a port with a production and a test adapter) | **yes**, on that seam |
| a new screen built on modules that already exist, a behaviour fix, a text or data change | no |

When in doubt, ask the user in one question; a declined module design is recorded, never asked again.

## Where it runs

- `/mra-roadmap`, only to flag it: a slice that sets a pattern later slices reuse (usually the first of them) gets the open point `[slice <#>] module design: <module>`.
- `/mra-propose`, before `openspec-propose` writes `design.md`: the main point.
- `/mra-update`, when a revision adds such a module or changes the interface of one already designed.

Never in `/mra-grill` (it settles domain and decisions, not module shape), `/mra-build`, `/mra-verify`, `/mra-fix` or `/mra-hotfix`: once tasks and a plan exist, a new interface means redoing specs and plan.

## How it runs

Call the Skill tool with `mattpocock-skills:codebase-design` and follow its `DESIGN-IT-TWICE.md` on the module's interface: several radically different interfaces, compared on depth, locality and seam placement. Read the code repo's current modules first (the ones the new module replaces or sits next to). The user picks one; the others are the rejected alternatives.

## How it is recorded

In `design.md`, a `## Module design` section, one `### <module>` per designed module:

- **Interface**: what a caller must know: the entry points, their inputs and outputs, invariants, error modes, required configuration;
- **Seam**: where the interface lives (file or package) and its adapters, if any (production, test);
- **Rejected**: each alternative in one line, with why it lost;
- **Callers**: the later changes or slices expected to use it.

A declined module design is one line in that section: `module design: declined (<reason>)`. The section is omitted when no module qualifies.
