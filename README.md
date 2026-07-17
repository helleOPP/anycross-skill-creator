# AnyCross Creator

A [Claude Code](https://claude.com/claude-code) skill that builds, validates, and packages **AnyCross** workflows (the Lark/Feishu automation platform) as importable `.zip` files.

> Hi everyone,
>
> This is a skill for creating AnyCross workflows — I hope you find it useful.
> If you need any help, contact me on WhatsApp: **+84 96 246 02 65**
>
> Thank you,
>
> **Phuc**

---

## Why this exists

Writing AnyCross `flow.json` by hand is unforgiving. The logic is the easy part — the trap is that **every connector ID, operation ID, credential ID, and parameter shape is tenant- and version-specific**.

Two Bitable connectors exist in the wild:

| Version | connectorId | "update a record" operationId |
|---|---|---|
| v2.0 | `7241926900765982725` | `7241926901814525957` |
| v2.7 | `7576576101812538807` | `7576576102517181878` |

Different IDs, different operation IDs, *different parameter names for the same action*. An LLM guessing these produces a zip that either fails to import or — worse — imports cleanly and silently does the wrong thing.

So this skill is built around one rule: **copy IDs from a real export, never from memory.** Everything in it was reverse-engineered from real, running AnyCross exports rather than from documentation.

## Install

Drop the `anycross-creator/` folder into a skills directory:

```bash
# Available in every project (personal scope)
git clone https://github.com/helleOPP/anycross-skill-creator.git
cp -r anycross-skill-creator/anycross-creator ~/.claude/skills/

# Or scoped to one project
cp -r anycross-skill-creator/anycross-creator /path/to/your-project/.claude/skills/
```

Requirements: **Python 3.8+**. No third-party packages — standard library only.

Verify Claude can see it:

```
/anycross-creator
```

## How to use

Just describe the automation you want. The skill triggers on its own when you mention AnyCross, a `flow.json`, or a Lark automation:

> Build me an AnyCross workflow: every day at 6am, read the pending rows from my Bitable, and post a summary card to a Lark group.

Claude then walks a five-step loop:

| Step | What happens | Why it matters |
|---|---|---|
| **0. Ask for a template** | Claude asks for a `.zip` export of any workflow already running in your tenant | The single highest-leverage step — see below |
| **1. Constants** | Collects `app_token`, `table_id`, credentials — or wires them to AnyCross **project variables** so no tenant IDs land in the file at all | Keeps the flow portable and free of secrets |
| **2. Generate** | Writes a Python generator script that emits `flow.json` | Reproducible and reviewable, unlike hand-edited JSON |
| **3. Validate** | Runs the pre-import checks (below) | Catches in seconds what costs minutes to find in the UI |
| **4. Test & learn** | You import it and report any error verbatim; Claude diagnoses, fixes, **and writes the lesson into the skill** | The skill gets smarter with every failure |
| **5. Report** | Tells you what was built, what it depends on, and which parts are unverified | No silent guesses |

### Step 0 is the important one

If you have *any* AnyCross workflow already running in the same tenant, export it and hand over the path. It gives Claude, for free:

- the exact connector versions your tenant has installed
- working credential IDs
- the real parameter names for each operation
- spel reference paths that actually resolve

Without one, Claude falls back to the bundled inventory and will tell you plainly that the first import is a probe, not a delivery.

### Step 4 is what makes it improve

Claude cannot see the AnyCross UI — you are its only sensor. When something fails, it asks for specific things (the red banner text verbatim, the failed node's **Input** panel, the previous node's **Output** panel), because those show the real shape of the data instead of a guess.

Once diagnosed, the lesson is appended to `references/known-errors.md` as a *class* of mistake rather than an incident, so the next build avoids it instead of re-discovering it.

## The scripts

All three are standalone — usable without Claude.

**Inspect a real export** — the anti-hallucination tool. Prints every node's connector name/version, connectorId, operationId, parameter keys, credentials, and optionally every spel reference:

```bash
python anycross-creator/scripts/inspect_export.py "My Flow.zip"
python anycross-creator/scripts/inspect_export.py "My Flow.zip" --spel
python anycross-creator/scripts/inspect_export.py "My Flow.zip" --node bitable-1
```

**Validate before importing** — checks UTF-8 validity, `structure` ↔ `steps` parity (including nested `subSteps`), node shape (`operation` present, `js_code` not `code`, credentials under `auth` not `parameters`), and spel drift per node_tree type:

```bash
python anycross-creator/scripts/validate_flow.py out/flow.json
```

It is calibrated against real production exports, so an error means a real defect, not a style opinion. A clean run means the zip **will import** — it does not mean the flow is *correct*; wrong operation IDs and wrong field names pass every static check and fail at runtime.

**Package** — validates, then wraps into an importable zip (and refuses to pack a failing flow):

```bash
python anycross-creator/scripts/pack_flow.py out/flow.json "out/My Workflow.zip"
```

## What's inside

```
anycross-creator/
├── SKILL.md                        # the workflow Claude follows
├── references/
│   ├── flow-schema.md              # flow.json anatomy: structure/steps, node shape,
│   │                               #   value types, the four spel types, loop/branch/while
│   ├── connectors.md               # verified connector/operation inventory
│   ├── larkbase.md                 # Bitable field read/write formats, filters, extract() helpers
│   ├── integrations.md             # HTTP, Lark card, Google Docs, e-signature, subflow, cron
│   └── known-errors.md             # the error ledger — read before debugging, append after
├── scripts/
│   ├── inspect_export.py           # harvest IDs from a real export
│   ├── validate_flow.py            # pre-import checks
│   └── pack_flow.py                # validate + zip
└── assets/
    └── generator_skeleton.py       # starting point, with all the value-type helpers
```

## Some things it knows that cost real time to learn

- **Node IDs live inside an `operation` object** — `{connectorId, operationId, connectorName, connectorVersion}` — not at the top level of the node.
- **Script node output is namespaced under `.result`.** A handler returning `{rows: [...]}` in `script-2` is read as `$.script-2.result.rows`, not `$.script-2.rows`. Get this wrong and the reference resolves to null *silently* — no error, just empty data downstream.
- **spel has four `node_tree` types**, and only `json_path` repeats the full path in `expression`. `project_var` and `flow_variable` paths are relative (`$.config.x.y` pairs with path `x.y`), which looks like a bug and is not.
- **`$.config.*` project variables** let you keep `app_token`/`table_id` out of the flow file entirely — the value lives in AnyCross project settings, so the same JSON moves between environments unedited.
- **Non-ASCII is *not* what breaks imports.** A widely repeated claim says Vietnamese text or emoji cause `Unable to parse uploaded file`. It's false — AnyCross's own UI exports are full of raw non-ASCII. The real constraint is **valid UTF-8**; the usual culprit is writing the file through a locale codec (cp1252 on Windows). `ensure_ascii=True` is still a good default, but as a cheap safeguard, not a taboo.
- **LarkBase read shapes are not write shapes.** A Person field must be passed back as the raw object array, not an extracted name. A URL field needs `{link, text}` — a plain string returns `URLFieldConvFail`.

More in `references/known-errors.md`, each entry written as a reusable class of mistake.

## Verified vs. unverified

The skill is explicit about its own confidence, and so is this README:

- **Verified** against real exports: Bitable (both connector generations), script, http-client GET, cronjob, webhook, im (Lark cards), card_helper, contact, subflow, loop/branch/while, variable, delay, terminate.
- **Unverified** — inherited from an earlier version and never confirmed against a real export: `http-client` POST/PUT operation IDs, Google Docs, Google Drive, and the Zoho Sign patterns.

If you have an export using any of the unverified connectors, an issue or PR with the `inspect_export.py` output would firm those up for everyone.

## Contributing

The most useful contribution is a **connector ID from a tenant this skill hasn't seen**, or a **new entry in `known-errors.md`**. Two conventions keep that file useful:

1. **Record the class, not the incident.** "Wrote a plain string to a URL field → `URLFieldConvFail`" helps everyone; "fixed the link on the booking flow" helps nobody.
2. **No tenant data.** No app_tokens, table IDs, credential IDs, chat IDs, or real record IDs — use `<app_token>` placeholders. This file gets shared.

## Contact

Questions or help: **WhatsApp +84 96 246 02 65** — Phuc
