# Known Errors

The ledger of AnyCross failures already paid for. Read it before debugging — most errors here look like a logic bug and are actually a shape bug.

## How to add an entry

After diagnosing any AnyCross error, add it here **before moving on**. The problem is solved for the user at that point, which is exactly why this step gets skipped and why the next build pays for it again.

Use this shape:

```markdown
### <Error text or code, verbatim as the UI shows it>

**Stage:** import | publish | runtime
**Symptom:** what the user sees, and where.
**Cause:** the actual mechanism.
**Fix:** the change that resolved it.
**Generalizes to:** the class of mistake, so the next build avoids it rather than re-diagnosing.
```

Two rules that keep this file useful:

- **Record the class, not the incident.** "Wrote a plain string to a URL field" is reusable. "Fixed the docUrl in the booking flow" is not, and it drags a client's name into a shared skill.
- **No tenant data.** No app_tokens, table IDs, credential IDs, chat IDs, or real record IDs. Use `<app_token>` placeholders. This file is shared across every project the skill touches.

If the diagnosis proves a reference file wrong — an ID that doesn't exist, a renamed parameter — fix the reference too and note the connector version. A wrong ID in `connectors.md` gets copied confidently forever; that is worse than a blank.

---

### Unable to parse uploaded file

**Stage:** import
**Symptom:** the zip is rejected outright; no nodes appear.
**Cause:** `flow.json` is not valid UTF-8. On Windows the usual mechanism is a write through the locale codec — `open(path, "w")` without `encoding=` uses cp1252, which either raises on non-Latin text or emits bytes the importer cannot decode.
**Fix:** write with `encoding="utf-8"`. Dumping with `ensure_ascii=True` also fixes it, by escaping everything above ASCII to `\uXXXX` so the codec question never arises.
**Generalizes to:** the constraint is *valid UTF-8*, not *ASCII*.

**Correction (2026-07-16):** an earlier version of this skill taught that non-ASCII characters themselves cause this error, and the validator failed the build on any of them. That is wrong. AnyCross's own UI exports contain raw non-ASCII text — one export downloaded straight from the UI carries 364 such characters, untouched. The platform emits raw UTF-8, so it plainly accepts it. `ensure_ascii=True` was a real fix for a real error, but the diagnosis attached to it was a superstition, and it had hardened into a rule that failed valid flows. The validator now warns rather than errors, and errors only on genuinely invalid UTF-8.

`ensure_ascii=True` is still the recommended default — it costs nothing and removes an entire class of encoding bugs. The difference is that it is now a belt-and-braces measure with a known reason, not a taboo.

---

### `expression` / `node_tree.path` "mismatch" that is actually correct

**Stage:** n/a — a validator false positive worth knowing about
**Symptom:** a flow that runs fine in production looks broken because `expression` is `_("$.config.foo.bar")` while `node_tree.path` is just `foo.bar`.
**Cause:** only `node_tree.t == "json_path"` repeats the full path in `expression`. The other three types don't: `project_var` paths are relative to `$.config.`, `flow_variable` paths are relative to `$.variable.`, and `binary` has no `path` at all.
**Fix:** see the node_tree table in `flow-schema.md`; the drift check must be per-`t`.
**Generalizes to:** before "fixing" something a real, running export does, assume the export is right and the rule is wrong. Production flows are the ground truth here — this skill is not.

---

### URLFieldConvFail

**Stage:** runtime, on a Bitable write node
**Symptom:** the write fails with this code; the URL field is the culprit.
**Cause:** a plain string was written to a LarkBase URL field.
**Fix:** write `{link: "https://...", text: "label"}`, even when link and text are the same.
**Generalizes to:** LarkBase field write shapes are not the read shapes and are not intuitive — check the table in `larkbase.md` before writing any field that isn't text or number. Person and Link fields have the same trap.

---

### Person field write rejected / person lost

**Stage:** runtime
**Symptom:** a Person field writes blank, or the node errors on the field value.
**Cause:** the record was read, `extract()`-ed into a display name string, and that string written back. LarkBase wants the object array.
**Fix:** pass the raw value through — `f['<PersonField>'] || []`.
**Generalizes to:** `extract()` is for *rendering* a value into text (a card, a document, a log). It is not for round-tripping a value back into LarkBase. Reading and writing the same field are different operations with different shapes.

---

### Script node parameter rejected at import

**Stage:** import or publish
**Symptom:** the script node is invalid or its code is empty after import.
**Cause:** the parameter key was `code`.
**Fix:** the key is `js_code`.
**Generalizes to:** parameter names come from the connector's own schema, not from what reads naturally. When a node imports but arrives empty, suspect a key name before suspecting the value. `inspect_export.py` on a real export settles it.

---

### Credential not applied / auth error despite a credential being set

**Stage:** runtime
**Symptom:** the node behaves as if unauthenticated.
**Cause:** the credential envelope was placed in `parameters` instead of `auth.credentials`.
**Fix:** move it — `auth: {key: "", parameters: null, credentials: {"type": "cred", "value": "<CRED_ID>"}}`.
**Generalizes to:** auth is structurally separate from parameters in the node shape. See `flow-schema.md`.

---

### spel resolves to null, node receives nothing

**Stage:** runtime
**Symptom:** a downstream node gets `null`/empty where the previous node clearly produced data.
**Cause:** usually one of three: (a) a script output referenced without the `.result` segment — `$.script-1.foo` instead of `$.script-1.result.foo`; (b) `expression` and `node_tree.path` disagree because only one was edited; (c) the referenced node ID doesn't exist (typo, or renumbered during a rewrite).
**Fix:** match the output-path table in `flow-schema.md`; keep `expression` and `node_tree.path` generated from one variable so they cannot drift. `validate_flow.py` catches (b) and (c).
**Generalizes to:** spel failures are silent — they produce empty output, not an error. When a node's output looks empty, check its Input panel in the run history before rewriting its logic; the bug is usually upstream of the node you're staring at.

---

### Bitable node imports but returns nothing / wrong operation

**Stage:** runtime
**Symptom:** a search returns no records against a table that obviously has them, or an update targets the wrong thing.
**Cause:** operation IDs from the wrong connector version. Two Bitable connectors are live — v2.0 (`7241926900765982725`) and v2.7 (`7576576101812538807`) — with different operation IDs and different parameter names for the same action.
**Fix:** harvest the IDs from a template export in the same tenant.
**Generalizes to:** this is the argument for Step 0. Any ID taken from memory or from another tenant's flow is a hypothesis. Connector versions differ per tenant and the IDs change with them.

---

### Filter with no conditions returns every record

**Stage:** runtime
**Symptom:** a search meant to be narrow returns the whole table; downstream loops process far too much.
**Cause:** an empty `conditions` array reads as "no filter", not "match nothing".
**Fix:** build the filter conditionally in Python — omit the `filter` parameter entirely when there are no conditions.
**Generalizes to:** empty-means-everything is a live footgun in the Lark ecosystem generally, not just here.

---

### im node fails to send to a group

**Stage:** runtime
**Symptom:** permission error on send, though the credential is valid and works for Bitable.
**Cause:** the bot behind the credential is not a member of the target chat.
**Fix:** add the bot to the group in Lark. No JSON change will fix it.
**Generalizes to:** a valid credential is not the same as access to a specific resource. When a node's auth "works elsewhere" but fails here, check resource membership before touching the flow.
