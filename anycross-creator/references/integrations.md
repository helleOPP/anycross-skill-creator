# Integration Patterns

## Contents

- [Cron trigger](#cron-trigger)
- [Webhook trigger](#webhook-trigger)
- [HTTP client](#http-client)
- [Sending a Lark message or card](#sending-a-lark-message-or-card)
- [Subflows](#subflows)
- [Pagination: variable + while](#pagination-variable--while)
- [Google Docs](#google-docs)
- [Zoho Sign](#zoho-sign)

## Cron trigger

Real payload from a monthly-on-the-28th flow:

```python
"cronjob": {"type": "object", "value": {
    "trigger_type":               s("INTERVAL_TRIGGER"),
    "interval_trigger_type":      s("month"),          # min | hour | day | week | month
    "interval_trigger_frequency": n(28),
    "trigger_day":                {"type": "array", "value": [n(28)]},
    "special_trigger_day":        s("CUSTOM_DAY"),
    "execute_time":               s("06:00:00"),
    "timezone":                   s("Asia/Kuala_Lumpur"),
}}
```

`execute_time` is local to `timezone`. For sub-daily schedules use `interval_trigger_type: "min"` with `interval_trigger_frequency`, and drop `trigger_day` / `special_trigger_day` / `execute_time`. Other keys observed on minute/hour schedules: `effective_period`, `skip_time`, `skip_duration`.

Pick the timezone the business actually runs on (`Asia/Ho_Chi_Minh`, `Asia/Kuala_Lumpur`) — not UTC — or the "1st of the month" job fires on the wrong day for half the year's edge cases.

## Webhook trigger

Params: `authorization_config`, `body_type`, `webhook`. Payload reads back as `$.webhook-trigger-1.body.<field>`.

The webhook URL is assigned by AnyCross after import, so anything calling it (a Lark Base button, an external system) has to be pointed at the URL *after* the flow is published — worth saying out loud when handing over.

## HTTP client

```python
"parameters": {
    "url":                      s("https://api.example.com/things"),
    "queries": {"type": "array", "value": [
        {"type": "object", "value": {"key": s("per_page"), "value": s("all")}}
    ]},
    "headers": {"type": "array", "value": [
        {"type": "object", "value": {"key": s("Authorization"), "value": spel("$.subflow-caller-1.data.authHeader")}},
        {"type": "object", "value": {"key": s("Accept"), "value": s("application/json")}},
    ]},
    "response_parser":          s("json"),
    "response_encoding_format": s("utf8"),
    "success_status_code":      s("between"),
    "status_code_range":        s("[200,299]"),
}
```

Response reads back as `$.http-client-N.body` when `response_parser` is `json`.

`success_status_code: "between"` + `status_code_range` is what makes a 4xx actually fail the node instead of flowing a garbage body downstream. Set it.

## Sending a Lark message or card

Use the `im` connector — it handles the token itself. Building a card via HTTP + a hand-fetched tenant token is a step backwards.

```python
"parameters": {
    "receive_id_type": s("chat_id"),          # chat_id | open_id | union_id | user_id | email
    "receive_id":      s("oc_xxxxxxxx"),
    "msg_type":        s("interactive"),      # interactive = card; text = plain
    "content":         spel("$.script-1.result.card_str"),
}
```

`auth.credentials` must be a Lark credential whose bot is **already a member of the target chat**, otherwise the send fails at runtime with a permission error no amount of JSON fixing will solve.

Two ways to build the card:

- **Static card, few variables** → `card_helper` node: `card_json` is a string `{"content": "<card JSON with ${var} placeholders>"}`, `variables` supplies the values.
- **Dynamic card, variable row count** → build the whole card JSON as a string in a script node and pass it straight to `im.content`. `card_helper` can't grow a list.

Deep-link a card element back to a Base record with `<BASE_URL>&record=<record_id>`.

## Subflows

Caller side:

```python
CHILD_FLOW_ID = "<flow_id of the child flow>"   # from the child's export or its URL

"parameters": {
    "sub_flow_id": {"type": "subFlow", "value": CHILD_FLOW_ID},
    "flow_id":     s(CHILD_FLOW_ID),
    "flow_input":  {"type": "object", "value": { ... }},
    "limit_time":  n(60),
}
```

`sub_flow_id` and `flow_id` carry the same value in every export seen — one as a `subFlow` envelope, one as a plain string.

Child side ends with a `subflow-response` node whose `flow_input` is the return payload. The caller reads it at `$.subflow-caller-N.data.<key>`.

This is the right shape for anything token-shaped: one child flow fetches and caches a token, every parent calls it. It keeps the credential in one place and the refresh logic out of every flow.

## Pagination: variable + while

The observed idiom for cursor-paginated Lark APIs:

1. `variable` (set) — initialize `page_token` to `""` and an accumulator list.
2. `while` — condition on "first pass OR page_token non-empty".
3. Inside: the API node → `variable` (list push) to accumulate → `variable` (set) to advance `page_token`.

`variable` list-push takes `key`, `list`, `position`.

## Google Docs

Unverified against any real export — see the caveat in `connectors.md`.

- **Copy template** → params `fileId`, `name`, `mimeType` (`application/vnd.google-apps.document`), `parents`. The new doc's ID comes back at `$.google_docs-N.id`.
- **Replace text** → params `documentId` (the copied ID), `requests` (array of `replaceAllText`).
- **Export PDF** → params `fileId`, `mimeType` (`application/pdf`). Binary at `$.google_docs-N.file`.

```python
def replace_request(search_text, spel_expr):
    return {"type": "object", "value": {
        "replaceAllText": {"type": "object", "value": {
            "containsText": {"type": "object", "value": {
                "text":      s(search_text),
                "matchCase": b(True),
            }},
            "replaceText": spel_expr,
        }}
    }}
```

**Shareable URL** — build it in a script node, and return the `{link, text}` object ready for a Base URL field:

```javascript
function handler(input) {
  var url = 'https://docs.google.com/document/d/' + input.docId;
  return { docUrl: { link: url, text: input.docName || 'Document' } };
}
```

**Variable-length tables**: Google Docs `replaceAllText` cannot add table rows. The workaround is one placeholder per column, each holding a `\n`-joined string — `{{items_no}}` → `"1\n2\n3"`, `{{items_desc}}` → `"Item A\nItem B\nItem C"`. The template's table then has a single row that grows vertically. For grouped sections, use a separate placeholder set per group.

## Zoho Sign

Unverified against any real export.

- Token: call the token child flow via `subflow-caller`; header at `$.subflow-caller-N.data.auth_header`.
- Create request: `POST https://sign.zoho.com/api/v1/requests` — multipart, file + a `data` JSON part.
- Submit: `POST https://sign.zoho.com/api/v1/requests/{request_id}/submit`.
- The document must carry the signature tag `{{Signature*}}` (the `*` marks it mandatory) or the submit is rejected.
