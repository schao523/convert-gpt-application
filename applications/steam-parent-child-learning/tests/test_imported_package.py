from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import unittest


EXPECTED_MEMBERS = [{'path': '.codex-plugin/plugin.json', 'size': 1215, 'sha256': '897d9836b8b8bd2e6112a11fb8020737cd1c75af542156a1251521d83f0af7e1'}, {'path': 'PLUGIN-BUILDER-MANIFEST.json', 'size': 57528, 'sha256': '81e1305c1b669d891e9dc25cfcbeea05522eff93f89015af52f9f1a301617f4e'}, {'path': 'PRIVACY.md', 'size': 326, 'sha256': '3404301b009aed4006fff12bd613f4ad16bde23e7a8fc7c2c60ac12434449523'}, {'path': 'README.md', 'size': 979, 'sha256': '9cd0b24592b96d5203e26dea509e92400c4cc3884fc37ce0d94b942f3f3877f0'}, {'path': 'THIRD_PARTY_CONTENT.md', 'size': 478, 'sha256': '764d60060073c71ee64ca2e0970ab6ca8a71a8e0c8495fa0609eae3ab96cf810'}, {'path': 'plugin.json', 'size': 1365, 'sha256': 'c13429fbd751d49f77416f1351da2556e5d62d39bd35bb453569b7e544c75064'}, {'path': 'skills/checking-safety-and-age/SKILL.md', 'size': 3369, 'sha256': 'ae9f9a0958ab9cdbb4ca12661e748ec663c45947055a8b767d9f40f3c48b32eb'}, {'path': 'skills/checking-safety-and-age/agents/openai.yaml', 'size': 165, 'sha256': '13163f87a3d75927b513e2bd2a7f6498af8455845acb19431db46a5e54d98eb0'}, {'path': 'skills/checking-safety-and-age/references/RM08_STEAM_Child_Safety_and_Age_Adaptation_Guide.md', 'size': 9174, 'sha256': '69e5d94ccadac5502db223cc1f9e94c788914e1fa60f8daa02a098fb1cf35e44'}, {'path': 'skills/consulting-source-evidence/SKILL.md', 'size': 5766, 'sha256': 'e729b0e567caefa779dbb4dd2a82d74bbdddf1a55350daff354324f77e70966e'}, {'path': 'skills/consulting-source-evidence/agents/openai.yaml', 'size': 182, 'sha256': '962864010dc931635ebf0ab9471817e7487a478297efd503f2f29bc5f94cc294'}, {'path': 'skills/consulting-source-evidence/references/Knowledge_Quality_Acceptance_R02.md', 'size': 4150, 'sha256': '83aef11c9ffdfebb3468d7f2d118438386c62079480f84ed7d2101adac4189e5'}, {'path': 'skills/consulting-source-evidence/references/OWNER_DECISION_CLOSURE_2026-10-23.md', 'size': 1046, 'sha256': '6894c305349f04d68a8255506acfd33b16539100713d80d3b34e849b6d46d379'}, {'path': 'skills/consulting-source-evidence/references/Original_Source_Inventory.json', 'size': 1009, 'sha256': 'd4762b77eb9d3ab59a718a010a25cb00980764ca70fc19b3b11688b1334ce9cd'}, {'path': 'skills/consulting-source-evidence/references/QC04_Framework_Differences.csv', 'size': 2934, 'sha256': 'e53c54a49d0c90ad9fdc8daa0156ef6cb1ea39e51cb7db7814235ee0c8d1bd9d'}, {'path': 'skills/consulting-source-evidence/references/QC05_Visual_Review.csv', 'size': 901, 'sha256': 'cbe7a7af7bbb49984d0571ffe73fc0a57689e499be1af4319dc34b9e9c50ff46'}, {'path': 'skills/consulting-source-evidence/references/QC08_Activity_Safety_Audit.csv', 'size': 4612, 'sha256': '664fe7fdd441242fc8a5ee4ba217e26dcff3cc0db8d81eacc168f9ef16ddc920'}, {'path': 'skills/consulting-source-evidence/references/R02_Subsequent_Owner_Approval_and_Provenance.json', 'size': 2223, 'sha256': 'e9b216cbd3c616a18284917f85afadf072146bd472c4eb96fafdf80af7c54ef6'}, {'path': 'skills/consulting-source-evidence/references/Reference_Material_Usage_Map_R02.csv', 'size': 4256, 'sha256': '4984187797bacf3a859773e9f6f88b6d678623471876a0901dd35e644e5c023e'}, {'path': 'skills/consulting-source-evidence/references/deterministic-operations.md', 'size': 1773, 'sha256': '7b8c92f7f4a40dd9c92fa88f4914699789f649ae2ef2f1983bbe6f24f3ea7dd0'}, {'path': 'skills/consulting-source-evidence/references/steam-tool-contract.json', 'size': 6106, 'sha256': '94c3cd2b75cb85f4351d14f2cec0990d74f2855d80ccdc1f6501bd4a86a06e41'}, {'path': 'skills/creating-game-artifacts/SKILL.md', 'size': 4532, 'sha256': '5acb49e6f9f4fd74b0245db7cf0bca677039dc420cf873ea61ed0877a1316fdb'}, {'path': 'skills/creating-game-artifacts/agents/openai.yaml', 'size': 183, 'sha256': '6bd74e56b5200e7303c3a84c62390fb55643e34b61b9be6639c2d993b43f3e55'}, {'path': 'skills/creating-game-artifacts/references/RM06_Educational_Game_Creation_Framework.md', 'size': 3231, 'sha256': '268e76dc03806c948e9f632ccf29b179f90d7b545b602869925422703e92b093'}, {'path': 'skills/designing-educational-games/SKILL.md', 'size': 3900, 'sha256': '8a0282ba8657bc79fd790e3fc71921ecefa4facc3cf3b8748830f9afd1047bd6'}, {'path': 'skills/designing-educational-games/agents/openai.yaml', 'size': 175, 'sha256': '20c9afccb62a4349aeb08bbfb52e3d26e10e8e247f3c78a6ac4546fc360cfab9'}, {'path': 'skills/designing-educational-games/references/RM02_Game_Design_Innovation_Framework.md', 'size': 6270, 'sha256': 'b2a20d1ddaeabca49ef968d7943d450046b8d675af390cb90ba271d1ee562857'}, {'path': 'skills/designing-educational-games/references/RM03_Comprehensive_STEAM_Game_Design.md', 'size': 35131, 'sha256': '1a577c3b51570131ad1d69c914e7bbd2961937007506b281c5862561290a974f'}, {'path': 'skills/designing-educational-games/references/RM04_數字探險競技場.md', 'size': 5005, 'sha256': '68844a85f9031ebf2c3752f0b1868194af7c158b866e6111448e3d8eb602c62c'}, {'path': 'skills/evaluating-playtests/SKILL.md', 'size': 3447, 'sha256': '18d0b6abe9ebd8a22708af898dc39309211800bb7b555aba74f64de288d27208'}, {'path': 'skills/evaluating-playtests/agents/openai.yaml', 'size': 175, 'sha256': '9ae7e8d2e7ce51552f27a2ccd59cb33ab10e01e39117395ec3b748f2b292cf71'}, {'path': 'skills/evaluating-playtests/references/RM07_Educational_Game_Playtesting_and_Evaluation_Guide.md', 'size': 2010, 'sha256': 'a0edb0b1d0d8b9771b0a723bebc891c8b0bd305c933186cf732125cc1a80f218'}, {'path': 'skills/guiding-steam-activities/SKILL.md', 'size': 3950, 'sha256': '6133270b80f04df94bcccbf1a20bae1182396fddd66eae6d57f719e3f4daf075'}, {'path': 'skills/guiding-steam-activities/agents/openai.yaml', 'size': 177, 'sha256': '40a3909d50b56c4898e68065d23baad153f41a7e8a47c1d598a6c75e1e368b80'}, {'path': 'skills/guiding-steam-activities/references/RM01_STEAM_Template_Library.md', 'size': 7397, 'sha256': '2acd4e6b8bb4e1d7a38aa488c07ade3bd37496b566e35b956fc6a08a1b2a1580'}, {'path': 'skills/teaching-with-visuals/SKILL.md', 'size': 3379, 'sha256': '0229f504e49450c409e7d7dde7b3051a6b278fe6255d3e5cf6286a5fe8be33a4'}, {'path': 'skills/teaching-with-visuals/agents/openai.yaml', 'size': 171, 'sha256': '0305a3eaf8b8ad15ea8e2d1d2d82965e49b2bbd00f44e699e869f8377d9d9c23'}, {'path': 'skills/teaching-with-visuals/references/RM05_STEAM_Visual_Teaching_Guide.md', 'size': 2286, 'sha256': '79206f22730c76829314382602afd4fb03e4636e9a4e4dce745777ef5b11144e'}, {'path': 'tools/steam_contract_checks.py', 'size': 6372, 'sha256': 'f01e121eef79a204b7863587f8cc5080e04e46efa5010cbe2b8e2e78e80a7e71'}]
EXPECTED_TREE_SHA256 = '5f829f762fc115b6d7fdcd89f91f81f7f60b75587440cdc47d130a257f8af7ec'


def _tree_manifest(root: Path) -> list[dict[str, object]]:
    members = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        for name in sorted(names):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
        for name in sorted(files):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
            content = child.read_bytes()
            members.append({
                "path": child.relative_to(root).as_posix(),
                "size": len(content),
                "sha256": sha256(content).hexdigest(),
            })
    return sorted(members, key=lambda item: item["path"])


class ImportedPackageTests(unittest.TestCase):
    def test_manifest_pair_identity(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        identities = []
        for relative in ("plugin.json", ".codex-plugin/plugin.json"):
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            identities.append((payload["name"], payload["version"]))
        self.assertEqual(identities, [('steam-parent-child-learning', '1.0.0')] * 2)

    def test_exact_member_bytes(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        members = _tree_manifest(root)
        encoded = json.dumps(
            members, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
        self.assertEqual(members, EXPECTED_MEMBERS)
        self.assertEqual(sha256(encoded).hexdigest(), EXPECTED_TREE_SHA256)


if __name__ == "__main__":
    unittest.main()
