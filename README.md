# Pocketful - Dark Factory Hackathon Submission

This repository contains the result of a 3-seat AI Dark Factory building **Pocketful**, a wallet and payments system with strong concurrency and double-entry bookkeeping guarantees.

## The Factory

Our Dark Factory uses three distinct agent seats running on BAND Desktop:

1. **Architect**: Designs the API, database schema, and defines acceptance criteria.
2. **Developer**: Implements the backend (FastAPI, SQLite) and frontend (HTML/JS/CSS).
3. **Reviewer**: Tests the system, verifies invariants, and ensures container deployment works.

Read the complete factory breakdown in [FACTORY.md](FACTORY.md). The agent standing instructions are located in the `/mandates` folder.

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite (WAL mode for concurrency)
- **Frontend**: Vanilla HTML/CSS/JS (Single Page Application)
- **Deployment**: Docker

## How to Run

The application is fully containerized and requires no outbound network access at runtime.

```bash
docker-compose up --build
```

The app will be available at `http://localhost:8000`.

## Features

- **Double-Entry Bookkeeping**: Money is never created or destroyed. Every transfer creates balanced debit and credit ledger entries.
- **Computed Balances**: Balances are calculated dynamically from the ledger. There is no mutable `balance` column.
- **Integer Cents**: Floating point math is avoided entirely.
- **Idempotency**: Duplicate transfer requests (e.g., from network retries) are safely ignored.
- **Concurrency Safety**: `BEGIN IMMEDIATE` SQLite transactions prevent race conditions during concurrent transfers.
- **Refunds**: Completed transfers can be refunded, creating reverse ledger entries without altering historical data.

## Project Stages

The repository contains folders for each stage of the factory's output:
- `/stage-1`: Foundation (Database & Models)
- `/stage-2`: Core Features (Transfers & API)
- `/stage-3`: Hardening (Refunds & Idempotency)
- `/stage-4`: Polish (UI & Dockerization)
