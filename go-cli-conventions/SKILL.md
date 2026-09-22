---
name: go-cli-conventions
description: Use when creating, extending, or reviewing Go 1.24+ command-line applications, especially Cobra commands, flags, exit behavior, configuration, and testable CLI boundaries.
---

# Go CLI Conventions

## Overview

Keep the command layer thin: parse user input, call ordinary Go code, render results. Cobra wiring must not own business logic or terminate the process below `main`.

## When to use

- Adding a Cobra root command, subcommand, flag, or completion.
- Designing exit codes, stdout/stderr behavior, config precedence, or cancellation.
- Testing a Go CLI without spawning its binary for every case.
- Reviewing command code for hidden global state or untestable I/O.

## Core pattern

1. Build commands with constructors such as `NewRoot(deps Dependencies) *cobra.Command`.
2. Bind flags to command-local option structs, not package globals.
3. Use `RunE`; validate arguments with `Args` or an explicit validator.
4. Put behavior in functions returning values/errors.
5. Inject filesystem, clock, environment, and writers where determinism matters.
6. Let `main` translate the returned error into the process exit status.

```go
type ValidateOptions struct {
	Config string
}

func newValidateCmd(out io.Writer, run func(ValidateOptions) error) *cobra.Command {
	var opts ValidateOptions
	cmd := &cobra.Command{
		Use:          "validate",
		Args:         cobra.NoArgs,
		SilenceUsage: true,
		RunE: func(_ *cobra.Command, _ []string) error {
			return run(opts)
		},
	}
	cmd.SetOut(out)
	cmd.Flags().StringVarP(&opts.Config, "config", "c", "", "pivot file")
	return cmd
}
```

## Quick reference

| Concern | Convention |
|---|---|
| Errors | Wrap with operation context; preserve sentinels with `%w` |
| Usage | Show for syntax errors, suppress for runtime failures |
| Output | Results to stdout; diagnostics to stderr |
| Context | Use `cmd.Context()` for I/O and cancellation |
| Config | Explicit flag > environment > discovered/default file |
| Tests | Execute command with injected writers and dependencies |
| Version | Keep build metadata injectable through `-ldflags` |

## Common mistakes

- Calling `os.Exit`, `log.Fatal`, or `panic` in commands: return an error instead.
- Reading global environment during package initialization: resolve it at execution time.
- Sharing mutable option variables across command instances: constructors must return independent trees.
- Printing an error and returning it: choose one owner to avoid duplicate diagnostics.
- Testing only helpers: execute the Cobra command to cover parsing and routing.
