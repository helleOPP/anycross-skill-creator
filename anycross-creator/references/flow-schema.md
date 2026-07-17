# AnyCross flow.json Schema

Everything here was read out of real, running AnyCross exports — not from documentation. Where a shape is inferred rather than observed, it says so.

## Contents

- [Top level](#top-level)
- [structure vs steps](#structure-vs-steps)
- [Node shape](#node-shape)
- [Value types](#value-types)
- [Referencing other nodes (spel)](#referencing-other-nodes-spel)
- [Container nodes: loop, branch, while](#container-nodes-loop-branch-while)
- [Error handler](#error-handler)
- [The zip](#the-zip)

## Top level

```json
{
  "name": "Workflow Name",
  "version": "2.0",
  "sourceType": "self",
  "flowID": 7614715678494314207,
  "structure": [ ... ],
  "steps": [ ... ]
}
```

`flowID` is a snowflake-style integer. On import AnyCross assigns its own, so any plausible unique integer works for a new flow. Keep the real one when regenerating an existing flow you intend to overwrite.

## structure vs steps

`structure` is the execution tree — IDs and nesting only. `steps` is the flat list of full node definitions. **Every node appears in both.** A node in `steps` but missing from `structure` is silently never executed; the reverse fails at import.

```json
"structure": [
  {"id": "cronjob_trigger-1", "type": "trigger", "subSteps": null},
  {"id": "script-1", "type": "normal", "subSteps": null},
  {"id": "loop-1", "type": "loop_parallel_parent", "subSteps": [
    {"id": "loop-1.default", "type": "loop_parallel_child", "subSteps": [
      {"id": "http-client-2", "type": "normal", "subSteps": null},
      {"id": "bitable-1", "type": "normal", "subSteps": null}
    ]}
  ]}
]
```

`structure` types seen in real exports: `trigger`, `normal`, `loop_parallel_parent`, `loop_parallel_child`, `loop_serial_parent`, `loop_serial_child`, `branch_exclusive_parent`, `branch_parallel_parent`, `while_parent`.

Note `steps` stays **flat** even when `structure` nests — `http-client-2` inside the loop is still a top-level entry in `steps`. The container's child wrapper (`loop-1.default`) is the exception: it exists in `structure` and also gets a bare entry in `steps` with no `operation`.

Node IDs follow `<connectorName>-<n>`, numbered per connector starting at 1. Nothing enforces this, but every export follows it and spel paths read much better for it.

## Node shape

```json
{
  "id": "script-1",
  "type": "normal",
  "operation": {
    "connectorId": "7296760306577965062",
    "operationId": "7296760306603212805",
    "connectorName": "script",
    "connectorVersion": "2.0"
  },
  "name": "Compute prev month range",
  "description": "",
  "auth": {
    "key": "",
    "parameters": null,
    "credentials": {"type": "cred", "value": "CRED_ID"}
  },
  "parameters": { ... },
  "errorHandler": { ... }
}
```

The four IDs live **inside `operation`**, not at the top level of the node. Container nodes add `"operationName"` inside `operation` (e.g. `"Parallel loop"`); ordinary nodes omit it.

`auth.credentials` is `null` for connectors that need no auth (script, cronjob, http-client to a public API, loop, delay). When a credential is needed it goes **here** — never in `parameters`.

Trigger nodes carry an extra `hook`:

```json
"hook": {"hookKey": {"type": "string", "value": ""}}
```

## Value types

Every parameter value is a `{type, value}` envelope, recursively — including keys nested inside objects and arrays.

```python
{"type": "string",  "value": "text"}
{"type": "number",  "value": 1}
{"type": "boolean", "value": True}
{"type": "array",   "value": [ ...envelopes... ]}
{"type": "object",  "value": { "key": ...envelope... }}
{"type": "cred",    "value": "CRED_ID"}
{"type": "subFlow", "value": "FLOW_ID"}
{"type": "spel",    "value": {"expression": ..., "node_tree": ...}}
```

The recursion is the thing people get wrong. An HTTP header list is an array of object-envelopes, each wrapping `key` and `value` envelopes:

```json
"headers": {"type": "array", "value": [
  {"type": "object", "value": {
    "key":   {"type": "string", "value": "Accept"},
    "value": {"type": "string", "value": "application/json"}
  }}
]}
```

## Referencing other nodes (spel)

```python
{"type": "spel", "value": {
    "expression": '_("$.script-2.result.meterList")',
    "node_tree": {"t": "json_path", "path": "$.script-2.result.meterList"}
}}
```

The editor renders from `node_tree`, the engine evaluates `expression`. Editing one and forgetting the other produces a node that looks right in the UI and resolves to null at runtime — so generate both from a single variable.

### The four node_tree types

`t` determines what `path` means, and **only `json_path` repeats the full path in `expression`**. The rest are relative, which looks like a bug and isn't:

| `t` | `expression` | `path` | What it reads |
|---|---|---|---|
| `json_path` | `_("$.script-2.result.meterList")` | `$.script-2.result.meterList` (identical) | another node's output |
| `project_var` | `_("$.config.main_base.app_token")` | `main_base.app_token` (no `$.config.`) | an AnyCross **project variable** |
| `flow_variable` | `_("$.variable.page_token")` | `page_token` (no `$.variable.`) | a `variable` node's value |
| `binary` | `'CurrentValue.[department_id]="' +_("$.subflow-trigger-1.data.department_id")+ '"'` | absent — has `left`, `op`, `right` instead | a computed expression |

### Project variables (`$.config.*`) — the alternative to hardcoding

`project_var` reads a variable defined in **AnyCross project settings**, not in `flow.json`. The export references it and nothing more; the value lives in the platform.

```python
{"type": "spel", "value": {
    "expression": '_("$.config.main_base.app_token")',
    "node_tree": {"t": "project_var", "path": "main_base.app_token"},
}}
```

This matters beyond tidiness. When `app_token` and `table_id` are project variables, the same flow JSON moves between environments without edits, the file carries no tenant identifiers, and a base migration is one settings change rather than a hunt through every node. Production flows do this routinely.

So when a build needs an `app_token`, `table_id`, or similar, **ask whether a project variable already exists** before writing the literal into the generator. Literals are the fallback, not the default. The catch: the variable must be defined in the target project before the flow runs, so an import into a fresh project fails until settings are populated — tell the user which variables their flow expects.

### Output paths by connector (observed)

| Node | Path to its output |
|------|--------------------|
| `script-N` | `$.script-N.result.<returnedKey>` — note the `.result` |
| `bitable-N` (search) | `$.bitable-N.data` — array of records |
| `http-client-N` | `$.http-client-N.body` (parsed when `response_parser: json`) |
| `subflow-caller-N` | `$.subflow-caller-N.data.<key>` |
| `webhook-trigger-1` | `$.webhook-trigger-1.body.<field>` |
| loop child scope | `$.loop-N.default.item` for the current element |

## Container nodes: loop, branch, while

These use string IDs, not snowflakes: `connectorId` equals the connector name.

**Loop** — `cid: "loop"`, `oid: "loop_parallel"` or `"loop_serial"`, version `0.0.1`.

```json
"parameters": {
  "maxSize": {"type": "number", "value": 1},
  "items":   {"type": "spel", "value": {...}}
}
```

`maxSize` is the parallelism cap and only applies to `loop_parallel`; `loop_serial` takes `items` alone. `maxSize: 1` on a parallel loop is effectively serial — a legitimate way to rate-limit an API without a `delay` node, though a `delay` inside the body is more explicit.

**Branch** — `cid: "branch"`, `oid: "branch_exclusive"` (if/else — first match wins) or `"branch_parallel"` (all matching arms run), version `0.0.1`. Parameters: `branches`, `maxSize`. Each arm becomes a child in `structure` under the `*_parent` node.

**While** — `cid: "while"`, `oid: "while"`, version `0.0.1`. Parameters: `condition`, `maxSize`. Used in real exports for paginated API reads (`page_token` loops), paired with a `variable` node to hold the cursor.

## Error handler

```python
# Stop the flow
{"defaultStrategy": {"id": "<node-id>.error_handler.default", "name": "", "action": "terminate"}}

# Retry, then stop if still failing
{"defaultStrategy": {"id": "<node-id>.error_handler.default", "name": "", "action": "retry",
                     "retryFallbackAction": "terminate"}}
```

The `id` must be the node's own ID plus `.error_handler.default`.

## The zip

One file, `flow.json`, at the archive root — no folder wrapper. The zip filename becomes the suggested workflow name on import.
