# UI preview: see a screen before it is specified

Rule shared by `/mra-roadmap`, `/mra-grill`, `/mra-propose`, `/mra-update`, `/mra-prototype` and `/mra-qa-ui`. Goal: the user sees and tries every UI change before it is specified, so nothing about a screen is a surprise once the epic or slice is built. A prototype shows shape and interaction, not real data (long lists, long translations, real errors, mobile): `/mra-qa-ui` still checks those after the build.

## Which preview a change gets

Look at each screen the change adds or modifies in a repo's `ui_paths` (`.mra-flow/bin/mra-repo ui-paths <key>`). A change that touches no `ui_paths` gets no preview.

| The change brings | Preview | Cost |
|---|---|---|
| a new route or screen; a new navigation element (menu, header, layout); a new interaction pattern, one the app does not have yet (dropdown menu, wizard, modal with its own flow, a form split into sections saved separately) | **prototype**: `/mra-prototype <question>` | a throwaway branch, minutes to an hour |
| a change to an existing screen only (a field, a column, a validation rule, a text, a reordering) | **sketch**: an ASCII mockup of the screen after the change, in a question with a `preview` (AskUserQuestion), or a screenshot of the current screen with the change marked | seconds, no branch |
| no visible change (logic, data, copy outside the screens) | none | - |

When one change brings both, the prototype covers the new parts and a sketch the rest. The user can decline any preview, as with the drift check; a declined preview is recorded, never asked again.

## Where it is asked

- `/mra-roadmap`, only to name each slice's preview (its *UI preview* cell), and to recommend a prototype early when the answer changes how the work is cut or sized (`.mra-flow/docs/agents/roadmap.md`).
- `/mra-grill`, before the close summary: the main point; for a roadmap slice whose prototype is already done, it reuses that note.
- `/mra-propose`, preflight: safety net for a change that skipped the grill or closed it early.
- `/mra-update`, when a revision adds a screen or pattern that needs a prototype.

Never in `/mra-build`: once tasks and a plan exist, a preview means redoing specs and plan.

## How it is recorded

Every new or changed screen ends with exactly one of these lines, in the grill close summary and then in the `## UI` section of `design.md`:

- `preview: prototype docs/prototypes/<slug>.md` — a prototype verdict;
- `preview: sketch accepted` — a sketch the user accepted (the sketch itself goes into `design.md` under the screen, as an ASCII block);
- `preview: declined (<reason>)` — the user declined.

## The prototype note

`/mra-prototype` writes `docs/prototypes/<slug>.md` at the orchestrator root as soon as the user states the verdict, before anything else, so no verdict lives only in the conversation:

```markdown
# <question ending in ?>

- Verdict: <the choice, e.g. "variant B: email dropdown with My profile and Sign out">
- Why: <the user's reason>
- Branch: <key> `prototype/<slug>` at `<sha>`
- Screens: <route> - <what the user sees>, one line each
- Screenshots: `docs/prototypes/<slug>/<n>-<screen>-<viewport>.png`
- Recorded as: ADR `docs/.../adr/NNNN-...md` | carried decision for `<change-id>`
```

Screenshots are taken from the accepted prototype for each screen it covers, `desktop` and, when the screen is used on phones, `mobile`. `/mra-propose` and `/mra-update` read the note and cite it in `design.md`; `/mra-qa-ui` uses its screenshots as the visual reference of those screens.
