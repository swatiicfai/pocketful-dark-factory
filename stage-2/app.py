"""
Pocketful - A Wallet & Payments API
Built with FastAPI + SQLite + Double-Entry Bookkeeping

Key Design Principles:
- Money is stored as integer cents (no floating-point)
- Balance is computed from immutable ledger entries
- Every transfer creates exactly 2 ledger entries (debit + credit)
- Refunds create new entries, never delete old ones
- Idempotency keys prevent duplicate transfers
- Transactions use BEGIN IMMEDIATE for concurrent safety
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import init_db, create_user, get_user, list_users
from database import get_wallet_balance, deposit, transfer_money
from database import refund_transfer, get_transactions
from models import (
    CreateUserRequest, DepositRequest, TransferRequest,
    dollars_to_cents, cents_to_dollars
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Pocketful",
    description="A wallet & payments API with double-entry bookkeeping",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the frontend."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Pocketful API", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pocketful"}


# ==================== USER ENDPOINTS ====================

@app.post("/api/users")
async def api_create_user(request: CreateUserRequest):
    """Create a new user with an associated wallet."""
    try:
        user = create_user(request.name, request.email)
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "wallet_id": user["wallet_id"],
            "created_at": user["created_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/users/{user_id}")
async def api_get_user(user_id: int):
    """Get user details by ID."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users")
async def api_list_users():
    """List all users."""
    return list_users()


# ==================== WALLET ENDPOINTS ====================

@app.get("/api/wallets/{wallet_id}/balance")
async def api_get_balance(wallet_id: int):
    """
    Get wallet balance, computed from ledger entries.
    Balance = SUM(credits) - SUM(debits)
    """
    balance_cents = get_wallet_balance(wallet_id)
    return {
        "wallet_id": wallet_id,
        "balance": cents_to_dollars(balance_cents),
        "balance_cents": balance_cents
    }


@app.post("/api/wallets/{wallet_id}/deposit")
async def api_deposit(wallet_id: int, request: DepositRequest):
    """Deposit money into a wallet (transfer from system wallet)."""
    try:
        amount_cents = dollars_to_cents(request.amount)
        transfer = deposit(wallet_id, amount_cents, request.description)
        return {
            "id": transfer["id"],
            "wallet_id": wallet_id,
            "amount": request.amount,
            "type": "DEPOSIT",
            "status": transfer["status"],
            "created_at": transfer["created_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/wallets/{wallet_id}/transactions")
async def api_get_transactions(wallet_id: int):
    """Get transaction history for a wallet."""
    transactions = get_transactions(wallet_id)
    result = []
    for t in transactions:
        result.append({
            "id": t["id"],
            "from_wallet_id": t["from_wallet_id"],
            "to_wallet_id": t["to_wallet_id"],
            "from_user": t["from_user_name"],
            "to_user": t["to_user_name"],
            "amount": cents_to_dollars(t["amount_cents"]),
            "type": t["transfer_type"],
            "status": t["status"],
            "description": t["description"],
            "created_at": t["created_at"]
        })
    return result


# ==================== TRANSFER ENDPOINTS ====================

@app.post("/api/transfers")
async def api_transfer(request: TransferRequest):
    """
    Transfer money between wallets.
    Uses idempotency keys to prevent duplicates.
    Checks balance inside a serialized transaction.
    """
    try:
        amount_cents = dollars_to_cents(request.amount)
        transfer = transfer_money(
            from_wallet_id=request.from_wallet_id,
            to_wallet_id=request.to_wallet_id,
            amount_cents=amount_cents,
            description=request.description,
            idempotency_key=request.idempotency_key
        )
        return {
            "id": transfer["id"],
            "from_wallet_id": transfer["from_wallet_id"],
            "to_wallet_id": transfer["to_wallet_id"],
            "amount": request.amount,
            "type": transfer["transfer_type"],
            "status": transfer["status"],
            "idempotency_key": transfer["idempotency_key"],
            "created_at": transfer["created_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/transfers/{transfer_id}/refund")
async def api_refund(transfer_id: int):
    """
    Refund a completed transfer.
    Creates reverse ledger entries (never deletes original).
    """
    try:
        refund = refund_transfer(transfer_id)
        return {
            "id": refund["id"],
            "original_transfer_id": refund["original_transfer_id"],
            "amount": cents_to_dollars(refund["amount_cents"]),
            "type": "REFUND",
            "status": refund["status"],
            "created_at": refund["created_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
