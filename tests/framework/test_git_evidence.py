from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from obvious_one_plugin_framework.git_evidence import (
    exact_byte_attributes,
    verify_git_evidence,
)


SCOPES = ("plugins/demo", "openclaw/demo")


def _git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, input=input_text, text=True,
        encoding="utf-8", capture_output=True, check=True,
    )


class GitEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        _git(self.repo, "init")
        _git(self.repo, "config", "user.name", "Framework Test")
        _git(self.repo, "config", "user.email", "framework@example.invalid")
        _git(self.repo, "config", "core.autocrlf", "true")
        for scope in SCOPES:
            (self.repo / scope).mkdir(parents=True)
        (self.repo / "plugins/demo/space 名稱.txt").write_bytes(b"one\ntwo\n")
        (self.repo / "openclaw/demo/CONTENT-MANIFEST.json").write_bytes(b"{}\n")
        (self.repo / ".gitattributes").write_text(
            exact_byte_attributes(SCOPES), encoding="utf-8", newline="\n"
        )
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-m", "fixture")

    def test_index_commit_and_fresh_checkout_keep_exact_bytes(self) -> None:
        report = verify_git_evidence(
            self.repo, SCOPES, commit="HEAD", fresh_checkout=True
        )

        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.codes, ())

    def test_staged_and_unstaged_differences_are_distinct(self) -> None:
        path = self.repo / "plugins/demo/space 名稱.txt"
        path.write_bytes(b"staged\n")
        _git(self.repo, "add", "--", "plugins/demo/space 名稱.txt")
        path.write_bytes(b"unstaged\n")

        report = verify_git_evidence(self.repo, SCOPES, commit="HEAD")

        self.assertIn("index_blob_mismatch", report.codes)
        self.assertIn("working_tree_mismatch", report.codes)

    def test_untracked_missing_attribute_and_incomplete_index_are_reported(self) -> None:
        tracked = "openclaw/demo/CONTENT-MANIFEST.json"
        initial_branch = _git(self.repo, "branch", "--show-current").stdout.strip()
        _git(self.repo, "switch", "-c", "other")
        (self.repo / tracked).write_text('{"side":"other"}\n', encoding="utf-8")
        _git(self.repo, "add", "--", tracked)
        _git(self.repo, "commit", "-m", "other side")
        _git(self.repo, "switch", initial_branch)
        (self.repo / tracked).write_text('{"side":"master"}\n', encoding="utf-8")
        _git(self.repo, "add", "--", tracked)
        _git(self.repo, "commit", "-m", "master side")
        merged = subprocess.run(
            ["git", "merge", "other"], cwd=self.repo, text=True,
            encoding="utf-8", capture_output=True, check=False,
        )
        self.assertNotEqual(merged.returncode, 0)
        (self.repo / "plugins/demo/untracked.txt").write_text("new\n", encoding="utf-8")
        (self.repo / ".gitattributes").write_text("# missing exact-byte rules\n", encoding="utf-8")
        staged_state = _git(self.repo, "ls-files", "--stage", "--", tracked).stdout
        self.assertIn(f" 1\t{tracked}", staged_state)

        report = verify_git_evidence(self.repo, SCOPES, commit="HEAD")

        self.assertIn("untracked_artifact", report.codes)
        self.assertIn("exact_byte_attribute_missing", report.codes)
        self.assertIn("incomplete_index_entry", report.codes)

    def test_verification_does_not_modify_repository(self) -> None:
        before = self._tree()

        verify_git_evidence(self.repo, SCOPES, commit="HEAD", fresh_checkout=True)

        self.assertEqual(self._tree(), before)

    def test_exact_byte_attributes_are_sorted_and_scoped(self) -> None:
        self.assertEqual(
            exact_byte_attributes(("openclaw/demo/", "plugins/demo", "plugins/demo")),
            "/openclaw/demo/** -text whitespace=cr-at-eol\n"
            "/plugins/demo/** -text whitespace=cr-at-eol\n",
        )

    def test_explicit_legacy_eol_policy_is_deterministic_evidence(self) -> None:
        (self.repo / ".gitattributes").write_text(
            "/openclaw/demo/** text eol=lf\n"
            "/plugins/demo/** text eol=lf\n",
            encoding="utf-8",
            newline="\n",
        )
        _git(self.repo, "add", ".gitattributes")

        report = verify_git_evidence(self.repo, SCOPES)

        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.codes, ())

    def _tree(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.repo).as_posix(): path.read_bytes()
            for path in sorted(self.repo.rglob("*"))
            if path.is_file() and ".git" not in path.relative_to(self.repo).parts
        }


if __name__ == "__main__":
    unittest.main()
