# FACTORY.md — Dark Factory Specification

This file is the **complete standing specification** for the Dark Factory. Any team can clone this repository, point it at a different problem statement, and run the same factory to build a different product.

---

## Factory Purpose

A Dark Factory is a closed-loop, autonomous software production system. Three AI agents — an Architect, a Developer, and a Reviewer — collaborate in a shared BAND room to build, test, and deploy software with **zero human intervention** after the initial problem statement is dispatched.

**The human's only input**: A single message to the Architect describing the problem to solve.  
**The human's only output**: The final deployed application.

---

## Seat Setup

### Seat 1 — Architect
- **Model**: Hermes (BAND Desktop)
- **Mandate file**: [`mandates/architect.md`](mandates/architect.md)
- **Access**: Read-only to the BAND room. Writes plans to the room. Cannot touch files or run code.
- **Cost (this run)**: ~12 Architect messages across 4 stages

### Seat 2 — Developer
- **Model**: Hermes (BAND Desktop)
- **Mandate file**: [`mandates/developer.md`](mandates/developer.md)
- **Access**: Full filesystem access. Reads Architect plans from the room. Writes code to disk. Posts file updates to the room.
- **Cost (this run)**: ~38 Developer messages, ~420 lines of code written

### Seat 3 — Reviewer
- **Model**: Hermes (BAND Desktop)
- **Mandate file**: [`mandates/reviewer.md`](mandates/reviewer.md)
- **Access**: Terminal access. Runs tests, curls endpoints, checks Docker. Posts TEST PASSED or TEST FAILED to the room.
- **Cost (this run)**: ~24 Reviewer messages, 0 stages approved without code changes

---

## How to Run This Factory on a New Problem

1. Clone this repository
2. Replace the contents of `/mandates` if needed (or keep them — the mandates are generic)
3. Open BAND Desktop and create a new Room
4. Add three agent seats using the mandate files in `/mandates`
5. Send a single message to `@Architect` describing the problem you want solved
6. Observe. Do not intervene.

---

## Stage Gate Protocol

Each stage must complete the following gate before moving to the next:

```
Architect  → Posts plan with acceptance criteria
Developer  → Implements according to plan, posts file list
Reviewer   → Tests against acceptance criteria
           → If PASS: posts "STAGE N: PASSED — ready for next stage"
           → If FAIL: posts specific error, Architect adjusts, Developer patches
```

**No human approval is needed at any gate.** The Reviewer is the sole gatekeeper.

---

## Design Rationale (This Run: DarkMint)

### Why Double-Entry Bookkeeping?
A mutable `balance` column is dangerous. A bug that increments instead of decrements creates money. With double-entry bookkeeping, every debit has a matching credit. `SUM(all_entries) = 0` is a mathematical invariant that can be checked at any time.

### Why Integer Cents?
`0.1 + 0.2 != 0.3` in IEEE 754 floating point. Financial software must never use floats. Every amount is stored as an integer number of cents (`$10.50 → 1050`).

### Why `BEGIN IMMEDIATE`?
SQLite's default isolation allows two concurrent reads of the same balance before either transfer commits — causing double-spending. `BEGIN IMMEDIATE` acquires a write lock at transaction start, serialising all transfers.

### Why Idempotency Keys?
Mobile clients retry on timeout. Without idempotency, a network error after a transfer commits but before the response is received causes a duplicate charge. Unique `idempotency_key` fields prevent this.

### Why No Balance Column?
Balances derived from `SUM(credits) - SUM(debits)` are always mathematically consistent with the ledger. A stored balance column can drift from the ledger due to bugs. Computed balances cannot.

---

## Error Recovery in This Run

The factory encountered and autonomously resolved the following issues:

| Stage | Issue | Recovery |
|-------|-------|----------|
| Stage 2 | Reviewer found concurrent transfer test allowed overdraft | Architect added `BEGIN IMMEDIATE` lock spec → Developer patched → Reviewer re-tested: PASS |
| Stage 3 | Reviewer found duplicate idempotency key returned 500 instead of 200 | Architect specified `ON CONFLICT IGNORE` semantics → Developer patched → Reviewer confirmed: PASS |
| Stage 4 | Reviewer found Docker container exposed port 8080 instead of 8000 | Architect updated container spec → Developer fixed `Dockerfile` CMD → Reviewer verified: PASS |

**In all cases: zero human involvement. The Reviewer's failure report was the only input to the next iteration.**

---

## Measured Factory Costs

| Metric | Value |
|--------|-------|
| Total messages | ~74 agent messages |
| Lines of code | ~420 lines (Python + HTML/JS/CSS) |
| Stages completed | 4 / 4 |
| Human code written | 0 lines |
| Human approvals given | 0 |
| Human interventions | 0 |
| Bugs caught by Reviewer before human saw them | 3 |
| Bugs that escaped to production | 0 |

---

## Key Invariant (Enforced by Reviewer at Every Stage)

```sql
SELECT SUM(amount) FROM ledger_entries;
-- Must always equal 0
```

Money is never created or destroyed. Deposits are modelled as transfers from a dedicated `system_wallet`. Every credit has an equal and opposite debit.

---

## Reusability

This factory is **problem-agnostic**. The mandates in `/mandates` contain no references to wallets, payments, or any specific domain. To build a different product:

1. Keep the mandate files as-is
2. Change only the initial `@Architect` message
3. The factory will design, build, test, and deploy whatever you specify

The factory has been validated on: wallet/payments (this run). It is ready for: inventory management, booking systems, task trackers, and any CRUD-heavy backend application.
