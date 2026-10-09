from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_authoring import (
    validate_delegated_references,
)


OWNER = "guiding-biblical-study"
NON_OWNER = "guiding-parenting-sessions"
REFERENCES = {
    "RM-04A": "reference-material/RM-04A_Bible_OT.pdf",
    "RM-04B": "reference-material/RM-04B_Bible_NT.pdf",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _profile(skill: str, *, delegated: list[dict[str, object]] | None = None) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "skill-reference-profile-v2" if delegated is not None else "skill-reference-profile-v1",
        "skill": skill,
        "major_intents": ["test intent"],
        "required": [],
        "conditional": [],
        "optional": [],
        "prohibited_substitutions": ["Do not fabricate exact Scripture."],
        "fallback": "Disclose unavailable required authority.",
    }
    if delegated is not None:
        value["delegated_references"] = delegated
    return value


def _handoffs() -> list[dict[str, object]]:
    return [
        {
            "reference_id": reference_id,
            "owner_skill": OWNER,
            "access_mode": "HANDOFF",
            "local_copy": False,
        }
        for reference_id in REFERENCES
    ]


class DelegatedReferenceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        owner = self.root / "skills" / OWNER
        non_owner = self.root / "skills" / NON_OWNER
        owner.mkdir(parents=True)
        non_owner.mkdir(parents=True)
        owner_links = "\n".join(
            f"- [{reference_id}](assets/{relative})"
            for reference_id, relative in REFERENCES.items()
        )
        (owner / "SKILL.md").write_text(
            f"# Owner\n\n{owner_links}\n",
            encoding="utf-8",
            newline="\n",
        )
        (non_owner / "SKILL.md").write_text(
            "# Non-owner\n\n"
            "## Delegated reference handoff\n\n"
            f"- Access: HANDOFF to `{OWNER}` for RM-04A and RM-04B.\n"
            "- Triggers: exact CUV quotation or verification; formal Bible study.\n"
            "- Return: the result returns to the response owner.\n"
            "- Fallback: if the owner or references are unavailable, disclose the limitation and do not fabricate exact Scripture.\n",
            encoding="utf-8",
            newline="\n",
        )
        owner_assets = []
        for reference_id, relative in REFERENCES.items():
            path = owner / "assets" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((reference_id + "\n").encode("ascii"))
            owner_assets.append({"id": reference_id, "file": relative})
        _write_json(owner / "assets/reference-profile.json", _profile(OWNER))
        _write_json(owner / "assets/knowledge-index.json", {"assets": owner_assets})
        _write_json(
            non_owner / "assets/reference-profile.json",
            _profile(NON_OWNER, delegated=_handoffs()),
        )
        _write_json(non_owner / "assets/knowledge-index.json", {"assets": []})

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def codes(self) -> set[str]:
        return {issue.code for issue in validate_delegated_references(self.root)}

    def test_valid_handoff_resolves_owner_assets_and_response_path(self) -> None:
        self.assertEqual(validate_delegated_references(self.root), ())

    def test_unique_legacy_filename_qualified_owner_ids_resolve(self) -> None:
        owner_index = self.root / "skills" / OWNER / "assets/knowledge-index.json"
        payload = json.loads(owner_index.read_text(encoding="utf-8"))
        for item in payload["assets"]:
            item["id"] = f"{item['id']}_Bible_legacy"
        _write_json(owner_index, payload)

        self.assertEqual(validate_delegated_references(self.root), ())

        payload["assets"].append(
            {"id": "RM-04A_Second_legacy", "file": REFERENCES["RM-04A"]}
        )
        _write_json(owner_index, payload)
        self.assertIn("delegated_reference_owner_index_ambiguous", self.codes())

    def test_profile_shape_and_reference_identity_fail_closed(self) -> None:
        profile_path = self.root / "skills" / NON_OWNER / "assets/reference-profile.json"
        cases = (
            (
                lambda profile: profile.update({"surprise": True}),
                "delegated_reference_profile_unknown_key",
            ),
            (
                lambda profile: profile["delegated_references"].append(  # type: ignore[union-attr]
                    dict(profile["delegated_references"][0])  # type: ignore[index]
                ),
                "delegated_reference_duplicate",
            ),
            (
                lambda profile: profile["delegated_references"][0].update(  # type: ignore[index,union-attr]
                    {"owner_skill": "missing-owner"}
                ),
                "delegated_reference_owner_missing",
            ),
            (
                lambda profile: profile["delegated_references"][0].update(  # type: ignore[index,union-attr]
                    {"access_mode": "COPY"}
                ),
                "delegated_reference_access_mode_invalid",
            ),
            (
                lambda profile: profile["delegated_references"][0].update(  # type: ignore[index,union-attr]
                    {"local_copy": True}
                ),
                "delegated_reference_local_copy_forbidden",
            ),
        )
        original = json.loads(profile_path.read_text(encoding="utf-8"))
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                profile = json.loads(json.dumps(original))
                mutate(profile)
                _write_json(profile_path, profile)
                self.assertIn(expected, self.codes())
        _write_json(profile_path, original)

    def test_non_owner_must_not_bind_or_link_delegated_assets_locally(self) -> None:
        non_owner = self.root / "skills" / NON_OWNER
        index_path = non_owner / "assets/knowledge-index.json"
        _write_json(
            index_path,
            {"assets": [{"id": "RM-04A", "file": REFERENCES["RM-04A"]}]},
        )
        self.assertIn("delegated_reference_non_owner_indexed", self.codes())

        _write_json(index_path, {"assets": []})
        with (non_owner / "SKILL.md").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"\n[stale](assets/{REFERENCES['RM-04A']})\n")
        self.assertIn("delegated_reference_non_owner_linked", self.codes())

    def test_owner_must_package_index_and_directly_link_each_reference(self) -> None:
        owner = self.root / "skills" / OWNER
        target = owner / "assets" / REFERENCES["RM-04A"]
        target.unlink()
        self.assertIn("delegated_reference_owner_asset_missing", self.codes())

        target.write_bytes(b"RM-04A\n")
        _write_json(
            owner / "assets/knowledge-index.json",
            {"assets": [{"id": "RM-04B", "file": REFERENCES["RM-04B"]}]},
        )
        self.assertIn("delegated_reference_owner_index_missing", self.codes())

        _write_json(
            owner / "assets/knowledge-index.json",
            {
                "assets": [
                    {"id": reference_id, "file": relative}
                    for reference_id, relative in REFERENCES.items()
                ]
            },
        )
        (owner / "SKILL.md").write_text(
            f"# Owner\n\n[RM-04B](assets/{REFERENCES['RM-04B']})\n",
            encoding="utf-8",
            newline="\n",
        )
        self.assertIn("delegated_reference_owner_link_missing", self.codes())

    def test_handoff_prose_must_define_trigger_return_and_fallback(self) -> None:
        skill = self.root / "skills" / NON_OWNER / "SKILL.md"
        variants = {
            "delegated_reference_trigger_missing": (
                "exact CUV quotation or verification; formal Bible study",
                "ordinary question",
            ),
            "delegated_reference_return_missing": (
                "the result returns to the response owner",
                "the result is available",
            ),
            "delegated_reference_fallback_missing": (
                "if the owner or references are unavailable, disclose the limitation and do not fabricate exact Scripture",
                "if unavailable, continue",
            ),
        }
        original = skill.read_text(encoding="utf-8")
        for expected, (old, new) in variants.items():
            with self.subTest(expected=expected):
                skill.write_text(original.replace(old, new), encoding="utf-8", newline="\n")
                self.assertIn(expected, self.codes())
        skill.write_text(original, encoding="utf-8", newline="\n")

    def test_delegated_reference_asset_must_not_be_duplicated_outside_owner(self) -> None:
        duplicate = self.root / "skills" / NON_OWNER / "assets" / REFERENCES["RM-04A"]
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_bytes(b"duplicate\n")
        self.assertIn("delegated_reference_asset_duplicated", self.codes())

    def test_v1_profiles_remain_compatible(self) -> None:
        non_owner = self.root / "skills" / NON_OWNER
        _write_json(non_owner / "assets/reference-profile.json", _profile(NON_OWNER))
        self.assertEqual(validate_delegated_references(self.root), ())


if __name__ == "__main__":
    unittest.main()
