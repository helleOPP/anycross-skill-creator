#!/usr/bin/env python3
"""Skeleton for an AnyCross flow generator. Copy, don't import.

Fill in the CONSTANTS block from the user and the template export, build the
nodes, run it, then validate + pack:

    python gen_<name>.py
    python <skill-dir>/scripts/validate_flow.py out/flow.json
    python <skill-dir>/scripts/pack_flow.py out/flow.json "out/My Workflow.zip"
"""
import json
from pathlib import Path

# --------------------------------------------------------------------------
# CONSTANTS -- from the user / the template export, never from memory.
#
# Before filling these in: check whether the AnyCross project already defines
# them as project variables. If it does, use pvar("base_x.app_token") below
# instead of a literal -- the flow then carries no tenant identifiers and moves
# between environments unedited. Literals are the fallback, not the default.
# --------------------------------------------------------------------------
APP_TOKEN = "<app_token>"
TABLE_ID = "<tbl...>"
LARK_CRED = "<cred_id>"
TIMEZONE = "Asia/Ho_Chi_Minh"

OUT_DIR = Path("out")
FLOW_NAME = "My Workflow"
FLOW_ID = 7614715678494314207  # any plausible snowflake for a new flow

# --------------------------------------------------------------------------
# Value-type helpers -- every parameter value is a {type, value} envelope,
# recursively, including keys nested inside objects and arrays.
# --------------------------------------------------------------------------
def s(v):    return {"type": "string", "value": v}
def n(v):    return {"type": "number", "value": v}
def b(v):    return {"type": "boolean", "value": v}
def arr(v):  return {"type": "array", "value": v}
def obj(v):  return {"type": "object", "value": v}
def cred(v): return {"type": "cred", "value": v}
def subflow(v): return {"type": "subFlow", "value": v}

def spel(path):
    """Reference another node's output: spel("$.script-1.result.rows").
    expression and node_tree.path are generated from one variable so they
    cannot drift apart."""
    return {"type": "spel", "value": {
        "expression": f'_("{path}")',
        "node_tree": {"t": "json_path", "path": path},
    }}

def pvar(path):
    """Reference an AnyCross project variable: pvar("main_base.app_token").
    Defined in project settings, not in this file -- keeps tenant IDs out of
    the flow. Note the path is relative: expression gets the $.config. prefix,
    node_tree.path does not."""
    return {"type": "spel", "value": {
        "expression": f'_("$.config.{path}")',
        "node_tree": {"t": "project_var", "path": path},
    }}

def fvar(key):
    """Reference a `variable` node's value: fvar("page_token")."""
    return {"type": "spel", "value": {
        "expression": f'_("$.variable.{key}")',
        "node_tree": {"t": "flow_variable", "path": key},
    }}

def kv(key, value_env):
    """One entry in an HTTP headers/queries array."""
    return obj({"key": s(key), "value": value_env})

# --------------------------------------------------------------------------
# Node builder
# --------------------------------------------------------------------------
def node(node_id, connector_name, connector_version, connector_id, operation_id,
         name, parameters, *, node_type="normal", credential=None,
         on_error="terminate", extra=None):
    nd = {
        "id": node_id,
        "type": node_type,
        "operation": {
            "connectorId": connector_id,
            "operationId": operation_id,
            "connectorName": connector_name,
            "connectorVersion": connector_version,
        },
        "name": name,
        "description": "",
        "auth": {
            "key": "",
            "parameters": None,
            "credentials": cred(credential) if credential else None,
        },
        "parameters": parameters,
    }
    if on_error and node_type != "trigger":
        nd["errorHandler"] = {"defaultStrategy": {
            "name": "", "action": on_error, "id": f"{node_id}.error_handler.default",
        }}
    if extra:
        nd.update(extra)
    return nd

def struct(node_id, node_type="normal", sub=None):
    return {"id": node_id, "type": node_type, "subSteps": sub}

# --------------------------------------------------------------------------
# JS helpers. Full family (extractLink, fmt, fmtDate) is in references/larkbase.md.
# Vietnamese in strings is fine -- ensure_ascii=True below escapes it to \uXXXX.
# --------------------------------------------------------------------------
JS_EXTRACT = r"""
function extract(val) {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string') return val;
  if (typeof val === 'number') return String(val);
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (Array.isArray(val)) {
    if (val.length === 0) return '';
    var f = val[0];
    if (typeof f === 'string') return val.join(', ');
    if (f && f.text !== undefined) return val.map(function(v){ return v.text || ''; }).join('');
    if (f && f.name !== undefined) return val.map(function(v){ return v.name || ''; }).join(', ');
    return '';
  }
  if (typeof val === 'object') {
    if (val.type !== undefined && Array.isArray(val.value)) {
      var inner = val.value;
      if (inner.length === 0) return '';
      var fi = inner[0];
      if (typeof fi === 'number') return String(fi);
      if (typeof fi === 'string') return fi;
      if (fi && fi.text !== undefined) return inner.map(function(v){ return v.text || ''; }).join('');
      return String(fi);
    }
    if (val.text !== undefined) return String(val.text);
    if (val.value !== undefined) return String(val.value);
    return '';
  }
  return String(val);
}
"""

# --------------------------------------------------------------------------
# Build -- example: cron -> bitable search -> script. Replace with the real flow.
# Node IDs follow <connectorName>-<n>; spel paths read much better for it.
# --------------------------------------------------------------------------
steps = [
    node("cronjob_trigger-1", "cronjob_trigger", "1.5",
         "7223328446464688134", "7223328446649221126",
         "Daily 06:00",
         {"cronjob": obj({
             "trigger_type": s("INTERVAL_TRIGGER"),
             "interval_trigger_type": s("day"),
             "interval_trigger_frequency": n(1),
             "execute_time": s("06:00:00"),
             "timezone": s(TIMEZONE),
         })},
         node_type="trigger",
         extra={"hook": {"hookKey": s("")}}),

    node("bitable-1", "bitable", "2.7",
         "7576576101812538807", "7576576102571707831",
         "Read records",
         {
             "app_token": s(APP_TOKEN),
             "table_id": s(TABLE_ID),
             "page_size": n(500),
             "user_id_type": s("open_id"),
         },
         credential=LARK_CRED),

    node("script-1", "script", "2.0",
         "7296760306577965062", "7296760306603212805",
         "Shape rows",
         {
             "input": obj({"records": spel("$.bitable-1.data")}),
             "js_code": s(JS_EXTRACT + r"""
function handler(input) {
  var rows = (input.records || []).map(function (r) {
    var f = r.fields || {};
    return { name: extract(f['Name']) };
  });
  return { rows: rows };   // read back as $.script-1.result.rows
}
"""),
         }),
]

structure = [
    struct("cronjob_trigger-1", "trigger"),
    struct("bitable-1"),
    struct("script-1"),
]

flow = {
    "name": FLOW_NAME,
    "version": "2.0",
    "sourceType": "self",
    "flowID": FLOW_ID,
    "structure": structure,
    "steps": steps,
}

# --------------------------------------------------------------------------
# Write. ensure_ascii=True is what keeps Vietnamese/emoji content legal:
# it escapes them to \uXXXX instead of emitting raw UTF-8 bytes, which the
# importer rejects with "Unable to parse uploaded file".
# --------------------------------------------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "flow.json"
out.write_text(json.dumps(flow, indent=2, ensure_ascii=True), encoding="ascii")
print(f"wrote {out}")
print("next: validate_flow.py then pack_flow.py")
