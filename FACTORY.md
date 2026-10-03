# Pocketful Dark Factory

## Overview
A three-seat AI dark factory that autonomously builds, tests, and verifies a financial application. The factory operates as a software production process where no human directs individual steps.

## Factory Architecture
- **Architect (Seat 1)**: Designs the system, plans stages, dictates the data model, and issues bug fix instructions when tests fail.
- **Developer (Seat 2)**: Writes all production code (FastAPI, SQLite, HTML/CSS/JS) strictly according to the Architect's plan.
- **Reviewer (Seat 3)**: Verifies the code, tests endpoints, checks UI logic, and tests the Docker container. Reports failures back to the room.

## How the Factory Works

### Stage 1: Foundation
- Architect designs the core SQLite schema, emphasizing double-entry bookkeeping.
- Developer implements `database.py` and `models.py`.
- Reviewer verifies the schema and basic database operations.

### Stage 2: Core Features
- Architect defines the API contract for the FastAPI backend.
- Developer implements `app.py` (users, transfers, balances).
- Reviewer tests concurrent transfers and verifies no double-spending occurs.

### Stage 3: Hardening
- Architect specifies idempotency and refund mechanisms.
- Developer implements refund logic (reversing ledger entries) and idempotency keys.
- Reviewer stress-tests failure modes (overdrafts, duplicate requests).

### Stage 4: Polish & Deployment
- Architect defines the responsive UI requirements and container spec.
- Developer builds the single-page application (`static/index.html`) and `Dockerfile`.
- Reviewer tests the UI and verifies the container builds and runs without outbound network access.

## Design Decisions
- **Double-Entry Bookkeeping**: A mutable balance field is dangerous. We use an immutable ledger. Every transaction has a debit and credit.
- **Computed Balances**: Wallet balances are derived dynamically (`SUM(credits) - SUM(debits)`), ensuring absolute mathematical consistency.
- **Integer Cents**: Floating-point math is avoided completely. All money is stored as integers in the database.
- **Serializable Transactions**: `BEGIN IMMEDIATE` is used in SQLite to prevent concurrent race conditions during transfers.
- **Idempotency**: Network retries will not result in double charges due to unique transaction keys.

## Key Invariant
The sum of all ledger entries across all wallets must *always* equal zero. Money is never created or destroyed. Deposits are handled as transfers from a dedicated "System Wallet".

## Error Recovery
If the Reviewer catches an issue (e.g., a concurrent transfer test fails), it posts the specific error to the BAND room. The Architect adjusts the plan if necessary, and the Developer patches the code. The human only observes.
