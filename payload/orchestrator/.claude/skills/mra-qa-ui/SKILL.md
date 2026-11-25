---
name: mra-qa-ui
description: Use when an OpenSpec change in an mra-flow orchestrator touches a repo's user interface and its screens must be checked in a real browser - run by /mra-verify, or on its own while building UI.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-qa-ui — UI check in a real browser

Check what the user sees on the screens the change touches, in three levels ordered by token cost (ADR-0007 of mra-flow). Every problem becomes a beads bug that `/mra-fix` handles; this skill fixes nothing.

`/mra-verify` runs these steps as its UI step (it cannot call this skill through the Skill tool); the user can also run `/mra-qa-ui <change-id>` alone. Work files live in `.worktrees/<change-id>/qa-ui/` (git-ignored, outside the code repos).

## Steps

1. Call the Skill tool with `superpowers:verification-before-completion`: evidence before claims.
2. **Does it apply?** For each repo with a worktree in `.worktrees/<change-id>/`: `.mra-flow/bin/mra-repo ui-paths <key>` (empty: the repo declares no UI). The repo's UI is touched when `git -C .worktrees/<change-id>/<key> diff --name-only <base> -- <ui paths>` is not empty, `<base>` being the branch base as in `/mra-verify`. No touched UI in any repo → result `SKIPPED (no UI paths touched)`, go to step 9. A repo with no UI paths whose diff still touches what the browser shows (components, pages, styles, templates, locale strings) is not a UI-free repo: say so in the result as `SKIPPED (<key> declares no ui_paths)` and recommend adding `ui_paths = [...]` to its `[repos.<key>]` table in `mra-flow.toml` (`mra-repo add --ui-path` sets it only for a new repo).
3. **Setup notes.** `bd memories qa-ui`: how to start the app, its base URL, how each role logs in (environment variable names, never passwords), the e2e suite command, the Playwright version, the interactive browser tool, the target environment. Missing or incomplete → ask the user, then save them with `bd remember --key qa-ui-<key> "<notes>"`.
4. **Preflight** (stop and report what is missing, with the install command):
   - the app answers at its base URL (start it as the notes say if not);
   - `node --version`; Playwright in `.worktrees/<change-id>/qa-ui/`: `npm i --no-save --prefix .worktrees/<change-id>/qa-ui playwright@<version>`, then `npx --prefix .worktrees/<change-id>/qa-ui playwright install chromium`;
   - the interactive browser tool of the notes responds (needed only if level 3 runs).
5. **Scope → plan.** Write `.worktrees/<change-id>/qa-ui/plan.json` (format below) from: the `## UI` section of `design.md` (routes, roles, states, viewports), the routes behind the touched UI files, and the spec scenarios that name what the user sees. A screen whose `preview:` line names a prototype note (`docs/prototypes/<slug>.md`) takes that note's screenshots as its visual reference. Every touched route gets at least one page entry per role the spec names; `expect` lists what must be visible (elements, texts, error states).
6. **Level 1 — project e2e suite**, if the notes name one. Run it, record the command and the result. A failing test on a touched screen is a finding; a failing test elsewhere is an out-of-scope finding.
7. **Level 2 — smoke.** From `.worktrees/<change-id>/qa-ui/`: `node <orchestrator>/.mra-flow/qa-ui/smoke.mjs plan.json`. Read only its JSON summary; do not open the screenshots of passing pages. Exit 2 = the plan or the setup is wrong: fix it and rerun, it is not a finding.
8. **Level 3 — interactive**, only for pages that failed level 2 and for screens the change creates, with the browser tool of the notes. At most 15 browser actions per page (the notes may change this). Goals: confirm each level-2 failure and reduce it to a minimal repro; walk the multi-step spec scenarios that level 2 cannot assert (forms, wizards, permission denied); for a screen with a prototype reference, compare it with the reference screenshots and report what differs from the accepted verdict (layout, controls, flow), not pixel details. Page snapshots (accessibility trees) are the main token cost, up to a few thousand tokens per screen: when the tool saves them to files, search them (the tool's find command, or grep) for the element refs you need instead of reading them whole; prefer a browser CLI run through Bash over an MCP server, whose tool definitions add a fixed cost (ADR-0007). Look at a screenshot only to confirm a visual defect, and save it under `.worktrees/<change-id>/qa-ui/<date>/`. Never run against an environment other than the one the notes name.
9. **File findings**, one at a time, after checking `bd list --parent <epic> -l qa-ui --status open` for duplicates:
   - In scope (a touched screen, or a defect this change causes):
     ```bash
     bd create "<finding>" -t bug -p <0-3> --parent <epic> -l repo:<key>,verify,qa-ui \
       -d "<route, role, viewport>; steps: <...>; expected: <...>; actual: <...>; <console/network errors>; evidence: <screenshot path>"
     ```
   - Out of scope (already broken on a screen the change does not touch): file it outside the epic, so it does not block the change:
     ```bash
     bd create "<finding>" -t bug -p <0-3> -l repo:<key>,qa-ui,needs-triage --deps discovered-from:<epic> -d "<same evidence>"
     ```
   Priority: 0 crash, blank page or data loss; 1 a spec scenario fails or a flow is blocked; 2 wrong state or message, console error, failed request, a screen that departs from its accepted prototype; 3 cosmetic.
10. **Result:** `qa-ui: PASS | FAIL (<n> bugs) | SKIPPED (<reason>)`, with the levels run and their commands. Run by `/mra-verify`: hand it back to verify's report and note. Run alone: `bd update <epic> --append-notes "qa-ui <date>: <result>, <commands>"`, then the next command: `/mra-fix <change-id>` if bugs are open, else `/mra-verify <change-id>`.

## Plan format

```json
{
  "baseUrl": "http://localhost:3000",
  "outDir": "screenshots",
  "roles": {
    "admin": {
      "login": [
        {"goto": "/login"},
        {"fill": "#username", "value": "${QA_ADMIN_USER}"},
        {"fill": "#password", "value": "${QA_ADMIN_PASSWORD}"},
        {"click": "button[type=submit]"},
        {"waitForUrl": "**/home"}
      ]
    }
  },
  "pages": [
    {"role": "admin", "path": "/certificates", "expect": ["text=Certificates", "role=button[name=\"New\"]"], "viewports": ["desktop", "mobile"]},
    {"role": "anonymous", "path": "/certificates", "expect": ["text=Sign in"]}
  ],
  "ignoreConsole": [],
  "ignoreRequests": []
}
```

- `expect` entries are Playwright selectors (`text=`, CSS, `role=`). `${VAR}` reads an environment variable. Role `anonymous` needs no login.
- Viewports: `desktop` (1366×900), `mobile` (390×844); default `desktop`.
- Optional: `timeoutMs` (15000), `expectTimeoutMs` (5000), `settleMs` (500); `ignoreConsole` / `ignoreRequests` are regexes for known noise, each one justified in the notes.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Do not fix anything here; report and file. A fix goes through `/mra-fix`, test first.
- A page "looks fine" is not evidence: the smoke summary or a saved screenshot is.
- Level 3 runs only where level 2 cannot settle it; never browse every page interactively.
