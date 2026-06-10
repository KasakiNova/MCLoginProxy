# coding=utf-8
"""SQLite-backed account database with schema migration support.

Table ``accounts`` uses a composite primary key ``(uuid, server)`` so
the same Minecraft UUID can appear on different authentication servers.

Thread safety is achieved via ``threading.local()`` — each thread
gets its own SQLite connection.
"""
import os
import sqlite3
import threading

import modules.globalVariables as gVar


def check_and_migrate_db() -> bool:
    """Detect old ``accounts`` schema (uuid-only PK) and migrate.

    Returns:
        True if a migration was performed, False otherwise.
    """
    if not os.path.isfile(gVar.accountsInfoDB):
        return False

    conn = sqlite3.connect(gVar.accountsInfoDB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts'"
    )
    row = cursor.fetchone()
    if not row or 'uuid TEXT PRIMARY KEY' not in row[0]:
        conn.close()
        return False

    conn.executescript('''
        CREATE TABLE IF NOT EXISTS accounts_new (
            uuid   TEXT    NOT NULL,
            name   TEXT    NOT NULL,
            server INTEGER NOT NULL,
            baned  INTEGER NOT NULL CHECK (baned IN (0, 1)),
            PRIMARY KEY (uuid, server)
        );
        INSERT OR IGNORE INTO accounts_new SELECT * FROM accounts;
        DROP TABLE accounts;
        ALTER TABLE accounts_new RENAME TO accounts;
    ''')
    conn.close()
    return True


class AccountInfoDB:
    """Thread-local access to the ``accounts`` SQLite table."""

    def __init__(self) -> None:
        self._db_path = gVar.accountsInfoDB
        self.local = threading.local()
        self.create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Return (or create) the per-thread SQLite connection."""
        if not hasattr(self.local, "connection"):
            self.local.connection = sqlite3.connect(self._db_path)
        return self.local.connection

    def create_table(self) -> None:
        """Create the ``accounts`` table if it does not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                uuid   TEXT    NOT NULL,
                name   TEXT    NOT NULL,
                server INTEGER NOT NULL,
                baned  INTEGER NOT NULL CHECK (baned IN (0, 1)),
                PRIMARY KEY (uuid, server)
            )
            ''')
            conn.commit()

    def insert_account(self, uuid: str, name: str, server: int,
                       ban: bool = False) -> None:
        """Insert a new account row; silently skip on PK conflict."""
        ban_value = 1 if ban else 0
        sql = (
            "INSERT OR IGNORE INTO accounts (uuid, name, server, baned) "
            "VALUES (?, ?, ?, ?)"
        )
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (uuid, name, server, ban_value))

    def get_account_by_name(self, name: str) -> list:
        """Return all rows matching *name* (case-insensitive by convention)."""
        sql = "SELECT * FROM accounts WHERE name = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (name,))
            return cursor.fetchall()

    def get_name_by_uuid(self, uuid: str, server: int) -> str | None:
        """Return the stored name for a given *uuid* and *server*."""
        sql = "SELECT name FROM accounts WHERE uuid = ? AND server = ? LIMIT 1"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (uuid, server))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_baned_by_uuid(self, uuid: str, server: int) -> bool | None:
        """Return the ``baned`` flag for *uuid* on *server*."""
        sql = "SELECT baned FROM accounts WHERE uuid = ? AND server = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (uuid, server))
            result = cursor.fetchone()
            return bool(result[0]) if result else None

    def update_account_name(self, uuid: str, server: int,
                            new_name: str) -> None:
        """Update the name for a specific *uuid* on *server*."""
        sql = "UPDATE accounts SET name = ? WHERE uuid = ? AND server = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (new_name, uuid, server))

    def set_account_baned(self, uuid: str, server: int,
                          status: int) -> bool:
        """Set the ``baned`` flag (0 or 1) for *uuid* on *server*."""
        sql = "UPDATE accounts SET baned = ? WHERE uuid = ? AND server = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (status, uuid, server))
            return True
        except sqlite3.Error:
            return False

    def check_uuid_exists(self, user_uuid: str, server_id: int) -> bool:
        """Return True if *user_uuid* already exists on *server_id*."""
        sql = (
            "SELECT * FROM accounts "
            "WHERE uuid = ? AND server = ? LIMIT 1"
        )
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_uuid, server_id))
            return cursor.fetchone() is not None

    def close(self) -> None:
        """Close the per-thread SQLite connection (if open)."""
        if hasattr(self.local, "connection"):
            self.local.connection.close()
            del self.local.connection
