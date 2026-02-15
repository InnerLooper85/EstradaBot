# Melt Banana Protocol (MBP) — Full Specification

Sean delivers requirements as a stream of prompts meant to be considered and acted upon together. The Melt Banana Protocol governs how Claude handles this batch-input workflow.

---

## Entering MBP

**Trigger phrases (any of these):**
- "Initiate Melt Banana Protocol"
- "Initiate MBP"

When MBP is initiated:

1. **STOP all immediate actions.** Do not write code, create files, run commands, or make any changes.
2. **Enter collection mode.** Your only job is to digest each prompt and update `memory.md`.
3. **Acknowledge each prompt with a numbered receipt:**
   - Example: `MBP #1: Rework the BLAST sequence to support 6-day weeks — captured.`
   - Example: `MBP #2: Add tooltip to schedule page showing core details — captured.`
   - Keep receipts short (one line). Show you understood the intent.
4. **Write collected requirements into `memory.md`** under a new section (e.g., `## MBP Session — [date]`). This is the primary deliverable during collection. Update it as each prompt arrives so nothing is lost if context compresses.
5. **Think, organize, and identify dependencies** between the collected items, but do NOT act on them yet.

---

## Exiting MBP (Go Signal)

**Trigger phrases (any of these):**
- "Melt Banana"
- "MELT BANANA"
- "Cook the Cavendish"

When the go signal is given:

1. **Present a consolidated briefing** — a single numbered summary of everything collected, grouped logically. This is a quick sanity check, not a blocker.
2. **Offer to deglaze.** End the briefing with: *"Want to deglaze before I execute?"* Sean can respond:
   - "No, go" / "Execute" / "Cook the Cavendish" → Proceed to step 3 immediately
   - "Yes" / "Deglaze the pan" → Run the Deglazing Protocol on the MBP collection (see `protocols/deglazing.md`), then return here after review
3. **Then execute immediately.** Full speed, autonomous, parallelize where possible, minimize questions. Only pause for genuinely destructive or irreversible actions.

---

## Aborting MBP

**Trigger phrases (any of these):**
- "Cancel MBP"
- "Stand down"
- "Abort MBP"

When aborted:
- Stop collection mode, return to normal interactive behavior.
- Keep anything already written to `memory.md` (don't delete collected notes).
- Acknowledge: "MBP cancelled. [N] items collected and saved to memory.md."

---

## Rules

- **Never break MBP to start building early.** Even if a prompt seems urgent or simple.
- **Priority ordering is Sean's job.** Collect everything; don't reorder or skip items.
- **Ask clarifying questions sparingly during MBP.** Only if a prompt is genuinely ambiguous. Prefer collecting and clarifying in the consolidated briefing.
- **MBP state survives context compression.** If you notice you're in MBP (check memory.md for an active MBP session section), stay in collection mode until the go signal.
