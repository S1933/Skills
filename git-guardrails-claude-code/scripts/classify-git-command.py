#!/usr/bin/env python3
"""Classify Claude Code Bash hook input as allowed or blocked."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Iterator, Sequence
from typing import NamedTuple


BLOCKED_EXIT = 2
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORS = frozenset(";&|()")
MAX_WRAPPER_DEPTH = 8


class Decision(NamedTuple):
    code: str
    detail: str


def reject(code: str, detail: str) -> int:
    print(f"{code}: {detail}", file=sys.stderr)
    return BLOCKED_EXIT


def command_segments(command: str) -> Iterator[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()$`")
    lexer.commenters = ""
    lexer.whitespace_split = True
    segment: list[str] = []

    for token in lexer:
        if token and all(character in SEPARATORS | {"$", "`"} for character in token):
            if segment:
                yield segment
                segment = []
            continue
        segment.append(token)

    if segment:
        yield segment


def skip_env_prefix(tokens: Sequence[str], index: int) -> int:
    index += 1
    options_with_value = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}

    while index < len(tokens):
        token = tokens[index]
        if ASSIGNMENT.match(token):
            index += 1
        elif token in options_with_value:
            index += 2
        elif token == "--":
            index += 1
            break
        elif token.startswith("-"):
            index += 1
        else:
            break
    return index


def executable_index(segment: Sequence[str]) -> int | None:
    index = 0
    while index < len(segment) and ASSIGNMENT.match(segment[index]):
        index += 1

    while index < len(segment):
        executable = os.path.basename(segment[index])
        if executable == "command":
            index += 1
            if index < len(segment) and segment[index] in {"-v", "-V"}:
                return None
            while index < len(segment) and segment[index] in {"-p", "--"}:
                index += 1
            continue
        if executable == "env":
            index = skip_env_prefix(segment, index)
            continue
        break

    return index


def git_arguments(segment: Sequence[str]) -> list[str] | None:
    index = executable_index(segment)

    if index is None or index >= len(segment) or os.path.basename(segment[index]) != "git":
        return None
    return list(segment[index + 1 :])


def split_git_subcommand(arguments: Sequence[str]) -> tuple[str | None, list[str], int]:
    index = 0
    options_with_value = {
        "-C",
        "-c",
        "--config-env",
        "--exec-path",
        "--git-dir",
        "--namespace",
        "--super-prefix",
        "--work-tree",
    }

    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            index += 1
            break
        if argument in options_with_value:
            index += 2
            continue
        if argument.startswith("-C") and argument != "-C":
            index += 1
            continue
        if any(argument.startswith(f"{option}=") for option in options_with_value if option.startswith("--")):
            index += 1
            continue
        if argument.startswith("-"):
            index += 1
            continue
        return argument, list(arguments[index + 1 :]), index

    if index < len(arguments):
        return arguments[index], list(arguments[index + 1 :]), index
    return None, [], index


def has_short_option(arguments: Sequence[str], option: str) -> bool:
    return any(
        argument.startswith("-")
        and not argument.startswith("--")
        and option in argument[1:]
        for argument in arguments
    )


def block_reason(subcommand: str | None, arguments: Sequence[str]) -> str | None:
    if subcommand == "push":
        if "--dry-run" in arguments or has_short_option(arguments, "n"):
            return None
        return "push"

    if subcommand == "reset" and "--hard" in arguments:
        return "reset-hard"

    if subcommand == "clean":
        if "--dry-run" in arguments or has_short_option(arguments, "n"):
            return None
        if "--force" in arguments or has_short_option(arguments, "f"):
            return "clean-force"

    if subcommand == "branch":
        if has_short_option(arguments, "D"):
            return "branch-force-delete"
        if "--delete" in arguments and (
            "--force" in arguments or has_short_option(arguments, "f")
        ):
            return "branch-force-delete"

    if subcommand in {"checkout", "restore"} and "." in arguments:
        return f"{subcommand}-working-tree"

    return None


def shell_payload(segment: Sequence[str]) -> str | None:
    """Return code executed by a supported shell wrapper, if present."""
    index = executable_index(segment)
    if index is None or index >= len(segment):
        return None
    executable = os.path.basename(segment[index])
    if executable == "eval":
        arguments = list(segment[index + 1 :])
        if arguments[:1] == ["--"]:
            arguments = arguments[1:]
        return " ".join(arguments)
    if executable not in {"bash", "dash", "sh", "zsh"}:
        return None
    for argument_index, argument in enumerate(segment[index + 1 :], start=index + 1):
        if argument == "-c" or (
            argument.startswith("-") and not argument.startswith("--") and "c" in argument[1:]
        ):
            payload_index = argument_index + 1
            if payload_index < len(segment) and segment[payload_index] == "--":
                payload_index += 1
            return segment[payload_index] if payload_index < len(segment) else ""
    return None


def alias_key_matches(key: str, subcommand: str) -> bool:
    section, separator, alias_name = key.partition(".")
    return bool(
        separator
        and section.lower() == "alias"
        and alias_name.lower() == subcommand.lower()
    )


def executable_alias(
    global_arguments: Sequence[str], subcommand: str | None, subcommand_arguments: Sequence[str]
) -> tuple[str | None, bool]:
    """Return the shell body of a matching `git -c alias.NAME=!… NAME` alias."""
    if subcommand is None:
        return None, False
    index = 0
    selected: str | None = None
    opaque = False
    while index < len(global_arguments):
        argument = global_arguments[index]
        value: str | None = None
        config_env: str | None = None
        if argument == "-c" and index + 1 < len(global_arguments):
            value = global_arguments[index + 1]
            index += 2
        elif argument == "--config-env" and index + 1 < len(global_arguments):
            config_env = global_arguments[index + 1]
            index += 2
        elif argument.startswith("--config-env="):
            config_env = argument.split("=", 1)[1]
            index += 1
        else:
            index += 1
        if config_env is not None and "=" in config_env:
            key = config_env.split("=", 1)[0]
            if alias_key_matches(key, subcommand):
                selected = None
                opaque = True
        if value is not None and "=" in value:
            key, alias_value = value.split("=", 1)
            if alias_key_matches(key, subcommand):
                selected = alias_value
                opaque = False
    if opaque:
        return None, True
    if selected is None:
        return None, False
    if selected.startswith("!"):
        return selected[1:], False
    prefix = shlex.join(list(global_arguments))
    suffix = shlex.join(list(subcommand_arguments))
    return " ".join(part for part in ("git", prefix, selected, suffix) if part), False


def has_opaque_env_split(segment: Sequence[str]) -> bool:
    index = 0
    while index < len(segment) and ASSIGNMENT.match(segment[index]):
        index += 1
    while index < len(segment) and os.path.basename(segment[index]) == "command":
        index += 1
        while index < len(segment) and segment[index] in {"-p", "--"}:
            index += 1
    if index >= len(segment) or os.path.basename(segment[index]) != "env":
        return False
    return any(
        argument in {"-S", "--split-string"}
        or argument.startswith("-S")
        or argument.startswith("--split-string=")
        for argument in segment[index + 1 :]
    )


def classify_command(command: str, depth: int = 0) -> Decision | None:
    """Apply syntax extraction first, then the destructive-Git policy."""
    if depth > MAX_WRAPPER_DEPTH:
        return Decision("GIT_GUARDRAIL_INPUT_ERROR", "wrapper-depth-exceeded")
    try:
        for segment in command_segments(command):
            if has_opaque_env_split(segment):
                return Decision("GIT_GUARDRAIL_BLOCKED", "opaque-env-split")
            payload = shell_payload(segment)
            if payload is not None:
                if not payload:
                    return Decision("GIT_GUARDRAIL_INPUT_ERROR", "opaque-shell-wrapper")
                decision = classify_command(payload, depth + 1)
                if decision:
                    return decision

            arguments = git_arguments(segment)
            if arguments is None:
                continue
            subcommand, subcommand_arguments, subcommand_index = split_git_subcommand(arguments)
            alias_payload, opaque_alias = executable_alias(
                arguments[:subcommand_index], subcommand, subcommand_arguments
            )
            if opaque_alias:
                return Decision("GIT_GUARDRAIL_BLOCKED", "opaque-alias-config-env")
            if alias_payload is not None:
                decision = classify_command(alias_payload, depth + 1)
                if decision:
                    return decision
            reason = block_reason(subcommand, subcommand_arguments)
            if reason:
                return Decision("GIT_GUARDRAIL_BLOCKED", reason)
    except ValueError:
        return Decision("GIT_GUARDRAIL_INPUT_ERROR", "malformed-command")
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return reject("GIT_GUARDRAIL_INPUT_ERROR", "malformed-json")

    try:
        command = payload["tool_input"]["command"]
    except (KeyError, TypeError):
        return reject("GIT_GUARDRAIL_INPUT_ERROR", "missing-command")

    if not isinstance(command, str) or not command.strip():
        return reject("GIT_GUARDRAIL_INPUT_ERROR", "invalid-command")

    decision = classify_command(command)
    if decision:
        detail = decision.detail
        if decision.code == "GIT_GUARDRAIL_BLOCKED":
            detail = f"{detail}: {command}"
        return reject(decision.code, detail)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
