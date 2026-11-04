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
