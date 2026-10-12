from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.marketplace import (
    load_preparation_catalog,
    prepare_marketplace,
    verify_marketplace,
)
from obvious_one_plugin_framework.marketplace_receipt import (
    build_marketplace_filesystem_receipt,
    verify_marketplace_filesystem_receipt,
    write_marketplace_filesystem_receipt,
)
from obvious_one_plugin_framework.results import ArtifactRecord, OperationResult
from tests.framework import test_marketplace as marketplace_fixture


SCHEMA = "marketplace-filesystem-verification-receipt-v1"
TOP_LEVEL_KEYS = {
    "schema",
    "marketplace_id",
    "operation",
    "status",
    "marketplace_identity",
    "controls",
    "plugins",
    "verification_profile",
    "receipt_sha256",
}
CONTROL_KEYS = {
    "preparation_catalog",
    "validation_registry",
    "marketplace_verifier",
    "marketplace_selector",
}


def _canonical_sha256(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_sha256", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


class MarketplaceReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = marketplace_fixture.MarketplaceTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.catalog = load_preparation_catalog(
            fixture.catalog_path,
            fixture.repository,
        )
        prepare_marketplace(self.catalog, fixture.baseline, fixture.output)
        self.verification = verify_marketplace(self.catalog, fixture.output)
        self.receipt_path = fixture.root / "evidence" / "filesystem-receipt.json"

    def _write_receipt(self) -> dict[str, object]:
        write_marketplace_filesystem_receipt(
            self.catalog,
            self.fixture.output,
            self.verification,
            self.receipt_path,
        )
        return json.loads(self.receipt_path.read_text(encoding="ascii"))

    def test_receipt_has_closed_canonical_identity_contract(self) -> None:
        receipt = build_marketplace_filesystem_receipt(
            self.catalog,
            self.fixture.output,
            self.verification,
        )

        self.assertEqual(set(receipt), TOP_LEVEL_KEYS)
        self.assertEqual(receipt["schema"], SCHEMA)
        self.assertEqual(receipt["operation"], "verify-marketplace")
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(set(receipt["controls"]), CONTROL_KEYS)
        self.assertEqual(
            [plugin["plugin_id"] for plugin in receipt["plugins"]],
            ["legacy", "modern"],
        )
        self.assertEqual(
            [target["name"] for target in receipt["plugins"][0]["targets"]],
            ["codex", "openclaw"],
        )
        self.assertEqual(receipt["receipt_sha256"], _canonical_sha256(receipt))
        encoded = json.dumps(receipt, ensure_ascii=True, sort_keys=True)
        for forbidden in (str(Path.home()), "timestamp", "hostname", "username"):
            self.assertNotIn(forbidden, encoded)

    def test_receipt_write_is_ascii_lf_deterministic_and_transactional(self) -> None:
        first = write_marketplace_filesystem_receipt(
            self.catalog,
            self.fixture.output,
            self.verification,
            self.receipt_path,
        )
        first_bytes = self.receipt_path.read_bytes()
        second_path = self.fixture.root / "second-receipt.json"
        second = write_marketplace_filesystem_receipt(
            self.catalog,
            self.fixture.output,
            self.verification,
            second_path,
        )

        self.assertEqual(first_bytes, second_path.read_bytes())
        self.assertTrue(first_bytes.endswith(b"\n"))
        self.assertNotIn(b"\r", first_bytes)
        first_bytes.decode("ascii")
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(first.sha256, sha256(first_bytes).hexdigest())
        self.assertEqual(first.kind, "marketplace_filesystem_verification_receipt")

        self.receipt_path.write_bytes(b"preserve-me\n")
        bad = OperationResult(
            operation="verify-marketplace",
            status="FAIL",
            code="marketplace_verification_failed",
        )
        with self.assertRaisesRegex(ValueError, "receipt_verification_not_passed"):
            write_marketplace_filesystem_receipt(
                self.catalog,
                self.fixture.output,
                bad,
                self.receipt_path,
            )
        self.assertEqual(self.receipt_path.read_bytes(), b"preserve-me\n")

    def test_writer_rejects_catalog_collision_and_linked_parent_without_mutation(self) -> None:
        catalog_before = self.fixture.catalog_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "unsafe_receipt_output"):
            write_marketplace_filesystem_receipt(
                self.catalog,
                self.fixture.output,
                self.verification,
                self.fixture.catalog_path,
            )
        self.assertEqual(self.fixture.catalog_path.read_bytes(), catalog_before)

        linked_parent = self.fixture.root / "linked-evidence"
        linked_output = linked_parent / "receipt.json"
        with patch(
            "obvious_one_plugin_framework.marketplace_receipt._path_is_link",
            side_effect=lambda path: Path(path) == linked_parent,
        ):
            with self.assertRaisesRegex(ValueError, "unsafe_receipt_output"):
                write_marketplace_filesystem_receipt(
                    self.catalog,
                    self.fixture.output,
                    self.verification,
                    linked_output,
                )
        self.assertFalse(linked_output.exists())

    def test_build_rejects_nonpassing_or_wrong_marketplace_verification(self) -> None:
        cases = (
            OperationResult("other", "PASS", "marketplace_verified"),
            OperationResult(
                "verify-marketplace",
                "PASS",
                "marketplace_verified",
                artifacts=(ArtifactRecord("staged", "marketplace_stage", "0" * 64, 1),),
            ),
        )
        for verification in cases:
            with self.subTest(operation=verification.operation):
                with self.assertRaises(ValueError):
                    build_marketplace_filesystem_receipt(
                        self.catalog,
                        self.fixture.output,
                        verification,
                    )

    def test_validation_rejects_closed_schema_and_digest_corruption(self) -> None:
        original = self._write_receipt()
        cases: list[tuple[str, dict[str, object]]] = []

        unknown = deepcopy(original)
        unknown["unknown"] = True
        cases.append(("unknown", unknown))
        malformed = deepcopy(original)
        malformed["receipt_sha256"] = "not-a-digest"
        cases.append(("malformed", malformed))
        duplicate = deepcopy(original)
        duplicate["plugins"].append(deepcopy(duplicate["plugins"][0]))
        duplicate["receipt_sha256"] = _canonical_sha256(duplicate)
        cases.append(("duplicate", duplicate))
        nonpassing = deepcopy(original)
        nonpassing["status"] = "FAIL"
        nonpassing["receipt_sha256"] = _canonical_sha256(nonpassing)
        cases.append(("nonpassing", nonpassing))
        unsafe = deepcopy(original)
        unsafe["plugins"][0]["targets"][0]["destination"] = "../outside"
        unsafe["receipt_sha256"] = _canonical_sha256(unsafe)
        cases.append(("unsafe", unsafe))

        for name, payload in cases:
            with self.subTest(name=name):
                self.receipt_path.write_text(
                    json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
                    encoding="ascii",
                    newline="\n",
                )
                result = verify_marketplace_filesystem_receipt(
                    self.catalog,
                    self.fixture.output,
                    self.receipt_path,
                )
                self.assertEqual(result.status, "FAIL")
                self.assertEqual(result.code, "marketplace_receipt_invalid")
                self.assertEqual(len(result.diagnostics), 1)

    def test_validation_detects_every_bound_identity_change(self) -> None:
        mutations = {
            "tree": lambda: (self.fixture.output / "untouched.txt").write_bytes(b"changed\n"),
            "catalog": lambda: self.fixture.catalog_path.write_bytes(
                self.fixture.catalog_path.read_bytes() + b" \n"
            ),
            "registry": lambda: (self.fixture.output / ".obvious-one-validation.json").write_bytes(
                (self.fixture.output / ".obvious-one-validation.json").read_bytes() + b" \n"
            ),
            "verifier": lambda: (self.fixture.output / "tools" / "verify_marketplace.py").write_bytes(
                (self.fixture.output / "tools" / "verify_marketplace.py").read_bytes() + b"# changed\n"
            ),
            "selector": lambda: (self.fixture.output / "tools" / "select_marketplace_plugins.py").write_bytes(
                b"# changed selector\n"
            ),
            "plugin": lambda: (self.fixture.output / "plugins" / "legacy" / ".codex-plugin" / "plugin.json").write_bytes(
                b'{"name":"legacy","version":"9.9.9"}\n'
            ),
        }

        for name, mutate in mutations.items():
            with self.subTest(name=name):
                prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)
                self.verification = verify_marketplace(self.catalog, self.fixture.output)
                self._write_receipt()
                mutate()

                result = verify_marketplace_filesystem_receipt(
                    self.catalog,
                    self.fixture.output,
                    self.receipt_path,
                )

                self.assertEqual(result.status, "FAIL")
                self.assertEqual(result.code, "marketplace_receipt_mismatch")
                self.assertEqual(len(result.diagnostics), 1)


if __name__ == "__main__":
    unittest.main()
