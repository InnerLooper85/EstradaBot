# Deglazing Protocol — Full Specification

A critical review protocol. Like deglazing a pan — recover the fond (what's good), identify what's burnt (bad ideas, stale info), and produce something clean before serving.

The Deglazing Protocol applies a critical eye to **plans, conversations, or MBP collections** before they become code. It asks: are these good ideas? What's missing? What will cause problems?

---

## Entering the Deglazing Protocol

**Trigger phrases (any of these):**
- "Initiate Deglazing Protocol"
- "Deglaze"
- "Deglaze [document name]"
- "Deglaze the pan"
- "Let's deglaze what we just [created/talked about/collected]"

---

## What Can Be Deglazed

The protocol works on three target types:

1. **A document** — a planning file, roadmap, or spec (e.g., "Deglaze MVP_2.0_Planning.md")
2. **The current conversation** — ideas discussed or decisions made in this session (e.g., "Let's deglaze what we just talked about")
3. **An MBP collection** — the batch of requirements collected during MBP, reviewed before the go signal executes (e.g., "Yes, deglaze the pan" when offered at the end of an MBP briefing)

If the target is unclear, ask.

---

## What Claude Does

When the Deglazing Protocol is initiated:

1. **Identify the target** (document, conversation, or MBP collection).

2. **Review the target and produce a Deglaze Report** with these sections:

   **THE FOND (Still Good)** — Ideas, items, or decisions that are solid. List briefly so Sean knows what's NOT being questioned.

   **BURNT BITS (Problems)** — Items that are bad ideas, stale, over-engineered, risky, or will cause quality problems. For each: what the issue is and why it's a problem. Be direct — this is the whole point of deglazing.

   **MISSING INGREDIENTS** — Things that should be there but aren't. Missing edge cases, untested assumptions, gaps in the plan, dependencies nobody mentioned.

   **OPEN QUESTIONS** — Decisions that need Sean's input before proceeding. Number these `DG-Q1`, `DG-Q2`, etc. For each: the question, why it matters, what's blocked.

   **RECOMMENDATIONS** — Specific changes to make, ordered by importance. For documents: proposed edits. For conversations/MBP: items to drop, modify, add, or reorder. These are proposals, not actions.

3. **Present the report and wait.** Do NOT edit documents or execute anything yet.

---

## After the Report

Sean will review and respond. Common patterns:
- "Approve all" or "Looks good, make the changes" → Apply all recommendations
- "Approve except #3 and #7" → Apply all except those, discuss the exceptions
- Inline corrections → Incorporate Sean's edits and apply
- "Let's discuss [topic]" → Switch to discussion, then return to the report
- "Drop items 2 and 5, then go" (after MBP deglaze) → Remove those from the plan, then execute the rest

---

## MBP Integration

The Deglazing Protocol is the natural quality gate between MBP collection and MBP execution:

1. MBP collects requirements → go signal given
2. Claude presents consolidated briefing
3. Claude offers: *"Want to deglaze before I execute?"*
4. If yes → Deglaze Report on the collected items. Focus on: Are these worth building? Any bad ideas? Missing anything? Ordering problems?
5. Sean approves/modifies → Claude executes the reviewed set

If Sean initiates MBP *during* a Deglaze session (wants to add new requirements), the Deglazing Protocol pauses. MBP collects new items. When MBP completes, the new items are incorporated into the Deglaze report before applying.

---

## Rules

- **Never edit or execute before presenting the report.** The report is a conversation starter, not a fait accompli.
- **Be genuinely critical.** The value of deglazing is catching problems early. Don't rubber-stamp. If something is a bad idea, say so and say why.
- **Keep the report scannable.** Bullet points, not paragraphs. Sean should be able to approve/reject individual items quickly.
- **Number open questions consistently.** `DG-Q1`, `DG-Q2`, etc. so Sean can reference them easily.
- **Track what was approved.** After applying changes to a document, update `planning/state.md` with a session log entry noting what was deglazed and what changed.
