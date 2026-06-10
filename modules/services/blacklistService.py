# coding=utf-8
"""Player blacklist service backed by the ``accounts`` table.

Provides ban/unban by player name (with optional index for
disambiguating players who share a name across servers).
"""
from modules.database.accountInfoDB import AccountInfoDB


class BlacklistService:
    """Check and update ban status for Minecraft player accounts."""

    def __init__(self) -> None:
        self.db_account = AccountInfoDB()

    def check_is_blacklisted(self, uuid: str, server: str) -> bool:
        """Return True if *uuid* is banned on *server*."""
        return bool(self.db_account.get_baned_by_uuid(uuid, server))

    def ban(self, name: str) -> dict:
        """Ban all accounts matching *name* (single match) or return Multiple."""
        return self._set_status(name, 1)

    def unban(self, name: str) -> dict:
        """Unban all accounts matching *name* (single match) or return Multiple."""
        return self._set_status(name, 0)

    def ban_by_index(self, name: str, index: int) -> dict:
        """Ban the account at the 1-based *index* among matches."""
        return self._set_status_by_index(name, index, 1)

    def unban_by_index(self, name: str, index: int) -> dict:
        """Unban the account at the 1-based *index* among matches."""
        return self._set_status_by_index(name, index, 0)

    def _set_status(self, name: str, status: int) -> dict:
        """Set ``baned`` flag for a uniquely-matched *name*."""
        accounts = self.db_account.get_account_by_name(name.lower())
        if not accounts:
            return {"msg": "NotFound"}
        if len(accounts) == 1:
            row = accounts[0]
            uuid, _, server, baned = row
            if baned == status:
                return {"msg": "Already"}
            self.db_account.set_account_baned(uuid, server, status)
            return {"msg": "Success", "data": row}
        return {"msg": "Multiple", "data": accounts}

    def _set_status_by_index(self, name: str, index: int,
                             status: int) -> dict:
        """Set ``baned`` flag for a specific index among matches."""
        accounts = self.db_account.get_account_by_name(name.lower())
        if not accounts or index < 1 or index > len(accounts):
            return {"msg": "IndexError"}
        row = accounts[index - 1]
        uuid, _, server, baned = row
        if baned == status:
            return {"msg": "Already"}
        self.db_account.set_account_baned(uuid, server, status)
        return {"msg": "Success", "data": row}
