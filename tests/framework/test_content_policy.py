from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.content_policy import (
    ContentPolicyError,
    ResolvedContentPolicy,
    resolve_content_policies,
    write_canonical_file,
)
from obvious_one_plugin_framework.contract import (
    ContentRule,
    RedistributionEvidence,
    load_contract,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ContentPolicyTests(unittest.TestCase):
    def contract(self):
        return load_contract(FIXTURES / "plugin-v3" / "distribution.json")

    def test_unclassified_and_ambiguous_paths_block(self) -> None:
        contract = self.contract()
        with self.assertRaisesRegex(ContentPolicyError, "unclassified_files"):
            resolve_content_policies(contract, ("README.md", "new.txt"))

        overlapping = replace(
            contract,
            content_rules=contract.content_rules
            + (
                ContentRule(
                    "also-readme",
                    ("README.md",),
                    (),
                    "text",
                    RedistributionEvidence("approved", "docs/source-decisions.md"),
                ),
            ),
        )
        with self.assertRaisesRegex(ContentPolicyError, "ambiguous_file_classification"):
            resolve_content_policies(overlapping, ("README.md",))

    def test_text_is_lf_binary_is_exact_and_bom_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            text_source = root / "text-source"
            text_output = root / "text-output"
            binary_source = root / "binary-source"
            binary_output = root / "binary-output"
            text_policy = ResolvedContentPolicy("text", "text", "utf8-lf", "test")
            binary_policy = ResolvedContentPolicy("binary", "binary", "exact", "test")

            text_source.write_bytes(b"one\r\ntwo\rthree")
            write_canonical_file(text_source, text_output, text_policy)
            self.assertEqual(text_output.read_bytes(), b"one\ntwo\nthree")

            binary_source.write_bytes(b"\x00\r\n\xff")
            write_canonical_file(binary_source, binary_output, binary_policy)
            self.assertEqual(binary_output.read_bytes(), binary_source.read_bytes())

            bom_source = root / "bom-source"
            bom_source.write_bytes(b"\xef\xbb\xbfunsafe")
            with self.assertRaisesRegex(ContentPolicyError, "text_bom_forbidden"):
                write_canonical_file(bom_source, root / "bom-output", text_policy)

    def test_invalid_utf8_and_casefold_collisions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "invalid"
            source.write_bytes(b"\xff")
            policy = ResolvedContentPolicy("invalid", "text", "utf8-lf", "test")
            with self.assertRaisesRegex(ContentPolicyError, "text_invalid_utf8"):
                write_canonical_file(source, root / "output", policy)

        with self.assertRaisesRegex(ContentPolicyError, "casefold_path_collision"):
            resolve_content_policies(self.contract(), ("README.md", "Readme.md"))

    def test_prefix_matching_uses_path_segment_boundaries(self) -> None:
        contract = self.contract()
        policies = resolve_content_policies(contract, ("docs/source-decisions.md",))
        self.assertEqual(policies["docs/source-decisions.md"].classification, "text")
        with self.assertRaisesRegex(ContentPolicyError, "unclassified_files"):
            resolve_content_policies(contract, ("docs-extra/file.md",))

    def test_text_preserves_final_newline_presence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = ResolvedContentPolicy("text", "text", "utf8-lf", "test")
            for name, source_bytes, expected in (
                ("none", b"one\r\ntwo", b"one\ntwo"),
                ("present", b"one\r\ntwo\r\n", b"one\ntwo\n"),
            ):
                source = root / f"{name}.source"
                destination = root / f"{name}.output"
                source.write_bytes(source_bytes)
                write_canonical_file(source, destination, policy)
                self.assertEqual(destination.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
