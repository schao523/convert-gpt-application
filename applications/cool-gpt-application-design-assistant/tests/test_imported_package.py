from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import unittest


EXPECTED_MEMBERS = [{'path': '.codex-plugin/plugin.json', 'size': 901, 'sha256': '10ced057ff1e89c4b0bc3fe82d7c978af980e38c8da441a28d3d92a110f6482e'}, {'path': 'PLUGIN-BUILDER-MANIFEST.json', 'size': 36319, 'sha256': '9fef29eeb5b64c7c8cb8d9e4abdc2c8259c3f8d6ec1d3ba05c9c9b8a947dd47d'}, {'path': 'README.md', 'size': 860, 'sha256': '94a0175573e51aa6874bd7b16e746585af536a81a9c9aadd303a5061ba8d4303'}, {'path': 'THIRD_PARTY_CONTENT.md', 'size': 514, 'sha256': '9b23f3ac8ab1b523fd2a68db9689cc8995bf03e12c2f419000e902231970a029'}, {'path': 'docs/runtime-boundaries.md', 'size': 1409, 'sha256': '5a0f6b719a74f5fc990a3ca74112a55ea2fb567893930927d702f4bbd80a566e'}, {'path': 'plugin.json', 'size': 1047, 'sha256': '81e3b37ec289f4adc6cb9cdc011348954e81933a2253a36125aa0bd757a1763e'}, {'path': 'skills/adapting-platforms-and-delivering-packages/SKILL.md', 'size': 3122, 'sha256': 'c12877dd597b4f3f519211cda84d1293b808cc11c9ce7ecea818a3edd415cad0'}, {'path': 'skills/adapting-platforms-and-delivering-packages/agents/openai.yaml', 'size': 173, 'sha256': '0960659b6fa890f26eee3380489d8586f6caf5b60debaa20615909e768b18518'}, {'path': 'skills/adapting-platforms-and-delivering-packages/references/module-contracts.json', 'size': 6192, 'sha256': 'c075ba2f0413a376b23aa9cf8ddc4c8bb2a5986fd2f4254eae4f2916b00a1f45'}, {'path': 'skills/consulting-design-references/SKILL.md', 'size': 3736, 'sha256': '895c4f8b2e1867738adb21584a61d7ece5e43eb5dc8752d0fc32be6e4e8f6f64'}, {'path': 'skills/consulting-design-references/agents/openai.yaml', 'size': 140, 'sha256': '5c576a4e876370928c81ee8854a0e954bf26faa48afd457c671fd88f7658ff15'}, {'path': 'skills/consulting-design-references/references/Human-in-the-Loop_Guide.md', 'size': 885, 'sha256': '490e19be70b1a6886afb4765bae1d1305c0af9a4e3caf7b1e672b6680c8e40a8'}, {'path': 'skills/consulting-design-references/references/Platform_Target_Adaptation_Requirements.md', 'size': 6393, 'sha256': 'a50df5428f5a378847e0d81e6c32981a8331e282373e06d7c794b222dfd97e57'}, {'path': 'skills/consulting-design-references/references/Reference_Evaluation_and_Usage_Map.md', 'size': 12439, 'sha256': 'fd1c9f214c6c633790347f6feb84d9f02affc51a4c283fe64e6608b0962bcd73'}, {'path': 'skills/consulting-design-references/references/builder_guide.md', 'size': 4475, 'sha256': '006d1fb1a7981e7d72aadb158620da8c9d6b74e8b6d83d493b51a1ac014690f5'}, {'path': 'skills/consulting-design-references/references/interaction_patterns_guide.md', 'size': 2032, 'sha256': 'fc77d59ecb8cafb7a08f86993050f084daf462630bf7dec97fe86d32e3d8c605'}, {'path': 'skills/consulting-design-references/references/knowledge-index.json', 'size': 4290, 'sha256': '1ce7521e23ae5e0071bbe0e81b8bbde6f563340b0ab38dedefa55bd1e59ff007'}, {'path': 'skills/consulting-design-references/references/knowledge_module_template.md', 'size': 794, 'sha256': 'dd71beed2b1395c2198903943c0389ed66bf2861753765a678e3815538e58cea'}, {'path': 'skills/consulting-design-references/references/modular_design_guide.md', 'size': 4517, 'sha256': 'bb9ef68d14da09a8a5c9fb5b323736747c6f8f136dafc58fe206274cdac44579'}, {'path': 'skills/consulting-design-references/references/module-contracts.json', 'size': 2665, 'sha256': 'ee82dbd381d366008935b1a2bab4933ea9a26fb758505feb0ea3415cce0d245e'}, {'path': 'skills/consulting-design-references/references/original-instructions.docx', 'size': 30446, 'sha256': 'a64f379d4061b0566939cb3feff3587bd69ba4ecb69b8c61be46292f5f3430c8'}, {'path': 'skills/consulting-design-references/references/prompt_refactoring_patterns.md', 'size': 1461, 'sha256': 'eb2fabc97397998366dc76325a54a85230a04ac1e861342ab0f33baea1f63bb7'}, {'path': 'skills/consulting-design-references/references/resource_binding_patterns.md', 'size': 1659, 'sha256': '8e39935ca412fae6369400974a03f9640dbeaa93ba299435015b5a4f8bdd5b4c'}, {'path': 'skills/consulting-design-references/references/resource_evaluation_guide.md', 'size': 1252, 'sha256': '6a75667d514b9a1530f98bd2c654174fc9d333df8ebd4dd0c593b40b063fc8ed'}, {'path': 'skills/consulting-design-references/references/resource_types_guide.md', 'size': 1385, 'sha256': '6e7f9056e194b36f7be5033740d6249699e9ead71458c2847d949f079423af19'}, {'path': 'skills/consulting-design-references/references/source-inventory.json', 'size': 19217, 'sha256': '75d96ac4e80269a785d8bc4554c0a6d9410fdc5216af376ab072b5e34d44bba9'}, {'path': 'skills/consulting-design-references/references/testing_guide.md', 'size': 2725, 'sha256': '130d692779c127207d45037748280358e90b637cd2655d5fbc2cc9903982fe45'}, {'path': 'skills/consulting-design-references/references/use_case_brainstorm_guide.md', 'size': 1310, 'sha256': '022854c3dc0b46ab276d6d3c1c7d9af27a03f37c4eda8508a1819557dc1618c7'}, {'path': 'skills/designing-and-reviewing-interactions/SKILL.md', 'size': 2767, 'sha256': 'dd7582bc53da70013c0c8396ad6b9981b1a5c65299971710954764322a8724e3'}, {'path': 'skills/designing-and-reviewing-interactions/agents/openai.yaml', 'size': 162, 'sha256': '8ede8db3f42258f095faba4ec645c2ee722dead1c29ab7ba35a9b85c334c7ff9'}, {'path': 'skills/designing-and-reviewing-interactions/references/module-contracts.json', 'size': 7353, 'sha256': '368d07a454850d9ce5406dce5dd0ca42920cf06386cc8378d406fb57df85d84c'}, {'path': 'skills/designing-custom-instructions/SKILL.md', 'size': 2671, 'sha256': 'd8704f643038249160454c51a2f1094e260fbdfc28d7acbc4e8c9010a1782e8c'}, {'path': 'skills/designing-custom-instructions/agents/openai.yaml', 'size': 152, 'sha256': '97723e5059f084c64ef2f42598b9290369ad25b6f50960d8572cb8ef4d18cb7f'}, {'path': 'skills/designing-custom-instructions/references/module-contracts.json', 'size': 7120, 'sha256': '2b6605958abc40df47840843dbbb50b567c4b5edb5ab58352078a50b37f97576'}, {'path': 'skills/evaluating-and-binding-resources/SKILL.md', 'size': 2343, 'sha256': '6f9d3391662cd7b9d5904122380423577a66af2ca8654b1a30918150f7424d8e'}, {'path': 'skills/evaluating-and-binding-resources/agents/openai.yaml', 'size': 156, 'sha256': '89040521e8bab7880daee3eed5ab281b60c1d646c2f23f8119862375074b6169'}, {'path': 'skills/evaluating-and-binding-resources/references/module-contracts.json', 'size': 4727, 'sha256': '2182ecf1b39ec046657cd8b8cef47db89a417ce1da72a6f2d12fc5a9b7f2e06f'}, {'path': 'skills/guiding-application-design-sessions/SKILL.md', 'size': 2281, 'sha256': '3cf059ea15b166e3fc709546b44dbadf48126f55c13775b7c5aa2be1408ee879'}, {'path': 'skills/guiding-application-design-sessions/agents/openai.yaml', 'size': 143, 'sha256': 'b3d8c01b358d919045c7898ecf07fe826b5ad01bd8125eebddc302abda515966'}, {'path': 'skills/guiding-application-design-sessions/references/module-contracts.json', 'size': 4967, 'sha256': 'd8844a7b971d96f34c8a4e4e071cabf27954b552416792883f1c1e890a26aa1d'}, {'path': 'skills/testing-and-improving-instructions/SKILL.md', 'size': 2930, 'sha256': 'b22259240f848fb5610da4d56e7ff57754ef93a19b880218ebd248d60b713862'}, {'path': 'skills/testing-and-improving-instructions/agents/openai.yaml', 'size': 157, 'sha256': 'dd82b4703a2596fc01c84f9efaa70e6f500ed8ef4da8f71a5bd393e66d944699'}, {'path': 'skills/testing-and-improving-instructions/references/module-contracts.json', 'size': 5335, 'sha256': '07d0bbd6e85807c6a50bda3db1af3132088f708323bc9089b8f89a47ba0957da'}, {'path': 'tools/contracts/application-policy.md', 'size': 3389, 'sha256': 'da2bf9a1bcb29986379dd6e87fb8f9a6a6a88202d69c654beb4d4366d17f37bd'}, {'path': 'tools/contracts/artifact-contracts.md', 'size': 5027, 'sha256': '5ccfa7796a25297a5b40ac1940aedf40ebf9febbe12906c42ff5fbef1386b025'}, {'path': 'tools/contracts/interaction-protocols.json', 'size': 10961, 'sha256': 'e64b97ca55b45b53755c57a0c7da917afd5c876ed2d021aebd91ac699fef64ec'}, {'path': 'tools/contracts/requirements.json', 'size': 16212, 'sha256': 'ab4ab46f1468061ed7b7eb923218e3cbd904e5843772750ff5f612a2bc5259f6'}, {'path': 'tools/contracts/workflows.json', 'size': 41947, 'sha256': 'da08e4551a2b83544ca81cfc8b85aa9497bfdee218b5b9078570497c49860442'}, {'path': 'tools/design-integrity-contract.json', 'size': 6472, 'sha256': '12d74409b34d95c243e5f0a52ee11b6c857cabe81c90203ece1a636de7a1e079'}, {'path': 'tools/design_integrity.py', 'size': 9975, 'sha256': 'c8ac985ec5485f988647a329362ee9a651a23cadb03dea0539de22bb45c84f1d'}, {'path': 'tools/operation-guide.md', 'size': 2129, 'sha256': '1eab9af571ff523996b526dd48f85f7c8da219db61de6099e1709a86fca58b37'}, {'path': 'verification/representative-tests.json', 'size': 35036, 'sha256': '51c24d92d7a4ebb476472e265c81007def87336fb950e1fde5993d862c8b80e3'}]
EXPECTED_TREE_SHA256 = 'ee616098935dbdc0ff525ec0f1e4e72d2fb91eec03927e1d37d10590237b0a59'


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
        self.assertEqual(identities, [('cool-gpt-application-design-assistant', '1.0.0')] * 2)

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
