# AnyCross Creator — build Lark AnyCross workflows from `flow.json`

Documentation and tooling for the **AnyCross** workflow file format (`flow.json`), packaged as an **AI agent skill** that generates, validates, and packages AnyCross workflows into importable `.zip` files.

AnyCross is Lark/Feishu's automation platform (their answer to Zapier or Make). It has no public schema documentation for the exported workflow file — so everything here was **reverse-engineered from real, running exports**: connector IDs, operation IDs, the node shape, the four spel reference types, LarkBase field read/write formats, and the error messages you hit along the way.

## Works with any AI coding agent — or none

The packaging follows the [Agent Skills](https://code.claude.com/docs/en/skills) convention (a `SKILL.md` plus supporting files), which [Claude Code](https://claude.com/claude-code) loads automatically. But **nothing inside is Claude-specific**:

| Layer | What it is | Portable to |
|---|---|---|
| `SKILL.md` | The build procedure, in plain markdown | Any agent that reads instructions — Cursor, Copilot, Codex, Gemini CLI, Windsurf, Cline. Paste it as context or a system prompt. |
| `references/` | The AnyCross schema documentation | Anything. It's just markdown. Feed it to your model, or read it yourself. |
| `scripts/` | `inspect_export.py`, `validate_flow.py`, `pack_flow.py` | Plain Python 3.8+, standard library only. No AI involved — run them from a terminal or a CI job. |

So use it three ways: let an agent drive the whole loop, hand your model the reference files as context, or ignore the AI part entirely and use the scripts plus docs by hand.

This is a **documentation-first** project that happens to ship as a skill — the schema knowledge is the asset, and it outlives whichever agent you point at it.

> Hi everyone,
>
> This is a skill for creating AnyCross workflows — I hope you find it useful.
> If you need any help, contact me at **phucvn2019@gmail.com**
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

```bash
git clone https://github.com/helleOPP/anycross-skill-creator.git
```

Requirements: **Python 3.8+**. No third-party packages — standard library only.

**Claude Code** — drop the folder into a skills directory and it loads on its own:

```bash
cp -r anycross-skill-creator/anycross-creator ~/.claude/skills/              # every project
cp -r anycross-skill-creator/anycross-creator /path/to/project/.claude/skills/   # one project
```

Check it registered with `/anycross-creator`.

**Cursor / Copilot / Codex / Gemini CLI / any other agent** — there's no plugin to install. Point your model at the files:

- Paste `anycross-creator/SKILL.md` in as context, a system prompt, or a rules file (`.cursorrules` and friends).
- When it starts building, give it the relevant `references/*.md` too — `connectors.md` and `flow-schema.md` carry the IDs and shapes it would otherwise hallucinate.

**No agent at all** — the scripts stand alone:

```bash
python anycross-creator/scripts/inspect_export.py "My Flow.zip"
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

## Troubleshooting AnyCross errors

The errors below are the ones that cost real hours, with the actual cause rather than the folklore. Full ledger, with the reasoning behind each, in [`references/known-errors.md`](anycross-creator/references/known-errors.md).

### "Unable to parse uploaded file"

Your `flow.json` is not valid UTF-8. On Windows the usual culprit is `open(path, "w")` without `encoding=`, which writes through the cp1252 locale codec and mangles any non-Latin text.

**It is *not* caused by non-ASCII characters**, despite that claim being widely repeated. AnyCross's own UI exports are full of raw Vietnamese and emoji. Write with `encoding="utf-8"`, or dump with `ensure_ascii=True` if you want the codec question to never arise.

### `URLFieldConvFail`

You wrote a plain string into a LarkBase URL field. It needs an object:

```javascript
{link: "https://example.com", text: "Open"}   // even when link and text are identical
```

### A Person field writes blank, or the node rejects the value

You read the Person field, ran it through `extract()` into a display name, and wrote the string back. LarkBase wants the object array it gave you — pass `f['<PersonField>'] || []` through untouched. Read shapes and write shapes are not the same thing.

### A spel reference silently resolves to null

No error, just empty data downstream. Three usual causes:

1. **Missing `.result`** — script node output is namespaced. A handler returning `{rows: [...]}` in `script-2` is `$.script-2.result.rows`, not `$.script-2.rows`.
2. **`expression` and `node_tree.path` disagree** because only one was edited. Generate both from one variable.
3. The referenced node ID doesn't exist — a typo, or renumbering during a rewrite.

`validate_flow.py` catches (2) and (3).

### The script node imports empty

The parameter key is `js_code`, not `code`.

### A Bitable search returns nothing, on a table that clearly has rows

Either the operation ID belongs to the other Bitable connector generation (v2.0 and v2.7 have different IDs *and* different parameter names for the same action), or your filter has an empty `conditions` array — which means "no filter, return everything", not "match nothing".

### An `im` node fails to send to a group

The bot behind the credential is not a member of the target chat. No amount of JSON fixing helps — add the bot to the group in Lark.

## Verified vs. unverified

The skill is explicit about its own confidence, and so is this README:

- **Verified** against real exports: Bitable (both connector generations), script, http-client GET, cronjob, webhook, im (Lark cards), card_helper, contact, subflow, loop/branch/while, variable, delay, terminate.
- **Unverified** — inherited from an earlier version and never confirmed against a real export: `http-client` POST/PUT operation IDs, Google Docs, Google Drive, and the Zoho Sign patterns.

If you have an export using any of the unverified connectors, an issue or PR with the `inspect_export.py` output would firm those up for everyone.

## Contributing

The most useful contribution is a **connector ID from a tenant this skill hasn't seen**, or a **new entry in `known-errors.md`**. Two conventions keep that file useful:

1. **Record the class, not the incident.** "Wrote a plain string to a URL field → `URLFieldConvFail`" helps everyone; "fixed the link on the booking flow" helps nobody.
2. **No tenant data.** No app_tokens, table IDs, credential IDs, chat IDs, or real record IDs — use `<app_token>` placeholders. This file gets shared.

## License

[MIT](LICENSE) — use it, fork it, modify it, ship it in your own work, commercially or not. Just keep the copyright notice. No warranty.

## Contact

Stuck on a flow, or want one built for you? Get in touch — **phucvn2019@gmail.com**

I build automation and analytics for SMEs: Lark/Feishu (AnyCross, Lark Base), n8n, and BI/reporting — mostly around **supply chain and operations**, where the flow has to survive contact with how people actually work, not just pass a demo.

— Phuc
