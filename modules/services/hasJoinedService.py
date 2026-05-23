# coding=utf-8
import threading
from typing import TypedDict

import requests

import modules.globalVariables as gVar
from modules.Errors import FailureToFetchProfile, PlayerIsBaned
from modules.database.accountInfoDB import AccountInfoDB
from modules.services.blacklistService import BlacklistService
from modules.utils.logger import info, error, warning, debug as log_debug


session = requests.Session()
session.trust_env = False


class MsgType(TypedDict):
    status: bool
    data: dict


class HasJoinedService:
    def __init__(self):
        self.__username = ""
        self.__server_id = ""
        self.__proxy_enable = gVar.cfgContext['Proxy']['enable']
        self.__proxies = gVar.proxies
        self.blacklist = BlacklistService()
        self.account_db = AccountInfoDB()

    def get_profile(self, username: str, server_id: str):
        self.__username = username
        self.__server_id = server_id
        servers = gVar.cfgContext["Server"]
        # Use a for loop to iterate through the server list
        for dict_server_id, serial in servers.items():
            # If ServerType is about mojang or official, running this
            if serial['ServerType'].lower() in {"mojang", "official"}:
                try:
                    msg: MsgType = self.request_mojang(serial['NeedProxy'])
                    if msg['status'] is False:
                        raise FailureToFetchProfile(
                            f"Unable to get {username} profile from {serial['Name']} server")
                    is_allowed = self.check_profile(msg, dict_server_id)
                    if is_allowed:
                        info(f"Successfully fetched player {self.__username} in {serial['Name']} server")
                        return msg['data']
                    else:
                        raise PlayerIsBaned(
                            f"Player {username} has baned"
                        )
                except FailureToFetchProfile as e:
                    error(str(e))
                    continue
                except PlayerIsBaned as e:
                    warning(str(e))
                    return None
            elif serial['ServerType'].lower() in {"blessing"}:
                try:
                    msg: MsgType = self.request_blessing(serial['Url'], serial['NeedProxy'])
                    if msg['status'] is False:
                        raise FailureToFetchProfile(
                            f"Unable to get {username} profile from {serial['Name']} server")
                    is_allowed = self.check_profile(msg, dict_server_id)
                    if is_allowed:
                        info(f"Successfully fetched player {self.__username} in {serial['Name']} server")
                        return msg['data']
                    else:
                        raise PlayerIsBaned(
                            f"Player {username} has baned"
                        )
                except FailureToFetchProfile as e:
                    error(str(e))
                    continue
                except PlayerIsBaned as e:
                    warning(str(e))
                    return None
        warning(f"Unable to get player {username} profile from All server")
        return None


    # Enter the self.request_* dictionary and the server id in the configuration file
    # to try to determine whether the account is banned.
    # If it is not banned, try to add it to the database
    def check_profile(self, msg: MsgType, server_id) -> bool:
        if not msg['status']:
            return False
        if gVar.debugMode:
            log_debug(str(msg['data']))
        if self.blacklist.check_is_blacklisted(msg['data']['id'], server_id):
            return False
        self.try_to_add_account_to_db_thread(
            msg['data']['name'],
            msg['data']['id'],
            server_id
        )
        return True


    # request_tool use to requests.get, but support proxy
    def request_tool(self, url, proxy) -> dict:
        if proxy and self.__proxy_enable:
            response = requests.get(url, proxies=self.__proxies)
        else:
            response = requests.get(url=url)
        if response.status_code != 200:
            return {'status': False}
        return_msg: MsgType = {'status': True, 'data': response.json()}
        return return_msg


    # Request Mojang official session server
    # insert username and serverId build full url
    def request_mojang(self, proxy: bool):
        # this is mojang official session server
        domain = "https://sessionserver.mojang.com"
        # build request hasJoined Link
        url = f"{domain}/session/minecraft/hasJoined?username={self.__username}&serverId={self.__server_id}"
        # use request_tool to request
        return self.request_tool(url, proxy)


    # Request blessing skin server Yggdrasil API session server
    # insert username and serverId build full url
    def request_blessing(self, i_url, proxy: bool):
        # just build blessing skin server Yggdrasil API link
        url = f"{i_url}/sessionserver/session/minecraft/hasJoined?username={self.__username}&serverId={self.__server_id}"
        return self.request_tool(url, proxy)


    #Create a new thread to try to add the account to the database.
    # If it already exists, do nothing.
    # If it already exists but the player name has changed, update the name
    def try_to_add_account_to_db_thread(self, name, uuid, server):
        """Try to add account to accountDB thread"""
        def try_thread():
            if self.account_db.check_uuid_exists(uuid, server):
                if self.account_db.get_name_by_uuid(uuid, server) != name.lower():
                    self.account_db.update_account_name(uuid, name.lower())
            else:
                self.account_db.insert_account(uuid, name.lower(), server)
        # this well be created a new thread
        try_add_thread = threading.Thread(target=try_thread)
        try_add_thread.daemon=True
        try_add_thread.start()

