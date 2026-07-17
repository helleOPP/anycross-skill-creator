#!/usr/bin/env python3
"""Pre-import checks for an AnyCross flow.json.

Catches the failures that are cheap here and expensive in the UI:
  - non-ASCII bytes            -> "Unable to parse uploaded file"
  - structure/steps mismatch   -> node silently never runs, or import fails
  - node shape errors          -> `code` vs `js_code`, creds in parameters, missing operation
  - spel drift                 -> expression != node_tree.path, or points at a nonexistent node

A clean run means the zip will import. It does not mean the flow is correct:
wrong operation IDs and wrong field names pass every check here and fail at runtime.

Usage:
    python validate_flow.py <flow.json>
"""
import json
import re
import sys
from pathlib import Path

errors: list[str] = []
warnings: list[str] = []


def walk(steps):
    for st in steps:
        yield st
        if st.get("subSteps"):
            yield from walk(st["subSteps"])


def structure_ids(nodes):
    for nd in nodes:
        yield nd["id"]
        if nd.get("subSteps"):
            yield from structure_ids(nd["subSteps"])


def check_encoding(path: Path):
    """The file must be valid UTF-8. Raw non-ASCII is legal — AnyCross's own
    exports contain raw Vietnamese — so it is only flagged as a warning."""
    data = path.read_bytes()
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"not valid UTF-8 at byte {e.start} — import will fail to parse")
        errors.append("    likely cause: written with a locale codec (cp1252 on Windows).")
        errors.append("    fix: open(path, 'w', encoding='utf-8'), or dump with ensure_ascii=True")
        return None

    bad = [(i, ch) for i, ch in enumerate(raw) if ord(ch) > 127]
    if bad:
        warnings.append(
            f"{len(bad)} raw non-ASCII character(s) (e.g. line "
            f"{raw.count(chr(10), 0, bad[0][0]) + 1}: U+{ord(bad[0][1]):04X} {bad[0][1]!r}). "
            "Legal, but ensure_ascii=True escapes them to \\uXXXX and removes a whole class "
            "of encoding bugs for free — prefer it unless you have a reason not to."
        )
    return raw


def check_parity(d: dict):
    s_ids = set(structure_ids(d.get("structure", [])))
    p_ids = {st["id"] for st in walk(d.get("steps", []))}
    for missing in sorted(s_ids - p_ids):
        errors.append(f"in structure but not steps: {missing} — import will fail")
    for missing in sorted(p_ids - s_ids):
        errors.append(f"in steps but not structure: {missing} — node will never execute")


def check_nodes(d: dict):
    triggers = 0
    for st in walk(d.get("steps", [])):
        nid = st.get("id", "<no id>")
        if st.get("type") == "trigger":
            triggers += 1
        op = st.get("operation")
        is_container_child = "." in nid and not st.get("parameters")
        if not op and not is_container_child:
            errors.append(f"{nid}: missing `operation` object (connectorId/operationId/connectorName/connectorVersion)")
            continue
        if not op:
            continue
        for key in ("connectorId", "operationId", "connectorName", "connectorVersion"):
            if not op.get(key):
                errors.append(f"{nid}: operation.{key} is missing or empty")

        params = st.get("parameters") or {}
        if op.get("connectorName") == "script":
            if "code" in params and "js_code" not in params:
                errors.append(f"{nid}: script parameter must be `js_code`, not `code`")
            if "js_code" not in params:
                errors.append(f"{nid}: script node has no `js_code`")

        for key in params:
            if key in ("credential", "credentials", "cred"):
                errors.append(f"{nid}: credentials belong in auth.credentials, not parameters.{key}")

        auth = st.get("auth")
        if auth is None and not is_container_child:
            warnings.append(f"{nid}: no `auth` block — real exports always carry one (credentials may be null)")

        eh = st.get("errorHandler")
        if eh:
            want = f"{nid}.error_handler.default"
            got = (eh.get("defaultStrategy") or {}).get("id")
            if got != want:
                errors.append(f"{nid}: errorHandler id is {got!r}, expected {want!r}")

    if triggers == 0:
        errors.append("no node with type 'trigger' — the flow cannot start")
    elif triggers > 1:
        warnings.append(f"{triggers} trigger nodes — usually exactly one is intended")


def check_spel(d: dict):
    """spel comes in four flavours and only `json_path` cross-references a node.
    See references/flow-schema.md."""
    node_ids = {st["id"] for st in walk(d.get("steps", []))}
    # container children expose scoped outputs like $.loop-1.item / $.loop-6.item.x
    scopes = node_ids | {i.split(".")[0] for i in node_ids}

    def scan(obj, nid):
        if isinstance(obj, dict):
            if obj.get("type") == "spel" and isinstance(obj.get("value"), dict):
                v = obj["value"]
                tree = v.get("node_tree") or {}
                t = tree.get("t")
                path = tree.get("path") or ""
                expr = v.get("expression", "")

                if t == "json_path":
                    if expr != f'_("{path}")':
                        errors.append(f"{nid}: spel drift — expression {expr!r} vs node_tree.path {path!r}")
                    m = re.match(r"\$\.([A-Za-z0-9_.-]+?)(?:\.|$)", path)
                    if m and m.group(1) not in scopes:
                        errors.append(f"{nid}: spel points at unknown node {m.group(1)!r} ({path})")
                    ms = re.match(r"\$\.(script-\d+)\.(.+)", path)
                    if ms and not ms.group(2).startswith("result"):
                        warnings.append(
                            f"{nid}: {path} — script output is namespaced under `.result`; "
                            f"did you mean $.{ms.group(1)}.result.{ms.group(2)}?"
                        )
                elif t == "flow_variable":
                    # expression is $.variable.<key>, path is the bare key
                    if expr != f'_("$.variable.{path}")':
                        errors.append(f"{nid}: flow_variable drift — expression {expr!r} vs path {path!r} "
                                      f"(expected _(\"$.variable.{path}\"))")
                elif t == "project_var":
                    # expression is $.config.<path>, path is bare; the variable is
                    # defined in AnyCross project settings, not in this file
                    if expr != f'_("$.config.{path}")':
                        errors.append(f"{nid}: project_var drift — expression {expr!r} vs path {path!r} "
                                      f"(expected _(\"$.config.{path}\"))")
                elif t == "binary":
                    pass  # expression tree with left/op/right; nothing cheap to check
                elif t is None:
                    errors.append(f"{nid}: spel value has no node_tree.t")
                else:
                    warnings.append(f"{nid}: unrecognised node_tree.t {t!r} — not validated")
                return
            for v in obj.values():
                scan(v, nid)
        elif isinstance(obj, list):
            for v in obj:
                scan(v, nid)

    for st in walk(d.get("steps", [])):
        scan(st.get("parameters") or {}, st.get("id", "?"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    raw = check_encoding(path)
    if raw is None:
        print("\n".join(f"ERROR {e}" for e in errors))
        sys.exit(1)

    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: not valid JSON — {e}")

    check_parity(d)
    check_nodes(d)
    check_spel(d)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print()
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s) — do not pack this")
        sys.exit(1)
    print(f"OK: import-safe ({len(warnings)} warning(s)). Runtime correctness still unverified.")


if __name__ == "__main__":
    main()
