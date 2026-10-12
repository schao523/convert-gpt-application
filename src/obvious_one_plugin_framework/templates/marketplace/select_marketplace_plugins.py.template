"""Select marketplace plugins affected by an explicit Git revision range."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys


SHARED_CONTROLS = frozenset(
    {
        ".agents/plugins/marketplace.json",
        ".claude-plugin/marketplace.json",
        ".codex-plugin/marketplace.json",
        "openclaw/marketplace.json",
        ".obvious-one-validation.json",
        "tools/verify_marketplace.py",
        "tools/select_marketplace_plugins.py",
        ".github/workflows/validate.yml",
        ".gitattributes",
    }
)


class SelectionError(ValueError):
    pass


class ResultParser(argparse.ArgumentParser):
    def error(self, message):
        raise SelectionError("selection_arguments_invalid")


def _result(status, code, *, diagnostics=(), evidence=None):
    return {
        "result_schema_version": 1,
        "operation": "select-marketplace-plugins",
        "status": status,
        "code": code,
        "diagnostics": list(diagnostics),
        "artifacts": [],
        "mutations": [],
        "evidence": evidence or {},
    }


def _safe_relative(value):
    if not isinstance(value, str) or not value:
        raise SelectionError("registry_path_invalid")
    normalized = value.replace("\\", "/")
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or any(part in ("", ".", "..") for part in posix.parts)
    ):
        raise SelectionError("registry_path_invalid")
    return posix.as_posix()


def _safe_git_relative(value):
    if not isinstance(value, str) or not value:
        raise SelectionError("git_diff_unrecognized")
    posix = PurePosixPath(value)
    if (
        posix.is_absolute()
        or any(part in ("", ".", "..") for part in posix.parts)
    ):
        raise SelectionError("git_diff_unrecognized")
    return value


def _digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_artifact(artifact):
    if not isinstance(artifact, dict) or set(artifact) != {
        "content_sha256", "file_count", "files", "total_bytes"
    }:
        raise SelectionError("registry_invalid")
    records = artifact.get("files")
    if not isinstance(records, list):
        raise SelectionError("registry_invalid")
    normalized = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "size", "sha256"}:
            raise SelectionError("registry_invalid")
        path = _safe_relative(record.get("path"))
        size = record.get("size")
        if (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not _digest(record.get("sha256"))
        ):
            raise SelectionError("registry_invalid")
        normalized.append({"path": path, "size": size, "sha256": record["sha256"]})
    paths = [record["path"] for record in normalized]
    if paths != sorted(set(paths)):
        raise SelectionError("registry_invalid")
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if (
        artifact.get("file_count") != len(normalized)
        or artifact.get("total_bytes") != sum(record["size"] for record in normalized)
        or artifact.get("content_sha256") != sha256(encoded).hexdigest()
    ):
        raise SelectionError("registry_invalid")


def _validate_commands(commands, applicable_targets):
    if not isinstance(commands, list):
        raise SelectionError("registry_invalid")
    identifiers = []
    for command in commands:
        if not isinstance(command, dict) or set(command) != {"id", "artifact", "argv"}:
            raise SelectionError("registry_invalid")
        identifier = command.get("id")
        artifact = command.get("artifact")
        argv = command.get("argv")
        if (
            not isinstance(identifier, str)
            or not identifier
            or artifact not in applicable_targets
            or not isinstance(argv, list)
            or not argv
            or not all(isinstance(argument, str) and argument for argument in argv)
        ):
            raise SelectionError("registry_invalid")
        identifiers.append(identifier)
    if len(identifiers) != len(set(identifiers)):
        raise SelectionError("registry_invalid")


def _validate_clawhub(clawhub, applicable_targets):
    if clawhub == {"state": "NOT APPLICABLE"}:
        return
    if (
        not isinstance(clawhub, dict)
        or set(clawhub) != {"state", "family", "native_manifest"}
        or clawhub.get("state") != "CONFIGURED"
        or clawhub.get("family") != "native-plugin"
        or "openclaw" not in applicable_targets
    ):
        raise SelectionError("registry_invalid")
    _safe_relative(clawhub.get("native_manifest"))


def _load_registry(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SelectionError("registry_invalid") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "marketplace_id", "plugins"
    }:
        raise SelectionError("registry_invalid")
    if (
        value.get("schema_version") != 2
        or not isinstance(value.get("marketplace_id"), str)
        or not value.get("marketplace_id")
    ):
        raise SelectionError("registry_invalid")
    records = value.get("plugins")
    if not isinstance(records, list) or not records:
        raise SelectionError("registry_invalid")

    plugin_ids = []
    ownership = []
    for plugin in records:
        if not isinstance(plugin, dict) or set(plugin) != {
            "plugin_id", "version", "targets", "commands", "clawhub"
        }:
            raise SelectionError("registry_invalid")
        plugin_id = plugin.get("plugin_id")
        version = plugin.get("version")
        if (
            not isinstance(plugin_id, str)
            or not plugin_id
            or not isinstance(version, str)
            or not version
        ):
            raise SelectionError("registry_invalid")
        plugin_ids.append(plugin_id)
        targets = plugin.get("targets")
        if not isinstance(targets, dict) or set(targets) != {"codex", "openclaw"}:
            raise SelectionError("registry_invalid")
        applicable_targets = set()
        for name in ("codex", "openclaw"):
            target = targets[name]
            if target == {"state": "NOT APPLICABLE"}:
                continue
            if (
                not isinstance(target, dict)
                or set(target) != {"state", "mode", "path", "artifact"}
                or target.get("state") != "STATICALLY VERIFIED"
                or target.get("mode") not in {"build", "verify_existing"}
            ):
                raise SelectionError("registry_invalid")
            _validate_artifact(target.get("artifact"))
            ownership.append((_safe_relative(target.get("path")), plugin_id))
            applicable_targets.add(name)
        if not applicable_targets:
            raise SelectionError("registry_invalid")
        _validate_commands(plugin.get("commands"), applicable_targets)
        _validate_clawhub(plugin.get("clawhub"), applicable_targets)
    if plugin_ids != sorted(set(plugin_ids)):
        raise SelectionError("registry_duplicate_plugin")

    folded = sorted(
        ((tuple(part.casefold() for part in PurePosixPath(path).parts), path, plugin_id)
         for path, plugin_id in ownership),
        key=lambda item: item[0],
    )
    for index, (parts, _path, _plugin_id) in enumerate(folded):
        for other_parts, _other_path, _other_plugin_id in folded[index + 1:]:
            if parts == other_parts or parts == other_parts[:len(parts)]:
                raise SelectionError("registry_destination_overlap")
    return tuple(plugin_ids), tuple(sorted(ownership))


def _git(root, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        shell=False,
        timeout=30,
    )


def _resolve(root, revision):
    try:
        completed = _git(root, "rev-parse", "--verify", revision + "^{commit}")
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    try:
        value = completed.stdout.decode("ascii").strip()
    except UnicodeError:
        return None
    if len(value) not in (40, 64) or any(character not in "0123456789abcdef" for character in value):
        return None
    return value


def _changes(root, base, head):
    completed = _git(
        root,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        "--find-copies",
        "--find-copies-harder",
        base,
        head,
        "--",
    )
    if completed.returncode != 0:
        raise SelectionError("git_diff_failed")
    fields = completed.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    result = []
    index = 0
    try:
        while index < len(fields):
            status = fields[index].decode("ascii")
            index += 1
            count = 2 if status.startswith(("R", "C")) else 1
            if not status or status[0] not in "ACDMRTUXB" or index + count > len(fields):
                raise SelectionError("git_diff_unrecognized")
            paths = []
            for field in fields[index:index + count]:
                paths.append(_safe_git_relative(field.decode("utf-8", "surrogateescape")))
            index += count
            result.append({"status": status, "paths": paths})
    except (UnicodeError, SelectionError) as exc:
        if isinstance(exc, SelectionError):
            raise
        raise SelectionError("git_diff_unrecognized") from exc
    return sorted(result, key=lambda item: (item["paths"], item["status"]))


def _digest(records):
    encoded = json.dumps(
        records,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


def _selection(plugin_ids, records, ownership):
    if not records:
        return "NONE", [], None
    selected = set()
    for record in records:
        for path in record["paths"]:
            folded = path.casefold()
            if folded in {control.casefold() for control in SHARED_CONTROLS}:
                return "ALL", list(plugin_ids), "shared_control_changed"
            path_parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
            owners = {
                plugin_id
                for destination, plugin_id in ownership
                if path_parts[:len(PurePosixPath(destination).parts)]
                == tuple(part.casefold() for part in PurePosixPath(destination).parts)
            }
            if len(owners) != 1:
                return "ALL", list(plugin_ids), "changed_path_unmapped"
            selected.update(owners)
    return "AFFECTED", sorted(selected), None


def _evidence(mode, plugins, records, reason, base_commit, head_commit):
    return {
        "selection_mode": mode,
        "selected_plugins": plugins,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "changed_path_count": len(records),
        "changed_paths_sha256": _digest(records),
        "fallback_reason": reason,
        "matrix": {"plugin": plugins},
    }


def main(argv=None):
    parser = ResultParser()
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--all", dest="all_reason")
    parser.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
        if args.registry is None:
            raise SelectionError("selection_arguments_invalid")
        registry_path = args.registry.resolve()
        root = registry_path.parent
        plugin_ids, ownership = _load_registry(registry_path)
        if args.all_reason is not None:
            if args.base is not None or args.head is not None or not args.all_reason:
                raise SelectionError("selection_arguments_invalid")
            evidence = _evidence(
                "ALL", list(plugin_ids), [], args.all_reason, None, None
            )
        else:
            if args.base is None or args.head is None:
                raise SelectionError("selection_arguments_invalid")
            base_commit = _resolve(root, args.base)
            head_commit = _resolve(root, args.head)
            if base_commit is None or head_commit is None:
                evidence = _evidence(
                    "ALL",
                    list(plugin_ids),
                    [],
                    "revision_unavailable",
                    base_commit,
                    head_commit,
                )
            else:
                try:
                    records = _changes(root, base_commit, head_commit)
                    mode, selected, reason = _selection(plugin_ids, records, ownership)
                except (OSError, subprocess.SubprocessError, SelectionError):
                    records = []
                    mode, selected, reason = "ALL", list(plugin_ids), "git_diff_failed"
                evidence = _evidence(
                    mode, selected, records, reason, base_commit, head_commit
                )
        result = _result("PASS", "marketplace_plugins_selected", evidence=evidence)
        exit_code = 0
    except Exception as exc:
        code = str(exc) or "marketplace_selection_failed"
        result = _result(
            "FAIL",
            "marketplace_selection_failed",
            diagnostics=[
                {
                    "code": code,
                    "path": None,
                    "message": "marketplace plugin selection failed",
                    "candidates": [],
                }
            ],
        )
        exit_code = 3
    sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
