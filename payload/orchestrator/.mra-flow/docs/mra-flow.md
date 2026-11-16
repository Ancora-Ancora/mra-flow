# mra-flow

The workflow of this orchestrator: which command to run in which phase, which skills each command calls, and what it leaves behind. Source of truth for the rules: `CLAUDE.md` (section *Workflow*) and `.claude/skills/mra-*`.

Colours: `mra-*` commands and the skills they call share the colour of the skill family — light blue = OpenSpec · green = superpowers · yellow = mattpocock-skills · purple = custom `mra-*` logic · red = beads (`bd`) · orange = hook · white dashed = artifact · white solid = plain step. A command that calls skills of one family has that family's colour; one that mixes families (or adds its own logic to them) is white with one band per family. In the phase diagram each command box lists the skills it calls through the Skill tool (prefixes `superpowers:` and `mattpocock-skills:` omitted). Dashed border = optional command.

| | Family | Commands |
|---|---|---|
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#a5d8ff;border:1px solid #1e1e1e;"></span> | **OpenSpec** | `/mra-explore`, `/mra-sync` and the `openspec-*` skills |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#b2f2bb;border:1px solid #1e1e1e;"></span> | **superpowers** | `/mra-build` and the `superpowers:*` skills |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#ffec99;border:1px solid #1e1e1e;"></span> | **Matt Pocock** | `/mra-grill`, `/mra-prototype`, `/mra-research` and the `mattpocock-skills:*` skills |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#d0bfff;border:1px solid #1e1e1e;"></span> | **custom** | `/mra-track`, `/mra-drift`: own logic only |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:linear-gradient(90deg,#a5d8ff 0% 50%,#ffec99 50% 100%);border:1px solid #1e1e1e;"></span> | **mixed** | white box, one band per family: `/mra-propose`, `/mra-fix` |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:linear-gradient(90deg,#a5d8ff 0% 33%,#b2f2bb 33% 66%,#d0bfff 66% 100%);border:1px solid #1e1e1e;"></span> | **mixed + custom** | white box, one band per family: `/mra-update`, `/mra-verify`, `/mra-qa-ui`, `/mra-hotfix`, `/mra-archive` |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#ffc9c9;border:1px solid #1e1e1e;"></span> | **beads (`bd`)** | issue tracking steps |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#ffd8a8;border:1px solid #1e1e1e;"></span> | **hook** | SessionStart hooks |
| <span style="display:inline-block;width:2.2em;height:1.1em;vertical-align:middle;background:#ffe3e3;border:1px solid #e03131;background-image:linear-gradient(to top right,transparent 46%,#e03131 46% 54%,transparent 54%),linear-gradient(to bottom right,transparent 46%,#e03131 46% 54%,transparent 54%);"></span> | **blocked** | `/opsx:apply`: use `/mra-build` |

## 1. Phases

```mermaid
%%{init: {"themeCSS": ".bos,.bsp,.bmp,.bcu{white-space:nowrap} .t{font-size:1.25em;font-weight:700} .bos,.bsp,.bmp,.bcu{padding:2px 6px} .bos{background:#a5d8ff} .bsp{background:#b2f2bb} .bmp{background:#ffec99} .bcu{background:#d0bfff} .x{display:inline-block;padding:12px 20px;border:1px solid #e03131;background:linear-gradient(to top right,transparent calc(50% - 1.5px),#e03131 calc(50% - 1.5px),#e03131 calc(50% + 1.5px),transparent calc(50% + 1.5px)),linear-gradient(to bottom right,transparent calc(50% - 1.5px),#e03131 calc(50% - 1.5px),#e03131 calc(50% + 1.5px),transparent calc(50% + 1.5px)),#ffe3e3}", "flowchart": {"wrappingWidth": 400}}}%%
flowchart LR
    classDef phase fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef oswrap fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef striped fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e
    classDef stripedopt fill:#ffffff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef spwrap fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mpwrap fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef optional fill:#d0bfff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef oswrapopt fill:#a5d8ff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef mpwrapopt fill:#ffec99,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef blocked fill:transparent,stroke:transparent,color:#e03131

    explore(["<b class='t'>/mra-explore</b><br/>optional<br/><b>OpenSpec</b><br/>openspec-explore"]):::oswrapopt
    grill["<b class='t'>/mra-grill</b><br/>1 · grill<br/><b>Matt Pocock</b><br/>grilling<br/>domain-modeling"]:::mpwrap
    propose["<b class='t'>/mra-propose</b><br/>2 · propose<br/><span class='bos'><b>OpenSpec</b><br/>openspec-propose<br/>openspec-update-change</span><br/><span class='bmp'><b>Matt Pocock</b><br/>domain-modeling</span>"]:::striped
    track["<b class='t'>/mra-track</b><br/>3 · track"]:::phase
    build["<b class='t'>/mra-build</b><br/>4 · build<br/><b>superpowers</b><br/>using-git-worktrees<br/>writing-plans<br/>subagent-driven-development<br/>test-driven-development"]:::spwrap
    verify["<b class='t'>/mra-verify</b><br/>5 · verify<br/><span class='bsp'><b>superpowers</b><br/>verification-before-completion<br/>receiving-code-review</span><br/><span class='bmp'><b>Matt Pocock</b><br/>code-review</span><br/><span class='bcu'>custom</span>"]:::striped
    qaui(["<b class='t'>/mra-qa-ui</b><br/>verify step · or alone<br/><span class='bsp'><b>superpowers</b><br/>verification-before-completion</span><br/><span class='bcu'>custom</span>"]):::stripedopt
    fix["<b class='t'>/mra-fix</b><br/>6 · fix<br/><span class='bsp'><b>superpowers</b><br/>systematic-debugging<br/>test-driven-development</span><br/><span class='bmp'><b>Matt Pocock</b><br/>diagnosing-bugs</span>"]:::striped
    archive["<b class='t'>/mra-archive</b><br/>7 · archive<br/><span class='bos'><b>OpenSpec</b><br/>openspec-archive-change</span><br/><span class='bsp'><b>superpowers</b><br/>finishing-a-development-branch</span><br/><span class='bcu'>custom</span>"]:::striped
    update["<b class='t'>/mra-update</b><br/>any time<br/><span class='bos'><b>OpenSpec</b><br/>openspec-update-change</span><br/><span class='bmp'><b>Matt Pocock</b><br/>domain-modeling</span><br/><span class='bcu'>custom</span>"]:::striped
    sync["<b class='t'>/mra-sync</b><br/>rare<br/><b>OpenSpec</b><br/>openspec-sync-specs"]:::oswrap
    hotfix["<b class='t'>/mra-hotfix</b><br/>rare · archived feature<br/><span class='bsp'><b>superpowers</b><br/>using-git-worktrees<br/>systematic-debugging<br/>test-driven-development<br/>verification-before-completion<br/>finishing-a-development-branch</span><br/><span class='bmp'><b>Matt Pocock</b><br/>diagnosing-bugs</span><br/><span class='bcu'>custom</span>"]:::striped
    drift(["<b class='t'>/mra-drift</b><br/>any time · read-only"]):::optional
    proto(["<b class='t'>/mra-prototype</b><br/>stuck on design<br/><b>Matt Pocock</b><br/>prototype<br/>domain-modeling"]):::mpwrapopt
    research(["<b class='t'>/mra-research</b><br/>stuck on a fact<br/><b>Matt Pocock</b><br/>research"]):::mpwrapopt
    apply["<span class='x'>/opsx:apply<br/>blocked</span>"]:::blocked

    explore -. decisions to make .-> grill
    explore -. decisions already recorded .-> propose
    grill --> propose --> track --> build --> verify
    verify -- bugs open --> fix
    verify -. ui_paths touched .-> qaui
    qaui -. "bugs (qa-ui)" .-> fix
    fix -- re-verify --> verify
    verify -- "PASS, no open bugs" --> archive
    archive -. drift gate .-> drift
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
    grill -. open design question .-> proto
    update -. open design question .-> proto
    proto -. verdict .-> grill
    proto -. verdict .-> update
    grill -. external fact .-> research
    propose -. external fact .-> research
    update -. external fact .-> research
    research -. cited note .-> grill
    research -. cited note .-> propose
    research -. cited note .-> update
    apply -. use instead .-> build
```

## 2. Skills called by each phase

### Discovery and specification

```mermaid
%%{init: {"themeCSS": ".t{font-size:1.25em;font-weight:700} .bos,.bsp,.bmp,.bcu{padding:2px 6px} .bos{background:#a5d8ff} .bsp{background:#b2f2bb} .bmp{background:#ffec99} .bcu{background:#d0bfff}"}}%%
flowchart TB
    classDef phase fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef oswrap fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef striped fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e
    classDef stripedopt fill:#ffffff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef spwrap fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mpwrap fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e

    subgraph EX["<b class='t'>/mra-explore</b>"]
        direction TB
        ex["<b class='t'>/mra-explore</b>"]:::oswrap --> ex1["openspec-explore"]:::os
        ex1 --> exA["nothing written"]:::art
    end
    subgraph GR["<b class='t'>/mra-grill</b>"]
        direction TB
        gr["<b class='t'>/mra-grill</b>"]:::mpwrap --> gr1["mattpocock-skills:grilling"]:::mp
        gr --> gr2["mattpocock-skills:domain-modeling"]:::mp
        gr1 & gr2 --> grA["GLOSSARY.md<br/>docs/adr/NNNN-*.md<br/>carried decisions → /mra-propose"]:::art
    end
    subgraph PR["<b class='t'>/mra-propose</b>"]
        direction TB
        pr["<b class='t'>/mra-propose</b><br/><span class='bos'>OpenSpec</span><span class='bmp'>mattpocock</span>"]:::striped --> pr1["openspec-propose"]:::os
        pr1 --> pr2["openspec validate --strict"]:::os
        pr2 -- gaps --> pr3["openspec-update-change"]:::os
        pr2 -- ADR candidates --> pr4["mattpocock-skills:domain-modeling"]:::mp
        pr2 --> prA["openspec/changes/#lt;id#gt;/<br/>proposal · specs/ · design.md (Contract sections) · tasks.md"]:::art
    end
    subgraph TR["<b class='t'>/mra-track</b>"]
        direction TB
        tr["<b class='t'>/mra-track</b>"]:::phase --> tr1["bd create<br/>epic + 1 issue per task"]:::bd
        tr1 --> tr2["bd dep add"]:::bd
        tr2 --> tr3["bd dep cycles · bd ready · plan check"]:::bd
        tr3 --> trA["beads epic openspec:#lt;id#gt;<br/>repo:#lt;key#gt; labels · task=X.Y metadata"]:::art
    end
```

### Implementation, verification and integration

```mermaid
%%{init: {"themeCSS": ".t{font-size:1.25em;font-weight:700} .bos,.bsp,.bmp,.bcu{padding:2px 6px} .bos{background:#a5d8ff} .bsp{background:#b2f2bb} .bmp{background:#ffec99} .bcu{background:#d0bfff}"}}%%
flowchart TB
    classDef phase fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef oswrap fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef striped fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e
    classDef stripedopt fill:#ffffff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef spwrap fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mpwrap fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e
    classDef sub fill:#ebfbee,stroke:#2f9e44,stroke-dasharray:4 4,color:#1e1e1e
    classDef step fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e

    subgraph BU["<b class='t'>/mra-build</b>"]
        direction TB
        bu["<b class='t'>/mra-build</b>"]:::spwrap --> bu0["toolchain preflight"]:::step
        bu0 --> bu1["superpowers:using-git-worktrees"]:::sp
        bu1 --> bu2["superpowers:writing-plans"]:::sp
        bu2 --> bu3["superpowers:subagent-driven-development"]:::sp
        bu3 --> bu4["implementer subagent<br/>+ superpowers:test-driven-development"]:::sub
        bu4 --> bu5["reviewer subagent"]:::sub
        bu3 -. per task .-> bu6["bd claim · bd close<br/>progress bars: closed/total children · current task (estimated)"]:::bd
        bu3 -. spec gap .-> bu7["<b class='t'>/mra-update</b><br/><span class='bos'>OpenSpec</span><span class='bmp'>mattpocock</span><span class='bcu'>custom</span>"]:::striped
        bu5 --> bu8["final review per repo<br/>findings: bd create bug (epic) · needs-triage (outside)"]:::bd
        bu8 --> bu9["SDD rulings → epic notes"]:::bd
        bu9 --> buA[".worktrees/#lt;id#gt;/#lt;key#gt; · branch change/#lt;id#gt;<br/>plan.md (archived with the change) · 1 commit per issue"]:::art
    end
    subgraph VE["<b class='t'>/mra-verify</b>"]
        direction TB
        ve["<b class='t'>/mra-verify</b><br/><span class='bsp'>superpowers</span><span class='bmp'>mattpocock</span><span class='bcu'>custom</span>"]:::striped --> ve1["superpowers:verification-before-completion"]:::sp
        ve1 --> ve6["contract on live servers"]:::step
        ve6 --> ve8["<b class='t'>/mra-qa-ui</b> steps, if ui_paths touched<br/>1 · project e2e suite<br/>2 · smoke.mjs: pages × roles × viewports, JSON summary<br/>3 · interactive browser, failing/new pages only<br/><span class='bsp'>superpowers</span><span class='bcu'>custom</span>"]:::striped
        ve8 --> ve2["mattpocock-skills:code-review<br/>per repo, lockfiles excluded"]:::mp
        ve2 --> ve3["superpowers:receiving-code-review"]:::sp
        ve3 --> ve4["openspec validate --strict"]:::os
        ve4 --> ve7["plan check<br/>tasks.md ↔ epic tasks (task metadata)"]:::step
        ve7 --> ve5["bd create -t bug<br/>plan-drift → /mra-update"]:::bd
        ve5 --> veA["pass/fail report<br/>verify note on the epic"]:::art
    end
    subgraph FX["<b class='t'>/mra-fix</b>"]
        direction TB
        fx["<b class='t'>/mra-fix</b><br/><span class='bsp'>superpowers</span><span class='bmp'>mattpocock</span>"]:::striped --> fx1["superpowers:systematic-debugging<br/>default"]:::sp
        fx --> fx2["mattpocock-skills:diagnosing-bugs<br/>perf · flaky · regression · cross-repo · 3 failed hypotheses"]:::mp
        fx1 & fx2 --> fx3["superpowers:test-driven-development<br/>reuse the reproducing test"]:::sp
        fx3 --> fx4["bd claim · bd close bug"]:::bd
        fx4 --> fxA["fix + regression test<br/>→ /mra-verify"]:::art
    end
    subgraph AR["<b class='t'>/mra-archive</b>"]
        direction TB
        ar["<b class='t'>/mra-archive</b><br/><span class='bos'>OpenSpec</span><span class='bsp'>superpowers</span><span class='bcu'>custom</span>"]:::striped --> ar0["drift gate<br/>colleagues' commits since merge-base → /mra-drift --exclude-change"]:::step
        ar0 -. "blocks: touched requirement · DRIFT-CODE · same files" .-> ar0b["<b class='t'>/mra-update</b> · /mra-fix · rebase<br/>→ /mra-verify"]:::phase
        ar0 --> ar1["superpowers:finishing-a-development-branch<br/>per repo, in integration order"]:::sp
        ar1 --> ar2["openspec-archive-change<br/>syncs specs"]:::os
        ar2 --> ar3["bd close epic"]:::bd
        ar3 --> arA["merge / PR per repo<br/>openspec/specs/ updated · epic closed"]:::art
    end
```

### Any time

```mermaid
%%{init: {"themeCSS": ".t{font-size:1.25em;font-weight:700} .bos,.bsp,.bmp,.bcu{padding:2px 6px} .bos{background:#a5d8ff} .bsp{background:#b2f2bb} .bmp{background:#ffec99} .bcu{background:#d0bfff}"}}%%
flowchart LR
    classDef phase fill:#d0bfff,stroke:#1e1e1e,color:#1e1e1e
    classDef oswrap fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef striped fill:#ffffff,stroke:#1e1e1e,color:#1e1e1e
    classDef stripedopt fill:#ffffff,stroke:#1e1e1e,stroke-dasharray:5 5,color:#1e1e1e
    classDef spwrap fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mpwrap fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef sp fill:#b2f2bb,stroke:#1e1e1e,color:#1e1e1e
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef os fill:#a5d8ff,stroke:#1e1e1e,color:#1e1e1e
    classDef bd fill:#ffc9c9,stroke:#1e1e1e,color:#1e1e1e

    up["<b class='t'>/mra-update</b><br/><span class='bos'>OpenSpec</span><span class='bmp'>mattpocock</span><span class='bcu'>custom</span>"]:::striped --> up1["mattpocock-skills:domain-modeling<br/>new decision → ADR"]:::mp
    up --> up2["openspec-update-change"]:::os
    up --> up3["reconcile beads<br/>/mra-track steps · bd dep"]:::bd
    sy["<b class='t'>/mra-sync</b>"]:::oswrap --> sy1["openspec-sync-specs"]:::os
    hf["<b class='t'>/mra-hotfix</b><br/><span class='bsp'>superpowers</span><span class='bmp'>mattpocock</span><span class='bcu'>custom</span>"]:::striped --> hf1["bd create -t bug<br/>hotfix · spec:#lt;capability#gt;"]:::bd
    hf1 --> hf2["superpowers:using-git-worktrees<br/>.worktrees/hotfix-#lt;bd-id#gt;"]:::sp
    hf2 --> hf3["diagnosis skill as in /mra-fix<br/>+ superpowers:test-driven-development"]:::sp
    hf3 --> hf4["superpowers:verification-before-completion"]:::sp
    hf4 --> hf5["superpowers:finishing-a-development-branch"]:::sp
    hf5 --> hf6["bd close · note on active change epics"]:::bd
    dr["<b class='t'>/mra-drift</b>"]:::phase --> dr1["git log per owning repo<br/>vs. origin/#lt;default-branch#gt;"]:::sp
    dr1 --> dr2["classify: ALIGNED · DRIFT-SPEC · DRIFT-CODE · UNVERIFIABLE · UNSPECIFIED"]:::os
    dr2 --> drA["drift report<br/>→ /mra-propose or /mra-fix or /mra-hotfix, on confirmation"]
    pt["<b class='t'>/mra-prototype</b>"]:::mpwrap --> pt1["git worktree<br/>.worktrees/proto-#lt;slug#gt; · branch prototype/#lt;slug#gt;"]:::sp
    pt1 --> pt2["mattpocock-skills:prototype<br/>logic or UI"]:::mp
    pt2 --> pt3["mattpocock-skills:domain-modeling<br/>verdict → ADR or carried decision"]:::mp
    pt3 --> pt4["bd update epic --append-notes<br/>only if the change is tracked"]:::bd
    rs["<b class='t'>/mra-research</b>"]:::mpwrap --> rs1["mattpocock-skills:research<br/>background agent · primary sources"]:::mp
    rs1 --> rsA["docs/research/YYYY-MM-DD-#lt;slug#gt;.md<br/>cited by ADRs and design.md"]
    rs1 --> rs2["bd update epic --append-notes<br/>only with --change"]:::bd
```

## 3. Session continuity

```mermaid
%%{init: {"themeCSS": ".t{font-size:1.25em;font-weight:700} .bos,.bsp,.bmp,.bcu{padding:2px 6px} .bos{background:#a5d8ff} .bsp{background:#b2f2bb} .bmp{background:#ffec99} .bcu{background:#d0bfff}"}}%%
flowchart LR
    classDef mp fill:#ffec99,stroke:#1e1e1e,color:#1e1e1e
    classDef hook fill:#ffd8a8,stroke:#1e1e1e,color:#1e1e1e
    classDef art fill:#f8f9fa,stroke:#495057,stroke-dasharray:4 4,color:#1e1e1e

    ho["/mattpocock-skills:handoff<br/>rules in CLAUDE.md"]:::mp --> hf["handoff/ho-#lt;datetime#gt;.md<br/>read: false"]:::art
    ss["SessionStart<br/>startup · clear · compact"]:::hook --> bp["bd prime<br/>beads rules + bd memories"]:::hook
    ss --> lh["load-handoff.py<br/>newest handoff only"]:::hook
    lh -- "if read: false → inject, mark read: true" --> hf
    ss2["SessionStart<br/>startup · resume"]:::hook --> cd["check-drift.py<br/>no repos yet, or per repo: origin/HEAD sha vs. drift-state.json"]:::hook
    cd -- "no repos registered → recommend, don't run" --> mr["mra-repo add"]
    cd -- "sha moved since last check → recommend, don't run" --> dr["<b class='t'>/mra-drift</b>"]
```
