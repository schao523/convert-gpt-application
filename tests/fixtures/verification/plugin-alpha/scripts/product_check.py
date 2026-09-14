from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("smoke", "build"))
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--plugin-id", default="plugin-alpha")
    args = parser.parse_args()
    if args.operation == "smoke":
        print(json.dumps({"status": "ok", "plugin_id": args.plugin_id}))
        return 0
    if args.destination is None:
        parser.error("--destination is required for build")
    source = Path(__file__).resolve().parents[1]
    target = args.destination / "plugins" / args.plugin_id
    shutil.copytree(source, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
