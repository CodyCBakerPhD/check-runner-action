#!/bin/bash
# Prints "true" when a self-hosted runner of the repository or organization is online and carries every label,
# and "false" otherwise. Exits non-zero when the runners cannot be listed, so that is never mistaken for offline.
set -uo pipefail

if [ $# -ne 2 ] || [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <owner/repo or organization> <comma-separated labels>" >&2
  exit 2
fi
scope="$1"
labels="$2"

if [[ "$scope" == */* ]]; then
  endpoint="repos/$scope/actions/runners"
else
  endpoint="orgs/$scope/actions/runners"
fi

# A page holds 30 runners by default, so an organization with more would otherwise lose the rest.
if ! response=$(gh api --paginate "$endpoint"); then
  echo "Error: could not list the runners at $endpoint." >&2
  exit 1
fi

# Labels compare whole. `contains` would match a substring, so `dandi` would accept a runner labelled `dandi-old`.
echo "$response" | jq --raw-output --slurp --arg labels "$labels" '
  ($labels | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0))) as $required
  | [.[].runners[] | select(.status == "online") | select(($required - [.labels[].name]) | length == 0)]
  | if length > 0 then "true" else "false" end
'
