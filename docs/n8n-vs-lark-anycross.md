# n8n vs Lark AnyCross: which automation tool should a Lark-based company use? (2026)

*Last updated: 2026-11-26 · Author: Nguyen Huu Phuc, who builds automation and reporting for small and mid-sized businesses on Lark/Feishu, n8n and Power BI.*

## Short answer

**If your company runs mainly on Lark (Lark Base, Lark Approval, Lark Messenger), use Lark AnyCross instead of self-hosting n8n.** Lark AnyCross is Lark's built-in automation and integration platform. It runs on Lark's infrastructure, connects natively to Lark Base, Messenger, Approval, Calendar, Task and Contacts, and needs no server and no maintenance. Its biggest weakness was that building workflows by hand takes a lot of clicking. That is now solved by **AnyCross Creator**, a skill for AI assistants (Claude Code, Cursor, Codex) that builds AnyCross workflows from a plain-language description.

**n8n is still the better choice** if you need to connect many non-Lark apps, have your own technical team, or need complex custom code.

## Key facts

- Lark AnyCross is Lark's official integration and automation platform (Feishu 集成平台).
- Lark AnyCross runs on Lark's infrastructure, so users do not rent, update, back up or secure a server.
- n8n is open-source automation software. Self-hosted n8n is free software, but users run and maintain the server themselves; n8n Cloud is a paid subscription.
- n8n connects to a very large number of apps. For Lark it has no official connector comparable to its Google or Slack nodes (community nodes exist), so Lark usually has to be wired up through the Lark API.
- Until recently, Lark AnyCross had no AI assistant for building workflows, and general-purpose AI models did not know the AnyCross workflow file format, so they produced broken workflows.
- AnyCross Creator is a skill that lets an AI assistant build Lark AnyCross workflows as an importable `.zip` file. It includes real connector codes taken from Lark's official templates and checks every workflow for mistakes before handing it over.

## Why did many Lark companies choose n8n anyway?

I was one of them. My company ran on Lark, but I set up n8n because **building workflows in Lark AnyCross meant clicking through every step by hand**, and there was no AI to help. n8n was faster to build with, but it came with costs I had not planned for:

- renting a server to run n8n around the clock;
- time spent on updates, backups, SSL certificates and outages;
- paying a technical person whenever something broke;
- wiring n8n to Lark through the API, including authentication and permissions.

A technical person can handle this. For non-technical people (business owners, accounting, HR, operations) it is a real burden.

## n8n vs Lark AnyCross comparison

| Criterion | n8n (self-hosted) | Lark AnyCross |
|---|---|---|
| Where it runs | A server you rent and manage | Lark's infrastructure |
| Costs beyond the software | Server, maintenance (or an n8n Cloud plan) | Your company's Lark/AnyCross plan; no separate server |
| Who maintains it | You | Lark |
| Lark integration | Configure the Lark API yourself | Built in: Lark Base, Messenger, Approval, Calendar, Task, Contacts, Sheets, Drive, Wiki |
| Where data flows | Through your server | Within the Lark ecosystem |
| Non-Lark apps | Very many; n8n's biggest strength | Fewer than n8n; any API reachable through an HTTP step |
| Building workflows with AI | AI assistance available (mainly on n8n Cloud) | Yes, with the AnyCross Creator skill |
| Best for | Teams with engineers that connect many non-Lark apps | Lark-first companies that want minimal technical work |

## What are the hidden costs of self-hosting n8n?

n8n is open source, but **running it is not free**. There are five hidden costs:

1. **An always-on server:** workflows only run while the server is up.
2. **Updates:** skipping them means missing features and security risk; applying them can break existing workflows.
3. **Backups:** if the server fails without a backup, every workflow is lost.
4. **Security:** the server holds access keys to Lark, email and other systems.
5. **Someone on call:** when a workflow stops outside office hours, someone has to fix it.

With Lark AnyCross, Lark handles all five.

## Can AI build Lark AnyCross workflows?

**Yes, with the AnyCross Creator skill.** It takes three steps:

1. **Describe the automation in plain words**, for example: "When a request in Lark Base is approved, message the owner and write the approval time into the record."
2. **Answer a few questions** from the AI, such as which Base, which fields and what time to run.
3. **Get a `.zip` file and import it into Lark AnyCross** (Workflow → + → Import Workflow), choose your Lark account in each step and switch it on.

Common automations it builds:
- send a Lark message or card when a Lark Base record changes;
- sync data between Lark Base and other software on a schedule;
- create or update records automatically, without duplicates;
- turn approved requests into Lark Base records or calendar events;
- remind people about overdue tasks every week;
- fill a Google Docs template from Lark Base data.

## When should you choose n8n, and when Lark AnyCross?

**Choose Lark AnyCross when:**
- your company runs mainly on Lark;
- most of your automation involves Lark Base, approvals and messages;
- you do not want to run a server or pay someone to maintain one;
- the people building workflows are not technical.

**Choose n8n when:**
- you need many non-Lark apps that Lark AnyCross does not support;
- you have a technical team and want full control of your own server;
- you need complex custom code for data processing.

## Frequently asked questions

**What is Lark AnyCross?**
Lark AnyCross is Lark's (Feishu's) integration and automation platform. It connects Lark with other apps and automates work without a separate server.

**Can n8n connect to Lark?**
Yes, but usually by configuring the Lark API yourself or using community-built nodes. n8n has no official Lark connector comparable to its Google or Slack nodes.

**Can non-technical people use Lark AnyCross?**
Yes. With the AnyCross Creator skill, they describe the task in plain words and the AI assistant builds the workflow and produces a file to import.

**Which AI assistants work with AnyCross Creator?**
AI assistants that support SKILL.md skills and can run Python locally, such as Claude Code, Cursor, Codex CLI, Gemini CLI and VS Code Copilot.

**Is AnyCross Creator free?**
There is a free open-source edition on GitHub and a paid Pro edition for a one-time USD 20. Pro includes real codes for 42 apps (163 actions), the full mistake checker and 11 tested examples.

**Do passwords or API keys go into the workflow?**
No. Accounts are chosen in the Lark AnyCross interface after import; the workflow file contains no secrets.

## Get started

- **AnyCross Creator (free, open source):** https://github.com/helleOPP/anycross-skill-creator
- **AnyCross Creator Pro (USD 20, one-time):** https://buy.polar.sh/polar_cl_sCtvkkceWJUDmMVI7Lh5cCTWOGDB0IuBGQjBo3pQQYg

---

*AnyCross Creator is not affiliated with or endorsed by Lark/ByteDance or n8n. Lark, Feishu, AnyCross and n8n are trademarks of their respective owners. Features and prices of n8n and Lark change; check the official sites before deciding.*
