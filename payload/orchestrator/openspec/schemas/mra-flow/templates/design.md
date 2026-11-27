# Design

## Context

<!-- Current state and constraints that shape the approach. See proposal.md for motivation - don't restate it -->

## Goals / Non-Goals

**Goals:**
<!-- What this design aims to achieve -->

**Non-Goals:**
<!-- What is explicitly out of scope -->

## Decisions

<!-- Key design decisions with rationale and alternatives considered -->

## Contract: <repo> -> <dependency>

<!-- One section per touched repo whose depends_on dependency is touched too (keys from mra-flow.toml): endpoints, payloads, status codes, error shapes, auth, or the equivalent. If no such pair is touched, keep a single "## Contract" section with "N/A - no dependent repos touched" -->

## UI

<!-- Only if the change touches a repo's ui_paths: one bullet per screen, "<route> - roles: <...> - states: <...> - viewports: desktop|mobile". /mra-qa-ui checks these. Under each new or changed screen: "preview: prototype docs/prototypes/<slug>.md | sketch accepted | declined (<reason>)" (.mra-flow/docs/agents/ui-preview.md). Omit otherwise -->

## Module design

<!-- Only for a module other changes or slices will reuse, or a seam (.mra-flow/docs/agents/module-design.md): one "### <module>" each with Interface, Seam, Rejected (alternatives, one line each with why), Callers; or "module design: declined (<reason>)". Omit otherwise -->

## Risks / Trade-offs

<!-- Known risks and trade-offs -->

## ADR candidates

<!-- Hard-to-reverse, surprising, real trade-off decisions to record in docs/adr/. Omit if none -->
