# UI QA runs in three levels, with a Node + Playwright smoke runner

A change that touches a repo's user interface is checked in a real browser by `/mra-qa-ui`, which `/mra-verify` runs as one of its steps. The check is split by token cost: (1) the project's own end-to-end suite, if any; (2) `.mra-flow/qa-ui/smoke.mjs`, a shipped Playwright script that loads every page × role × viewport of a JSON plan and prints only a compact JSON summary (console errors, failed requests, missing elements; screenshots stay on disk); (3) interactive browsing with an agent browser tool, only on the pages that failed level 2 or that the change creates, under a step budget.

Considered and rejected: gstack `/qa` (fixes and commits on its own, which bypasses `/mra-fix`'s test-first loop; adds Bun and a skill pack with its own conventions) and Playwright MCP for everything (an accessibility snapshot after nearly every action makes it the most expensive option in tokens when multiplied by pages, roles and states).

The runner is Node, not Python: browser automation lives in the Node ecosystem and only repos with a UI need it. ADR-0003 still holds for the installer and `mra-repo`. Which paths of a repo are UI is declared in `mra-flow.toml` (`ui_paths`); how to start the app, log in per role and run the e2e suite is project knowledge kept in `bd memories qa-ui`.
