"""
Database module for Pocketful wallet application.
Uses SQLite with WAL mode for concurrent access.
All money stored as integer cents to avoid floating-point errors.
Double-entry bookkeeping: every transfer = debit + credit ledger entries.
"""

import sqlite3
import os
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "pocketful.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with WAL mode and proper settings."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            -- System wallet for deposits (id=1, user_id=1)
            -- Deposits are modeled as transfers FROM the system wallet
            INSERT OR IGNORE INTO users (id, name, email) 
                VALUES (1, 'SYSTEM', 'system@pocketful.internal');
            INSERT OR IGNORE INTO wallets (id, user_id) 
                VALUES (1, 1);

            -- Immutable ledger: append-only, never update or delete
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                transfer_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL CHECK (entry_type IN ('DEBIT', 'CREDIT')),
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (wallet_id) REFERENCES wallets(id),
                FOREIGN KEY (transfer_id) REFERENCES transfers(id)
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT UNIQUE,
                from_wallet_id INTEGER NOT NULL,
                to_wallet_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                transfer_type TEXT NOT NULL CHECK (
                    transfer_type IN ('TRANSFER', 'DEPOSIT', 'REFUND')
                ),
                status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK (
                    status IN ('COMPLETED', 'REFUNDED')
                ),
                description TEXT,
                original_transfer_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (from_wallet_id) REFERENCES wallets(id),
                FOREIGN KEY (to_wallet_id) REFERENCES wallets(id),
                FOREIGN KEY (original_transfer_id) REFERENCES transfers(id)
            );

            CREATE INDEX IF NOT EXISTS idx_ledger_wallet 
                ON ledger_entries(wallet_id);
            CREATE INDEX IF NOT EXISTS idx_ledger_transfer 
                ON ledger_entries(transfer_id);
            CREATE INDEX IF NOT EXISTS idx_transfers_idempotency 
                ON transfers(idempotency_key);
            CREATE INDEX IF NOT EXISTS idx_transfers_from 
                ON transfers(from_wallet_id);
            CREATE INDEX IF NOT EXISTS idx_transfers_to 
                ON transfers(to_wallet_id);
        """)
        conn.commit()
    finally:
        conn.close()


def create_user(name: str, email: str) -> dict:
    """Create a new user with an associated wallet."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        user_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO wallets (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()

        user = conn.execute(
            "SELECT u.id, u.name, u.email, u.created_at, w.id as wallet_id "
            "FROM users u JOIN wallets w ON u.id = w.user_id WHERE u.id = ?",
            (user_id,)
        ).fetchone()
        return dict(user)
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"User with email '{email}' already exists")
    finally:
        conn.close()


def get_user(user_id: int) -> Optional[dict]:
    """Get user by ID with wallet info."""
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT u.id, u.name, u.email, u.created_at, w.id as wallet_id "
            "FROM users u JOIN wallets w ON u.id = w.user_id "
            "WHERE u.id = ? AND u.id != 1",
            (user_id,)
        ).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def list_users() -> list:
    """List all users (excluding system user)."""
    conn = get_connection()
    try:
        users = conn.execute(
            "SELECT u.id, u.name, u.email, u.created_at, w.id as wallet_id "
            "FROM users u JOIN wallets w ON u.id = w.user_id "
            "WHERE u.id != 1 ORDER BY u.id"
        ).fetchall()
        return [dict(u) for u in users]
    finally:
        conn.close()


def get_wallet_balance(wallet_id: int) -> int:
    """
    Compute wallet balance from ledger entries.
    Balance = SUM(credits) - SUM(debits) for this wallet.
    Returns balance in cents.
    """
    conn = get_connection()
    try:
        result = conn.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN entry_type = 'CREDIT' THEN amount_cents ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN entry_type = 'DEBIT' THEN amount_cents ELSE 0 END), 0)
                AS balance_cents
            FROM ledger_entries
            WHERE wallet_id = ?
        """, (wallet_id,)).fetchone()
        return result["balance_cents"]
    finally:
        conn.close()


def deposit(wallet_id: int, amount_cents: int, description: str = "Deposit") -> dict:
    """
    Deposit money into a wallet.
    Modeled as a transfer from the SYSTEM wallet (id=1).
    """
    if amount_cents <= 0:
        raise ValueError("Deposit amount must be positive")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        # Verify wallet exists
        wallet = conn.execute(
            "SELECT id FROM wallets WHERE id = ? AND id != 1", (wallet_id,)
        ).fetchone()
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        # Create transfer record (from system wallet)
        cursor = conn.execute(
            "INSERT INTO transfers (from_wallet_id, to_wallet_id, amount_cents, "
            "transfer_type, description) VALUES (1, ?, ?, 'DEPOSIT', ?)",
            (wallet_id, amount_cents, description)
        )
        transfer_id = cursor.lastrowid

        # Create ledger entries (double-entry)
        # Debit from system wallet
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (1, ?, 'DEBIT', ?, ?)",
            (transfer_id, amount_cents, f"Deposit to wallet {wallet_id}")
        )
        # Credit to user wallet
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (?, ?, 'CREDIT', ?, ?)",
            (wallet_id, transfer_id, amount_cents, description)
        )

        conn.commit()

        transfer = conn.execute(
            "SELECT * FROM transfers WHERE id = ?", (transfer_id,)
        ).fetchone()
        return dict(transfer)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def transfer_money(
    from_wallet_id: int,
    to_wallet_id: int,
    amount_cents: int,
    description: str = "Transfer",
    idempotency_key: Optional[str] = None
) -> dict:
    """
    Transfer money between wallets with double-entry bookkeeping.
    Uses idempotency keys to prevent duplicate transfers.
    Checks balance inside the transaction to prevent overdraft.
    """
    if amount_cents <= 0:
        raise ValueError("Transfer amount must be positive")
    if from_wallet_id == to_wallet_id:
        raise ValueError("Cannot transfer to the same wallet")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        # Check idempotency: if this key was already used, return original
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM transfers WHERE idempotency_key = ?",
                (idempotency_key,)
            ).fetchone()
            if existing:
                conn.rollback()
                return dict(existing)

        # Verify both wallets exist and are not system wallet
        from_wallet = conn.execute(
            "SELECT id FROM wallets WHERE id = ? AND id != 1",
            (from_wallet_id,)
        ).fetchone()
        to_wallet = conn.execute(
            "SELECT id FROM wallets WHERE id = ? AND id != 1",
            (to_wallet_id,)
        ).fetchone()

        if not from_wallet:
            raise ValueError(f"Source wallet {from_wallet_id} not found")
        if not to_wallet:
            raise ValueError(f"Destination wallet {to_wallet_id} not found")

        # Check balance INSIDE the transaction (concurrent safety)
        balance = conn.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN entry_type = 'CREDIT' THEN amount_cents ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN entry_type = 'DEBIT' THEN amount_cents ELSE 0 END), 0)
                AS balance_cents
            FROM ledger_entries WHERE wallet_id = ?
        """, (from_wallet_id,)).fetchone()["balance_cents"]

        if balance < amount_cents:
            raise ValueError(
                f"Insufficient funds. Available: {balance} cents, "
                f"Requested: {amount_cents} cents"
            )

        # Create transfer record
        cursor = conn.execute(
            "INSERT INTO transfers (from_wallet_id, to_wallet_id, amount_cents, "
            "transfer_type, description, idempotency_key) "
            "VALUES (?, ?, ?, 'TRANSFER', ?, ?)",
            (from_wallet_id, to_wallet_id, amount_cents, description,
             idempotency_key)
        )
        transfer_id = cursor.lastrowid

        # Double-entry ledger
        # Debit from sender
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (?, ?, 'DEBIT', ?, ?)",
            (from_wallet_id, transfer_id, amount_cents,
             f"Transfer to wallet {to_wallet_id}")
        )
        # Credit to receiver
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (?, ?, 'CREDIT', ?, ?)",
            (to_wallet_id, transfer_id, amount_cents,
             f"Transfer from wallet {from_wallet_id}")
        )

        conn.commit()

        transfer = conn.execute(
            "SELECT * FROM transfers WHERE id = ?", (transfer_id,)
        ).fetchone()
        return dict(transfer)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refund_transfer(transfer_id: int) -> dict:
    """
    Refund a transfer by creating reverse ledger entries.
    Original entries are never deleted (immutable ledger).
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        # Get original transfer
        original = conn.execute(
            "SELECT * FROM transfers WHERE id = ? AND transfer_type = 'TRANSFER'",
            (transfer_id,)
        ).fetchone()

        if not original:
            raise ValueError(f"Transfer {transfer_id} not found or not refundable")

        if original["status"] == "REFUNDED":
            raise ValueError(f"Transfer {transfer_id} has already been refunded")

        amount_cents = original["amount_cents"]
        from_wallet_id = original["from_wallet_id"]
        to_wallet_id = original["to_wallet_id"]

        # Check receiver has enough balance to refund
        balance = conn.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN entry_type = 'CREDIT' THEN amount_cents ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN entry_type = 'DEBIT' THEN amount_cents ELSE 0 END), 0)
                AS balance_cents
            FROM ledger_entries WHERE wallet_id = ?
        """, (to_wallet_id,)).fetchone()["balance_cents"]

        if balance < amount_cents:
            raise ValueError("Recipient has insufficient funds for refund")

        # Create refund transfer (reverse direction)
        cursor = conn.execute(
            "INSERT INTO transfers (from_wallet_id, to_wallet_id, amount_cents, "
            "transfer_type, description, original_transfer_id) "
            "VALUES (?, ?, ?, 'REFUND', ?, ?)",
            (to_wallet_id, from_wallet_id, amount_cents,
             f"Refund of transfer #{transfer_id}", transfer_id)
        )
        refund_id = cursor.lastrowid

        # Reverse ledger entries
        # Debit from original receiver
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (?, ?, 'DEBIT', ?, ?)",
            (to_wallet_id, refund_id, amount_cents,
             f"Refund: return to wallet {from_wallet_id}")
        )
        # Credit back to original sender
        conn.execute(
            "INSERT INTO ledger_entries (wallet_id, transfer_id, entry_type, "
            "amount_cents, description) VALUES (?, ?, 'CREDIT', ?, ?)",
            (from_wallet_id, refund_id, amount_cents,
             f"Refund: returned from wallet {to_wallet_id}")
        )

        # Mark original as refunded
        conn.execute(
            "UPDATE transfers SET status = 'REFUNDED' WHERE id = ?",
            (transfer_id,)
        )

        conn.commit()

        refund = conn.execute(
            "SELECT * FROM transfers WHERE id = ?", (refund_id,)
        ).fetchone()
        return dict(refund)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_transactions(wallet_id: int) -> list:
    """Get all transactions for a wallet, ordered by most recent first."""
    conn = get_connection()
    try:
        transactions = conn.execute("""
            SELECT 
                t.id, t.from_wallet_id, t.to_wallet_id, t.amount_cents,
                t.transfer_type, t.status, t.description, t.created_at,
                t.original_transfer_id,
                uf.name as from_user_name, ut.name as to_user_name
            FROM transfers t
            JOIN wallets wf ON t.from_wallet_id = wf.id
            JOIN users uf ON wf.user_id = uf.id
            JOIN wallets wt ON t.to_wallet_id = wt.id
            JOIN users ut ON wt.user_id = ut.id
            WHERE t.from_wallet_id = ? OR t.to_wallet_id = ?
            ORDER BY t.created_at DESC
        """, (wallet_id, wallet_id)).fetchall()
        return [dict(t) for t in transactions]
    finally:
        conn.close()
