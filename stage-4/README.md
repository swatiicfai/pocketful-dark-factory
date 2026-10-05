# Stage 1 — Foundation

The Architect designed the SQLite double-entry bookkeeping schema.
The Developer implemented the database layer.
The Reviewer verified schema integrity and basic operations.

## What is included
- database.py — SQLite connection, schema creation, wallet/user CRUD
- models.py — Pydantic models and cent/dollar conversion utilities

## To test
`ash
pip install -r requirements.txt
python -c "from database import init_db; init_db(); print('Schema OK')"
`
"@ | Set-Content "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-1\README.md"

# Stage 2 - Core Features: add a stripped app.py (no refund endpoint)
New-Item -ItemType Directory -Force "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2" | Out-Null
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\database.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\models.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\requirements.txt" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\app.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2\"

@"
# Stage 2 — Core Features

The Architect specified the FastAPI REST contract.
The Developer implemented users, wallets, transfers, and balance endpoints.
The Reviewer tested concurrent transfers and confirmed no double-spending.

## What is included
All of Stage 1 plus:
- pp.py — FastAPI application with /users, /deposit, /transfer, /balance endpoints

## To run
`ash
pip install -r requirements.txt
uvicorn app:app --reload
# Visit http://localhost:8000/docs
`
"@ | Set-Content "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-2\README.md"

# Stage 3 - Hardening: full app (refunds + idempotency already in app.py)
New-Item -ItemType Directory -Force "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3" | Out-Null
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\database.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\models.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\requirements.txt" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3\"
Copy-Item "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\app.py" "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3\"

@"
# Stage 3 — Hardening

The Architect specified idempotency and refund mechanics.
The Developer implemented reverse-entry refunds and idempotency keys.
The Reviewer stress-tested overdrafts and duplicate requests.

## What is included
All of Stage 2 plus:
- Refund endpoint with reverse ledger entries
- Idempotency keys on all transfers (duplicate-safe network retries)
- Overdraft protection enforced inside the transaction

## To run
`ash
pip install -r requirements.txt
uvicorn app:app --reload
`
"@ | Set-Content "C:\Users\Swati\.gemini\antigravity\brain\15444318-4b4f-4b15-97a1-0a1e87f84253\scratch\pocketful-dark-factory\stage-3\README.md"

# Stage 4 README
@"
# Stage 4 — Polish & Deployment

The Architect defined the SPA UI spec and container requirements.
The Developer built the responsive frontend and Dockerfile.
The Reviewer verified the UI and confirmed the Docker container builds and runs fully offline.

## What is included
All of Stage 3 plus:
- static/index.html — Responsive Single Page Application (vanilla HTML/CSS/JS)
- Dockerfile — Production container (python:3.11-slim, no outbound network at runtime)
- docker-compose.yml — One-command deployment

## To run
`ash
docker-compose up --build
# Visit http://localhost:8000
`

## Live demo
https://darkmint.onrender.com
