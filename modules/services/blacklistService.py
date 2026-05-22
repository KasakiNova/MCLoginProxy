# coding=utf-8
from modules.database.accountInfoDB import AccountInfoDB


class BlacklistService:
    def __init__(self):
        self.db_account = AccountInfoDB()

    def check_is_blacklisted(self, uuid, server):
        if self.db_account.get_baned_by_uuid(uuid, server):
            return True
        else:
            return False

    def ban(self, name: str):
        return self._set_status(name, 1)

    def unban(self, name: str):
        return self._set_status(name, 0)

    def ban_by_index(self, name: str, index: int):
        return self._set_status_by_index(name, index, 1)

    def unban_by_index(self, name: str, index: int):
        return self._set_status_by_index(name, index, 0)

    def _set_status(self, name: str, status: int):
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
        else:
            return {"msg": "Multiple", "data": accounts}

    def _set_status_by_index(self, name: str, index: int, status: int):
        accounts = self.db_account.get_account_by_name(name.lower())
        if not accounts or index < 1 or index > len(accounts):
            return {"msg": "IndexError"}
        row = accounts[index - 1]
        uuid, _, server, baned = row
        if baned == status:
            return {"msg": "Already"}
        self.db_account.set_account_baned(uuid, server, status)
        return {"msg": "Success", "data": row}