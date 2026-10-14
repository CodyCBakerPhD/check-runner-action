# Agent instructions

## What this repository is

A GitHub Action that fails a job unless a self-hosted runner carrying every given label is online. It is
meant to run first, on a GitHub-hosted runner, so a workflow whose self-hosted runner is offline fails at
once rather than waiting in the queue.

## Versioning

- `VERSION` holds the tag this tree is meant to be published under, and is the only place that tag is
  decided. The tests read it rather than a literal, so a reference left on the previous tag fails before
  the commit lands.
- Every reference to this repository in the README names that tag. Bump `VERSION` in the same commit that
  rewrites them.
- Cut a new major tag when the action's inputs or behaviour change incompatibly.
- Release by publishing the draft that `Prepare release draft` keeps on every merge to `main`. Its tag name
  comes from `VERSION` and its target from that commit, so the tag is never typed. It prepares nothing when
  the tag already exists, since moving a published tag is a deliberate act rather than a release.
- The `action-versions-agree` pre-commit hook runs the tests, so a drift between the references and
  `VERSION` fails at commit time rather than in CI.

## Interface

- Every value the action uses arrives as an input. It never reads `${{ env.* }}` from the calling workflow.
- Inputs reach `run:` bodies through `env:`, never interpolated into the script. The token in particular
  reaches the GitHub CLI only as `GH_TOKEN`.
- A composite action does not enforce `required`. Check a required input before using it.
- Failing to list the runners is an error, never a report that they are offline.

## Code style

- Avoid excessive em-dashes, colons, and semicolons in written text such as documentation. Prefer
  breaking into separate, shorter sentences instead.
- Keep inline comments sparse. Only explain non-obvious "why", not "what" the code does.

## Tests

- Run `pytest` before pushing, and `pre-commit run --all-files`.
- The script's tests put a stub `gh` first on `PATH`. They need `jq`, which GitHub-hosted runners provide.
- Follow assertion style: actual on left, expected on right.
- Always mark AI-generated tests with the `ai_generated` pytest marker.
