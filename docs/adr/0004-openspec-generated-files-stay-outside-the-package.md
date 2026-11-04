# OpenSpec-generated skills stay outside the package, behind a version gate

The `openspec-*` skills and `.claude/commands/opsx/` that the `mra-*` skills call are generated and updated by the OpenSpec CLI (`openspec init`, `openspec update`), so the package does not ship copies of them: a frozen copy would drift from the installed CLI. Instead the package declares a minimum OpenSpec version (below it, the installer stops) and the version it was tested with (above it, the installer only warns), so OpenSpec can always be upgraded independently; a breakage is fixed by a new mra-flow release.
