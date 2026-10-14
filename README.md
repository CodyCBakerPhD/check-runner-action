# check-runner-action

GitHub Action for checking if a self-hosted runner is online.

A job queued for a self-hosted runner that is offline waits, silently, until the runner returns or the job times out. Run this first on a GitHub-hosted runner to fail fast instead:

```yaml
jobs:
  CheckRunner:
    runs-on: ubuntu-latest
    steps:
      - uses: CodyCBakerPhD/check-runner-action@v1
        with:
          labels: typhon,dandi
          token: ${{ secrets.RUNNER_STATUS_TOKEN }}

  Work:
    needs: CheckRunner
    runs-on: [self-hosted, typhon, dandi]
    steps:
      - run: echo "The runner is online."
```

The job fails unless at least one runner is online and carries every label. Labels compare whole, so `dandi` is not satisfied by `dandi-old`.

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `labels` | yes | | Comma-separated labels the runner must carry. For example, `typhon,dandi`. |
| `token` | yes | | Token that can list the self-hosted runners of `scope`. See [Token](#token). |
| `scope` | no | the calling repository | Repository (`owner/repo`) or organization whose self-hosted runners are listed. |

Set `scope` to the organization when the runner is registered there rather than to the repository.

## Token

The workflow's own `GITHUB_TOKEN` cannot list self-hosted runners, so the action needs a personal access token.

- **Runner registered to a repository.** A fine-grained token with `Administration: Read-only` on that repository.
- **Runner registered to an organization.** A fine-grained token with the organization permission `Self-hosted runners: Read-only`.

A classic token needs the `repo` scope for a repository, or `admin:org` for an organization.
