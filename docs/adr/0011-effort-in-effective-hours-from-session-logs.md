# Effort is measured in effective hours from the Claude Code session logs

ADR-0010 sized roadmap slices in person-days and took a slice's actual from the distinct dates of its commits. A day with one commit and a day of full work counted the same, and the time spent grilling, verifying or waiting on reviews left no commit at all, so the actuals could not tell anyone how long a slice really took or check an estimate. We measure effort in **effective hours**: the time the agent or the user was active on a change, read from this orchestrator's Claude Code session logs (each session with its subagents). An interval between two timestamped events counts when it is at most 10 minutes long, so nights, a suspended laptop and long waits drop out, and it goes to the phase of the `/mra-*` command in progress when that command names the change. `.mra-flow/bin/mra-effort` does the arithmetic (`measure`, `record`, `report`): the per-phase figures are confirmed by the user at `/mra-archive`, written into the roadmap, and `docs/roadmap/<initiative>-effort.md` is regenerated with the variance of each done slice against the **upper bound** of its original estimate (red over, green within) and the hours per phase.

## Considered Options

- **Keep active days from commit dates.** Rejected: too coarse to compare with an estimate, and blind to the phases that commit nothing.
- **Ask the user for the hours.** Rejected as the source: nobody tracks them; the user still confirms or corrects the measured figure, because some work happens outside a session or under no command.
- **Let the agent compute totals and variances from the skill text.** Rejected: agent arithmetic drifts; a script keeps the figures repeatable and testable.
- **Variance against the midpoint of the range.** Rejected by the user: the upper bound is the figure an estimate promises not to exceed.

## Consequences

- Roadmap columns are *Estimate (h)*, *Revised (h)*, *Actual (h)*; the default size scale is S 2–4, M 4–8, L 8–14, XL > 14 hours. `mra-effort` refuses a roadmap still in days: convert it by hand once.
- The measure depends on the Claude Code log layout (`projects/<orchestrator path>/*.jsonl`, `<session>/subagents/*.jsonl`, `timestamp`, `<command-name>`/`<command-args>`); a change in that layout breaks `measure`, not the roadmap.
- Work done under no command, or under a command that does not name the change (a grill topic, a hotfix id), is listed as unattributed for the user to assign, or counted with `--alias`.
- Parallel sessions are summed, so overlapping work counts twice; in practice the overlap is small and the user can correct the figure.
- Each slice epic carries the upper bound of its current range as its beads estimate (`--estimate`, minutes), so `bd show` and `bd list` show it; the variance report shows the original range next to the upper bound it compares against (0.1.32).
