#!/bin/bash
set -euo pipefail

readonly script_dir="${BASH_SOURCE[0]%/*}"
readonly classifier="${script_dir}/classify-git-command.py"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'GIT_GUARDRAIL_INPUT_ERROR: python3-unavailable' >&2
  exit 2
fi

if [[ ! -r "$classifier" ]]; then
  printf '%s\n' 'GIT_GUARDRAIL_INPUT_ERROR: classifier-unavailable' >&2
  exit 2
fi

exec python3 "$classifier"
