# Model display

The user always sees which model does the work: the model running the phase, and the model of every subagent the phase dispatches. Every `mra-*` skill follows this rule.

## The model line

One line, as plain text: `Model: <model> (<role>)`, with the model's friendly name (`Opus 5.5`, `Sonnet 5.5`, `Haiku 5.5`), never a bare tier word or an id alone.

- `<role>` is `session` for the model the session itself runs on, otherwise the subagent's role: `implementer`, `reviewer`, `final review`, `explorer`, `research`, `qa-ui`, … A subagent dispatched with no explicit model inherits the session's: say so, `Model: Opus 5.5 (reviewer, inherited)`.
- Several subagents in flight on different models: one line, comma-separated, `Model: Sonnet 5.5 (implementer), Opus 5.5 (final review hub)`.

## When

- **Phase start:** the first message of the phase carries `Model: <model> (session)`.
- **Every dispatch:** before or with each subagent dispatch, the model line of that subagent. Never dispatch silently on a model the user has not been told about.
- **Every change:** whenever the model in use changes (another role takes over, a fix round escalates to a more capable model, the user switches the session model with `/model` or fast mode), the next message carries the new model line.
- Repeated messages on the same model need no new line, except where a skill prints the line in a fixed block (the `/mra-build` progress block prints it every time).

## Record

The models also stay on the issue they worked on, after the conversation is gone: when a phase closes an issue (or records its outcome on the epic), it sets one metadata key with every model that did work on it, in the order they worked:

`bd update <id> --set-metadata models="implementer=Sonnet 5.5; reviewer=Sonnet 5.5; fix 1=Opus 5.5; re-review 1=Sonnet 5.5"`

- Roles as in the model line; a role that ran several times on the same model is listed once, with a count (`reviewer=Sonnet 5.5 ×2`); work done by the controller itself, with no subagent, is `session=<model>`.
- The token and time breakdown per task and model comes from `.mra-flow/bin/mra-effort breakdown <change-id>`, which `/mra-archive` runs at the end.
- `bd show <id>` prints it; `bd list --json` carries it in `metadata.models`.
- Where it is written: `/mra-build` on each task issue at close and on the epic for the final reviews (`final review <key>=...`), `/mra-fix` and `/mra-hotfix` on each bug they close, `/mra-verify` on the epic for its own run (`verify=...`, `qa-ui=...`).

## Where else it shows

- The **status line** (`statusLine` in the user's `settings.json`) gets the session's model in its JSON input (`.model.display_name`), so it can show the session model; it does not get the subagents' models.
- The **agent panel** (`subagentStatusLine`) gets one row per running subagent with that subagent's own `model`, and can show it next to the subagent's label.
- Both are user-level configuration, outside mra-flow: mra-flow neither installs nor edits them. The model line in the conversation is the one place mra-flow guarantees.
