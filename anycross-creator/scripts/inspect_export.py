#!/usr/bin/env python3
"""Dump a real AnyCross export so its IDs and shapes can be copied instead of guessed.

Usage:
    python inspect_export.py <flow.zip|flow.json>
    python inspect_export.py <flow.zip> --node bitable-1     # full JSON for one node
    python inspect_export.py <flow.zip> --spel               # every spel reference
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path


def load(path: Path) -> dict:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith("flow.json")]
            if not names:
                sys.exit(f"no flow.json inside {path}")
            return json.loads(z.read(names[0]))
    return json.loads(path.read_text(encoding="utf-8"))


def walk(steps):
    for st in steps:
        yield st
        if st.get("subSteps"):
            yield from walk(st["subSteps"])


def find_spel(obj, path="$"):
    """Yield (json-ish location, spel path) for every spel envelope in the tree."""
    if isinstance(obj, dict):
        if obj.get("type") == "spel" and isinstance(obj.get("value"), dict):
            tree = obj["value"].get("node_tree") or {}
            expr = obj["value"].get("expression", "")
            yield path, tree.get("path", ""), expr
            return
        for k, v in obj.items():
            yield from find_spel(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from find_spel(v, f"{path}[{i}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--node", help="print full JSON for this node id")
    ap.add_argument("--spel", action="store_true", help="list all spel references")
    args = ap.parse_args()

    d = load(args.path)
    steps = {s["id"]: s for s in d.get("steps", [])}

    if args.node:
        st = steps.get(args.node)
        if not st:
            sys.exit(f"no such node: {args.node}. have: {', '.join(steps)}")
        print(json.dumps(st, indent=2, ensure_ascii=False))
        return

    print(f"# {d.get('name')}")
    print(f"  version={d.get('version')}  sourceType={d.get('sourceType')}  flowID={d.get('flowID')}")
    print()

    print("## structure")
    def show(nodes, depth=0):
        for nd in nodes:
            print("  " * (depth + 1) + f"{nd['id']}  [{nd['type']}]")
            if nd.get("subSteps"):
                show(nd["subSteps"], depth + 1)
    show(d.get("structure", []))
    print()

    print("## nodes")
    for st in walk(d.get("steps", [])):
        op = st.get("operation") or {}
        if not op:
            print(f"  {st['id']}  [{st.get('type')}]  (container child, no operation)")
            continue
        cred = ((st.get("auth") or {}).get("credentials") or {}).get("value")
        print(f"  {st['id']}  \"{st.get('name', '')}\"")
        print(f"      connector : {op.get('connectorName')} v{op.get('connectorVersion')}")
        print(f"      cid / oid : {op.get('connectorId')} / {op.get('operationId')}")
        print(f"      params    : {', '.join(sorted((st.get('parameters') or {}).keys())) or '(none)'}")
        if cred:
            print(f"      cred      : {cred}")
    print()

    if args.spel:
        print("## spel references")
        for st in walk(d.get("steps", [])):
            refs = list(find_spel(st.get("parameters") or {}))
            if not refs:
                continue
            print(f"  {st['id']}:")
            for loc, p, expr in refs:
                flag = "" if f'_("{p}")' == expr else "   <-- expression/node_tree MISMATCH"
                print(f"      {loc.replace('$.', '', 1)} -> {p}{flag}")
        print()

    print("## reminder")
    print("  IDs above are valid for THIS tenant and these connector versions.")
    print("  Copy them; do not assume they match another tenant.")


if __name__ == "__main__":
    main()
