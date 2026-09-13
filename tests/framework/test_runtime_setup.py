from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.templates.runtime.obvious_one_runtime.remote_assets import (
    RemoteMemberRecord,
    extract_verified,
)
from obvious_one_plugin_framework.templates.runtime.obvious_one_runtime.setup import (
    BootstrapConfig,
    RemoteAssetGroup,
    SetupError,
    setup_rag,
)


RUNTIME_SHA = "a" * 64
MODEL_SHA = "b" * 64


class RuntimeSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def make_archive(self, name: str, members: dict[str, bytes]) -> tuple[Path, tuple[RemoteMemberRecord, ...]]:
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            for member, payload in members.items():
                archive.writestr(member, payload)
        records = tuple(
            RemoteMemberRecord(member, len(payload), sha256(payload).hexdigest())
            for member, payload in members.items()
        )
        return path, records

    def config(self, plugin_id: str, archive: Path, members: tuple[RemoteMemberRecord, ...]) -> BootstrapConfig:
        return BootstrapConfig(
            plugin_id=plugin_id,
            app_id=plugin_id,
            namespace=f"{plugin_id}:docs",
            data_root=self.root / "ObviousOne",
            runtime_lock_digest=RUNTIME_SHA,
            model_digest=MODEL_SHA,
            asset_groups=(RemoteAssetGroup(
                name="index",
                url="https://example.invalid/index.zip",
                size=archive.stat().st_size,
                sha256=sha256(archive.read_bytes()).hexdigest(),
                install_subdir="indexes",
                members=members,
            ),),
            required_free_bytes=0,
        )

    def installers(self, archive: Path):
        def populate_runtime(stage: Path) -> None:
            (stage / "python.exe").write_bytes(b"runtime")

        def verify_runtime(path: Path) -> None:
            self.assertEqual((path / "python.exe").read_bytes(), b"runtime")

        def populate_model(stage: Path) -> None:
            (stage / "model.bin").write_bytes(b"model")

        def verify_model(path: Path) -> None:
            self.assertEqual((path / "model.bin").read_bytes(), b"model")

        def fetch(_group: RemoteAssetGroup, destination: Path) -> Path:
            shutil.copyfile(archive, destination)
            return destination

        return populate_runtime, verify_runtime, populate_model, verify_model, fetch

    def test_setup_requires_explicit_download_consent(self) -> None:
        archive, members = self.make_archive("index.zip", {"index.sqlite3": b"index"})
        with self.assertRaisesRegex(SetupError, "downloads_not_accepted"):
            setup_rag(self.config("plugin-alpha", archive, members), accept_downloads=False)

    def test_archive_member_cannot_escape_plugin_staging(self) -> None:
        archive, _ = self.make_archive("unsafe.zip", {"../outside.bin": b"bad"})
        expected = {"../outside.bin": RemoteMemberRecord("../outside.bin", 3, sha256(b"bad").hexdigest())}
        with self.assertRaisesRegex(SetupError, "unsafe_archive_member"):
            extract_verified(archive, self.root / "stage", expected)

    def test_setup_shares_dependencies_but_isolates_plugin_assets(self) -> None:
        archive, members = self.make_archive("index.zip", {"index.sqlite3": b"index"})
        installers = self.installers(archive)
        alpha = setup_rag(self.config("plugin-alpha", archive, members), True,
                          runtime_populate=installers[0], runtime_verify=installers[1],
                          model_populate=installers[2], model_verify=installers[3],
                          asset_fetch=installers[4], smoke_test=lambda _: None)
        beta = setup_rag(self.config("plugin-beta", archive, members), True,
                         runtime_populate=installers[0], runtime_verify=installers[1],
                         model_populate=installers[2], model_verify=installers[3],
                         asset_fetch=installers[4], smoke_test=lambda _: None)
        alpha_config = json.loads(alpha.config_path.read_text(encoding="utf-8"))
        beta_config = json.loads(beta.config_path.read_text(encoding="utf-8"))
        self.assertEqual(alpha_config["runtime_dir"], beta_config["runtime_dir"])
        self.assertEqual(alpha_config["model_dir"], beta_config["model_dir"])
        self.assertNotEqual(alpha_config["index_dir"], beta_config["index_dir"])
        self.assertEqual(alpha.state, "rag_ready")
        self.assertEqual(beta.state, "rag_ready")

    def test_failed_smoke_test_preserves_previous_configuration(self) -> None:
        archive, members = self.make_archive("index.zip", {"index.sqlite3": b"index"})
        installers = self.installers(archive)
        config = self.config("plugin-alpha", archive, members)
        ready = setup_rag(config, True, runtime_populate=installers[0], runtime_verify=installers[1],
                          model_populate=installers[2], model_verify=installers[3],
                          asset_fetch=installers[4], smoke_test=lambda _: None)
        before = ready.config_path.read_bytes()
        with self.assertRaisesRegex(SetupError, "smoke_test_failed"):
            setup_rag(config, True, repair=True, runtime_populate=installers[0], runtime_verify=installers[1],
                      model_populate=installers[2], model_verify=installers[3],
                      asset_fetch=installers[4], smoke_test=lambda _: (_ for _ in ()).throw(ValueError("bad")))
        self.assertEqual(ready.config_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
