#!/usr/bin/env python3
"""Classify Claude Code Bash hook input as allowed or blocked."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Iterator, Sequence


BLOCKED_EXIT = 2
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORS = frozenset(";&|()")


def reject(code: str, detail: str) -> int:
    print(f"{code}: {detail}", file=sys.stderr)
    return BLOCKED_EXIT


def command_segments(command: str) -> Iterator[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.commenters = ""
    lexer.whitespace_split = True
    segment: list[str] = []

    for token in lexer:
        if token and all(character in SEPARATORS for character in token):
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


def git_arguments(segment: Sequence[str]) -> list[str] | None:
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

    if index >= len(segment) or os.path.basename(segment[index]) != "git":
        return None
    return list(segment[index + 1 :])


def split_git_subcommand(arguments: Sequence[str]) -> tuple[str | None, list[str]]:
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
        return argument, list(arguments[index + 1 :])

    if index < len(arguments):
        return arguments[index], list(arguments[index + 1 :])
    return None, []


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

    try:
        segments = command_segments(command)
        for segment in segments:
            arguments = git_arguments(segment)
            if arguments is None:
                continue
            subcommand, subcommand_arguments = split_git_subcommand(arguments)
            reason = block_reason(subcommand, subcommand_arguments)
            if reason:
                return reject("GIT_GUARDRAIL_BLOCKED", f"{reason}: {command}")
    except ValueError:
        return reject("GIT_GUARDRAIL_INPUT_ERROR", "malformed-command")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
