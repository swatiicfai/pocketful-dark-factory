# DarkMint — Pocketful Dark Factory

> **Live Demo**: https://darkmint.onrender.com  
> **Hackathon**: WeAreDevelopers Hackathon 2026 — Agent Builder Track (Internet of Agents)

A three-seat AI Dark Factory that autonomously designed, built, tested, and deployed **DarkMint** — a production-grade wallet and payments system with double-entry bookkeeping guarantees.

**No human wrote any application code. No human steered any stage. The single human input was the initial problem statement dispatched to the Architect.**

---

## The Factory

Our Dark Factory uses three distinct agent seats running on BAND Desktop, each with a strict mandate and no overlap of responsibilities:

| Seat | Role | Mandate |
|------|------|---------|
| 1 | **Architect** | Designs the system, plans stages, sets acceptance criteria |
| 2 | **Developer** | Writes all production code based strictly on Architect's plan |
| 3 | **Reviewer** | Tests, verifies invariants, stress-tests, approves or rejects each stage |

Read the complete factory breakdown in [FACTORY.md](FACTORY.md).  
Agent standing instructions are in [`/mandates`](mandates/).

---

## What DarkMint Does

DarkMint is a wallet and payments REST API + SPA frontend that solves the hardest financial software problems:

| Problem | DarkMint's Solution |
|---------|-------------------|
| Race conditions | `BEGIN IMMEDIATE` SQLite transactions |
| Floating point errors | Integer cents only — no floats ever |
| Duplicate charges | Idempotency keys on every transfer |
| Audit trail gaps | Immutable double-entry ledger — no balance column |
| Bad refunds | Reverse ledger entries — historical data never altered |

**Key invariant**: `SUM(all ledger entries) = 0` — always. Money is never created or destroyed.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115.0 (Python 3.11) |
| Database | SQLite with WAL mode |
| Frontend | Vanilla HTML/CSS/JS (Single Page Application) |
| Server | Uvicorn 0.30.0 |
| Validation | Pydantic 2.9.0 |
| Deployment | Docker + docker-compose |
| AI Platform | BAND Desktop (3-seat Dark Factory) |

---

## How to Run

```bash
# Option 1: Docker (recommended)
docker-compose up --build
# App available at http://localhost:8000

# Option 2: Local
pip install -r requirements.txt
uvicorn app:app --reload
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Create a user |
| `GET` | `/users/{id}/balance` | Get computed balance |
| `POST` | `/transfers` | Transfer between wallets (idempotent) |
| `POST` | `/transfers/{id}/refund` | Refund a transfer |
| `GET` | `/ledger` | View all ledger entries |

---

## Features

- **Double-Entry Bookkeeping**: Every transfer creates balanced debit and credit ledger entries. Money is never created or destroyed.
- **Computed Balances**: Balances are calculated dynamically from the ledger. There is no mutable `balance` column.
- **Integer Cents**: Floating point math is avoided entirely. `$10.50` is stored as `1050`.
- **Idempotency**: Duplicate transfer requests (e.g., from network retries) are safely ignored via unique `idempotency_key`.
- **Concurrency Safety**: `BEGIN IMMEDIATE` SQLite transactions prevent race conditions during concurrent transfers.
- **Refunds**: Completed transfers can be refunded, creating reverse ledger entries without altering historical data.

---

## Factory Stages

The factory completed 4 stages autonomously:

| Stage | What Happened |
|-------|--------------|
| **Stage 1: Foundation** | Architect designed SQLite schema. Developer built `database.py` + `models.py`. Reviewer verified schema and basic operations. |
| **Stage 2: Core Features** | Architect specified FastAPI contract. Developer built `app.py`. Reviewer tested concurrent transfers and verified no double-spending. |
| **Stage 3: Hardening** | Architect specified idempotency + refund mechanics. Developer implemented reverse-entry refunds and idempotency keys. Reviewer stress-tested overdrafts and duplicate requests. |
| **Stage 4: Polish & Deployment** | Architect defined UI spec and container requirements. Developer built the SPA and Dockerfile. Reviewer verified the UI and confirmed Docker container builds and runs offline. |
