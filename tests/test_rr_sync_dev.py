from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
RR_SCRIPT = ROOT / "private-skills" / "[REMOVED-INTERNAL-SKILL]" / "rr.zsh"


@unittest.skipUnless(shutil.which("zsh") and shutil.which("git"), "zsh and git are required")
class RrSyncDevTests(unittest.TestCase):
    def run_rr(
        self,
        repository: Path,
        *arguments: str,
        environment_overrides: dict[str, str] | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = 'source "$1"; shift; rr "$@"'
        environment = os.environ.copy()
        environment.update({
            "RR_DEFAULT_PROJECT": "default-project",
            "RR_REMOTE_HOST": "example.invalid",
            "RR_REMOTE_PROJECT_ROOT": "/srv/projects",
        })
        environment.update(environment_overrides or {})
        return subprocess.run(
            ["zsh", "-f", "-c", command, "rr-test", str(RR_SCRIPT), *arguments],
            cwd=repository,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            input=input_text,
        )

    def initialise_repository(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=root, check=True)

    def test_positionals_are_files_and_project_option_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            (root / "one file.txt").write_text("one", encoding="utf-8")
            (root / "deux.txt").write_text("two", encoding="utf-8")
            result = self.run_rr(root, "--dry-run", "--project", "chosen", "one file.txt", "deux.txt", "one file.txt")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Project: chosen", result.stdout)
            self.assertIn("one file.txt", result.stdout)
            self.assertIn("deux.txt", result.stdout)
            self.assertEqual(1, result.stdout.count(" - one file.txt"))

    def test_unknown_option_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            result = self.run_rr(root, "--unknown")
            self.assertEqual(2, result.returncode)
            self.assertIn("Unknown option", result.stderr)

    def test_project_cannot_escape_remote_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            result = self.run_rr(root, "--dry-run", "--project", "..")
            self.assertEqual(2, result.returncode)
            self.assertIn("Invalid project name", result.stderr)

    def test_no_argument_mode_requires_a_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_rr(Path(temporary), "--dry-run")
            self.assertEqual(2, result.returncode)
            self.assertIn("Git working tree required", result.stderr)

    def test_rsync_operands_are_protected_from_option_and_remote_shell_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            filename = "-danger name.txt"
            (root / filename).write_text("content", encoding="utf-8")
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            log = root / "rsync-arguments"
            fake_rsync = fake_bin / "rsync"
            fake_rsync.write_text(
                "#!/bin/sh\nprintf '%s\\0' \"$@\" > \"$RR_TEST_LOG\"\n",
                encoding="utf-8",
            )
            fake_rsync.chmod(0o755)
            result = self.run_rr(
                root,
                "--",
                filename,
                environment_overrides={
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                    "RR_TEST_LOG": str(log),
                },
                input_text="y\n",
            )
            self.assertEqual(0, result.returncode, result.stderr)
            arguments = log.read_bytes().decode().split("\0")[:-1]
            self.assertIn("--", arguments)
            self.assertEqual(filename, Path(arguments[-2]).name)
            self.assertIn(r"-danger\ name.txt", arguments[-1])

    def test_git_paths_are_resolved_from_repository_root_when_called_in_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            subdirectory = root / "sub"
            subdirectory.mkdir()
            (subdirectory / "unicode é.txt").write_text("content", encoding="utf-8")
            result = self.run_rr(subdirectory, "--dry-run")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("sub/unicode é.txt", result.stdout)

    def test_explicit_file_must_stay_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            root.mkdir()
            self.initialise_repository(root)
            outside = root.parent / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            result = self.run_rr(root, "--dry-run", "../outside.txt")
            self.assertEqual(2, result.returncode)
            self.assertIn("outside Git working tree", result.stderr)

    def test_rsync_failure_is_propagated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            (root / "file.txt").write_text("content", encoding="utf-8")
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            fake_rsync = fake_bin / "rsync"
            fake_rsync.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
            fake_rsync.chmod(0o755)
            result = self.run_rr(
                root,
                "file.txt",
                environment_overrides={"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
                input_text="y\n",
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("rsync failed", result.stderr)

    def test_git_status_handles_rename_spaces_unicode_and_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialise_repository(root)
            old = root / "old name.txt"
            deleted = root / "deleted.txt"
            old.write_text("old", encoding="utf-8")
            deleted.write_text("gone", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            old.rename(root / "nouveau é.txt")
            deleted.unlink()
            (root / "space file.txt").write_text("new", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "-z"],
                cwd=root,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout
            self.assertIn("nouveau é.txt".encode(), status)

            result = self.run_rr(root, "--dry-run")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stderr)
            self.assertIn("nouveau é.txt", result.stdout)
            self.assertIn("space file.txt", result.stdout)
            self.assertIn("Deleted files are reported but not removed remotely", result.stdout)
            self.assertNotIn("old name.txt", result.stdout)
