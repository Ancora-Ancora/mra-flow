# A project can replace branch integration with its own command

`/mra-archive` and `/mra-hotfix` integrate each repo's branch through `superpowers:finishing-a-development-branch` (merge locally, push + PR, keep), which assumes the host's conventions (a `gh`-style PR, a local merge being acceptable). Some projects integrate differently: QCP, for one, always goes through a pull request into `develop` on Bitbucket, merged with a merge commit and verified from git before pulling. A project declares that once, as `[integration] command` in `mra-flow.toml`; `mra-repo integrate <key> <branch>` runs it from the orchestrator root as `<command> <key> <repo-path> <branch>`, and the two skills then offer only "integrate with the project command" or "keep". The command reports the outcome (merge sha or PR url) on its last output line and fails with a non-zero exit, which the skills report without retrying.

## Considered Options

- **Each project edits its installed `mra-archive`/`mra-hotfix`.** Rejected: an edited package file stops receiving updates (ADR-0002), and the integration rule is project data, not workflow text.
- **Built-in support for each host (GitHub, Bitbucket, GitLab).** Rejected: the package would have to own API credentials and merge policies it cannot know; a command keeps those in the project.

## Consequences

- Without `[integration]` nothing changes: the skills still use `finishing-a-development-branch`.
- The command owns everything host-specific (credentials, PR title, merge strategy, pulling the integration branch afterwards); the package only passes the repo and the branch.
