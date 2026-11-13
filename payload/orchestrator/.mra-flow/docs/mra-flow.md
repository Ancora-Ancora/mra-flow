# mra-flow

The workflow of this orchestrator: which command to run in which phase, which skills each command calls, and what it leaves behind. Source of truth for the rules: `CLAUDE.md` (section *Workflow*) and `.claude/skills/mra-*`.

Colours: blue = `mra-*` command · green = superpowers · yellow = mattpocock-skills · purple = OpenSpec · red = beads (`bd`) · orange = hook · white dashed = artifact · white solid = plain step.

## 1. Phases

```mermaid
flowchart LR
    classDef phase fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef optional fill:#a5d8ff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef blocked fill:#ffe3e3,stroke:#e03131,color:#e03131

    explore(["/mra-explore<br/>optional"]):::optional
    grill["/mra-grill<br/>1 · grill"]:::phase
    propose["/mra-propose<br/>2 · propose"]:::phase
    track["/mra-track<br/>3 · track"]:::phase
    build["/mra-build<br/>4 · build"]:::phase
    verify["/mra-verify<br/>5 · verify"]:::phase
    fix["/mra-fix<br/>6 · fix"]:::phase
    archive["/mra-archive<br/>7 · archive"]:::phase
    update["/mra-update<br/>any time"]:::phase
    sync["/mra-sync<br/>rare"]:::phase
    hotfix["/mra-hotfix<br/>rare · archived feature"]:::phase
    drift(["/mra-drift<br/>any time · read-only"]):::optional
    apply["/opsx:apply<br/>✖ blocked"]:::blocked

    explore -. decisions to make .-> grill
    explore -. decisions already recorded .-> propose
    grill --> propose --> track --> build --> verify
    verify -- bugs open --> fix
    fix -- re-verify --> verify
    verify -- "PASS, no open bugs" --> archive
    update -. revise artifacts .-> propose
    update -. reconcile beads .-> track
    sync -. specs before archive .-> archive
    hotfix -. spec gap: escalate .-> grill
    hotfix -. fix closed .-> drift
    grill -. existing capability .-> drift
    propose -. existing capability .-> drift
    drift -. DRIFT-SPEC .-> propose
    drift -. DRIFT-CODE, epic open .-> fix
    drift -. DRIFT-CODE, archived .-> hotfix
    apply -. use instead .-> build
```

## 2. Skills called by each phase

### Discovery and specification

```mermaid
flowchart TB
    classDef phase fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e

    subgraph EX["/mra-explore"]
        direction TB
        ex["/mra-explore"]:::phase --> ex1["openspec-explore"]:::os
        ex1 --> exA["nothing written"]:::art
    end
    subgraph GR["/mra-grill"]
        direction TB
        gr["/mra-grill"]:::phase --> gr1["mattpocock-skills:grilling"]:::mp
        gr --> gr2["mattpocock-skills:domain-modeling"]:::mp
        gr1 & gr2 --> grA["GLOSSARY.md<br/>docs/adr/NNNN-*.md<br/>carried decisions → /mra-propose"]:::art
    end
    subgraph PR["/mra-propose"]
        direction TB
        pr["/mra-propose"]:::phase --> pr1["openspec-propose"]:::os
        pr1 --> pr2["openspec validate --strict"]:::os
        pr2 -- gaps --> pr3["openspec-update-change"]:::os
        pr2 -- ADR candidates --> pr4["mattpocock-skills:domain-modeling"]:::mp
        pr2 --> prA["openspec/changes/#lt;id#gt;/<br/>proposal · specs/ · design.md (Contract sections) · tasks.md"]:::art
    end
    subgraph TR["/mra-track"]
        direction TB
        tr["/mra-track"]:::phase --> tr1["bd create<br/>epic + 1 issue per task"]:::bd
        tr1 --> tr2["bd dep add"]:::bd
        tr2 --> tr3["bd dep cycles · bd ready"]:::bd
        tr3 --> trA["beads epic openspec:#lt;id#gt;<br/>repo:#lt;key#gt; labels"]:::art
    end
```

### Implementation, verification and integration

```mermaid
flowchart TB
    classDef phase fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e
    classDef sub fill:#ebfbee,stroke:#2f9e44,stroke-dasharray:4 4,color:#1e1e1e
    classDef step fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e

    subgraph BU["/mra-build"]
        direction TB
        bu["/mra-build"]:::phase --> bu0["toolchain preflight"]:::step
        bu0 --> bu1["superpowers:using-git-worktrees"]:::sp
        bu1 --> bu2["superpowers:writing-plans"]:::sp
        bu2 --> bu3["superpowers:subagent-driven-development"]:::sp
        bu3 --> bu4["implementer subagent<br/>+ superpowers:test-driven-development"]:::sub
        bu4 --> bu5["reviewer subagent"]:::sub
        bu3 -. per task .-> bu6["bd claim · bd close<br/>progress bar: closed/total children"]:::bd
        bu3 -. spec gap .-> bu7["/mra-update"]:::phase
        bu5 --> bu8["final review per repo<br/>findings: bd create bug (epic) · needs-triage (outside)"]:::bd
        bu8 --> bu9["SDD rulings → epic notes"]:::bd
        bu9 --> buA[".worktrees/#lt;id#gt;/#lt;key#gt; · branch change/#lt;id#gt;<br/>plan.md (archived with the change) · 1 commit per issue"]:::art
    end
    subgraph VE["/mra-verify"]
        direction TB
        ve["/mra-verify"]:::phase --> ve1["superpowers:verification-before-completion"]:::sp
        ve1 --> ve6["contract on live servers<br/>+ page in Playwright Chromium"]:::step
        ve6 --> ve2["mattpocock-skills:code-review<br/>per repo, lockfiles excluded"]:::mp
        ve2 --> ve3["superpowers:receiving-code-review"]:::sp
        ve3 --> ve4["openspec validate --strict"]:::os
        ve4 --> ve5["bd create -t bug"]:::bd
        ve5 --> veA["pass/fail report<br/>verify note on the epic"]:::art
    end
    subgraph FX["/mra-fix"]
        direction TB
        fx["/mra-fix"]:::phase --> fx1["superpowers:systematic-debugging<br/>default"]:::sp
        fx --> fx2["mattpocock-skills:diagnosing-bugs<br/>perf · flaky · regression · cross-repo · 3 failed hypotheses"]:::mp
        fx1 & fx2 --> fx3["superpowers:test-driven-development<br/>reuse the reproducing test"]:::sp
        fx3 --> fx4["bd claim · bd close bug"]:::bd
        fx4 --> fxA["fix + regression test<br/>→ /mra-verify"]:::art
    end
    subgraph AR["/mra-archive"]
        direction TB
        ar["/mra-archive"]:::phase --> ar1["superpowers:finishing-a-development-branch<br/>per repo, in integration order"]:::sp
        ar1 --> ar2["openspec-archive-change<br/>syncs specs"]:::os
        ar2 --> ar3["bd close epic"]:::bd
        ar3 --> arA["merge / PR per repo<br/>openspec/specs/ updated · epic closed"]:::art
    end
```

### Any time

```mermaid
flowchart LR
    classDef phase fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e

    up["/mra-update"]:::phase --> up1["mattpocock-skills:domain-modeling<br/>new decision → ADR"]:::mp
    up --> up2["openspec-update-change"]:::os
    up --> up3["reconcile beads<br/>/mra-track steps · bd dep"]:::bd
    sy["/mra-sync"]:::phase --> sy1["openspec-sync-specs"]:::os
    hf["/mra-hotfix"]:::phase --> hf1["bd create -t bug<br/>hotfix · spec:#lt;capability#gt;"]:::bd
    hf1 --> hf2["superpowers:using-git-worktrees<br/>.worktrees/hotfix-#lt;bd-id#gt;"]:::sp
    hf2 --> hf3["diagnosis skill as in /mra-fix<br/>+ superpowers:test-driven-development"]:::sp
    hf3 --> hf4["superpowers:verification-before-completion"]:::sp
    hf4 --> hf5["superpowers:finishing-a-development-branch"]:::sp
    hf5 --> hf6["bd close · note on active change epics"]:::bd
    dr["/mra-drift"]:::phase --> dr1["git log per owning repo<br/>vs. origin/#lt;default-branch#gt;"]:::sp
    dr1 --> dr2["classify: ALIGNED · DRIFT-SPEC · DRIFT-CODE · UNVERIFIABLE · UNSPECIFIED"]:::os
    dr2 --> drA["drift report<br/>→ /mra-propose or /mra-fix or /mra-hotfix, on confirmation"]
```

## 3. Session continuity

```mermaid
flowchart LR
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef hook fill:#ffd8a8,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e

    ho["/mattpocock-skills:handoff<br/>rules in CLAUDE.md"]:::mp --> hf["handoff/ho-#lt;datetime#gt;.md<br/>read: false"]:::art
    ss["SessionStart<br/>startup · clear · compact"]:::hook --> bp["bd prime<br/>beads rules + bd memories"]:::hook
    ss --> lh["load-handoff.py<br/>newest handoff only"]:::hook
    lh -- "if read: false → inject, mark read: true" --> hf
```
