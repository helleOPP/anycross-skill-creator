#!/usr/bin/env python3
"""Wrap a flow.json into an importable AnyCross zip.

Runs validate_flow.py first and refuses to pack a failing flow — a zip that
imports and misbehaves costs far more of the user's time than a failed build.

Usage:
    python pack_flow.py <flow.json> "<output-dir>/<Workflow Name>.zip"
    python pack_flow.py <flow.json> <out.zip> --skip-validate
"""
import argparse
import subprocess
import sys
import zipfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("flow_json", type=Path)
    ap.add_argument("out_zip", type=Path)
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    if not args.flow_json.exists():
        sys.exit(f"no such file: {args.flow_json}")

    if not args.skip_validate:
        validator = Path(__file__).with_name("validate_flow.py")
        r = subprocess.run([sys.executable, str(validator), str(args.flow_json)])
        if r.returncode != 0:
            sys.exit("refusing to pack: validation failed (--skip-validate to override)")

    args.out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        # flow.json at the archive root, no folder wrapper
        z.write(args.flow_json, "flow.json")

    print(f"packed: {args.out_zip}  ({args.out_zip.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
