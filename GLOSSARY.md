# mra-flow

A spec-driven workflow for projects split across several code repos, packaged so it can be installed into, and updated in, any orchestrator.

## Language

### Layout

**Orchestrator**:
The repo that holds a project's specs, decisions, issue tracker and workflow skills, but no application code.
_Avoid_: Parent repo, meta repo, monorepo

**Code repo**:
A separate git repo with application code, cloned inside the orchestrator and declared in its repo registry.
_Avoid_: Subrepo, module, submodule

**Repo key**:
The short, stable name of a code repo, used in task tags, issue labels and worktree paths.
_Avoid_: Repo name, alias

**Repo registry**:
The orchestrator's declaration of its code repos and their dependencies (`mra-flow.toml`).
_Avoid_: Repo config, repo list

**Dependency**:
A code repo that another code repo consumes; it is integrated first, and a change touching both needs a contract.
_Avoid_: Upstream, parent

**Contract**:
The agreed interface between a code repo and one of its dependencies, written in a change's design.
_Avoid_: API spec, interface doc

### Workflow

**Change**:
One feature or fix carried through the workflow phases, from proposal to archive.
_Avoid_: Feature branch, ticket, story

**Initiative**:
An effort too large for one change, cut into slices by a roadmap.
_Avoid_: Program, project, theme

**Roadmap**:
The file that lists an initiative's slices with their order, estimates, status and actuals (`docs/roadmap/<initiative>.md`).
_Avoid_: Backlog, plan, release plan

**Slice**:
One row of a roadmap: a future change, named by its change id, that delivers observable value on its own.
_Avoid_: Milestone, phase, story

**Estimate**:
A slice's expected effort as a range of effective hours, with a confidence; the original one is never rewritten, and the variance is measured against its upper bound.
_Avoid_: Story points, guess

**Actual**:
The effective hours a done slice took, per phase: the time the agent or the user was active on it, measured at archive from the session logs and confirmed by the user.
_Avoid_: Spent time, burn, active days

**Effective hours**:
Time the agent or the user was actually working, counted from the session logs with pauses longer than a few minutes left out; never calendar time.
_Avoid_: Person-days, elapsed time

**Variance**:
A done slice's actual minus the upper bound of its estimate, in hours and in percent; over the estimate is red, within it green.
_Avoid_: Delta, slippage

### Packaging

**Package**:
The set of files mra-flow installs into an orchestrator, at one released version.
_Avoid_: Template, scaffold, distribution

**Owned file**:
A file installed by the package, tracked in the manifest, and rewritten only by an update.
_Avoid_: Managed file, generated file

**Local edit**:
A change made in the orchestrator to an owned file, detected because its checksum no longer matches the manifest.
_Avoid_: Customization, override
