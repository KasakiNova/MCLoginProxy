# coding=utf-8
"""Query upstream Yggdrasil auth servers for player profiles.

Iterates over configured servers (Mojang and Blessing Skin types),
fetches ``hasJoined`` data, checks the local blacklist, and records
new accounts in the SQLite database.
"""
import threading
from typing import TypedDict

import requests

import modules.globalVariables as gVar
from modules.Errors import FailureToFetchProfile, PlayerIsBaned
from modules.database.accountInfoDB import AccountInfoDB
from modules.services.blacklistService import BlacklistService
from modules.utils.logger import info, error, warning, debug as log_debug


class MsgType(TypedDict):
    status: bool
    data: dict


class HasJoinedService:
    """Service that proxies Minecraft ``hasJoined`` requests."""

    def __init__(self) -> None:
        self.__username = ""
        self.__server_id = ""
        self.__proxy_enable = gVar.cfgContext['Proxy']['enable']
        self.__proxies = gVar.proxies
        self.blacklist = BlacklistService()
        self.account_db = AccountInfoDB()

    def get_profile(self, username: str, server_id: str) -> dict | None:
        """Query all configured auth servers for *username* and *server_id*.

        Returns the first un-banned profile dict, or None.
        """
        self.__username = username
        self.__server_id = server_id
        servers = gVar.cfgContext["Server"]

        for dict_server_id, serial in servers.items():
            server_type = serial['ServerType'].lower()

            if server_type in {"mojang", "official"}:
                url = (
                    f"https://sessionserver.mojang.com"
                    f"/session/minecraft/hasJoined"
                    f"?username={username}&serverId={server_id}"
                )
            elif server_type == "blessing":
                url = (
                    f"{serial['Url']}/sessionserver/session/minecraft/"
                    f"hasJoined?username={username}&serverId={server_id}"
                )
            else:
                continue

            result = self._try_server(
                url, serial['NeedProxy'], serial['Name'], dict_server_id
            )
            if result is not None:
                return result

        warning(f"Unable to get player {username} profile from All server")
        return None

    def _try_server(self, url: str, need_proxy: bool,
                    server_name: str, server_id: str) -> dict | None:
        """Request one auth server and check profile / ban status.

        Returns:
            Profile dict on success, None to try next server, or a
            sentinel ``False`` (returned as None to caller) when the
            player is banned.
        """
        msg = self._request(url, need_proxy)
        if not msg['status']:
            error(
                f"Unable to get {self.__username} profile "
                f"from {server_name} server"
            )
            return None

        if not self.check_profile(msg, server_id):
            warning(f"Player {self.__username} has baned")
            return None

        info(
            f"Successfully fetched player {self.__username} "
            f"in {server_name} server"
        )
        return msg['data']

    def check_profile(self, msg: MsgType, server_id: str) -> bool:
        """Check if *msg* is valid and the player is not blacklisted.

        If the player passes, asynchronously record the account.
        """
        if not msg['status']:
            return False
        if gVar.debugMode:
            log_debug(str(msg['data']))
        if self.blacklist.check_is_blacklisted(msg['data']['id'], server_id):
            return False
        self._record_account(
            msg['data']['name'],
            msg['data']['id'],
            server_id
        )
        return True

    def _request(self, url: str, proxy: bool) -> dict:
        """Perform an HTTP GET, optionally through the configured proxy.

        Returns a ``{'status': bool, 'data': dict}``-shaped dict.
        """
        try:
            if proxy and self.__proxy_enable:
                response = requests.get(
                    url, proxies=self.__proxies, timeout=10
                )
            else:
                response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return {'status': False}
            return {'status': True, 'data': response.json()}
        except requests.exceptions.RequestException:
            return {'status': False}

    def _record_account(self, name: str, uuid: str,
                        server: str) -> None:
        """Upsert an account row in a background thread."""
        def _work():
            if self.account_db.check_uuid_exists(uuid, server):
                if self.account_db.get_name_by_uuid(uuid, server) != name.lower():
                    self.account_db.update_account_name(
                        uuid, server, name.lower()
                    )
            else:
                self.account_db.insert_account(uuid, name.lower(), server)

        thread = threading.Thread(target=_work)
        thread.daemon = True
        thread.start()
