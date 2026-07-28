#!/usr/bin/env bash
set -euo pipefail

readonly tests_dir="${BASH_SOURCE[0]%/*}"
readonly skill_dir="${tests_dir%/*}"
readonly hook="${skill_dir}/scripts/block-dangerous-git.sh"

failures=0
checks=0

payload_for() {
  python3 -c 'import json, sys; print(json.dumps({"tool_input": {"command": sys.argv[1]}}))' "$1"
}

record_failure() {
  printf '[FAIL] %s\n' "$1" >&2
  failures=$((failures + 1))
}

run_fixtures() {
  local fixture_file="$1"
  local expected_status="$2"
  local expected_code="$3"
  local command payload output status

  while IFS= read -r command || [[ -n "$command" ]]; do
    [[ -z "$command" || "$command" == \#* ]] && continue
    checks=$((checks + 1))
    payload=$(payload_for "$command")

    set +e
    output=$(printf '%s' "$payload" | "$hook" 2>&1)
    status=$?
    set -e

    if [[ "$status" -ne "$expected_status" ]]; then
      record_failure "${command}: expected exit ${expected_status}, got ${status}: ${output}"
      continue
    fi
    if [[ -n "$expected_code" && "$output" != *"$expected_code"* ]]; then
      record_failure "${command}: missing ${expected_code}: ${output}"
    fi
  done < "$fixture_file"
}

run_invalid_input_case() {
  local name="$1"
  local payload="$2"
  local output status

  checks=$((checks + 1))
  set +e
  output=$(printf '%s' "$payload" | "$hook" 2>&1)
  status=$?
  set -e

  if [[ "$status" -ne 2 || "$output" != *"GIT_GUARDRAIL_INPUT_ERROR"* ]]; then
    record_failure "${name}: expected fail-closed exit 2, got ${status}: ${output}"
  fi
}

run_without_jq() {
  local python_path temp_dir payload output status
  python_path=$(command -v python3)
  temp_dir=$(mktemp -d)
  ln -s "$python_path" "$temp_dir/python3"
  payload=$(payload_for 'git push origin main')

  checks=$((checks + 1))
  set +e
  output=$(printf '%s' "$payload" | PATH="$temp_dir" /bin/bash "$hook" 2>&1)
  status=$?
  set -e

  rm "$temp_dir/python3"
  rmdir "$temp_dir"

  if [[ "$status" -ne 2 || "$output" != *"GIT_GUARDRAIL_BLOCKED"* ]]; then
    record_failure "missing jq: expected blocked exit 2, got ${status}: ${output}"
  fi
}

run_fixtures "$tests_dir/blocked.txt" 2 'GIT_GUARDRAIL_BLOCKED'
run_fixtures "$tests_dir/allowed.txt" 0 ''
run_invalid_input_case 'malformed JSON' '{not-json'
run_invalid_input_case 'missing command' '{"tool_input":{}}'
run_without_jq

if [[ "$failures" -ne 0 ]]; then
  printf '%s/%s guardrail checks failed\n' "$failures" "$checks" >&2
  exit 1
fi

printf '%s guardrail checks passed\n' "$checks"
