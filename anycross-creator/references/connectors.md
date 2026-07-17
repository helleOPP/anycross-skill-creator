# Connector & Operation Inventory

**Read this second, not first.** These IDs were harvested from real exports across several tenants. They are strong priors, not guarantees: connectors are versioned per tenant, and a tenant on an older version has a *different `connectorId`* for the same connector — not just a different version string. Confirm against a template export (`scripts/inspect_export.py`) whenever one exists.

The Bitable row is the cautionary tale: two live connectors, different IDs, different operation IDs, and different parameter names for the same "update a record" action.

## Contents

- [How to harvest IDs from an export](#how-to-harvest-ids-from-an-export)
- [Triggers](#triggers)
- [LarkBase / Bitable](#larkbase--bitable)
- [Lark platform](#lark-platform)
- [Logic & control flow](#logic--control-flow)
- [Script](#script)
- [HTTP](#http)
- [Subflow](#subflow)
- [Google Workspace](#google-workspace)

## How to harvest IDs from an export

```bash
python <skill-dir>/scripts/inspect_export.py "<path-to.zip>"
python <skill-dir>/scripts/inspect_export.py "<path-to.zip>" --node bitable-1   # full node JSON
```

Prefer an export from the **same tenant** as the target. Cross-tenant exports still tell you parameter shapes and spel patterns, just not necessarily the right IDs or credentials.

## Triggers

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `cronjob_trigger` | 1.5 | `7223328446464688134` | `7223328446649221126` | `cronjob` |
| `cronjob_trigger` (alt op) | 1.5 | `7223328446464688134` | `7223328446724702214` | `cronjob` |
| `webhook-trigger` | 1.5 | `7270411537485938693` | `7270411537515282438` | `authorization_config`, `body_type`, `webhook` |
| `subflow-trigger` | 1.0 | `7163946939149451270` | `7163946939409514502` | `flow_id`, `sub_flow_id` |

Two cronjob operation IDs appear in the wild for the same connector version; both take a `cronjob` object. Copy whichever the template uses. See `integrations.md` for the `cronjob` payload.

## LarkBase / Bitable

**v2.7 — `connectorId: 7576576101812538807`**

| Operation | operationId | params |
|---|---|---|
| Search records | `7576576102571707831` | `app_token`, `table_id`, `page_size`, `user_id_type`, `filter` (optional) |
| Update record | `7576576102517181878` | `app_token`, `table_id`, `record_id`, `fields`, `user_id_type`, `ignore_consistency_check` |
| Batch create records | `7576576102533991862` | `app_token`, `table_id`, `records`, `user_id_type`, `ignore_consistency_check` |

**v2.0 — `connectorId: 7241926900765982725`** (older tenants; note `field_names` instead of returning all fields, and batch ops that v2.7 splits differently)

| Operation | operationId | params |
|---|---|---|
| Query records | `7241926902343024645` | `app_token`, `table_id`, `filter`, `field_names`, `user_id_type` |
| Batch create | `7241926901642559494` | `app_token`, `table_id`, `records`, `user_id_type` |
| Batch update | `7241926901315436549` | `app_token`, `table_id`, `records`, `user_id_type` |
| Create single | `7241926901348958214` | `app_token`, `table_id`, `fields`, `user_id_type` |
| Update single | `7241926901814525957` | `app_token`, `table_id`, `record_id`, `fields`, `user_id_type` |

Requires `auth.credentials` = a Lark credential. Field read/write formats and filter builders live in `larkbase.md`.

## Lark platform

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `im` — send message/card | 2.9 | `7531952617174351884` | `7531952617258287110` | `receive_id_type`, `receive_id`, `msg_type`, `content` |
| `card_helper` — fill card template | 1.2 | `7299347175140491269` | `7299347175169851398` | `card_json`, `variables` |
| `contact` — list departments (nested) | 1.1 | `7237034493419274246` | `7237034493951868933` | `parent_department_id`, `fetch_child`, `page_size`, `page_token`, `department_id_type`, `user_id_type` |
| `contact` — list users in department | 1.1 | `7237034493419274246` | `7237034494182572038` | `department_id`, `page_size`, `page_token`, `department_id_type`, `user_id_type` |
| `contact` — get user detail | 1.1 | `7237034493419274246` | `7237034494493081605` | `user_id`, `user_id_type`, `department_id_type` |
| `contact` — get department detail | 1.1 | `7237034493419274246` | `7237034494266556422` | `department_id`, `department_id_type`, `user_id_type` |
| `contact` — list authorized users | 1.1 | `7237034493419274246` | `7237034494010687493` | `page_size`, `page_token`, `department_id_type`, `user_id_type` |

`im` is the native way to post a Lark message or card — no manual token fetch, no HTTP node. The bot behind the credential must already be a member of the target chat. See `integrations.md`.

## Logic & control flow

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `loop` parallel | 0.0.1 | `loop` | `loop_parallel` | `items`, `maxSize` |
| `loop` serial | 0.0.1 | `loop` | `loop_serial` | `items` |
| `branch` exclusive | 0.0.1 | `branch` | `branch_exclusive` | `branches`, `maxSize` |
| `branch` parallel | 0.0.1 | `branch` | `branch_parallel` | `branches`, `maxSize` |
| `while` | 0.0.1 | `while` | `while` | `condition`, `maxSize` |
| `variable` — set | 1.1 | `7234033487534096389` | `7234033488075177990` | `variables` |
| `variable` — list push | 1.1 | `7234033487534096389` | `7234033488037412869` | `key`, `list`, `position` |
| `delay` | 1.1 | `7234358606060060678` | `7234358606278164486` | `time_unit` |
| `terminate` | 1.0 | `7163966129067524102` | `7163966129315004421` | (none) |

`variable` + `while` is the observed pagination idiom: initialize `page_token`, loop while it's non-empty, push results onto a list.

## Script

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `script` | 2.0 | `7296760306577965062` | `7296760306603212805` | `input`, `js_code` |
| `script` | 1.2 | `7215804708106010629` | `7215804708286382085` | `input`, `js_code` |

Both versions: the key is `js_code` (not `code`), `input` is an object map of name → envelope, and the code defines `function handler(input) { ... return {...} }`. Output reads back as `$.script-N.result.<key>`.

## HTTP

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `http-client` GET | 1.7 | `7327606926668267526` | `7327606926726938630` | `url`, `queries`, `headers`, `response_parser`, `response_encoding_format`, `success_status_code`, `status_code_range` |
| `http-client` POST | 1.7 | `7327606926668267526` | `7327606926697594885` | above + body params |
| `http-client` PUT | 1.7 | `7327606926668267526` | `7327606926810939398` | above + body params |

GET is verified from a real export. POST/PUT operation IDs come from an earlier version of this skill and are **not** confirmed against any verified export — verify before relying on them, and flag them to the user as unverified if you ship them.

## Subflow

| Connector | ver | connectorId | operationId | params |
|---|---|---|---|---|
| `subflow-caller` (with timeout) | 1.0 | `7163956383816122373` | `7163956384122273797` | `flow_id`, `sub_flow_id`, `flow_input`, `limit_time` |
| `subflow-caller` (fire & forget) | 1.0 | `7163956383816122373` | `7163956384160038917` | `flow_id`, `sub_flow_id`, `flow_input` |
| `subflow-response` | 1.0 | `7163946591265488901` | `7163946591588483077` | `flow_input`, `sub_flow_id` |

`sub_flow_id` takes a `{"type": "subFlow", "value": "<FLOW_ID>"}` envelope.

## Google Workspace

From an earlier version of this skill — **not confirmed** against any verified export. Treat as a starting hypothesis and verify.

| Connector | connectorId | Operation | operationId |
|---|---|---|---|
| `google_docs` | `7532338149482250252` | Copy file (from template) | `7532338149574311942` |
| `google_docs` | `7532338149482250252` | Replace text (batchUpdate) | `7532338149645664268` |
| `google_docs` | `7532338149482250252` | Export / download | `7532338149670780934` |
| `drive` | `7531965935779856396` | Download file | `7531965935884730374` |

Patterns for these live in `integrations.md`.
